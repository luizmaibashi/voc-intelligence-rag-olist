"""Métricas de avaliação de busca (Precisão@k, Revocação@k, RR) e inferência estatística.

Mede o desempenho dos modelos de recuperação (MiniLM, E5 e TF-IDF) sobre
avaliações de clientes a partir do gabarito montado por pooling:
- precisao_k: fração de itens relevantes retornados no top-k.
- revocacao_k: fração de itens relevantes recuperados sobre o total conhecido.
- rr: inverso da posição (1-based) do primeiro item relevante encontrado.

Limitações conhecidas:
- Revocação relativa ao pool: avaliações relevantes que nenhuma das buscas candidatas
  encontrou ficam fora do gabarito, tornando a revocação medida otimista.
- Intervalos de confiança via bootstrap: calculados por reamostragem sobre as perguntas.
  Como o número de perguntas avaliadas (n) é pequeno, os ICs refletem essa incerteza.
"""
from typing import Mapping
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]


def _validar_relevancias(relevancias) -> list:
    lista = list(relevancias)
    for v in lista:
        if v not in (0, 1):
            raise ValueError(f"Relevância deve ser 0 ou 1, obtido: {v}")
    return lista


def precisao_k(relevancias, k: int = 10) -> float:
    """Calcula a Precisão@k dividindo pelo corte k (mesmo com menos itens)."""
    elems = _validar_relevancias(relevancias)
    return float(sum(elems[:k])) / float(k)


def revocacao_k(relevancias, total_relevantes: int, k: int = 10) -> float:
    """Calcula a Revocação@k em relação ao total de relevantes da pergunta."""
    elems = _validar_relevancias(relevancias)
    if total_relevantes == 0:
        return float("nan")
    return float(sum(elems[:k])) / float(total_relevantes)


def rr(relevancias) -> float:
    """Calcula o Reciprocal Rank (1/posição 1-based do primeiro item relevante)."""
    elems = _validar_relevancias(relevancias)
    for i, val in enumerate(elems, start=1):
        if val == 1:
            return 1.0 / float(i)
    return 0.0


def metricas_por_pergunta(
    pool: pd.DataFrame,
    total_relevantes: Mapping,
    k: int = 10,
) -> pd.DataFrame:
    """Calcula métricas agrupadas por (busca, id_pergunta) ordenadas pela posição."""
    linhas = []
    # Agrupa por busca e pergunta mantendo a ordem observada no DataFrame
    for (busca, id_pergunta), grupo in pool.groupby(["busca", "id_pergunta"], sort=False):
        # Acesso direto sem fallback para lançar KeyError se a pergunta não constar no mapa
        total = total_relevantes[id_pergunta]
        grupo_ordenado = grupo.sort_values("posicao")
        rels = grupo_ordenado["relevante"].tolist()
        linhas.append({
            "busca": busca,
            "id_pergunta": id_pergunta,
            "precisao": precisao_k(rels, k=k),
            "revocacao": revocacao_k(rels, total_relevantes=total, k=k),
            "rr": rr(rels),
        })

    colunas = ["busca", "id_pergunta", "precisao", "revocacao", "rr"]
    return pd.DataFrame(linhas, columns=colunas)


def carregar(pasta: Path) -> tuple[pd.DataFrame, dict]:
    """Carrega pool_origem e julgamento, associando o julgamento humano a cada resultado."""
    pasta = Path(pasta)
    pool_origem = pd.read_csv(pasta / "pool_origem.csv", sep=";", encoding="utf-8")
    julgamento = pd.read_csv(pasta / "julgamento.csv", sep=";", encoding="utf-8")
    # Par julgado duas vezes duplicaria linhas no merge e inflaria as métricas.
    if julgamento.duplicated(["id_pergunta", "review_id"]).any():
        raise ValueError("Par (id_pergunta, review_id) julgado mais de uma vez.")

    merged = pool_origem.merge(
        julgamento[["id_pergunta", "review_id", "relevante"]],
        on=["id_pergunta", "review_id"],
        how="left",
    )

    if merged["relevante"].isna().any():
        raise ValueError("Existem pares no pool de origem sem julgamento correspondente.")

    merged["relevante"] = merged["relevante"].astype(int)
    pool = merged[["id_pergunta", "busca", "posicao", "relevante"]]

    total_relevantes = (
        julgamento.groupby("id_pergunta")["relevante"].sum().astype(int).to_dict()
    )

    return pool, total_relevantes


def ic_bootstrap(
    valores,
    n_boot: int = 10000,
    semente: int = 42,
    alfa: float = 0.05,
) -> tuple[float, float, float]:
    """Estima média e intervalo de confiança percentil via bootstrap com reposição."""
    arr = np.asarray(valores, dtype=float)
    if arr.size == 0:
        raise ValueError("Amostra não pode ser vazia.")
    if np.isnan(arr).any():
        raise ValueError("Amostra não pode conter valores NaN.")

    media = float(np.mean(arr))
    rng = np.random.default_rng(semente)
    reamostras = rng.choice(arr, size=(n_boot, len(arr)), replace=True)
    medias_boot = reamostras.mean(axis=1)

    lo = float(np.percentile(medias_boot, 100.0 * (alfa / 2.0)))
    hi = float(np.percentile(medias_boot, 100.0 * (1.0 - alfa / 2.0)))
    return media, lo, hi


def ic_diferenca_pareada(
    a: pd.Series,
    b: pd.Series,
    **kwargs,
) -> tuple[float, float, float]:
    """Calcula IC bootstrap da diferença pareada alinhando pelo índice de a."""
    if set(a.index) != set(b.index):
        raise ValueError("Os índices das séries devem conter o mesmo conjunto de elementos.")
    b_alinhado = b.loc[a.index]
    diferenca = a - b_alinhado
    return ic_bootstrap(diferenca, **kwargs)


def main() -> None:
    pasta_eval = RAIZ / "data" / "eval"
    pool, total = carregar(pasta_eval)
    tabela = metricas_por_pergunta(pool, total, k=10)

    # Duas casas: com n = 14 perguntas, a terceira casa é ruído.
    print("Métricas por busca (k=10, IC95% por bootstrap sobre as perguntas):")
    for busca in sorted(tabela["busca"].unique()):
        sub = tabela[tabela["busca"] == busca]
        print(f"\nBusca: {busca}")
        for metrica in ["precisao", "revocacao", "rr"]:
            valores = sub[metrica].dropna().values
            # Revocação é NaN em pergunta sem resposta: sai do cálculo, mas o n mostra.
            fora = len(sub) - len(valores)
            aviso = f", {fora} sem relevante fora" if fora else ""
            media, lo, hi = ic_bootstrap(valores)
            print(f"  {metrica:10s}: {media:.2f} [{lo:.2f}; {hi:.2f}] (n = {len(valores)}{aviso})")

    if "minilm" in tabela["busca"].values and "e5" in tabela["busca"].values:
        s_minilm = tabela[tabela["busca"] == "minilm"].set_index("id_pergunta")["precisao"]
        s_e5 = tabela[tabela["busca"] == "e5"].set_index("id_pergunta")["precisao"]
        diff_media, diff_lo, diff_hi = ic_diferenca_pareada(s_minilm, s_e5)
        print("\nDiferença pareada de precisão (minilm - e5):")
        print(f"  precisao  : {diff_media:+.2f} [{diff_lo:+.2f}; {diff_hi:+.2f}] (n = {len(s_minilm)})")


def avaliar(origem: pd.DataFrame, julgamento: pd.DataFrame, k: int = 10) -> pd.DataFrame:
    if k < 1:
        raise ValueError("k deve ser positivo")
    chave = ["id_pergunta", "review_id"]
    if julgamento.duplicated(chave).any() or julgamento.relevante.isna().any():
        raise ValueError("julgamento duplicado ou incompleto")
    if not julgamento.relevante.isin([0, 1]).all():
        raise ValueError("relevante deve ser 0 ou 1")
    if origem.duplicated(["id_pergunta", "busca", "posicao"]).any():
        raise ValueError("posição duplicada")
    candidatos = origem[origem.posicao <= k].merge(
        julgamento[chave + ["relevante"]], on=chave, how="left", validate="many_to_one"
    )
    if candidatos.relevante.isna().any():
        raise ValueError("resultado sem julgamento")
    totais = julgamento.groupby("id_pergunta").relevante.sum()
    linhas = []
    for (pergunta, busca), grupo in candidatos.groupby(["id_pergunta", "busca"]):
        grupo = grupo.sort_values("posicao")
        pos = grupo.loc[grupo.relevante.eq(1), "posicao"]
        total = int(totais.loc[pergunta])
        linhas.append({"id_pergunta": pergunta, "busca": busca,
                       "precisao": float(grupo.relevante.sum() / k),
                       "revocacao_pool": float(grupo.relevante.sum() / total) if total else np.nan,
                       "mrr": float(1 / pos.iloc[0]) if len(pos) else 0.0})
    return pd.DataFrame(linhas)


def resumo(metricas: pd.DataFrame, n_boot: int = 10000, semente: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(semente)
    linhas = []
    for busca, grupo in metricas.groupby("busca"):
        for metrica in ("precisao", "revocacao_pool", "mrr"):
            valores = grupo[metrica].dropna().to_numpy()
            if not len(valores):
                continue
            amostras = rng.choice(valores, size=(n_boot, len(valores)), replace=True).mean(axis=1)
            linhas.append({"busca": busca, "metrica": metrica, "n": len(valores),
                           "media": valores.mean(), "ic_inf": np.quantile(amostras, .025),
                           "ic_sup": np.quantile(amostras, .975)})
    return pd.DataFrame(linhas)


if __name__ == "__main__":
    main()
