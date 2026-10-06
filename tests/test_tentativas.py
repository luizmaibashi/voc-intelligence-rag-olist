import json
import sys
from pathlib import Path

import httpx
import pytest
from google.genai.errors import APIError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def controlador():
    from src.rag.tentativas import GeradorComTentativas
    return GeradorComTentativas


@pytest.mark.parametrize("erro", [
    *(APIError(c, {"error": {"message": "SEGREDO"}}) for c in [408, 429, 500, 502, 503, 504]),
    httpx.ReadTimeout("SEGREDO"), httpx.ConnectError("SEGREDO"),
    httpx.RemoteProtocolError("SEGREDO"),
])
def test_transitorio_registra_antes_de_esperar_e_preserva_falha(controlador, erro):
    eventos = []
    ordem = []
    chamadas = []
    tempos = iter([1., 1.125, 3.125, 3.5])
    saida = {"status": "respondida", "texto": "Resposta sintética", "review_ids": ["a"]}

    def gerar(*_args):
        chamadas.append(True)
        if len(chamadas) == 1:
            raise erro
        return saida

    def registrar(evento):
        eventos.append(evento)
        ordem.append("registro")

    def esperar(segundos):
        assert segundos == 2
        ordem.append("espera")

    gerar_com_tentativas = controlador(gerar, registrar, esperar=esperar, relogio=lambda: next(tempos))
    assert gerar_com_tentativas("Pergunta", [{"review_id": "a", "texto": "Sintético"}]) == saida
    assert gerar_com_tentativas.tentativas == 2
    assert ordem == ["registro", "espera", "registro"]
    assert [e["tentativa"] for e in eventos] == [1, 2]
    assert eventos[0]["duracao_ms"] == 125
    assert eventos[0]["espera_planejada_s"] == 2
    assert eventos[0]["havera_repeticao"] is True
    assert eventos[0]["erro_integracao"]["classe"] == type(erro).__name__
    assert eventos[1]["duracao_ms"] == 375
    assert eventos[1]["saida_provedor"] == saida
    assert eventos[1]["erro_integracao"] is None
    assert eventos[1]["espera_planejada_s"] == 0
    assert "SEGREDO" not in json.dumps(eventos)


def test_duas_falhas_encerram_sem_terceira(controlador):
    eventos = []
    esperas = []
    erro = httpx.ReadTimeout("SEGREDO")

    def gerar(*_args):
        raise erro

    funcao = controlador(gerar, eventos.append, esperar=esperas.append)
    with pytest.raises(httpx.ReadTimeout):
        funcao("Pergunta", [])
    assert funcao.tentativas == 2
    assert esperas == [2]
    assert [e["havera_repeticao"] for e in eventos] == [True, False]
    assert eventos[-1]["espera_planejada_s"] == 0


class ErroLocal(Exception):
    code = 503


@pytest.mark.parametrize("erro", [
    APIError(400, {"error": {"message": "SEGREDO"}}),
    APIError(401, {"error": {"message": "SEGREDO"}}),
    APIError(404, {"error": {"message": "SEGREDO"}}),
    ErroLocal("SEGREDO"), json.JSONDecodeError("inválido", "x", 0),
])
def test_erro_permanente_ou_local_nao_repete(controlador, erro):
    eventos = []

    def gerar(*_args):
        raise erro

    funcao = controlador(gerar, eventos.append, esperar=lambda *_: pytest.fail("espera indevida"))
    with pytest.raises(type(erro)):
        funcao("Pergunta", [])
    assert funcao.tentativas == 1
    assert len(eventos) == 1
    assert eventos[0]["havera_repeticao"] is False
    assert "SEGREDO" not in json.dumps(eventos)


@pytest.mark.parametrize("saida", [
    {"status": "sem_evidencia", "texto": "Sem suporte", "review_ids": []},
    {"status": [], "texto": "Inválido", "review_ids": []},
    {"status": "respondida", "texto": "Inválido", "review_ids": ["inventado"]},
    None,
])
def test_saida_retornada_nao_repete(controlador, saida):
    eventos = []
    funcao = controlador(lambda *_: saida, eventos.append,
                         esperar=lambda *_: pytest.fail("espera indevida"))
    assert funcao("Pergunta", []) == saida
    assert funcao.tentativas == 1
    assert len(eventos) == 1


def test_saida_nao_serializavel_tem_marcador_seguro(controlador):
    eventos = []
    saida = object()
    assert controlador(lambda *_: saida, eventos.append)("Pergunta", []) is saida
    assert eventos[0]["saida_provedor"] == {"tipo_nao_serializavel": "object"}


def test_falha_de_registro_interrompe_antes_da_repeticao(controlador):
    chamadas = []

    def gerar(*_args):
        chamadas.append(True)
        raise httpx.ReadTimeout("SEGREDO")

    def registrar(_evento):
        raise OSError("Registro indisponível")

    with pytest.raises(OSError):
        controlador(gerar, registrar, esperar=lambda *_: pytest.fail("espera indevida"))("Pergunta", [])
    assert chamadas == [True]


def test_interrupcao_nao_repete(controlador):
    def gerar(*_args):
        raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        controlador(gerar, lambda *_: pytest.fail("não há saída concluída"),
                    esperar=lambda *_: pytest.fail("espera indevida"))("Pergunta", [])


def test_interrupcao_na_espera_preserva_falha_anterior(controlador):
    eventos = []
    chamadas = []

    def gerar(*_args):
        chamadas.append(True)
        raise httpx.ConnectError("SEGREDO")

    def esperar(_segundos):
        raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        controlador(gerar, eventos.append, esperar=esperar)("Pergunta", [])
    assert chamadas == [True]
    assert len(eventos) == 1
    assert eventos[0]["havera_repeticao"] is True
