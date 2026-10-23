import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.eval.ganho_hibrida import (  # noqa: E402
    COLUNAS_PLANILHA, CRITERIO, K_RRF, PROFUNDIDADE, avaliar_criterio, fundir, medir,
    montar_formulario, montar_planilha, rotulos_conhecidos,
)


def origem(linhas):
    """linhas: (id_pergunta, braco, posicao, review_id, texto)."""
    df = pd.DataFrame(linhas, columns=["id_pergunta", "braco", "posicao", "review_id", "texto"])
    return df.assign(nota=1, freq_texto=1, score=0.0)


def julgamento(linhas):
    """linhas: (id_pergunta, review_id, texto, relevante)."""
    df = pd.DataFrame(linhas, columns=["id_pergunta", "review_id", "texto", "relevante"])
    return df.assign(pergunta="pergunta " + df.id_pergunta, nota=1, freq_texto=1)[COLUNAS_PLANILHA]


def test_parametros_congelados_pela_spec():
    assert (PROFUNDIDADE, K_RRF) == (100, 60)
    assert CRITERIO == {"ganho_mrr_min": 0.03, "ganho_p10_min": 0.0, "perda_p10_max_pergunta": 0.2,
                        "latencia_extra_max_s": 1.0}


def test_rrf_premia_quem_aparece_nas_duas_listas_e_usa_representante_da_densa():
    o = origem([("P01", "densa", 1, "a", "Só densa"), ("P01", "densa", 2, "b_densa", "Nas Duas"),
                ("P01", "tfidf", 1, "c", "Só tfidf"), ("P01", "tfidf", 2, "b_tfidf", "nas duas")])
    h = fundir(o)
    assert h.review_id.tolist() == ["b_densa", "a", "c"]
    assert h.score.iloc[0] == pytest.approx(2 / (K_RRF + 2))
    # Empate em score: desempata pela melhor posição e depois pelo texto, sem depender da ordem de entrada.
    assert h.posicao.tolist() == [1, 2, 3]


def test_rrf_rejeita_texto_repetido_na_mesma_lista():
    o = origem([("P01", "densa", 1, "a", "Igual"), ("P01", "densa", 2, "b", "igual")])
    with pytest.raises(ValueError, match="repetido"):
        fundir(o)


def test_planilha_traz_ineditas_dos_tres_bracos_e_ancoras_de_setembro():
    o = origem([("P01", "densa", 1, "a", "Julgado em setembro"),
                ("P01", "densa", 2, "b", "Julgado nos filtros"),
                ("P01", "tfidf", 1, "c", "Inédito tfidf")])
    setembro = julgamento([("P01", "x", "julgado em setembro", 1), ("P01", "y", "Outro", 0)])
    filtros = julgamento([("P01", "z", "julgado nos filtros", 1)])
    perguntas = pd.DataFrame({"id_pergunta": ["P01"], "pergunta": ["pergunta P01"]})
    p = montar_planilha(o, setembro, filtros, perguntas)
    assert list(p.columns) == COLUNAS_PLANILHA
    assert set(p.texto) == {"Inédito tfidf", "julgado em setembro", "Outro"}
    assert p.relevante.eq("").all()


def test_setembro_manda_e_ancora_divergente_vira_deriva():
    setembro = julgamento([("P01", "a", "A", 1), ("P01", "b", "B", 0)])
    filtros = julgamento([("P01", "a", "a", 1), ("P01", "c", "C", 1)])
    novos = julgamento([("P01", "b", "B", 1), ("P01", "d", "D", 0)])
    rotulos, deriva = rotulos_conhecidos(setembro, filtros, novos)
    assert rotulos.loc[("P01", "b")] == 0
    assert rotulos.loc[("P01", "d")] == 0
    assert deriva == {"julgamento_filtros": {"n": 1, "discordancias": 0},
                      "julgamento_hibrida": {"n": 1, "discordancias": 1}}


def _cenario(perde_em_p02: bool):
    """Densa acha o relevante em 2º; TF-IDF o traz em 1º, e a híbrida o sobe para 1º."""
    linhas, rot = [], []
    for pid in ("P01", "P02"):
        linhas += [(pid, "densa", 1, f"{pid}r", "ruim"), (pid, "densa", 2, f"{pid}b", "bom"),
                   (pid, "tfidf", 1, f"{pid}b2", "bom")]
        rot += [(pid, f"{pid}r", "ruim", 0), (pid, f"{pid}b", "bom", 1)]
    if perde_em_p02:
        # Três relevantes só na densa (posições 3 a 5) somem do top-10 da híbrida
        # porque sete textos irrelevantes no topo do TF-IDF passam à frente deles.
        for i in range(3):
            linhas.append(("P02", "densa", 3 + i, f"rel{i}", f"relevante {i}"))
            rot.append(("P02", f"rel{i}", f"relevante {i}", 1))
        for i in range(10):
            linhas.append(("P02", "tfidf", 2 + i, f"lixo{i}", f"lixo {i}"))
            linhas.append(("P02", "densa", 6 + i, f"lixo{i}d", f"lixo {i}"))
            rot.append(("P02", f"lixo{i}", f"lixo {i}", 0))
    rotulos, _ = rotulos_conhecidos(julgamento(rot), julgamento([]), julgamento([]))
    return medir(origem(linhas), rotulos)


def test_criterio_adota_quando_hibrida_sobe_mrr_sem_perder_precisao():
    tabela = _cenario(perde_em_p02=False)
    latencia = pd.DataFrame({"tfidf_consulta_s": [0.01, 0.02], "tfidf_ajuste_s": [0.5, 0.5]})
    veredito = avaliar_criterio(tabela, latencia)
    assert veredito["ganho_mrr"] == {"valor": 0.5, "passa": True}
    assert veredito["adota"] is True
    assert avaliar_criterio(tabela)["adota"] is False  # sem latência medida não há adoção


def test_criterio_barra_media_que_esconde_pergunta_que_piorou():
    tabela = _cenario(perde_em_p02=True)
    veredito = avaliar_criterio(tabela, pd.DataFrame({"tfidf_consulta_s": [0.0], "tfidf_ajuste_s": [0.0]}))
    assert veredito["pior_pergunta_p10"]["passa"] is False
    assert veredito["adota"] is False


def test_medir_falha_se_falta_julgamento():
    rotulos, _ = rotulos_conhecidos(julgamento([("P01", "a", "A", 1)]), julgamento([]), julgamento([]))
    with pytest.raises(ValueError, match="sem julgamento"):
        medir(origem([("P01", "densa", 1, "b", "B")]), rotulos)


def test_formulario_troca_marcadores_uma_vez_e_cai_no_criterio_geral():
    planilha = julgamento([("P99", "a", "Texto <novo>", "")])
    setembro = julgamento([("P99", "s", "Exemplo sim", 1), ("P99", "n", "Exemplo não", 0)])
    pagina = montar_formulario(planilha, setembro)
    assert "__DADOS_JSON__" not in pagina and "julgamento_filtros" not in pagina
    assert "Julgamento da busca híbrida (spec 0014)" in pagina
    assert "Exemplo sim" in pagina and "Texto \\u003cnovo>" in pagina
