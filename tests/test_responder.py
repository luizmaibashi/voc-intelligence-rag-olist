import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import duckdb
import numpy as np
import pandas as pd
import pytest

from src.rag.responder import executar_rag, responder  # noqa: E402
from src.rag.provedor_gemini import GeradorGemini  # noqa: E402
from src.retrieval.indice import DIM, criar_indice  # noqa: E402


EVIDENCIAS = [
    {"review_id": "r1", "texto": "O produto chegou quebrado; pedi troca."},
    {"review_id": "r2", "texto": "A entrega atrasou dois dias."},
]


def test_resposta_cita_id_do_contexto():
    def gerar(pergunta, evidencias):
        return {"status": "respondida", "limitacao": "",
                "afirmacoes": [{"frase": "Há relato de produto quebrado.", "review_ids": ["r1"]}]}

    resposta = responder("Houve produto quebrado?", EVIDENCIAS, gerar)
    assert resposta.status == "respondida"
    assert resposta.review_ids == ["r1"]
    assert resposta.afirmacoes == [{"frase": "Há relato de produto quebrado.", "review_ids": ["r1"]}]


def test_recusa_sem_contexto_nao_chama_modelo():
    def gerar(pergunta, evidencias):
        raise AssertionError("modelo não deve ser chamado")

    assert responder("Qual o prazo oficial?", [], gerar).status == "sem_evidencia"


def test_id_inventado_falha_fechado():
    def gerar(pergunta, evidencias):
        return {"status": "respondida", "limitacao": "",
                "afirmacoes": [{"frase": "Resposta inventada", "review_ids": ["r999"]}]}

    resposta = responder("Pergunta", EVIDENCIAS, gerar)
    assert resposta.status == "erro_geracao"
    assert resposta.review_ids == []


def test_resposta_sem_citacao_falha_fechado():
    def gerar(pergunta, evidencias):
        return {"status": "respondida", "limitacao": "",
                "afirmacoes": [{"frase": "Resposta sem fonte", "review_ids": []}]}

    assert responder("Pergunta", EVIDENCIAS, gerar).status == "erro_geracao"


def test_saida_malformada_falha_fechado():
    assert responder("Pergunta", EVIDENCIAS, lambda *_: {"texto": "x"}).status == "erro_geracao"


@pytest.mark.parametrize("status", [[], {}, None, 1, True, "desconhecido"])
def test_status_fora_do_dominio_retornado_pelo_modelo_falha_fechado(status):
    resposta = responder("Pergunta", EVIDENCIAS,
                         lambda *_: {"status": status, "limitacao": "",
                                     "afirmacoes": [{"frase": "x", "review_ids": ["r1"]}]})
    assert resposta.status == "erro_geracao"
    assert resposta.review_ids == []


def test_id_valido_e_inventado_juntos_falham_fechado():
    gerar = lambda *_: {"status": "respondida", "limitacao": "",
                        "afirmacoes": [{"frase": "x", "review_ids": ["r1", "r999"]}]}
    assert responder("Pergunta", EVIDENCIAS, gerar).status == "erro_geracao"


@pytest.mark.parametrize("citacoes", [["r999"], ["r1", "r999"], [{}], [None]])
def test_recusa_com_citacao_invalida_falha_fechado(citacoes):
    gerar = lambda *_: {"status": "sem_evidencia", "limitacao": "Sem suporte",
                        "afirmacoes": [{"frase": "x", "review_ids": citacoes}]}
    assert responder("Pergunta", EVIDENCIAS, gerar).status == "erro_geracao"


@pytest.mark.parametrize("citacoes", [[], ["r1"]])
def test_recusa_com_citacoes_validas_preserva_mensagem_generica(citacoes):
    gerar = lambda *_: {"status": "sem_evidencia", "limitacao": "Limite do contexto",
                        "afirmacoes": [] if not citacoes else [{"frase": "x", "review_ids": citacoes}]}
    resposta = responder("Pergunta", EVIDENCIAS, gerar)
    assert resposta.status == ("sem_evidencia" if not citacoes else "erro_geracao")
    assert resposta.texto == ("As avaliações recuperadas não sustentam a resposta solicitada."
                             if not citacoes else "Recusa contém afirmações.")
    assert resposta.review_ids == []


def test_falha_do_modelo_nao_vaza_detalhes():
    def gerar(*_):
        raise RuntimeError("segredo-no-erro")

    resposta = responder("Pergunta", EVIDENCIAS, gerar)
    assert resposta.status == "erro_geracao"
    assert "segredo-no-erro" not in resposta.texto


def test_contexto_malformado_recusa_sem_chamar_modelo():
    gerar = lambda *_: (_ for _ in ()).throw(AssertionError("não chamar"))
    assert responder("Pergunta", [{"review_id": ["r1"], "texto": "x"}], gerar).status == "erro_geracao"


def test_politica_oficial_pode_ser_recusada_com_tema_parecido():
    def gerar(pergunta, evidencias):
        assert evidencias[0]["texto"].startswith("O produto")
        return {"status": "sem_evidencia", "limitacao": "Os relatos não informam política oficial.",
                "afirmacoes": []}

    resposta = responder("Qual o prazo oficial de troca?", EVIDENCIAS, gerar)
    assert resposta.status == "sem_evidencia"


def test_recusa_nao_exibe_afirmacao_livre_do_modelo():
    gerar = lambda *_: {"status": "sem_evidencia",
                        "limitacao": "O prazo oficial de troca é 30 dias.",
                        "afirmacoes": []}
    resposta = responder("Qual o prazo oficial de troca?", EVIDENCIAS, gerar)
    assert resposta.status == "sem_evidencia"
    assert resposta.review_ids == []
    assert "30 dias" not in resposta.texto


@pytest.mark.parametrize("modelo,esperado", [
    (None, "gemini-3.1-flash-lite"),
    ("gemini-3.5-flash-lite", "gemini-3.5-flash-lite"),
])
def test_adaptador_envia_contexto_e_schema_sem_rede(modelo, esperado):
    class Models:
        def generate_content(self, **kwargs):
            self.chamada = kwargs
            return type("R", (), {"text": '{"status":"sem_evidencia","limitacao":"Sem prazo oficial.","afirmacoes":[]}'})()

    class Client:
        models = Models()

    client = Client()
    argumentos = {} if modelo is None else {"modelo": modelo}
    saida = GeradorGemini(client=client, contexto_revisado=True, **argumentos)("Qual o prazo oficial?", EVIDENCIAS)
    assert saida["status"] == "sem_evidencia"
    assert '"review_id": "r1"' in client.models.chamada["contents"]
    assert client.models.chamada["config"].response_mime_type == "application/json"
    assert client.models.chamada["model"] == esperado


def test_adaptador_exige_revisao_do_contexto_antes_de_enviar():
    class Models:
        def generate_content(self, **_kwargs):
            raise AssertionError("não enviar")

    class Client:
        models = Models()

    import pytest
    with pytest.raises(ValueError, match="Revise PII"):
        GeradorGemini(client=Client())("Pergunta", EVIDENCIAS)


@pytest.mark.parametrize("motivo,esperado", [("MAX_TOKENS", "truncamento_observado"),
                                             (None, "json_invalido")])
def test_adaptador_registra_json_invalido_sem_inferir_truncamento(motivo, esperado):
    class Models:
        def generate_content(self, **_kwargs):
            candidatos = ([type("C", (), {"finish_reason": type("F", (), {"name": motivo})()})()]
                          if motivo else [])
            return type("R", (), {"text": '{"status":', "candidates": candidatos})()
    class Client:
        models = Models()
    saida = GeradorGemini(client=Client(), contexto_revisado=True)("Pergunta", EVIDENCIAS)
    assert saida == {"_erro_contrato": esperado, "_finish_reason": motivo}


def test_pipeline_embeda_filtra_recupera_e_cita():
    docs = pd.DataFrame({"review_id": ["r1", "r2"], "texto": ["Quebrou", "Chegou bem"],
                         "nota": [1, 5], "situacao_entrega": ["atrasado", "no_prazo"],
                         "categorias": ["vaso", "vaso"]})
    vetores = np.zeros((2, DIM), dtype=np.float32)
    vetores[0, 0] = 1
    vetores[1, 1] = 1
    con = duckdb.connect()
    criar_indice(con, docs, vetores)

    class Modelo:
        def encode(self, pergunta, normalize_embeddings):
            assert normalize_embeddings is True
            assert pergunta == "Houve elogio?"
            return vetores[1]

    def gerar(pergunta, evidencias):
        assert [e["review_id"] for e in evidencias] == ["r2"]
        return {"status": "respondida", "limitacao": "",
                "afirmacoes": [{"frase": "Há elogio à entrega.", "review_ids": ["r2"]}]}

    resposta = executar_rag("Houve elogio?", con, Modelo(), gerar, nota_min=4)
    assert resposta.status == "respondida"
    assert resposta.review_ids == ["r2"]


def test_pipeline_sem_resultados_recusa_sem_gerar():
    docs = pd.DataFrame({"review_id": ["r1"], "texto": ["Quebrou"], "nota": [1],
                         "situacao_entrega": ["atrasado"], "categorias": ["vaso"]})
    vetor = np.zeros((1, DIM), dtype=np.float32)
    vetor[0, 0] = 1
    con = duckdb.connect()
    criar_indice(con, docs, vetor)

    class Modelo:
        def encode(self, *_args, **_kwargs):
            return vetor[0]

    def gerar(*_args):
        raise AssertionError("não chamar sem evidências")

    assert executar_rag("Houve elogio?", con, Modelo(), gerar, nota_min=5).status == "sem_evidencia"


def test_pipeline_filtro_invalido_falha_sem_gerar():
    docs = pd.DataFrame({"review_id": ["r1"], "texto": ["Chegou bem"], "nota": [5],
                         "situacao_entrega": ["no_prazo"], "categorias": ["vaso"]})
    vetor = np.zeros((1, DIM), dtype=np.float32)
    vetor[0, 0] = 1
    chamadas = []

    class Modelo:
        def encode(self, *_args, **_kwargs):
            return vetor[0]

    def gerar(*_args):
        chamadas.append(True)
        return {"status": "sem_evidencia", "limitacao": "Sem suporte", "afirmacoes": []}

    with duckdb.connect() as con:
        criar_indice(con, docs, vetor)
        resposta = executar_rag("Houve elogio?", con, Modelo(), gerar, situacao_entrega="atrasadoo")
    assert resposta.status == "erro_geracao"
    assert chamadas == []
