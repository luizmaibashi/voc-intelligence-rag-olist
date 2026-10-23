"""Mede a busca híbrida (MiniLM + TF-IDF por RRF) contra a busca do produto (spec 0014).

Quatro passos, cada um com saída própria:
1. `origem`: top-100 da busca do produto (densa, sem filtro, mesmo cache de vetores do CLI)
   e do TF-IDF do pooling, nas perguntas do gabarito. Grava hibrida_origem.csv e o tempo
   de cada braço em hibrida_latencia.csv. Único passo que precisa de corpus e pesos MiniLM;
   não edita nenhum arquivo coberto pelo hash de liberação.
2. `planilha`: avaliações inéditas do top-10 de densa, TF-IDF e híbrida, mais âncoras.
3. `formulario`: página local de julgamento cego (data/processed, fora do Git).
4. `medir`: P@10, RR e revocação relativa ao pool por braço e o critério de adoção.

Fusão, planilha e medição leem só CSV: rodam sem corpus, modelo, DuckDB ou sklearn.
Junção por texto em minúsculas, como no ganho_filtros: a busca agrupa textos iguais.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.eval.ganho_filtros import _rotulos
from src.eval.metricas import ic_bootstrap, ic_diferenca_pareada

RAIZ = Path(__file__).resolve().parents[2]
PASTA = RAIZ / "data" / "eval"
ORIGEM = PASTA / "hibrida_origem.csv"
LATENCIA = PASTA / "hibrida_latencia.csv"
PLANILHA = PASTA / "julgamento_hibrida.csv"
FORMULARIO = RAIZ / "data" / "processed" / "julgamento_hibrida_local.html"

# Congelados na spec 0014 antes de rodar; mudar aqui exige mudar a spec.
PROFUNDIDADE = 100
K_RRF = 60
TOP_K = 10
SEMENTE = 42
ANCORAS_POR_PERGUNTA = 2
CRITERIO = {"ganho_mrr_min": 0.03, "ganho_p10_min": 0.0, "perda_p10_max_pergunta": 0.2,
            "latencia_extra_max_s": 1.0}

COLUNAS_ORIGEM = ["id_pergunta", "braco", "posicao", "review_id", "texto", "nota",
                  "freq_texto", "score"]
COLUNAS_PLANILHA = ["id_pergunta", "pergunta", "review_id", "nota", "freq_texto", "texto", "relevante"]
CRITERIO_GERAL = ("Sim se a avaliação ajuda a responder a pergunta, como no seu julgamento "
                  "de setembro. Não se fala de outro assunto ou só tangencia o tema.")


def _com_chave(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(chave=df.texto.str.lower())


def perguntas_avaliadas(perguntas: pd.DataFrame) -> pd.DataFrame:
    """Mesmo recorte do pooling: perguntas sem resposta ficam fora da recuperação."""
    return perguntas.loc[perguntas.tipo.ne("sem_resposta")].copy()


def gerar_origem(corpus: pd.DataFrame, perguntas: pd.DataFrame, modelo, vetores: np.ndarray,
                 profundidade: int = PROFUNDIDADE) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Top-N densa (busca do produto) e TF-IDF (configuração do pooling), com tempos."""
    import time

    import duckdb
    from sklearn.feature_extraction.text import TfidfVectorizer

    from src.retrieval.indice import buscar, codificar_pergunta, criar_indice

    freq = corpus.set_index("review_id").freq_texto
    # TF-IDF do pooling: um documento por texto distinto, primeira ocorrência.
    distintos = corpus[~corpus.texto.str.lower().duplicated()].reset_index(drop=True)
    inicio = time.perf_counter()
    tfidf = TfidfVectorizer(strip_accents="unicode", lowercase=True)
    mat_d = tfidf.fit_transform(distintos.texto)
    ajuste_s = time.perf_counter() - inicio

    linhas, tempos = [], []
    with duckdb.connect() as con:
        criar_indice(con, corpus, vetores)
        for pid, texto in zip(perguntas.id_pergunta, perguntas.pergunta):
            t0 = time.perf_counter()
            densa = buscar(con, codificar_pergunta(modelo, texto), k=profundidade)
            t1 = time.perf_counter()
            scores = (mat_d @ tfidf.transform([texto]).T).toarray().ravel()
            ordem = [i for i in np.argsort(-scores, kind="stable")[:profundidade] if scores[i] > 0]
            t2 = time.perf_counter()
            for pos, linha in enumerate(densa.itertuples(), start=1):
                linhas.append((pid, "densa", pos, linha.review_id, linha.texto, linha.nota,
                               freq.loc[linha.review_id], float(linha.score)))
            for pos, i in enumerate(ordem, start=1):
                doc = distintos.iloc[i]
                linhas.append((pid, "tfidf", pos, doc.review_id, doc.texto, doc.nota,
                               doc.freq_texto, float(scores[i])))
            tempos.append((pid, t1 - t0, t2 - t1, ajuste_s))
    return (pd.DataFrame(linhas, columns=COLUNAS_ORIGEM),
            pd.DataFrame(tempos, columns=["id_pergunta", "densa_s", "tfidf_consulta_s", "tfidf_ajuste_s"]))


def fundir(origem: pd.DataFrame, k_rrf: int = K_RRF, profundidade: int = PROFUNDIDADE) -> pd.DataFrame:
    """RRF por posição: cada texto soma 1/(k + posição) em cada lista onde aparece."""
    listas = _com_chave(origem[origem.braco.isin(["densa", "tfidf"]) & (origem.posicao <= profundidade)])
    if listas.duplicated(["id_pergunta", "braco", "chave"]).any():
        raise ValueError("texto repetido dentro de uma lista")
    listas = listas.assign(contrib=1 / (k_rrf + listas.posicao))
    linhas = []
    for pid, grupo in listas.groupby("id_pergunta"):
        # Representante da densa quando o texto aparece nas duas: é o review_id do produto.
        rep = grupo.sort_values(["braco", "posicao"]).drop_duplicates("chave").set_index("chave")
        soma = (grupo.groupby("chave").agg(score=("contrib", "sum"), melhor=("posicao", "min"))
                .reset_index().sort_values(["score", "melhor", "chave"], ascending=[False, True, True]))
        for pos, linha in enumerate(soma.head(profundidade).itertuples(), start=1):
            r = rep.loc[linha.chave]
            linhas.append((pid, "hibrida", pos, r.review_id, r.texto, r.nota, r.freq_texto,
                           float(linha.score)))
    return pd.DataFrame(linhas, columns=COLUNAS_ORIGEM)


def bracos(origem: pd.DataFrame) -> pd.DataFrame:
    return pd.concat([origem, fundir(origem)], ignore_index=True)


def montar_planilha(origem: pd.DataFrame, julgamento: pd.DataFrame, julgamento_filtros: pd.DataFrame,
                    perguntas: pd.DataFrame, ancoras_por_pergunta: int = ANCORAS_POR_PERGUNTA,
                    semente: int = SEMENTE, k: int = TOP_K) -> pd.DataFrame:
    """Inéditas do top-k dos três braços + âncoras de setembro; sem braço nem julgamento antigo."""
    topo = _com_chave(bracos(origem).query("posicao <= @k"))
    julgados = set(zip(_com_chave(julgamento).id_pergunta, _com_chave(julgamento).chave))
    julgados |= set(zip(_com_chave(julgamento_filtros).id_pergunta, _com_chave(julgamento_filtros).chave))
    ineditas = topo[[(p, c) not in julgados for p, c in zip(topo.id_pergunta, topo.chave)]]
    ineditas = ineditas.drop_duplicates(["id_pergunta", "chave"])
    ineditas = ineditas.assign(pergunta=ineditas.id_pergunta.map(perguntas.set_index("id_pergunta").pergunta))
    ancoras = (julgamento[julgamento.id_pergunta.isin(topo.id_pergunta.unique())]
               .groupby("id_pergunta").sample(ancoras_por_pergunta, random_state=semente))
    planilha = pd.concat([ineditas, ancoras], ignore_index=True)
    planilha = planilha.sample(frac=1, random_state=semente).sort_values("id_pergunta", kind="stable")
    return planilha.assign(relevante="")[COLUNAS_PLANILHA].reset_index(drop=True)


def rotulos_conhecidos(julgamento: pd.DataFrame, julgamento_filtros: pd.DataFrame,
                       novos: pd.DataFrame) -> tuple[pd.Series, dict]:
    """Setembro manda; filtros e híbrida só acrescentam textos inéditos. Âncoras medem a deriva."""
    rotulos = _rotulos(julgamento, "julgamento")
    deriva = {}
    for nome, df in (("julgamento_filtros", julgamento_filtros), ("julgamento_hibrida", novos)):
        recentes = _rotulos(df, nome)
        repetidos = recentes.index.isin(rotulos.index)
        comparados = recentes[repetidos]
        deriva[nome] = {"n": len(comparados),
                        "discordancias": int((comparados != rotulos.loc[comparados.index]).sum())}
        rotulos = pd.concat([rotulos, recentes[~repetidos]])
    return rotulos, deriva


def medir(origem: pd.DataFrame, rotulos: pd.Series, k: int = TOP_K) -> pd.DataFrame:
    """P@k, RR e revocação relativa ao pool conhecido por (pergunta, braço)."""
    topo = _com_chave(bracos(origem).query("posicao <= @k"))
    chaves = pd.MultiIndex.from_arrays([topo.id_pergunta, topo.chave])
    if not chaves.isin(rotulos.index).all():
        raise ValueError("resultado sem julgamento")
    topo = topo.assign(relevante=rotulos.loc[chaves].to_numpy())
    total = rotulos.groupby(level=0).sum()
    linhas = []
    for (pid, braco), grupo in topo.groupby(["id_pergunta", "braco"]):
        pos = grupo.loc[grupo.relevante.eq(1), "posicao"]
        acertos = int(grupo.relevante.sum())
        linhas.append({"id_pergunta": pid, "braco": braco, "precisao": acertos / k,
                       "rr": 1 / pos.min() if len(pos) else 0.0,
                       "revocacao_pool": acertos / total.loc[pid] if total.loc[pid] else float("nan")})
    return pd.DataFrame(linhas)


def avaliar_criterio(tabela: pd.DataFrame, latencia: pd.DataFrame | None = None,
                     criterio: dict = CRITERIO) -> dict:
    """Critério de adoção da spec 0014: os quatro itens precisam passar."""
    p = tabela.pivot(index="id_pergunta", columns="braco", values="precisao")
    r = tabela.pivot(index="id_pergunta", columns="braco", values="rr")
    dp, dr = p.hibrida - p.densa, r.hibrida - r.densa
    eps = 1e-9
    itens = {
        "ganho_mrr": (float(dr.mean()), dr.mean() >= criterio["ganho_mrr_min"] - eps),
        "ganho_p10": (float(dp.mean()), dp.mean() >= criterio["ganho_p10_min"] - eps),
        "pior_pergunta_p10": (float(dp.min()), dp.min() >= -criterio["perda_p10_max_pergunta"] - eps),
    }
    if latencia is not None:
        # No CLI cada pergunta é um processo: o ajuste do TF-IDF entra em toda execução.
        extra = float((latencia.tfidf_consulta_s + latencia.tfidf_ajuste_s).median())
        itens["latencia_extra_s"] = (extra, extra <= criterio["latencia_extra_max_s"] + eps)
    return {nome: {"valor": round(v, 4), "passa": bool(ok)} for nome, (v, ok) in itens.items()} | {
        "adota": all(ok for _, ok in itens.values()) and latencia is not None}


def _exemplo_sorteado(julgamento: pd.DataFrame, pid: str, valor: int, excluir: set,
                      semente: int = SEMENTE) -> str | None:
    candidatos = julgamento[(julgamento.id_pergunta == pid) & (julgamento.relevante.astype(int) == valor)
                            & ~julgamento.texto.str.lower().isin(excluir)]
    return None if candidatos.empty else candidatos.sample(1, random_state=semente).texto.iloc[0]


def montar_formulario(planilha: pd.DataFrame, julgamento: pd.DataFrame) -> str:
    """Reaproveita o modelo da spec 0009; critério próprio só onde a spec 0009 tinha."""
    from src.eval.gerar_formulario_filtros import CRITERIOS, EXEMPLOS, SEM_EXEMPLO_NAO, TEMPLATE, _exemplo

    excluir = set(planilha.texto.str.lower())
    perguntas = {}
    for pid, grupo in planilha.groupby("id_pergunta"):
        sim, nao = EXEMPLOS.get(pid, (None, None))
        try:
            exemplo_sim = _exemplo(julgamento, pid, sim, 1, excluir) if sim else None
            exemplo_nao = _exemplo(julgamento, pid, nao, 0, excluir) if nao else None
        except ValueError:
            # Âncora sorteada coincidiu com o exemplo fixo: o exemplo não pode entregar a resposta.
            exemplo_sim = exemplo_nao = None
        exemplo_sim = exemplo_sim or _exemplo_sorteado(julgamento, pid, 1, excluir) or "(sem exemplo julgado)"
        exemplo_nao = exemplo_nao or _exemplo_sorteado(julgamento, pid, 0, excluir) or SEM_EXEMPLO_NAO
        perguntas[pid] = {"pergunta": grupo.pergunta.iloc[0],
                          "criterio": CRITERIOS.get(pid, CRITERIO_GERAL),
                          "exemplo_sim": exemplo_sim, "exemplo_nao": exemplo_nao}
    itens = planilha.astype(str).to_dict("records")
    versao = hashlib.sha256(json.dumps(itens, ensure_ascii=False).encode()).hexdigest()[:12]
    dados = {"versao": versao, "colunas": list(planilha.columns), "perguntas": perguntas, "itens": itens}

    pagina = TEMPLATE.read_text(encoding="utf-8")
    trocas = [("__DADOS_JSON__", json.dumps(dados, ensure_ascii=False).replace("<", "\\u003c")),
              ("Julgamento dos filtros (spec 0009)", "Julgamento da busca híbrida (spec 0014)"),
              ("<title>Julgamento dos filtros</title>", "<title>Julgamento da busca híbrida</title>"),
              ('"julgamento_filtros_"', '"julgamento_hibrida_"'),
              ('"julgamento_filtros.csv"', '"julgamento_hibrida.csv"')]
    for antigo, novo in trocas:
        if pagina.count(antigo) != 1:
            raise ValueError(f"modelo do formulário mudou: {antigo!r}")
        pagina = pagina.replace(antigo, novo)
    return pagina


def _ler(caminho: Path) -> pd.DataFrame:
    return pd.read_csv(caminho, sep=";", encoding="utf-8-sig", keep_default_na=False)


def _gravar(df: pd.DataFrame, caminho: Path) -> None:
    df.to_csv(caminho, sep=";", index=False, encoding="utf-8-sig")
    print(f"{len(df)} linhas -> {caminho.relative_to(RAIZ)}")


def _imprimir_medicao(tabela: pd.DataFrame, deriva: dict, criterio: dict) -> None:
    for metrica in ("precisao", "rr", "revocacao_pool"):
        print(f"\n{metrica} por pergunta e braço:\n" + tabela.pivot(
            index="id_pergunta", columns="braco", values=metrica).to_string(float_format="{:.2f}".format))
    print(f"\nMédias com IC95% por bootstrap sobre as perguntas (n = {tabela.id_pergunta.nunique()}):")
    for (braco, metrica), grupo in tabela.melt(["id_pergunta", "braco"]).groupby(["braco", "variable"]):
        media, lo, hi = ic_bootstrap(grupo.value.dropna())
        print(f"  {braco:8} {metrica:15} {media:.2f} [{lo:.2f}; {hi:.2f}]")
    for metrica in ("precisao", "rr"):
        largura = tabela.pivot(index="id_pergunta", columns="braco", values=metrica)
        media, lo, hi = ic_diferenca_pareada(largura.hibrida, largura.densa)
        print(f"Diferença pareada híbrida - densa ({metrica}): {media:+.2f} [{lo:+.2f}; {hi:+.2f}]")
    print(f"\nÂncoras: {deriva}")
    print("Critério de adoção (spec 0014): " + json.dumps(criterio, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("acao", choices=["origem", "planilha", "formulario", "medir"])
    args = parser.parse_args()

    if args.acao == "origem":
        from sentence_transformers import SentenceTransformer

        from src.retrieval.cache import vetores_com_cache
        from src.retrieval.indice import DIM, MODELO, carregar_corpus
        corpus = carregar_corpus(RAIZ / "data" / "processed" / "corpus_reviews.parquet")
        perguntas = perguntas_avaliadas(pd.read_csv(PASTA / "perguntas.csv", sep=";"))
        modelo = SentenceTransformer(MODELO, local_files_only=True)
        # Mesmo cache e mesma identidade do CLI (spec 0010): a densa é a busca da demo.
        vetores = vetores_com_cache(RAIZ / "data" / "processed" / "emb_busca_minilm.npy", modelo,
                                    corpus.texto.tolist(), nome_modelo=MODELO, dimensao=DIM)
        origem, tempos = gerar_origem(corpus, perguntas, modelo, vetores)
        _gravar(origem, ORIGEM)
        _gravar(tempos, LATENCIA)
    elif args.acao == "planilha":
        if PLANILHA.exists() and _ler(PLANILHA).relevante.astype(str).str.strip().ne("").any():
            raise SystemExit(f"{PLANILHA.name} já tem julgamentos; não sobrescrevo.")
        _gravar(montar_planilha(_ler(ORIGEM), _ler(PASTA / "julgamento.csv"),
                                _ler(PASTA / "julgamento_filtros.csv"),
                                pd.read_csv(PASTA / "perguntas.csv", sep=";")), PLANILHA)
    elif args.acao == "formulario":
        FORMULARIO.parent.mkdir(parents=True, exist_ok=True)
        FORMULARIO.write_text(montar_formulario(_ler(PLANILHA), _ler(PASTA / "julgamento.csv")),
                              encoding="utf-8")
        print(FORMULARIO)
    else:
        rotulos, deriva = rotulos_conhecidos(_ler(PASTA / "julgamento.csv"),
                                             _ler(PASTA / "julgamento_filtros.csv"), _ler(PLANILHA))
        tabela = medir(_ler(ORIGEM), rotulos)
        _imprimir_medicao(tabela, deriva, avaliar_criterio(tabela, _ler(LATENCIA)))


if __name__ == "__main__":
    main()
