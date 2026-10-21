import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.eval.ganho_filtros import FILTROS, medir, montar_planilha  # noqa: E402

COLUNAS_PLANILHA = ["id_pergunta", "pergunta", "review_id", "nota", "freq_texto", "texto", "relevante"]


def origem(linhas):
    """linhas: (id_pergunta, braco, posicao, review_id, texto, nota)."""
    df = pd.DataFrame(linhas, columns=["id_pergunta", "braco", "posicao", "review_id", "texto", "nota"])
    df["freq_texto"] = 1
    return df


def julgamento(linhas):
    """linhas: (id_pergunta, review_id, texto, nota, relevante)."""
    df = pd.DataFrame(linhas, columns=["id_pergunta", "review_id", "texto", "nota", "relevante"])
    df["pergunta"] = "pergunta " + df.id_pergunta
    df["freq_texto"] = 1
    return df[COLUNAS_PLANILHA]


def test_filtros_primarios_congelados_pela_spec():
    primarios = {p: f for (p, braco), f in FILTROS.items() if braco == "primario"}
    assert primarios == {
        "P01": {"situacao_entrega": "atrasado"},
        "P02": {"situacao_entrega": "nao_entregue"},
        "P09": {"nota_min": 4},
        "P10": {"nota_min": 4},
        "P11": {"nota_max": 2},
    }


def test_planilha_traz_so_ineditas_por_texto_mais_ancoras_sem_julgamento():
    julg = julgamento([("P09", "a", "Chegou rápido", 5, 1), ("P09", "b", "Atrasou", 1, 0),
                       ("P09", "c", "Bom", 5, 1)])
    # "chegou RÁPIDO" tem outro review_id e outra caixa: já julgado, não é inédito.
    orig = origem([("P09", "sem_filtro", 1, "a", "Chegou rápido", 5),
                   ("P09", "primario", 1, "z", "chegou rápido", 5),
                   ("P09", "primario", 2, "n", "Entrega antes do prazo", 5),
                   ("P09", "exploratorio", 1, "n", "Entrega antes do prazo", 5)])
    planilha = montar_planilha(orig, julg, ancoras_por_pergunta=2, semente=1)
    assert list(planilha.columns) == COLUNAS_PLANILHA
    assert planilha.relevante.eq("").all()
    textos = planilha.texto.str.lower().tolist()
    assert textos.count("entrega antes do prazo") == 1
    assert len(planilha) == 3  # 1 inédita + 2 âncoras
    assert planilha.id_pergunta.eq("P09").all() and planilha.pergunta.eq("pergunta P09").all()
    assert set(textos) - {"entrega antes do prazo"} <= {"chegou rápido", "atrasou", "bom"}


def test_planilha_nao_revela_braco_nem_situacao_de_entrega():
    julg = julgamento([("P02", "a", "Não chegou", 1, 1)])
    orig = origem([("P02", "primario", 1, "n", "Nunca recebi", 1)])
    planilha = montar_planilha(orig, julg, ancoras_por_pergunta=1, semente=1)
    assert "braco" not in planilha.columns and "situacao_entrega" not in planilha.columns


def test_medir_junta_por_texto_e_calcula_precisao_por_braco():
    julg = julgamento([("P09", "a", "Chegou rápido", 5, 1), ("P09", "b", "Atrasou", 1, 0)])
    novos = julgamento([("P09", "n", "Entrega antes do prazo", 5, 1), ("P09", "a", "Chegou rápido", 5, 1)])
    orig = origem([("P09", "sem_filtro", 1, "a", "Chegou rápido", 5),
                   ("P09", "sem_filtro", 2, "b", "Atrasou", 1),
                   ("P09", "primario", 1, "z", "CHEGOU RÁPIDO", 5),
                   ("P09", "primario", 2, "n", "Entrega antes do prazo", 5)])
    tabela, ancoras = medir(orig, julg, novos, k=2)
    linha = tabela.set_index(["id_pergunta", "braco"]).loc[("P09", "primario")]
    assert linha.precisao == pytest.approx(1.0)
    assert tabela.set_index(["id_pergunta", "braco"]).loc[("P09", "sem_filtro")].precisao == pytest.approx(0.5)
    assert ancoras == {"n": 1, "discordancias": 0}


def test_medir_falha_com_item_sem_julgamento():
    julg = julgamento([("P09", "a", "Chegou rápido", 5, 1)])
    novos = julgamento([("P09", "n", "Outro texto", 5, 1)])
    orig = origem([("P09", "primario", 1, "x", "Sem julgamento", 5)])
    with pytest.raises(ValueError, match="sem julgamento"):
        medir(orig, julg, novos, k=1)


def test_medir_rejeita_planilha_incompleta():
    julg = julgamento([("P09", "a", "Chegou rápido", 5, 1)])
    novos = julgamento([("P09", "n", "Entrega antes do prazo", 5, 1)])
    novos["relevante"] = novos.relevante.astype(object)
    novos.loc[0, "relevante"] = ""
    orig = origem([("P09", "primario", 1, "n", "Entrega antes do prazo", 5)])
    with pytest.raises(ValueError, match="incompleto"):
        medir(orig, julg, novos, k=1)


def test_ancora_discordante_e_contada():
    julg = julgamento([("P09", "a", "Chegou rápido", 5, 1)])
    novos = julgamento([("P09", "a", "chegou rápido", 5, 0)])
    orig = origem([("P09", "primario", 1, "a", "Chegou rápido", 5)])
    _, ancoras = medir(orig, julg, novos, k=1)
    assert ancoras == {"n": 1, "discordancias": 1}


def test_formulario_confere_exemplos_e_preserva_colunas():
    from src.eval.gerar_formulario_filtros import SEM_EXEMPLO_NAO, montar_dados
    julg = julgamento([("P01", "a", "Tive atraso na entrega", 1, 1),
                       ("P01", "b", "Demorou demais para chegar aqui", 1, 1)])
    planilha = julgamento([("P01", "b", "Demorou demais para chegar aqui", 1, 1)]).assign(relevante="")
    dados = montar_dados(planilha, julg)
    assert dados["perguntas"]["P01"]["exemplo_sim"] == "Tive atraso na entrega"
    assert dados["perguntas"]["P01"]["exemplo_nao"] == SEM_EXEMPLO_NAO
    assert dados["colunas"] == COLUNAS_PLANILHA and len(dados["itens"]) == 1


def test_formulario_recusa_exemplo_que_esta_na_planilha():
    from src.eval.gerar_formulario_filtros import montar_dados
    julg = julgamento([("P01", "a", "Tive atraso na entrega", 1, 1)])
    planilha = julg.assign(relevante="")
    with pytest.raises(ValueError, match="exemplo inválido"):
        montar_dados(planilha, julg)


def test_formulario_recusa_pergunta_sem_criterio():
    from src.eval.gerar_formulario_filtros import montar_dados
    planilha = julgamento([("P05", "a", "Chegou quebrado", 1, 1)]).assign(relevante="")
    with pytest.raises(ValueError, match="sem critério"):
        montar_dados(planilha, planilha)
