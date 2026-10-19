"""Valida apenas o contrato estrutural; suporte factual exige julgamento humano."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.rag.responder import responder


FONTES = [{"review_id": "r1", "texto": "Chegou atrasado."},
          {"review_id": "r2", "texto": "A caixa veio amassada."}]


def saida(*afirmacoes, status="respondida", limitacao=""):
    return {"status": status, "limitacao": limitacao, "afirmacoes": list(afirmacoes)}


def par(frase, ids):
    return {"frase": frase, "review_ids": ids}


def test_pares_distintos_montam_texto_e_preservam_fontes():
    r = responder("O que ocorreu?", FONTES, lambda *_: saida(
        par("Chegou atrasado.", ["r1", "r1"]), par("A caixa veio amassada.", ["r2"]),
        limitacao="campo ignorado"))
    assert r.status == "respondida"
    assert r.texto == "Chegou atrasado. A caixa veio amassada."
    assert r.afirmacoes == [par("Chegou atrasado.", ["r1"]),
                           par("A caixa veio amassada.", ["r2"])]
    assert r.review_ids == ["r1", "r2"]


@pytest.mark.parametrize("invalida", [par("", ["r2"]), par("x", []),
                                     par("x", ["inventado"]), par("x", [None]),
                                     {"frase": "x"}, "x"])
def test_um_par_invalido_rejeita_resposta_inteira(invalida):
    r = responder("Pergunta", FONTES, lambda *_: saida(par("válida", ["r1"]), invalida))
    assert r.status == "erro_geracao"
    assert r.afirmacoes == []
    assert r.texto != "válida"


def test_recusa_com_afirmacao_e_invalida():
    r = responder("Pergunta", FONTES, lambda *_: saida(
        par("x", ["r1"]), status="sem_evidencia", limitacao="texto livre"))
    assert r.status == "erro_geracao"


def test_recusa_ignora_limitacao_livre():
    r = responder("Pergunta", FONTES, lambda *_: saida(
        status="sem_evidencia", limitacao="Prazo inventado de 30 dias."))
    assert r.status == "sem_evidencia"
    assert "30 dias" not in r.texto
