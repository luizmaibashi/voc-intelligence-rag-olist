import math
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from eval.metricas import (  # noqa: E402
    carregar,
    ic_bootstrap,
    ic_diferenca_pareada,
    metricas_por_pergunta,
    precisao_k,
    revocacao_k,
    rr,
)

PASTA_EVAL = Path(__file__).resolve().parents[1] / "data" / "eval"


# --- métricas de uma lista ordenada de relevâncias (1 = relevante) ---

def test_precisao_conta_relevantes_no_top_k():
    assert precisao_k([1, 0, 1, 1, 0, 0, 0, 0, 0, 0], k=10) == pytest.approx(0.3)


def test_precisao_divide_por_k_mesmo_com_menos_resultados():
    # Busca que devolve 2 resultados não ganha precisão 1,0 por devolver pouco.
    assert precisao_k([1, 1], k=10) == pytest.approx(0.2)


def test_precisao_ignora_o_que_passa_de_k():
    assert precisao_k([0, 0, 1, 1], k=2) == 0.0


def test_revocacao_relativa_ao_total_de_relevantes():
    assert revocacao_k([1, 0, 1], total_relevantes=4, k=10) == pytest.approx(0.5)


def test_revocacao_sem_relevantes_e_indefinida():
    # Pergunta sem resposta no corpus: revocação não existe, não é 0 nem 1.
    assert math.isnan(revocacao_k([0, 0, 0], total_relevantes=0, k=10))


def test_rr_usa_a_posicao_do_primeiro_relevante():
    assert rr([0, 0, 1, 1]) == pytest.approx(1 / 3)
    assert rr([1, 0]) == 1.0


def test_rr_sem_relevante_e_zero():
    assert rr([0, 0, 0]) == 0.0


@pytest.mark.parametrize("func", [precisao_k, rr])
def test_relevancia_fora_de_0_ou_1_falha(func):
    with pytest.raises(ValueError):
        func([1, 2, 0])


# --- tabela por pergunta ---

def _pool():
    # Ordem das linhas embaralhada de propósito: a posição é que manda.
    return pd.DataFrame({
        "id_pergunta": ["P1", "P1", "P1", "P2", "P2"],
        "busca": ["a", "a", "a", "a", "a"],
        "posicao": [3, 1, 2, 2, 1],
        "relevante": [1, 0, 0, 1, 0],
    })


def test_metricas_por_pergunta_ordena_pela_posicao():
    tabela = metricas_por_pergunta(_pool(), total_relevantes={"P1": 2, "P2": 1}, k=3)
    p1 = tabela.set_index("id_pergunta").loc["P1"]
    assert p1["rr"] == pytest.approx(1 / 3)
    assert p1["precisao"] == pytest.approx(1 / 3)
    assert p1["revocacao"] == pytest.approx(0.5)


def test_metricas_por_pergunta_tem_uma_linha_por_busca_e_pergunta():
    tabela = metricas_por_pergunta(_pool(), total_relevantes={"P1": 2, "P2": 1}, k=3)
    assert set(tabela.columns) >= {"busca", "id_pergunta", "precisao", "revocacao", "rr"}
    assert len(tabela) == 2


def test_metricas_por_pergunta_falha_se_pergunta_sem_total():
    with pytest.raises(KeyError):
        metricas_por_pergunta(_pool(), total_relevantes={"P1": 2}, k=3)


# --- intervalo de confiança por bootstrap sobre as perguntas ---

def test_bootstrap_de_valores_constantes_nao_tem_largura():
    assert ic_bootstrap([0.5, 0.5, 0.5]) == pytest.approx((0.5, 0.5, 0.5))


def test_bootstrap_e_reprodutivel_com_semente_e_contem_a_media():
    valores = [0.1, 0.9, 0.4, 0.7, 0.3]
    media, lo, hi = ic_bootstrap(valores, semente=7)
    assert (media, lo, hi) == ic_bootstrap(valores, semente=7)
    assert media == pytest.approx(0.48)
    assert lo < media < hi


@pytest.mark.parametrize("valores", [[], [0.5, float("nan")]])
def test_bootstrap_recusa_vazio_ou_nan(valores):
    with pytest.raises(ValueError):
        ic_bootstrap(valores)


def test_diferenca_pareada_alinha_pela_pergunta():
    a = pd.Series({"P1": 1.0, "P2": 0.0})
    b = pd.Series({"P2": 0.0, "P1": 0.5})  # mesma pergunta, ordem trocada
    media, lo, hi = ic_diferenca_pareada(a, b)
    assert media == pytest.approx(0.25)


def test_diferenca_pareada_recusa_perguntas_diferentes():
    with pytest.raises(ValueError):
        ic_diferenca_pareada(pd.Series({"P1": 1.0}), pd.Series({"P2": 1.0}))


def _gravar_eval(pasta, julgamento_linhas):
    pd.DataFrame({"id_pergunta": ["P1"], "busca": ["a"], "posicao": [1], "score": [0.9],
                  "review_id": ["r1"]}).to_csv(pasta / "pool_origem.csv", sep=";", index=False)
    pd.DataFrame(julgamento_linhas, columns=["id_pergunta", "review_id", "relevante"]).to_csv(
        pasta / "julgamento.csv", sep=";", index=False)


def test_carregar_recusa_par_sem_julgamento(tmp_path):
    _gravar_eval(tmp_path, [("P1", "outro", 1)])
    with pytest.raises(ValueError):
        carregar(tmp_path)


def test_carregar_recusa_par_julgado_duas_vezes(tmp_path):
    _gravar_eval(tmp_path, [("P1", "r1", 1), ("P1", "r1", 0)])
    with pytest.raises(ValueError):
        carregar(tmp_path)


# --- reprodução do ADR-0002 com o gabarito versionado ---

def test_reproduz_numeros_do_adr_0002():
    pool, total = carregar(PASTA_EVAL)
    medias = metricas_por_pergunta(pool, total, k=10).groupby("busca")[["precisao", "revocacao", "rr"]].mean()
    esperado = {
        "minilm": (0.72, 0.41, 0.79),
        "e5": (0.59, 0.37, 0.79),
        "tfidf": (0.58, 0.32, 0.78),
    }
    for busca, valores in esperado.items():
        assert tuple(medias.loc[busca].round(2)) == valores, busca
