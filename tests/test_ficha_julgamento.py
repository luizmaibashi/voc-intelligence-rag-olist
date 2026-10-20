"""Testes estruturais da ficha; suporte semântico é julgamento do Luiz."""
import json

import pytest

from src.eval.ficha_julgamento import gerar, resumir, validar


def _escrever(caminho, linhas):
    caminho.write_text("".join(json.dumps(l, ensure_ascii=False) + "\n" for l in linhas), encoding="utf-8")


def _manifesto(tmp_path):
    caminho = tmp_path / "manifesto.json"
    caminho.write_text(json.dumps({"casos": [
        {"id": "E01", "status_esperados": ["respondida"], "evidencias": [
            {"review_id": "r1", "texto": "Texto integral um."},
            {"review_id": "r2", "texto": "Texto integral dois."}]},
        {"id": "E02", "status_esperados": ["respondida"], "evidencias": []},
        {"id": "E20", "status_esperados": ["sem_evidencia"], "evidencias": []}]}), encoding="utf-8")
    return caminho


def _caso(cid, status, afirmacoes=None, classe=None):
    return {"tipo": "caso", "id": cid, "classe_operacional": classe,
            "resposta_aplicacao": {"status": status, "afirmacoes": afirmacoes or []}}


def _ficha(tmp_path):
    manifesto = _manifesto(tmp_path)
    antiga = tmp_path / "antiga.jsonl"
    nova = tmp_path / "nova.jsonl"
    _escrever(antiga, [_caso("E01", "sem_evidencia")])
    _escrever(nova, [
        _caso("E01", "respondida", [
            {"frase": "Primeira.", "review_ids": ["r1"]},
            {"frase": "Segunda.", "review_ids": ["r2"]}]),
        _caso("E02", "sem_evidencia"),
        _caso("E20", "sem_evidencia")])
    ficha = tmp_path / "ficha.jsonl"
    linhas = gerar([antiga, nova], ficha, manifesto)
    return ficha, linhas, manifesto, nova


def test_gera_frases_fontes_integrais_recusa_e_controle(tmp_path):
    ficha, linhas, _, _ = _ficha(tmp_path)
    assert len(linhas) == 4
    assert [(l["id"], l["ordem"], l["frase"]) for l in linhas[:2]] == [
        ("E01", 1, "Primeira."), ("E01", 2, "Segunda.")]
    assert linhas[0]["avaliacoes"] == [{"review_id": "r1", "texto": "Texto integral um."}]
    assert linhas[0]["status"] == "respondida"
    assert linhas[1]["review_ids"] == ["r2"]
    assert (linhas[0]["julgamento"], linhas[0]["motivo"], linhas[0]["nota"]) == (None, None, "")
    assert linhas[2]["julgamento_caso"] is None
    assert linhas[2]["status_esperados"] == ["respondida"]
    assert linhas[3]["tipo"] == "nao_julgavel"
    assert linhas[3]["classe"] == "controle_local"
    assert len(ficha.read_text(encoding="utf-8").splitlines()) == 4


def test_saida_existente_nao_sobrescrita(tmp_path):
    ficha, _, manifesto, captura = _ficha(tmp_path)
    original = ficha.read_bytes()
    with pytest.raises(FileExistsError):
        gerar([captura], ficha, manifesto)
    assert ficha.read_bytes() == original


def test_captura_mais_recente_vence_independente_da_ordem_dos_argumentos(tmp_path):
    manifesto = _manifesto(tmp_path)
    antiga = tmp_path / "antiga.jsonl"
    nova = tmp_path / "nova.jsonl"
    _escrever(antiga, [{"tipo": "cabecalho", "utc": "2026-10-19T12:00:00+00:00"},
                       _caso("E01", "sem_evidencia")])
    _escrever(nova, [{"tipo": "cabecalho", "utc": "2026-10-20T12:00:00+00:00"},
                     _caso("E01", "respondida", [{"frase": "Nova.", "review_ids": ["r1"]}])])
    linhas = gerar([nova, antiga], tmp_path / "ficha.jsonl", manifesto)
    assert len(linhas) == 1
    assert linhas[0]["frase"] == "Nova."


def test_ultima_ocorrencia_no_mesmo_arquivo_vence(tmp_path):
    manifesto = _manifesto(tmp_path)
    captura = tmp_path / "duas_ocorrencias.jsonl"
    _escrever(captura, [
        {"tipo": "cabecalho", "utc": "2026-10-20T12:00:00+00:00"},
        _caso("E01", "sem_evidencia"),
        _caso("E01", "respondida", [{"frase": "Última.", "review_ids": ["r1"]}]),
    ])
    linhas = gerar([captura], tmp_path / "ficha.jsonl", manifesto)
    assert [(l["tipo"], l.get("frase")) for l in linhas] == [("frase", "Última.")]


def test_captura_posterior_substitui_anterior_na_ordem_dos_argumentos(tmp_path):
    manifesto = _manifesto(tmp_path)
    antiga = tmp_path / "antiga.jsonl"
    nova = tmp_path / "nova.jsonl"
    _escrever(antiga, [{"tipo": "cabecalho", "utc": "2026-10-19T12:00:00+00:00"},
                       _caso("E01", "sem_evidencia")])
    _escrever(nova, [{"tipo": "cabecalho", "utc": "2026-10-20T12:00:00+00:00"},
                     _caso("E01", "respondida", [{"frase": "Nova.", "review_ids": ["r1"]}])])
    linhas = gerar([antiga, nova], tmp_path / "ficha.jsonl", manifesto)
    assert linhas[0]["frase"] == "Nova."


def test_falha_servico_e_contrato_nao_julgaveis(tmp_path):
    manifesto = _manifesto(tmp_path)
    captura = tmp_path / "falhas.jsonl"
    _escrever(captura, [_caso("E01", "erro_geracao", classe="falha_servico"),
                       _caso("E02", "erro_geracao", classe="falha_contrato")])
    linhas = gerar([captura], tmp_path / "ficha.jsonl", manifesto)
    assert [(l["tipo"], l["classe"]) for l in linhas] == [
        ("nao_julgavel", "falha_servico"), ("nao_julgavel", "falha_contrato")]
    assert resumir(linhas)["pendentes"] == ["E01", "E02"]


def test_frase_nao_julgada_falha_citando_frase(tmp_path):
    ficha, _, manifesto, _ = _ficha(tmp_path)
    with pytest.raises(ValueError, match="Primeira"):
        validar(ficha, manifesto)


@pytest.mark.parametrize("julgamento,motivo,erro", [
    ("NS", None, "NS exige motivo"),
    ("NS", "OUTRO", "NS exige motivo"),
    ("S", "TROCA", "S proíbe motivo"),
    ("X", None, "sem julgamento válido"),
])
def test_valida_pares_julgamento_motivo(tmp_path, julgamento, motivo, erro):
    ficha, linhas, manifesto, _ = _ficha(tmp_path)
    linhas[0].update(julgamento=julgamento, motivo=motivo)
    _escrever(ficha, linhas)
    with pytest.raises(ValueError, match=erro):
        validar(ficha, manifesto)


def test_resumo_exige_todas_frases_e_separa_recusa_indevida(tmp_path):
    ficha, linhas, manifesto, _ = _ficha(tmp_path)
    for linha in linhas[:2]:
        linha["julgamento"] = "S"
    linhas[2]["julgamento_caso"] = "S"
    _escrever(ficha, linhas)
    resumo = validar(ficha, manifesto)
    assert resumo["aprovados"] == 1
    assert resumo["n_julgados"] == 2
    assert resumo["pendentes"] == ["E20"]
    assert {r["id"]: r["motivo"] for r in resumo["resultados"]} == {
        "E01": "aprovado", "E02": "recusa_indevida"}
    linhas[1].update(julgamento="NS", motivo="SEM_BASE")
    _escrever(ficha, linhas)
    assert {r["id"]: r["motivo"] for r in validar(ficha, manifesto)["resultados"]}["E01"] == "NS"


def test_ficha_vazia_nao_aprova(tmp_path):
    ficha = tmp_path / "vazia.jsonl"
    ficha.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="vazia"):
        validar(ficha)


def test_id_ausente_fica_pendente(tmp_path):
    ficha, linhas, manifesto, _ = _ficha(tmp_path)
    _escrever(ficha, linhas[:2])
    for linha in linhas[:2]:
        linha["julgamento"] = "S"
    _escrever(ficha, linhas[:2])
    resumo = validar(ficha, manifesto)
    assert resumo["aprovados"] == 1
    assert resumo["n_julgados"] == 1
    assert resumo["pendentes"] == ["E02", "E20"]


def test_id_fora_do_manifesto_nao_infla_aprovacao(tmp_path):
    ficha, linhas, manifesto, _ = _ficha(tmp_path)
    linhas[0]["id"] = "EXTRA"
    linhas[0]["julgamento"] = "S"
    _escrever(ficha, linhas)
    with pytest.raises(ValueError, match="fora do manifesto"):
        validar(ficha, manifesto)


def test_frase_duplicada_nao_conta_duas_vezes(tmp_path):
    ficha, linhas, manifesto, _ = _ficha(tmp_path)
    linhas[0]["julgamento"] = "S"
    linhas[1]["julgamento"] = "S"
    linhas[1]["ordem"] = 1
    _escrever(ficha, linhas)
    with pytest.raises(ValueError, match="Frase duplicada"):
        validar(ficha, manifesto)


@pytest.mark.parametrize("julgamento,aprovados,motivo", [
    ("S", 1, "aprovado"), ("NS", 0, "recusa_reprovada"),
])
def test_recusa_esperada_julgada_explicitamente(tmp_path, julgamento, aprovados, motivo):
    manifesto = _manifesto(tmp_path)
    dados = json.loads(manifesto.read_text(encoding="utf-8"))
    dados["casos"][1]["status_esperados"] = ["sem_evidencia"]
    manifesto.write_text(json.dumps(dados), encoding="utf-8")
    captura = tmp_path / "recusa.jsonl"
    _escrever(captura, [_caso("E02", "sem_evidencia")])
    ficha = tmp_path / "ficha.jsonl"
    linhas = gerar([captura], ficha, manifesto)
    assert linhas[0]["julgamento_caso"] is None
    linhas[0]["julgamento_caso"] = julgamento
    _escrever(ficha, linhas)
    resumo = validar(ficha, manifesto)
    assert (resumo["aprovados"], resumo["n_julgados"]) == (aprovados, 1)
    assert resumo["resultados"] == [{"id": "E02", "motivo": motivo}]
    assert resumo["pendentes"] == ["E01", "E20"]


@pytest.mark.parametrize("classe", [
    "falha_servico", "falha_integracao", "falha_contrato", "truncamento_observado",
])
def test_cada_classe_nao_julgavel_e_controle_pendentes(tmp_path, classe):
    manifesto = _manifesto(tmp_path)
    captura = tmp_path / "falha.jsonl"
    _escrever(captura, [_caso("E01", "respondida", classe=classe),
                       _caso("E20", "sem_evidencia")])
    ficha = tmp_path / "ficha.jsonl"
    linhas = gerar([captura], ficha, manifesto)
    assert [(l["id"], l["tipo"], l["classe"]) for l in linhas] == [
        ("E01", "nao_julgavel", classe), ("E20", "nao_julgavel", "controle_local")]
    assert validar(ficha, manifesto)["pendentes"] == ["E01", "E20", "E02"]


def test_status_invalido_sem_classe_fica_nao_julgavel(tmp_path):
    manifesto = _manifesto(tmp_path)
    captura = tmp_path / "invalida.jsonl"
    _escrever(captura, [_caso("E01", "erro_geracao")])
    linhas = gerar([captura], tmp_path / "ficha.jsonl", manifesto)
    assert [(l["tipo"], l["classe"]) for l in linhas] == [("nao_julgavel", "saida_invalida")]


def test_resumo_nao_interrompe_apos_reprovacao_intermediaria():
    linhas = [
        {"id": "E01", "tipo": "frase", "julgamento": "S", "status_esperados": ["respondida"]},
        {"id": "E02", "tipo": "frase", "julgamento": "NS", "status_esperados": ["respondida"]},
        {"id": "E03", "tipo": "frase", "julgamento": "S", "status_esperados": ["respondida"]},
    ]
    resumo = resumir(linhas)
    assert (resumo["aprovados"], resumo["n_julgados"]) == (2, 3)
    assert resumo["resultados"] == [
        {"id": "E01", "motivo": "aprovado"},
        {"id": "E03", "motivo": "aprovado"},
        {"id": "E02", "motivo": "NS"},
    ]


@pytest.mark.parametrize("primeiro", [
    {"tipo": "nao_julgavel"},
    {"tipo": "frase", "julgamento": None, "status_esperados": ["respondida"]},
    {"tipo": "sem_evidencia", "julgamento_caso": None,
     "status_esperados": ["sem_evidencia"]},
])
def test_pendente_antes_de_aprovado_nao_interrompe_resumo(primeiro):
    linhas = [{"id": "E01", **primeiro},
              {"id": "E02", "tipo": "frase", "julgamento": "S",
               "status_esperados": ["respondida"]}]
    resumo = resumir(linhas)
    assert (resumo["aprovados"], resumo["n_julgados"]) == (1, 1)
    assert resumo["pendentes"] == ["E01"]
    assert resumo["resultados"] == [{"id": "E02", "motivo": "aprovado"}]


@pytest.mark.parametrize("motivo", ["TROCA", "EXTRAPOLA", "COMPOSTA", "SEM_BASE"])
def test_ns_aceito_com_cada_motivo(tmp_path, motivo):
    ficha, linhas, manifesto, _ = _ficha(tmp_path)
    linhas[0].update(julgamento="NS", motivo=motivo)
    linhas[1]["julgamento"] = "S"
    linhas[2]["julgamento_caso"] = "S"
    _escrever(ficha, linhas)
    resumo = validar(ficha, manifesto)
    assert {r["id"]: r["motivo"] for r in resumo["resultados"]}["E01"] == "NS"


def test_ns_tem_prioridade_sobre_status_incompativel():
    base = {"id": "E01", "tipo": "frase", "status_esperados": ["sem_evidencia"]}
    assert resumir([{**base, "julgamento": "S"}])["resultados"] == [
        {"id": "E01", "motivo": "status_incompativel"}]
    assert resumir([{**base, "julgamento": "NS"}])["resultados"] == [
        {"id": "E01", "motivo": "NS"}]


def test_frase_sem_review_ids_rejeitada(tmp_path):
    manifesto = _manifesto(tmp_path)
    captura = tmp_path / "sem_fontes.jsonl"
    _escrever(captura, [_caso("E01", "respondida", [
        {"frase": "Sem fonte.", "review_ids": []}])])
    with pytest.raises(ValueError, match="Fonte inválida"):
        gerar([captura], tmp_path / "ficha.jsonl", manifesto)
