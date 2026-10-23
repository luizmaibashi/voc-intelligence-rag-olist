import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import demo
from src.rag import liberacao
from tests.test_demo import ModeloFalso

AGORA = datetime(2026, 10, 16, 12, 0, tzinfo=timezone.utc)
PERGUNTA = "O que os clientes relatam sobre atraso?"


class GeradorFalso:
    def __init__(self, saida=None, erro=None):
        self.saida = saida
        self.erro = erro
        self.chamadas = 0

    def __call__(self, pergunta, evidencias):
        self.chamadas += 1
        if self.erro is not None:
            raise self.erro
        if self.saida is not None:
            return self.saida
        return {"status": "respondida", "texto": "Clientes relatam atraso.",
                "review_ids": [evidencias[0]["review_id"]]}


def fabrica(gerador):
    def criar():
        return gerador, None
    return criar


def proibido():
    raise AssertionError("cliente Gemini não deveria ser criado")


def previa(**extra):
    return demo.responder_cli(demo.corpus_sintetico(), PERGUNTA, ModeloFalso(), k=2,
                              registro=extra.pop("registro"), agora=AGORA,
                              criar_gerador=proibido, **extra)


def executar(registro, gerador, aprovacao=None, **extra):
    base = previa(registro=registro, **extra)
    return demo.responder_cli(demo.corpus_sintetico(), PERGUNTA, ModeloFalso(), k=2,
                              executar=True, aprovacao_sha256=aprovacao or base["hash"],
                              registro=registro, agora=AGORA,
                              criar_gerador=fabrica(gerador), **extra)


def linhas(registro):
    return [json.loads(l) for l in registro.read_text(encoding="utf-8").splitlines()]


def test_previa_nao_cria_cliente_nem_registra(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    registro = tmp_path / "execucoes.jsonl"
    saida = previa(registro=registro)
    assert saida["modo"] == "previa_sem_api"
    assert len(saida["hash"]) == 64
    assert [c["review_id"] for c in saida["contexto"]]
    assert saida["chamadas_restantes_hoje"] == liberacao.TETO_DIARIO
    assert "--aprovacao-sha256" in saida["proximo_passo"]
    assert not registro.exists()


def test_hash_estavel_e_sensivel_a_filtro(tmp_path):
    registro = tmp_path / "r.jsonl"
    a = previa(registro=registro)["hash"]
    b = previa(registro=registro)["hash"]
    c = previa(registro=registro, situacao_entrega="atrasado")["hash"]
    d = previa(registro=registro, categoria="sintetica", compra_de="2018-02-01")["hash"]
    assert a == b
    assert a != c
    assert a != d


def test_executar_sem_hash_ou_hash_divergente_bloqueia(tmp_path):
    registro = tmp_path / "r.jsonl"
    gerador = GeradorFalso()
    for aprovacao in (None, "0" * 64):
        with pytest.raises(liberacao.EnvioBloqueado):
            demo.responder_cli(demo.corpus_sintetico(), PERGUNTA, ModeloFalso(), k=2,
                               executar=True, aprovacao_sha256=aprovacao,
                               registro=registro, agora=AGORA,
                               criar_gerador=fabrica(gerador))
    assert gerador.chamadas == 0
    assert not registro.exists()


def test_executar_com_hash_responde_e_exibe_fontes_citadas(tmp_path):
    registro = tmp_path / "r.jsonl"
    saida = executar(registro, GeradorFalso())
    contexto = {c["review_id"] for c in saida["contexto"]}
    assert saida["modo"] == "geracao_real"
    assert saida["resposta"]["status"] == "respondida"
    assert set(saida["resposta"]["review_ids"]) <= contexto
    corpus = demo.corpus_sintetico().set_index("review_id")
    for fonte in saida["fontes_citadas"]:
        assert fonte["texto"] == corpus.loc[fonte["review_id"], "texto"]
    assert len(saida["fontes_citadas"]) == len(saida["resposta"]["review_ids"])


def test_citacao_fora_do_contexto_vira_erro(tmp_path):
    gerador = GeradorFalso({"status": "respondida", "texto": "x", "review_ids": ["inventado"]})
    saida = executar(tmp_path / "r.jsonl", gerador)
    assert saida["resposta"]["status"] == "erro_geracao"
    assert saida["fontes_citadas"] == []


def test_recusa_e_falha_de_servico_sao_distintas(tmp_path):
    recusa = executar(tmp_path / "a.jsonl", GeradorFalso(
        {"status": "sem_evidencia", "texto": "Sem suporte.", "review_ids": []}))
    falha = executar(tmp_path / "b.jsonl", GeradorFalso(erro=RuntimeError("caiu")))
    assert recusa["resposta"]["status"] == "sem_evidencia"
    assert falha["resposta"]["status"] == "erro_geracao"


def _registrar_envios(registro, quantidade, dia):
    with registro.open("w", encoding="utf-8") as f:
        for i in range(quantidade):
            f.write(json.dumps({"tipo": "envio", "execucao": f"e{i}", "utc": dia}) + "\n")
            f.write(json.dumps({"tipo": "resultado", "execucao": f"e{i}", "utc": dia,
                                "tentativas": 1}) + "\n")


def test_orcamento_bloqueia_quando_reserva_estoura_teto(tmp_path):
    registro = tmp_path / "r.jsonl"
    _registrar_envios(registro, 19, "2026-10-16T08:00:00+00:00")
    gerador = GeradorFalso()
    with pytest.raises(liberacao.EnvioBloqueado):
        executar(registro, gerador)
    assert gerador.chamadas == 0


def test_orcamento_ignora_outro_dia_utc(tmp_path):
    registro = tmp_path / "r.jsonl"
    _registrar_envios(registro, 19, "2026-10-15T23:59:00+00:00")
    assert executar(registro, GeradorFalso())["resposta"]["status"] == "respondida"


def test_envio_sem_resultado_reserva_duas_chamadas(tmp_path):
    registro = tmp_path / "r.jsonl"
    registro.write_text(json.dumps({"tipo": "envio", "execucao": "x",
                                    "utc": "2026-10-16T01:00:00+00:00"}) + "\n", encoding="utf-8")
    assert liberacao.chamadas_no_dia(registro, AGORA) == 2


def test_registro_corrompido_falha_visivel(tmp_path):
    registro = tmp_path / "r.jsonl"
    registro.write_text("{nao json\n", encoding="utf-8")
    with pytest.raises(ValueError):
        liberacao.chamadas_no_dia(registro, AGORA)


def test_registro_anexa_cabecalho_antes_e_resultado_depois(tmp_path):
    registro = tmp_path / "r.jsonl"
    registro.write_text(json.dumps({"tipo": "envio", "execucao": "antigo",
                                    "utc": "2026-10-01T00:00:00+00:00"}) + "\n", encoding="utf-8")
    vistos = []

    def gerador(pergunta, evidencias):
        vistos.append([l["tipo"] for l in linhas(registro)])
        return GeradorFalso()(pergunta, evidencias)

    executar(registro, gerador)
    tipos = [l["tipo"] for l in linhas(registro)]
    assert vistos == [["envio", "envio"]]
    assert tipos == ["envio", "envio", "tentativa", "resultado"]
    ultimo = linhas(registro)[-1]
    assert ultimo["tentativas"] == 1 and ultimo["status"] == "respondida"


@pytest.mark.parametrize("texto, tipo", [
    ("me liga 11 98765-4321", "telefone"),
    ("meu email é fulano@exemplo.com", "email"),
    ("cpf 123.456.789-09", "cpf"),
    ("cep 79000-000", "cep"),
])
def test_alerta_pii_informa_sem_bloquear(texto, tipo):
    alertas = liberacao.alertas_pii("pergunta", [{"review_id": "r1", "texto": texto}])
    assert alertas == [{"origem": "r1", "tipos": [tipo]}]


def test_previa_com_pii_continua_disponivel(tmp_path):
    corpus = demo.corpus_sintetico()
    corpus.loc[0, "texto"] = "Atrasou. Contato fulano@exemplo.com"
    saida = demo.responder_cli(corpus, PERGUNTA, ModeloFalso(), k=3,
                               registro=tmp_path / "r.jsonl", agora=AGORA,
                               criar_gerador=proibido)
    assert {"origem": "sintetico-01", "tipos": ["email"]} in saida["alertas_pii"]
    assert len(saida["hash"]) == 64


def test_gerador_falso_roda_sem_chave_e_sem_registro(tmp_path):
    registro = tmp_path / "r.jsonl"
    saida = demo.responder_cli(demo.corpus_sintetico(), PERGUNTA, ModeloFalso(), k=2,
                               gerador="falso", registro=registro, agora=AGORA,
                               criar_gerador=proibido)
    assert saida["modo"] == "simulado"
    assert saida["resposta"]["status"] == "respondida"
    assert not registro.exists()


def test_main_hash_divergente_sai_com_codigo_nao_zero(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(demo, "carregar_corpus", lambda caminho: demo.corpus_sintetico())
    monkeypatch.setattr(demo, "carregar_modelo", ModeloFalso)
    monkeypatch.setattr(demo, "REGISTRO_PADRAO", tmp_path / "r.jsonl")
    monkeypatch.setattr(demo, "_criar_gerador", proibido)
    codigo = demo.main(["--acao", "responder", "--pergunta", PERGUNTA,
                        "--executar", "--aprovacao-sha256", "0" * 64])
    assert codigo != 0
    assert "Envio bloqueado" in capsys.readouterr().err


def test_main_executar_exige_acao_responder():
    with pytest.raises(SystemExit):
        demo.main(["--acao", "buscar", "--pergunta", "x", "--executar"])


def test_main_executar_com_gerador_falso_e_invalido():
    with pytest.raises(SystemExit):
        demo.main(["--acao", "responder", "--pergunta", "x", "--executar", "--gerador", "falso"])
