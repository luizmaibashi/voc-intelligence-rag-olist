"""Reproduz métricas do pool julgado; revocação é relativa ao pool."""
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]


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
    origem = pd.read_csv(RAIZ / "data/eval/pool_origem.csv", sep=";")
    julgamento = pd.read_csv(RAIZ / "data/eval/julgamento.csv", sep=";")
    metricas = avaliar(origem, julgamento)
    print(resumo(metricas).to_string(index=False, float_format=lambda x: f"{x:.3f}"))
