"""Recria localmente o formulário dos 15 casos P09 ainda pendentes."""

import csv
import json
from pathlib import Path

import pandas as pd


RAIZ = Path(__file__).resolve().parents[2]
ROTULOS = RAIZ / "data/eval/p09_amostra_independente_rotulos.csv"
CORPUS = RAIZ / "data/processed/corpus_reviews.parquet"
TEMPLATE = Path(__file__).with_name("p09_fundamento_template.html")
SAIDA = RAIZ / "data/processed/p09_fundamento_elogio_geral_local.html"


def gerar() -> Path:
    with ROTULOS.open(encoding="utf-8-sig", newline="") as arquivo:
        rotulos = list(csv.DictReader(arquivo, delimiter=";"))
    ids = [
        linha["review_id"]
        for linha in rotulos
        if linha["tema"] == "elogio_geral"
        and linha["rotulo_final"] == "sim"
        and linha["previsao_regra"] == "nao"
    ]
    if len(ids) != 15 or len(set(ids)) != 15:
        raise ValueError("A seleção pendente de P09 não contém 15 IDs únicos.")

    corpus = pd.read_parquet(CORPUS, columns=["review_id", "texto"])
    textos = corpus.set_index("review_id")["texto"]
    if any(identificador not in textos.index for identificador in ids):
        raise ValueError("Há IDs pendentes ausentes no corpus local.")
    casos = [
        {"n": posicao, "id": identificador, "texto": textos.loc[identificador]}
        for posicao, identificador in enumerate(ids, start=1)
    ]
    dados = json.dumps(casos, ensure_ascii=False).replace("<", "\\u003c")
    modelo = TEMPLATE.read_text(encoding="utf-8")
    if modelo.count("__ROWS_JSON__") != 1:
        raise ValueError("Modelo do formulário sem marcador único de dados.")
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(modelo.replace("__ROWS_JSON__", dados), encoding="utf-8")
    return SAIDA


if __name__ == "__main__":
    print(gerar())
