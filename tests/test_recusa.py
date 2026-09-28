import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.eval.calibrar_recusa import faixa_de_separacao, pontuar  # noqa: E402
from src.eval.pool_candidatos import perguntas_para_pool  # noqa: E402


def test_pontuar_e_detectar_sobreposicao():
    perguntas = pd.DataFrame({"id_pergunta": ["p", "n"], "tem_resposta": ["1", "0"]})
    docs = np.array([[1., 0.], [0., 1.]])
    qs = np.array([[1., 0.], [0.9, 0.1]])
    scores = pontuar(perguntas, docs, qs)
    assert scores.indice_top1.tolist() == [0, 0]
    assert faixa_de_separacao(scores) == pytest.approx((0.9, 1.0))
    scores.loc[1, "score_top1"] = 1.1
    assert faixa_de_separacao(scores) is None


def test_pontuar_exige_uma_embedding_por_pergunta():
    perguntas = pd.DataFrame({"id_pergunta": ["p"], "tem_resposta": ["1"]})
    with pytest.raises(ValueError):
        pontuar(perguntas, np.eye(2), np.eye(2))


def test_negativas_nao_entram_na_regeneracao_do_pool():
    perguntas = pd.DataFrame({"id_pergunta": ["P01", "P15"],
                              "tipo": ["busca", "sem_resposta"]})
    assert perguntas_para_pool(perguntas).id_pergunta.tolist() == ["P01"]
