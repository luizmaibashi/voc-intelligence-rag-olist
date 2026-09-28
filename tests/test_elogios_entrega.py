import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analytics.elogios_entrega import classificar_elogio  # noqa: E402


@pytest.mark.parametrize(("texto", "temas"), [
    ("A entrega foi muito rápida.", {"prazo_rapidez"}),
    ("Chegou antes do prazo e em perfeitas condições.", {"prazo_rapidez", "integridade"}),
    ("Recebido na data prevista.", {"prazo_rapidez"}),
    ("Chegou em menos de 2 dias.", {"prazo_rapidez"}),
    ("Chegou tudo certinho conforme o pedido.", {"pedido_correto"}),
    ("Entrega excelente!", {"elogio_geral"}),
    ("Produto excelente, mas a entrega demorou.", set()),
    ("A entrega não foi rápida.", set()),
    ("Não chegou no prazo.", set()),
    ("Não chegou em menos de 2 dias.", set()),
    ("Chegou em menos de 500 dias.", set()),
    ("O prazo deveria ser menor.", set()),
    ("Produto excelente e entrega normal.", set()),
    ("Produto ótimo, entrega lenta.", set()),
])
def test_classifica_temas_e_evitar_falso_elogio(texto, temas):
    assert classificar_elogio(texto).temas == frozenset(temas)


def test_preserva_elogio_em_texto_misto():
    rotulo = classificar_elogio("Demorou pela greve. Fora isso, a entrega é bem rápida.")
    assert rotulo.temas == frozenset({"prazo_rapidez"})
    assert rotulo.misto is True


def test_pedido_correto_com_reclamacao_de_demora():
    rotulo = classificar_elogio("O produto chegou conforme o pedido, mas demorou demais.")
    assert rotulo.temas == frozenset({"pedido_correto"})
    assert rotulo.misto is True


@pytest.mark.parametrize(("texto", "tema"), [
    ("Meu produto veio antes do prazo.", "prazo_rapidez"),
    ("Entraga muito antes do prazo.", "prazo_rapidez"),
    ("Entrega boa.", "elogio_geral"),
    ("Rápido demais chegou.", "prazo_rapidez"),
    ("Tudo perfeito desde o produto até a entrega.", "elogio_geral"),
    ("Recebi no prazo estipulado, quanto ao produto não avalio.", "prazo_rapidez"),
    ("Produto recebido conforme anunciado.", "pedido_correto"),
    ("Veio inteiro, contudo a embalagem era arriscada.", "integridade"),
    ("Muito bom atendimento e prazo de entrega.", "prazo_rapidez"),
    ("Excelente processo de compra e entrega.", "elogio_geral"),
    ("Entrega antes do prazo, e não espero pela próxima compra.", "prazo_rapidez"),
])
def test_variacoes_observadas_na_analise_de_erros(texto, tema):
    assert tema in classificar_elogio(texto).temas


def test_veio_antes_e_correto_marca_dois_temas():
    assert classificar_elogio("Veio tudo certinho e antes do prazo.").temas == frozenset(
        {"pedido_correto", "prazo_rapidez"}
    )


@pytest.mark.parametrize("texto", ["", None, 123])
def test_entrada_invalida_falha(texto):
    with pytest.raises(ValueError):
        classificar_elogio(texto)
