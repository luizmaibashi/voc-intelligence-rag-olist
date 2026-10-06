"""Inspeciona sobreposição de scores; não fixa corte com este conjunto pequeno."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

from src.retrieval.indice import MODELO
from src.eval.pool_candidatos import embeddings_docs, textos_distintos

RAIZ = Path(__file__).resolve().parents[2]


def verificar_cache(modelo: SentenceTransformer, docs: pd.DataFrame,
                    vetores: np.ndarray) -> None:
    if len(vetores) != len(docs) or vetores.shape[1] != 384:
        raise ValueError("cache incompatível com tamanho do corpus ou do modelo")
    indices = sorted({0, len(docs) // 2, len(docs) - 1})
    amostra = modelo.encode(docs.texto.iloc[indices].tolist(), normalize_embeddings=True)
    if not np.allclose(amostra, vetores[indices], atol=1e-4):
        raise ValueError("cache não corresponde aos textos e ao modelo")


def pontuar(perguntas: pd.DataFrame, vetores: np.ndarray,
            vetores_perguntas: np.ndarray) -> pd.DataFrame:
    if len(perguntas) != len(vetores_perguntas):
        raise ValueError("uma embedding por pergunta é necessária")
    scores = vetores @ vetores_perguntas.T
    saida = perguntas[["id_pergunta", "tem_resposta"]].copy()
    saida["score_top1"] = scores.max(axis=0)
    saida["indice_top1"] = scores.argmax(axis=0)
    return saida


def faixa_de_separacao(scores: pd.DataFrame) -> tuple[float, float] | None:
    positivas = scores.loc[scores.tem_resposta.astype(str).eq("1"), "score_top1"]
    negativas = scores.loc[scores.tem_resposta.astype(str).eq("0"), "score_top1"]
    if positivas.empty or negativas.empty:
        raise ValueError("é preciso ter perguntas positivas e negativas confirmadas")
    maior_negativa = float(negativas.max())
    menor_positiva = float(positivas.min())
    return (maior_negativa, menor_positiva) if maior_negativa < menor_positiva else None


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    docs = textos_distintos(RAIZ / "data/processed/corpus_reviews.parquet")
    perguntas = pd.read_csv(RAIZ / "data/eval/perguntas.csv", sep=";", dtype={"tem_resposta": str})
    modelo = SentenceTransformer(MODELO)
    vetores = embeddings_docs("minilm", modelo, "", docs.texto.tolist())
    verificar_cache(modelo, docs, vetores)
    q = modelo.encode(perguntas.pergunta.tolist(), normalize_embeddings=True)
    scores = pontuar(perguntas, vetores, q)
    print(scores.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    # As 14 originais têm ao menos um relevante no pool julgado; rótulo provisório.
    rotulos = scores.copy()
    rotulos.loc[rotulos.tem_resposta.astype(str).eq("?"), "tem_resposta"] = "1"
    faixa = faixa_de_separacao(rotulos)
    if faixa is None:
        print("Scores sobrepostos: um corte único não separa este conjunto.")
    else:
        print(f"Faixa aparente entre {faixa[0]:.3f} e {faixa[1]:.3f}; não calibrada fora da amostra.")


if __name__ == "__main__":
    main()
