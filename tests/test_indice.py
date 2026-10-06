import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from retrieval.indice import DIM, buscar, carregar_corpus, criar_indice  # noqa: E402
from eval.metricas import avaliar  # noqa: E402


def vetor(i):
    v = np.zeros(DIM, dtype=np.float32)
    v[i] = 1
    return v


def test_busca_duckdb_igual_numpy_e_filtro():
    docs = pd.DataFrame({"review_id": ["a", "b", "c"], "texto": ["a", "b", "c"],
                         "nota": [1, 5, 4], "situacao_entrega": ["atrasado", "no_prazo", "atrasado"],
                         "categorias": ["x"] * 3})
    emb = np.stack([vetor(0), vetor(1), (vetor(0) + vetor(1)) / np.sqrt(2)])
    q = vetor(0)
    con = duckdb.connect()
    criar_indice(con, docs, emb)
    obtido = buscar(con, q, 3)
    esperado = np.argsort(-(emb @ q))
    assert obtido.review_id.tolist() == docs.review_id.iloc[esperado].tolist()
    np.testing.assert_allclose(obtido.score, (emb @ q)[esperado], atol=1e-6)
    assert buscar(con, q, nota_min=4, situacao_entrega="atrasado").review_id.tolist() == ["c"]
    assert buscar(con, q, nota_max=2).review_id.tolist() == ["a"]
    with pytest.raises(ValueError):
        criar_indice(con, docs, np.zeros_like(emb))
    assert buscar(con, q, 1).review_id.tolist() == ["a"]


def test_vetor_invalido_falha():
    with pytest.raises(ValueError):
        buscar(duckdb.connect(), np.zeros(DIM))


def test_metricas_usam_denominador_k_e_pool():
    origem = pd.DataFrame({"id_pergunta": ["p", "p"], "review_id": ["a", "b"],
                           "busca": ["x", "x"], "posicao": [1, 2]})
    julgamento = pd.DataFrame({"id_pergunta": ["p", "p", "p"],
                               "review_id": ["a", "b", "c"], "relevante": [1, 0, 1]})
    linha = avaliar(origem, julgamento, k=2).iloc[0]
    assert linha.precisao == .5
    assert linha.revocacao_pool == .5
    assert linha.mrr == 1


@pytest.mark.parametrize("inverter", [False, True])
def test_carregamento_preserva_copias_e_busca_filtra_antes_de_deduplicar(tmp_path, inverter):
    docs = pd.DataFrame({"review_id": ["a", "b", "c", "d"],
                         "texto": ["Chegou bem", "chegou bem", "CHEGOU BEM", "Outro relato"],
                         "nota": [1, 5, 4, 5],
                         "situacao_entrega": ["atrasado", "no_prazo", "atrasado", "no_prazo"],
                         "categorias": ["x"] * 4})
    if inverter:
        docs = docs.iloc[::-1]
    caminho = tmp_path / "corpus.parquet"
    docs.to_parquet(caminho, index=False)
    carregados = carregar_corpus(caminho)
    assert len(carregados) == 4
    emb = np.stack([vetor(0) if rid != "d" else vetor(1) for rid in carregados.review_id])
    with duckdb.connect() as con:
        criar_indice(con, carregados, emb)
        assert buscar(con, vetor(0), k=2).review_id.tolist() == ["a", "d"]
        assert buscar(con, vetor(0), nota_min=4, situacao_entrega="no_prazo").review_id.tolist() == ["b", "d"]
        assert buscar(con, vetor(0), nota_min=4, situacao_entrega="atrasado").review_id.tolist() == ["c"]
        assert buscar(con, vetor(0), nota_max=2).review_id.tolist() == ["a"]
        assert buscar(con, vetor(0), nota_min=5, situacao_entrega="atrasado").empty


def test_representante_de_texto_repetido_prioriza_score_antes_do_id():
    docs = pd.DataFrame({"review_id": ["a", "z", "b"],
                         "texto": ["Chegou bem", "CHEGOU BEM", "Outro relato"],
                         "nota": [5, 5, 5], "situacao_entrega": ["no_prazo"] * 3,
                         "categorias": ["x"] * 3})
    emb = np.stack([vetor(1), vetor(0), (vetor(0) + vetor(1)) / np.sqrt(2)])
    with duckdb.connect() as con:
        criar_indice(con, docs, emb)
        obtido = buscar(con, vetor(0), k=2)
        assert obtido.review_id.tolist() == ["z", "b"]
        assert obtido.score.iloc[0] == pytest.approx(1.)
