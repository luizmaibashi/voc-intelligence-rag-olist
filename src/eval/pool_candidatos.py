"""Monta a lista de candidatas para o Luiz julgar (pooling, como no TREC).

Para cada pergunta de data/eval/perguntas.csv, junta o top-k de três buscas:
MiniLM multilíngue, E5-small multilíngue e TF-IDF. A busca aqui é descartável,
só serve para montar o gabarito; a busca do produto é outra.

Julgamento cego: a planilha não diz qual busca trouxe cada candidata e a ordem é
embaralhada, para o julgamento não favorecer um modelo. A origem fica em arquivo à parte.

Limitação conhecida: avaliação relevante que nenhuma das três buscas acha nunca
entra no gabarito, então a revocação medida sai otimista.

Saídas:
- data/eval/julgamento.csv  (Luiz preenche a coluna `relevante` com 1 ou 0)
- data/eval/pool_origem.csv (qual busca trouxe cada candidata, em que posição)
- data/processed/emb_*.npy  (cache dos embeddings, regenerável)
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer

RAIZ = Path(__file__).resolve().parents[2]
CORPUS = RAIZ / "data" / "processed" / "corpus_reviews.parquet"
PERGUNTAS = RAIZ / "data" / "eval" / "perguntas.csv"
JULGAMENTO = RAIZ / "data" / "eval" / "julgamento.csv"
ORIGEM = RAIZ / "data" / "eval" / "pool_origem.csv"

TOP_K = 10
SEMENTE = 42

# E5 foi treinado com prefixos diferentes para pergunta e documento.
MODELOS = {
    "minilm": ("paraphrase-multilingual-MiniLM-L12-v2", "", ""),
    "e5": ("intfloat/multilingual-e5-small", "query: ", "passage: "),
}


def textos_distintos() -> pd.DataFrame:
    corpus = pd.read_parquet(CORPUS)
    # Mesma chave de repetição do corpus.py (texto em minúsculas).
    distintos = corpus[~corpus.texto.str.lower().duplicated()]
    return distintos[["review_id", "texto", "nota", "freq_texto"]].reset_index(drop=True)


def embeddings_docs(nome: str, modelo: SentenceTransformer, prefixo: str, textos: list[str]) -> np.ndarray:
    cache = RAIZ / "data" / "processed" / f"emb_{nome}.npy"
    if cache.exists():
        emb = np.load(cache)
        if len(emb) == len(textos):
            return emb
    emb = modelo.encode([prefixo + t for t in textos], batch_size=128,
                        normalize_embeddings=True, show_progress_bar=True)
    np.save(cache, emb)
    return emb


def top_k(scores: np.ndarray) -> np.ndarray:
    return np.argsort(-scores)[:TOP_K]


def perguntas_para_pool(perguntas: pd.DataFrame) -> pd.DataFrame:
    """Preserva o pool julgado; negativas são avaliadas separadamente."""
    return perguntas.loc[perguntas.tipo.ne("sem_resposta")].copy()


def main() -> None:
    docs = textos_distintos()
    perguntas = perguntas_para_pool(pd.read_csv(PERGUNTAS, sep=";"))
    textos = docs.texto.tolist()
    achados = []  # (id_pergunta, indice_doc, busca, posicao, score)

    for nome, (hf, pref_q, pref_d) in MODELOS.items():
        modelo = SentenceTransformer(hf)
        emb_d = embeddings_docs(nome, modelo, pref_d, textos)
        emb_q = modelo.encode([pref_q + p for p in perguntas.pergunta], normalize_embeddings=True)
        for pid, q in zip(perguntas.id_pergunta, emb_q):
            scores = emb_d @ q
            for pos, i in enumerate(top_k(scores), start=1):
                achados.append((pid, i, nome, pos, float(scores[i])))

    tfidf = TfidfVectorizer(strip_accents="unicode", lowercase=True)
    mat_d = tfidf.fit_transform(textos)
    mat_q = tfidf.transform(perguntas.pergunta)
    for pid, linha in zip(perguntas.id_pergunta, mat_q):
        scores = (mat_d @ linha.T).toarray().ravel()
        for pos, i in enumerate(top_k(scores), start=1):
            if scores[i] > 0:
                achados.append((pid, i, "tfidf", pos, float(scores[i])))

    origem = pd.DataFrame(achados, columns=["id_pergunta", "idx", "busca", "posicao", "score"])
    origem["review_id"] = docs.review_id.iloc[origem.idx].values
    origem.drop(columns="idx").to_csv(ORIGEM, sep=";", index=False, encoding="utf-8-sig")

    pool = origem[["id_pergunta", "idx"]].drop_duplicates()
    pool = pool.sample(frac=1, random_state=SEMENTE).sort_values("id_pergunta", kind="stable")
    julg = pool.merge(perguntas[["id_pergunta", "pergunta"]], on="id_pergunta")
    julg = julg.join(docs, on="idx").drop(columns="idx")
    julg["relevante"] = ""
    julg = julg[["id_pergunta", "pergunta", "review_id", "nota", "freq_texto", "texto", "relevante"]]
    julg.to_csv(JULGAMENTO, sep=";", index=False, encoding="utf-8-sig")

    por_pergunta = julg.groupby("id_pergunta").size()
    print(f"{len(julg)} candidatas para julgar ({por_pergunta.min()} a {por_pergunta.max()} por pergunta)")
    print(f"-> {JULGAMENTO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
