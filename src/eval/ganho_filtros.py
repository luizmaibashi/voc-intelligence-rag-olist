"""Mede o ganho dos filtros de metadados na Precisão@10 do MiniLM (spec 0009).

Três passos, cada um com saída em data/eval/:
1. `origem`: roda a busca do produto (`indice.buscar`) com e sem filtro nas perguntas
   da spec e grava o top-10 de cada braço (filtros_origem.csv). Busca local, sem rede.
2. `planilha`: monta julgamento_filtros.csv com as avaliações inéditas do top-10
   filtrado e âncoras já julgadas, embaralhadas, sem dizer de que braço vieram.
3. `medir`: junta julgamento.csv e julgamento_filtros.csv e calcula P@10 por braço.

Junção por texto em minúsculas, não por review_id: a busca filtra antes de agrupar
textos iguais (spec 0005), então o representante de um texto repetido pode mudar.

Limitação: com 5 perguntas, o IC da diferença pareada é só descritivo.
"""
import argparse
from pathlib import Path

import pandas as pd

from src.eval.metricas import ic_diferenca_pareada

RAIZ = Path(__file__).resolve().parents[2]
PASTA = RAIZ / "data" / "eval"
ORIGEM = PASTA / "filtros_origem.csv"
PLANILHA = PASTA / "julgamento_filtros.csv"

TOP_K = 10
SEMENTE = 42
ANCORAS_POR_PERGUNTA = 2

# Congelado na spec 0009 antes de rodar; mudar aqui exige mudar a spec.
FILTROS = {
    ("P01", "primario"): {"situacao_entrega": "atrasado"},
    ("P02", "primario"): {"situacao_entrega": "nao_entregue"},
    ("P09", "primario"): {"nota_min": 4},
    ("P10", "primario"): {"nota_min": 4},
    ("P11", "primario"): {"nota_max": 2},
    ("P01", "exploratorio"): {"nota_max": 2},
    ("P09", "exploratorio"): {"situacao_entrega": "no_prazo"},
}

COLUNAS_PLANILHA = ["id_pergunta", "pergunta", "review_id", "nota", "freq_texto", "texto", "relevante"]


def _com_chave(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(chave=df.texto.str.lower())


def gerar_origem(corpus: pd.DataFrame, perguntas: pd.DataFrame, modelo) -> pd.DataFrame:
    """Top-k de cada braço com a mesma função de busca do produto."""
    import duckdb

    from src.retrieval.indice import buscar, codificar_pergunta, criar_indice, gerar_vetores

    textos = perguntas.set_index("id_pergunta").pergunta
    bracos = {(p, "sem_filtro"): {} for p, _ in FILTROS} | FILTROS
    linhas = []
    with duckdb.connect() as con:
        criar_indice(con, corpus, gerar_vetores(corpus, modelo))
        for (pid, braco), filtro in sorted(bracos.items()):
            achados = buscar(con, codificar_pergunta(modelo, textos.loc[pid]), k=TOP_K, **filtro)
            achados = achados.merge(corpus[["review_id", "freq_texto"]], on="review_id", how="left")
            for pos, linha in enumerate(achados.itertuples(), start=1):
                linhas.append((pid, braco, pos, linha.review_id, linha.texto, linha.nota,
                               linha.freq_texto, float(linha.score)))
    return pd.DataFrame(linhas, columns=["id_pergunta", "braco", "posicao", "review_id",
                                         "texto", "nota", "freq_texto", "score"])


def montar_planilha(origem: pd.DataFrame, julgamento: pd.DataFrame,
                    ancoras_por_pergunta: int = ANCORAS_POR_PERGUNTA,
                    semente: int = SEMENTE) -> pd.DataFrame:
    """Inéditas por texto + âncoras já julgadas; sem braço, situação ou julgamento antigo."""
    origem, julgamento = _com_chave(origem), _com_chave(julgamento)
    julgados = set(zip(julgamento.id_pergunta, julgamento.chave))
    ineditas = origem[[(p, c) not in julgados for p, c in zip(origem.id_pergunta, origem.chave)]]
    ineditas = ineditas.drop_duplicates(["id_pergunta", "chave"])
    perguntas = julgamento.drop_duplicates("id_pergunta").set_index("id_pergunta").pergunta
    ineditas = ineditas.assign(pergunta=ineditas.id_pergunta.map(perguntas))
    ancoras = (julgamento[julgamento.id_pergunta.isin(origem.id_pergunta.unique())]
               .groupby("id_pergunta").sample(ancoras_por_pergunta, random_state=semente))
    planilha = pd.concat([ineditas, ancoras], ignore_index=True)
    planilha = planilha.sample(frac=1, random_state=semente).sort_values("id_pergunta", kind="stable")
    return planilha.assign(relevante="")[COLUNAS_PLANILHA].reset_index(drop=True)


def _rotulos(julgamento: pd.DataFrame, nome: str) -> pd.Series:
    rel = pd.to_numeric(julgamento.relevante.replace("", pd.NA), errors="coerce")
    if rel.isna().any() or not rel.isin([0, 1]).all():
        raise ValueError(f"{nome}: julgamento incompleto ou fora de 0/1")
    df = _com_chave(julgamento).assign(relevante=rel.astype(int))
    if df.duplicated(["id_pergunta", "chave"]).any():
        raise ValueError(f"{nome}: texto julgado duas vezes na mesma pergunta")
    return df.set_index(["id_pergunta", "chave"]).relevante


def medir(origem: pd.DataFrame, julgamento: pd.DataFrame, novos: pd.DataFrame,
          k: int = TOP_K) -> tuple[pd.DataFrame, dict]:
    """P@k, revocação relativa ao pool conhecido e RR por (pergunta, braço)."""
    antigos, recentes = _rotulos(julgamento, "julgamento"), _rotulos(novos, "julgamento_filtros")
    eh_ancora = recentes.index.isin(antigos.index)
    ancoras = recentes[eh_ancora]
    discordancias = int((ancoras != antigos.loc[ancoras.index]).sum())
    rotulos = pd.concat([antigos, recentes[~eh_ancora]])

    origem = _com_chave(origem[origem.posicao <= k])
    chaves = pd.MultiIndex.from_arrays([origem.id_pergunta, origem.chave])
    if not chaves.isin(rotulos.index).all():
        raise ValueError("resultado sem julgamento")
    origem = origem.assign(relevante=rotulos.loc[chaves].to_numpy())
    total = rotulos.groupby(level="id_pergunta").sum()

    linhas = []
    for (pid, braco), grupo in origem.groupby(["id_pergunta", "braco"]):
        grupo = grupo.sort_values("posicao")
        pos = grupo.loc[grupo.relevante.eq(1), "posicao"]
        acertos = int(grupo.relevante.sum())
        linhas.append({"id_pergunta": pid, "braco": braco, "precisao": acertos / k,
                       "revocacao_pool": acertos / total.loc[pid] if total.loc[pid] else float("nan"),
                       "rr": 1 / pos.iloc[0] if len(pos) else 0.0})
    return pd.DataFrame(linhas), {"n": len(ancoras), "discordancias": discordancias}


def _ler(caminho: Path) -> pd.DataFrame:
    return pd.read_csv(caminho, sep=";", encoding="utf-8-sig", keep_default_na=False)


def _gravar(df: pd.DataFrame, caminho: Path) -> None:
    df.to_csv(caminho, sep=";", index=False, encoding="utf-8-sig")
    print(f"{len(df)} linhas -> {caminho.relative_to(RAIZ)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("acao", choices=["origem", "planilha", "medir"])
    args = parser.parse_args()

    if args.acao == "origem":
        from sentence_transformers import SentenceTransformer

        from src.retrieval.indice import MODELO, carregar_corpus
        corpus = carregar_corpus(RAIZ / "data" / "processed" / "corpus_reviews.parquet")
        perguntas = pd.read_csv(PASTA / "perguntas.csv", sep=";")
        modelo = SentenceTransformer(MODELO, local_files_only=True)
        _gravar(gerar_origem(corpus, perguntas, modelo), ORIGEM)
    elif args.acao == "planilha":
        if PLANILHA.exists() and _ler(PLANILHA).relevante.astype(str).str.strip().ne("").any():
            raise SystemExit(f"{PLANILHA.name} já tem julgamentos; não sobrescrevo.")
        _gravar(montar_planilha(_ler(ORIGEM), _ler(PASTA / "julgamento.csv")), PLANILHA)
    else:
        tabela, ancoras = medir(_ler(ORIGEM), _ler(PASTA / "julgamento.csv"), _ler(PLANILHA))
        largura = tabela.pivot(index="id_pergunta", columns="braco", values="precisao")
        print("P@10 por pergunta e braço:\n" + largura.to_string(float_format="{:.1f}".format))
        print("\nRevocação relativa ao pool conhecido:\n" + tabela.pivot(
            index="id_pergunta", columns="braco", values="revocacao_pool"
        ).to_string(float_format="{:.2f}".format))
        media, lo, hi = ic_diferenca_pareada(largura.primario, largura.sem_filtro)
        print(f"\nDiferença pareada primário - sem filtro: {media:+.2f} [{lo:+.2f}; {hi:+.2f}] "
              f"(n = {len(largura)}, IC só descritivo)")
        print(f"Âncoras: {ancoras['discordancias']} discordâncias em {ancoras['n']}")


if __name__ == "__main__":
    main()
