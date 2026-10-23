from datetime import date

import pytest

from src.tela.logica import (PERGUNTAS_DEMO, ROTULOS_PERGUNTAS,
                            argumentos_responder, argumentos_trilha, caso_por_rotulo,
                            chave_entrada, contagem_citacoes_aprovadas,
                            descricao_recorte, hash_confere,
                            hash_envio_trilha, inteiro_pt, mensagem_status,
                            percentual_pt, posicoes_citacoes, resumo_execucoes,
                            situacao_legivel)


def test_argumentos_iguais_ao_cli_para_ea():
    args = argumentos_responder("O que os clientes relatam sobre entregas atrasadas?",
                                10.0, "", 2, "atrasado", "Todos", "", None)
    assert args == {"pergunta": "O que os clientes relatam sobre entregas atrasadas?",
                    "k": 10, "nota_min": None, "nota_max": 2,
                    "situacao_entrega": "atrasado", "categoria": None,
                    "compra_de": None, "compra_ate": None}
    assert type(args["k"]) is int


def test_datas_e_chave_para_cada_campo():
    args = argumentos_responder("p", 10, None, None, None, None, date(2018, 1, 1), None)
    assert args["compra_de"] == "2018-01-01"
    for campo in args:
        outro = dict(args)
        outro[campo] = "mudou"
        assert chave_entrada(outro) != chave_entrada(args)


def test_resumo_conta_erro_mediana_status_e_outros_formatos():
    linhas = [{"tipo": "tentativa", "erro_integracao": False, "duracao_ms": 10},
              {"tipo": "tentativa", "erro_integracao": True, "duracao_ms": 1000},
              {"tipo": "tentativa", "erro_integracao": False, "duracao_ms": 30},
              {"tipo": "resultado", "status": "respondida"},
              {"tipo": "resultado", "status": "sem_evidencia"},
              {"tipo": "outro", "classe_operacional": "x"}]
    resumo = resumo_execucoes(linhas)
    assert resumo["tentativas"] == 3
    assert resumo["erros_integracao"] == 1
    assert resumo["taxa_erro"] == pytest.approx(1 / 3)
    assert resumo["ic95_wilson"] == pytest.approx((0.06149194472039626, 0.7923403991979523))
    assert resumo["mediana_duracao_ms_sem_erro"] == 20
    assert resumo["resultados_por_status"] == {"respondida": 1, "sem_evidencia": 1}
    assert resumo["linhas_outro_formato"] == 1


def test_presets_usam_os_mesmos_argumentos_da_paridade():
    assert [caso["id"] for caso in PERGUNTAS_DEMO] == ["E-A", "E-B", "P15"]
    for caso in PERGUNTAS_DEMO:
        args = argumentos_responder(caso["pergunta"], caso["k"], caso["nota_min"],
                                    caso["nota_max"], caso["situacao"], caso["categoria"],
                                    caso["compra_de"], caso["compra_ate"])
        assert args == {"pergunta": caso["pergunta"], "k": 10, "nota_min": None,
                        "nota_max": 2, "situacao_entrega": "atrasado", "categoria": None,
                        "compra_de": None, "compra_ate": None}
        assert len(caso["hash"]) == 64


@pytest.mark.parametrize(("status", "esperado"), [
    ("respondida", "Resposta com fontes citadas (respondida)"),
    ("sem_evidencia", "Sem evidência nos relatos: o sistema recusou responder (sem_evidencia)"),
    ("erro_geracao", "Falha do serviço de geração (não é recusa) (erro_geracao)"),
    ("novo_status", "novo_status"),
])
def test_mensagem_status(status, esperado):
    assert mensagem_status(status) == esperado


def test_hash_colado_compara_exatamente_o_texto_enviado():
    assert hash_confere("abc", "abc")
    assert not hash_confere("def", "abc")
    assert not hash_confere(" abc ", "abc")


def test_rotulos_de_negocio_geram_argumentos_da_paridade():
    assert list(ROTULOS_PERGUNTAS.values()) == ["E-A", "E-B", "P15"]
    for rotulo, identificador in ROTULOS_PERGUNTAS.items():
        caso = caso_por_rotulo(rotulo)
        assert caso["id"] == identificador
        assert argumentos_trilha(caso["pergunta"], caso["nota_min"],
                                caso["nota_max"], caso["situacao"]) == {
            "pergunta": caso["pergunta"], "k": 10, "nota_min": None,
            "nota_max": 2, "situacao_entrega": "atrasado", "categoria": None,
            "compra_de": None, "compra_ate": None}
    assert caso_por_rotulo("Escrever minha pergunta") is None


def test_descricao_recorte_e_situacoes():
    assert descricao_recorte(None, 2, "atrasado") == "Recorte: nota até 2 · entrega atrasada"
    assert descricao_recorte() == "Recorte: todos os comentários"
    assert descricao_recorte(1, None, "no_prazo") == "Recorte: nota a partir de 1 · no prazo"
    assert situacao_legivel("nao_entregue") == "não entregue"


def test_posicoes_preservam_citacao_fora_do_contexto():
    contexto = [{"review_id": "a"}, {"review_id": "b"}, {"review_id": "c"}]
    assert posicoes_citacoes(contexto, ["a", "c"]) == [1, 3]
    assert posicoes_citacoes(contexto, ["b", "fora"]) == [2, "fora dos relatos aprovados"]
    assert posicoes_citacoes(contexto, []) == []
    assert contagem_citacoes_aprovadas([2, "fora dos relatos aprovados"]) == (1, 2)


def test_envio_trilha_usa_hash_da_previa_valida():
    previa = {"hash": "abc"}
    assert hash_envio_trilha(previa, True, "chave", "chave") == "abc"
    assert hash_envio_trilha(previa, False, "chave", "chave") is None
    assert hash_envio_trilha({"hash": ""}, True, "chave", "chave") is None
    assert hash_envio_trilha(previa, True, "nova", "antiga") is None


def test_formatacao_pt_br():
    assert inteiro_pt(3813) == "3.813"
    assert inteiro_pt(40303) == "40.303"
    assert percentual_pt(0.0946) == "9,46%"
    assert percentual_pt(0.28, 1) == "28,0%"
