import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analytics.frequencia import contar_atrasos  # noqa: E402


def test_conta_corpus_elegivel_e_exibe_base_e_periodo():
    corpus = pd.DataFrame({
        "review_id": ["a", "b", "c", "d", "e"],
        "texto": ["a", "b", "c", "d", "e"],
        "situacao_entrega": ["atrasado", "no_prazo", "nao_entregue", "atrasado", "no_prazo"],
        "data_compra": ["2017-01-01", "2017-02-01", "2016-01-01", "2018-03-01", "2018-04-01"],
    })
    resultado = contar_atrasos(corpus)
    referencia = corpus[corpus.situacao_entrega.isin(["atrasado", "no_prazo"])]
    assert resultado.atrasadas == int(referencia.situacao_entrega.eq("atrasado").sum()) == 2
    assert resultado.entregues == len(referencia) == 4
    assert resultado.proporcao == 0.5
    assert resultado.ic95_inf < resultado.proporcao < resultado.ic95_sup
    assert resultado.inicio == "2017-01-01"
    assert resultado.fim == "2018-04-01"
    assert "2 de 4" in resultado.resumo
    assert "2017-01-01" in resultado.resumo and "2018-04-01" in resultado.resumo


@pytest.mark.parametrize("corpus", [
    pd.DataFrame({"review_id": ["a", "a"], "situacao_entrega": ["atrasado", "no_prazo"],
                  "data_compra": ["2017-01-01", "2017-01-02"], "texto": ["a", "b"]}),
    pd.DataFrame({"review_id": ["a"], "situacao_entrega": ["desconhecido"],
                  "data_compra": ["2017-01-01"], "texto": ["a"]}),
    pd.DataFrame({"review_id": ["a"], "situacao_entrega": ["atrasado"],
                  "data_compra": [None], "texto": ["a"]}),
    pd.DataFrame({"review_id": ["a"], "situacao_entrega": ["nao_entregue"],
                  "data_compra": ["2017-01-01"], "texto": ["a"]}),
    pd.DataFrame({"review_id": ["a"], "situacao_entrega": ["atrasado"],
                  "data_compra": ["2017-01-01"], "texto": [""]}),
])
def test_entrada_sem_contrato_falha_visivelmente(corpus):
    with pytest.raises(ValueError):
        contar_atrasos(corpus)
