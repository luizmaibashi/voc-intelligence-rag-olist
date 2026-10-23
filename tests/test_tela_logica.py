from datetime import date

import pytest

from src.tela.logica import argumentos_responder, chave_entrada, resumo_execucoes


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
