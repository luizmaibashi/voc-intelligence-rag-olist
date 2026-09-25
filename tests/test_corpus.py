import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from preprocessing.corpus import eh_ausencia_mascarada, montar_corpus, montar_texto  # noqa: E402


def test_montar_texto_junta_titulo_e_mensagem_e_normaliza_espacos():
    assert montar_texto("Ótimo", "chegou\r\n  antes   do prazo") == "Ótimo. chegou antes do prazo"


@pytest.mark.parametrize("titulo", ["Excelente.", "Excelente!", "Excelente?"])
def test_montar_texto_nao_duplica_pontuacao_do_titulo(titulo):
    assert montar_texto(titulo, "Produto bom") == f"{titulo} Produto bom"


def test_montar_texto_usa_so_o_que_existe():
    assert montar_texto(None, "não chegou") == "não chegou"
    assert montar_texto("Péssimo", None) == "Péssimo"
    assert montar_texto(None, "   ") == ""


def test_montar_texto_preserva_negacao_acento_e_caixa():
    assert montar_texto(None, "NÃO recomendo") == "NÃO recomendo"


@pytest.mark.parametrize("texto,esperado", [(".", True), ("OK", True), ("-", True),
                                            ("ok, chegou certo", False), ("não", True)])
def test_ausencia_mascarada(texto, esperado):
    assert eh_ausencia_mascarada(texto) is esperado


@pytest.fixture
def tabelas():
    reviews = pd.DataFrame({
        "review_id": ["r1", "r1", "r2", "r3", "r4", "r5"],
        "order_id": ["o1", "o2", "o3", "o4", "o5", "o6"],
        "review_score": [1, 1, 5, 5, 3, 2],
        "review_comment_title": [None, None, None, None, "Demorou", None],
        "review_comment_message": ["não chegou", "não chegou", "muito bom", ".", None, "Muito bom"],
        "review_creation_date": pd.to_datetime(["2018-01-10"] * 6),
    })
    orders = pd.DataFrame({
        "order_id": ["o1", "o2", "o3", "o4", "o5", "o6"],
        "order_status": ["shipped", "shipped", "delivered", "delivered", "delivered", "delivered"],
        "order_purchase_timestamp": pd.to_datetime(["2018-01-01"] * 6),
        "order_delivered_customer_date": pd.to_datetime([None, None, "2018-01-05", "2018-01-05",
                                                         "2018-01-20", "2018-01-05"]),
        "order_estimated_delivery_date": pd.to_datetime(["2018-01-15"] * 6),
    })
    items = pd.DataFrame({"order_id": ["o3", "o3", "o5", "o6"],
                          "product_id": ["p1", "p2", "p1", "p3"]})
    products = pd.DataFrame({"product_id": ["p1", "p2", "p3"],
                             "product_category_name": ["cama_mesa_banho", "beleza_saude", None]})
    return reviews, orders, items, products


def test_corpus_uma_linha_por_review_id(tabelas):
    corpus = montar_corpus(*tabelas)
    assert corpus.review_id.is_unique
    assert "r1" in set(corpus.review_id)


def test_corpus_descarta_sem_texto_e_ausencia_mascarada(tabelas):
    corpus = montar_corpus(*tabelas)
    assert "r3" not in set(corpus.review_id)
    assert corpus.set_index("review_id").loc["r4", "texto"] == "Demorou"


def test_corpus_classifica_entrega(tabelas):
    c = montar_corpus(*tabelas).set_index("review_id")
    assert c.loc["r1", "situacao_entrega"] == "nao_entregue"
    assert c.loc["r2", "situacao_entrega"] == "no_prazo"
    assert c.loc["r4", "situacao_entrega"] == "atrasado"
    assert c.loc["r4", "dias_atraso"] == 5


def test_corpus_junta_categorias_do_pedido(tabelas):
    c = montar_corpus(*tabelas).set_index("review_id")
    assert c.loc["r2", "categorias"] == "beleza_saude|cama_mesa_banho"
    assert c.loc["r5", "categorias"] == "sem_categoria"
    assert c.loc["r1", "categorias"] == "sem_categoria"


def test_corpus_conta_texto_repetido_ignorando_caixa(tabelas):
    c = montar_corpus(*tabelas).set_index("review_id")
    assert c.loc["r2", "freq_texto"] == 2
    assert c.loc["r5", "freq_texto"] == 2
    assert c.loc["r1", "freq_texto"] == 1
