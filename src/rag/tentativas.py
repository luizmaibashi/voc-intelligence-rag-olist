"""Uma repetição transitória optativa, com registro de cada chamada externa."""
import json
import time

import httpx
from google.genai.errors import APIError

CODIGOS_TRANSITORIOS = (408, 429, 500, 502, 503, 504)
TIPOS_TRANSITORIOS = (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError)


def politica_tentativas() -> dict:
    return {"max_tentativas": 2, "espera_s": 2, "codigos_http": list(CODIGOS_TRANSITORIOS),
            "tipos_excecao": ["google.genai.errors.APIError", "httpx.TimeoutException",
                              "httpx.NetworkError", "httpx.RemoteProtocolError"]}


def _transitorio(erro: Exception) -> bool:
    return ((isinstance(erro, APIError) and type(erro.code) is int
             and erro.code in CODIGOS_TRANSITORIOS) or isinstance(erro, TIPOS_TRANSITORIOS))


def _erro_seguro(erro: Exception) -> dict:
    codigo = getattr(erro, "code", None)
    return {"classe": type(erro).__name__, "codigo": codigo if type(codigo) is int else None,
            "fase": "gerador"}


def _saida_serializavel(saida):
    try:
        json.dumps(saida, allow_nan=False)
        return saida
    except (TypeError, ValueError):
        return {"tipo_nao_serializavel": type(saida).__name__}


class GeradorComTentativas:
    def __init__(self, gerar, registrar, *, esperar=None, relogio=None):
        if not callable(gerar) or not callable(registrar):
            raise ValueError("Gerador e registro precisam ser funções.")
        self.gerar = gerar
        self.registrar = registrar
        self.esperar = time.sleep if esperar is None else esperar
        self.relogio = time.monotonic if relogio is None else relogio
        self.tentativas = 0

    def __call__(self, pergunta: str, evidencias: list[dict]):
        self.tentativas = 0
        for numero in (1, 2):
            inicio = self.relogio()
            self.tentativas = numero
            erro = None
            saida = None
            try:
                saida = self.gerar(pergunta, evidencias)
            except Exception as falha:
                erro = falha
            duracao_ms = round((self.relogio() - inicio) * 1000)
            repetir = erro is not None and numero == 1 and _transitorio(erro)
            # Registro fica fora do catch: falha de gravação não dispara nova chamada.
            self.registrar({"tentativa": numero, "saida_provedor": _saida_serializavel(saida),
                            "erro_integracao": _erro_seguro(erro) if erro is not None else None,
                            "duracao_ms": duracao_ms, "espera_planejada_s": 2 if repetir else 0,
                            "havera_repeticao": repetir})
            if repetir:
                self.esperar(2)
            elif erro is not None:
                raise erro
            else:
                return saida
