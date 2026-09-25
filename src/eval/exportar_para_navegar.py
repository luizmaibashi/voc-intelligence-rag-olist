"""Exporta o corpus em CSV para o Excel (pt-BR), para montar o gabarito à mão.

Uma linha por texto distinto; `review_id` é um exemplo representativo do texto.
Saída regenerável: data/eval/corpus_navegar.csv (fora do git).
"""
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
ENTRADA = RAIZ / "data" / "processed" / "corpus_reviews.parquet"
SAIDA = RAIZ / "data" / "eval" / "corpus_navegar.csv"

COLUNAS = ["review_id", "nota", "situacao_entrega", "dias_atraso", "categorias", "freq_texto", "texto"]


def main() -> None:
    corpus = pd.read_parquet(ENTRADA)
    # Mesma chave de repetição do corpus.py (texto em minúsculas), para bater com freq_texto.
    distintos = corpus[~corpus.texto.str.lower().duplicated()][COLUNAS]
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    # utf-8-sig e ";" para o Excel em português abrir com acento e colunas certas.
    distintos.to_csv(SAIDA, sep=";", index=False, encoding="utf-8-sig")
    print(f"{len(distintos)} textos distintos -> {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
