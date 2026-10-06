import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.eval import avaliar_geracao as avaliacao


@pytest.fixture
def manifesto():
    casos = []
    for i in range(1, 21):
        alias = f"caso-{i}"
        casos.append({"id": f"E{i:02d}", "origem": "real" if i <= 18 else
                      "sintetico" if i == 19 else "controle_local",
                      "pergunta": "Há relato?", "evidencias": [] if i == 20 else
                      [{"review_id": alias, "texto": "Comentário sintético para teste."}],
                      "fontes_locais": {alias: f"{i:032x}"} if i <= 18 else {},
                      "criterio_proposto": "Conferir suporte humano.",
                      "status_esperados": ["sem_evidencia"] if i in {13, 14, 15, 16, 19, 20}
                      else ["respondida", "sem_evidencia"]})
    return {"schema_version": 1, "modo": "contexto_curado", "modelo": avaliacao.MODELO_GERACAO,
            "estado": "proposta", "casos": casos}


def test_previa_nao_constroi_cliente(manifesto, monkeypatch):
    monkeypatch.setattr(avaliacao, "_criar_gerador", lambda: pytest.fail("cliente criado"))
    previa = avaliacao.previa(manifesto)
    assert previa["hash_lote"] == avaliacao.hash_lote(manifesto)
    assert previa["manifesto"] == manifesto
    assert "autorização" in previa["aviso"]


@pytest.mark.parametrize("defeito", ["extra", "ausente", "campo", "bool", "alias", "fonte", "negativa"])
def test_contrato_invalido_nao_chama_nem_cria(manifesto, tmp_path, defeito):
    if defeito == "extra":
        manifesto["casos"].append(copy.deepcopy(manifesto["casos"][0]))
    elif defeito == "ausente":
        manifesto["casos"].pop()
    elif defeito == "campo":
        manifesto["casos"][0]["nota"] = 5
    elif defeito == "bool":
        manifesto["schema_version"] = True
    elif defeito == "alias":
        manifesto["casos"][0]["evidencias"][0]["review_id"] = "alias com espaço"
    elif defeito == "fonte":
        manifesto["casos"][0]["fontes_locais"] = {}
    else:
        manifesto["casos"][12]["status_esperados"] = ["respondida"]
    saida = tmp_path / "resultados.jsonl"
    with pytest.raises(ValueError):
        avaliacao.executar(manifesto, aprovacao_sha256="errado", previsao=10, saida=saida,
                          gerar=lambda *_: pytest.fail("chamada"))
    assert not saida.exists()


@pytest.mark.parametrize("previsao", [True, -1, 21, "10", None])
def test_previsao_invalida_nao_cria_arquivo(manifesto, tmp_path, previsao):
    saida = tmp_path / "resultados.jsonl"
    with pytest.raises(ValueError):
        avaliacao.executar(manifesto, aprovacao_sha256=avaliacao.hash_lote(manifesto),
                          previsao=previsao, saida=saida, gerar=lambda *_: pytest.fail("chamada"))
    assert not saida.exists()


def test_hash_errado_e_arquivo_existente_nao_chamam(manifesto, tmp_path):
    saida = tmp_path / "resultado.jsonl"
    with pytest.raises(ValueError):
        avaliacao.executar(manifesto, aprovacao_sha256="0" * 64, previsao=1,
                          saida=saida, gerar=lambda *_: pytest.fail("chamada"))
    saida.write_text("preservar", encoding="utf-8")
    with pytest.raises(FileExistsError):
        avaliacao.executar(manifesto, aprovacao_sha256=avaliacao.hash_lote(manifesto), previsao=1,
                          saida=saida, gerar=lambda *_: pytest.fail("chamada"))
    assert saida.read_text() == "preservar"


def test_hash_muda_com_payload_e_configuracao(manifesto, monkeypatch):
    original = avaliacao.hash_lote(manifesto)
    manifesto["casos"][0]["evidencias"][0]["texto"] += " Alteração."
    assert avaliacao.hash_lote(manifesto) != original
    config = avaliacao.configuracao_geracao()
    atual = avaliacao.hash_lote(manifesto)
    monkeypatch.setattr(avaliacao, "configuracao_geracao", lambda: {**config, "timeout": 1})
    assert avaliacao.hash_lote(manifesto) != atual


@pytest.mark.parametrize("status_e17", ["respondida", "sem_evidencia"])
def test_rodada_preserva_saida_sem_declarar_acerto(manifesto, tmp_path, status_e17):
    chamadas = []
    def gerar(pergunta, evidencias):
        alias = evidencias[0]["review_id"]
        chamadas.append(alias)
        status = status_e17 if alias == "caso-17" else "respondida"
        return {"status": status, "texto": "Texto não avaliado semanticamente.",
                "review_ids": [alias] if status == "respondida" else []}
    saida = tmp_path / "resultados.jsonl"
    avaliacao.executar(manifesto, aprovacao_sha256=avaliacao.hash_lote(manifesto),
                      previsao=10, saida=saida, gerar=gerar)
    linhas = [json.loads(l) for l in saida.read_text(encoding="utf-8").splitlines()]
    casos = linhas[1:-1]
    assert len(chamadas) == 19
    assert len(casos) == 20
    assert casos[16]["status_esperado_compativel"] is True
    assert casos[18]["status_esperado_compativel"] is False
    assert casos[19]["saida_provedor"] is None
    assert all(c["julgamento_semantico"] == "pendente" for c in casos)
    assert linhas[-1]["casos_registrados"] == 20


def test_falha_http_e_saida_malformada_nao_vazam_segredo(manifesto, tmp_path):
    class Falha(Exception):
        code = 503
    chamadas = []
    def gerar(pergunta, evidencias):
        alias = evidencias[0]["review_id"]
        chamadas.append(alias)
        if alias == "caso-1":
            raise Falha("CHAVE_SECRETA")
        return {"status": "respondida", "texto": "sem referência", "review_ids": ["inventado"]}
    saida = tmp_path / "resultados.jsonl"
    avaliacao.executar(manifesto, aprovacao_sha256=avaliacao.hash_lote(manifesto),
                      previsao=1, saida=saida, gerar=gerar)
    bruto = saida.read_text(encoding="utf-8")
    casos = [json.loads(l) for l in bruto.splitlines()][1:-1]
    assert "CHAVE_SECRETA" not in bruto
    assert len(chamadas) == 19
    assert casos[0]["erro_integracao"] == {"classe": "Falha", "codigo": 503, "fase": "gerador"}
    assert casos[0]["resposta_aplicacao"]["status"] == "erro_geracao"
    assert casos[1]["saida_provedor"]["review_ids"] == ["inventado"]
    assert casos[1]["resposta_aplicacao"]["status"] == "erro_geracao"


def test_interrupcao_preserva_cabecalho_e_caso_anterior(manifesto, tmp_path):
    def gerar(pergunta, evidencias):
        if evidencias[0]["review_id"] == "caso-2":
            raise KeyboardInterrupt()
        return {"status": "sem_evidencia", "texto": "Limite", "review_ids": []}
    saida = tmp_path / "parcial.jsonl"
    with pytest.raises(KeyboardInterrupt):
        avaliacao.executar(manifesto, aprovacao_sha256=avaliacao.hash_lote(manifesto),
                          previsao=1, saida=saida, gerar=gerar)
    assert len(saida.read_text(encoding="utf-8").splitlines()) == 2


def test_status_malformado_preserva_saida_e_continua(manifesto, tmp_path):
    saida = tmp_path / "resultados.jsonl"
    avaliacao.executar(manifesto, aprovacao_sha256=avaliacao.hash_lote(manifesto), previsao=0,
                      saida=saida, gerar=lambda *_: {"status": [], "texto": "x", "review_ids": []})
    linhas = [json.loads(l) for l in saida.read_text(encoding="utf-8").splitlines()]
    assert linhas[1]["saida_provedor"]["status"] == []
    assert linhas[1]["resposta_aplicacao"]["status"] == "erro_geracao"
    assert linhas[1]["erro_integracao"] is None
    assert linhas[-1]["casos_registrados"] == 20


def test_excecao_inesperada_da_validacao_e_registrada_sem_segredo(manifesto, tmp_path, monkeypatch):
    original = avaliacao.responder
    def validar_com_falha(pergunta, evidencias, gerar):
        if not evidencias:
            return original(pergunta, evidencias, gerar)
        gerar(pergunta, evidencias)
        raise TypeError("segredo-no-erro-de-validacao")
    monkeypatch.setattr(avaliacao, "responder", validar_com_falha)
    saida = tmp_path / "validacao.jsonl"
    avaliacao.executar(manifesto, aprovacao_sha256=avaliacao.hash_lote(manifesto), previsao=0,
                      saida=saida, gerar=lambda *_: {"status": "sem_evidencia", "texto": "Sem suporte", "review_ids": []})
    bruto = saida.read_text(encoding="utf-8")
    linhas = [json.loads(l) for l in bruto.splitlines()]
    assert "segredo-no-erro-de-validacao" not in bruto
    assert linhas[1]["erro_integracao"] == {
        "classe": "TypeError", "codigo": None, "fase": "validacao_aplicacao"}
    assert linhas[1]["resposta_aplicacao"]["status"] == "erro_geracao"
    assert linhas[-2]["erro_integracao"] is None
    assert linhas[-1]["casos_registrados"] == 20


def test_cli_previa_e_erro_seguro(manifesto, tmp_path, capsys):
    caminho = tmp_path / "manifesto.json"
    caminho.write_text(json.dumps(manifesto), encoding="utf-8")
    assert avaliacao.main(["--manifesto", str(caminho)]) == 0
    assert json.loads(capsys.readouterr().out)["hash_lote"] == avaliacao.hash_lote(manifesto)
    assert avaliacao.main(["--manifesto", str(caminho), "--executar"]) == 2
    assert "Traceback" not in capsys.readouterr().err


def test_gates_antes_da_factory_e_pasta_nao_criada(manifesto, tmp_path, monkeypatch):
    monkeypatch.setattr(avaliacao, "_criar_gerador", lambda: pytest.fail("cliente criado"))
    digest = avaliacao.hash_lote(manifesto)
    with pytest.raises(ValueError):
        avaliacao.executar(manifesto, aprovacao_sha256="errado", previsao=0,
                          saida=tmp_path / "novo.jsonl")
    with pytest.raises(ValueError):
        avaliacao.executar(manifesto, aprovacao_sha256=digest, previsao=True,
                          saida=tmp_path / "novo.jsonl")
    with pytest.raises(ValueError):
        avaliacao.executar(manifesto, aprovacao_sha256=digest, previsao=0,
                          saida=tmp_path / "ausente" / "novo.jsonl")
    assert not (tmp_path / "ausente").exists()
    existente = tmp_path / "existente.jsonl"
    existente.write_text("preservar", encoding="utf-8")
    with pytest.raises(FileExistsError):
        avaliacao.executar(manifesto, aprovacao_sha256=digest, previsao=0, saida=existente)


def test_cliente_falso_configurado_sem_retry_e_fechado(manifesto, tmp_path, monkeypatch):
    from google import genai
    chamadas = []
    class Cliente:
        def __init__(self, **kwargs):
            self.opcoes = kwargs["http_options"]
            self.models = self
            self.fechado = False
            self.pedidos = []
            chamadas.append(self)
        def generate_content(self, **kwargs):
            self.pedidos.append(kwargs)
            return type("Saida", (), {"text": '{"status":"sem_evidencia","texto":"Limite","review_ids":[]}'})()
        def close(self):
            self.fechado = True
    monkeypatch.setattr(genai, "Client", Cliente)
    avaliacao.executar(manifesto, aprovacao_sha256=avaliacao.hash_lote(manifesto), previsao=0,
                      saida=tmp_path / "novo.jsonl")
    assert len(chamadas) == 1
    assert chamadas[0].opcoes.timeout == 25000
    assert chamadas[0].opcoes.retry_options.attempts == 1
    assert chamadas[0].fechado is True
    assert len(chamadas[0].pedidos) == 19
    config = avaliacao.configuracao_geracao()
    # Fora do callback: responder captura exceções do gerador, inclusive AssertionError.
    for pedido in chamadas[0].pedidos:
        payload = json.loads(pedido["contents"])
        assert set(payload) == {"pergunta", "avaliacoes"}
        assert all(set(e) == {"review_id", "texto"} for e in payload["avaliacoes"])
        assert "fontes_locais" not in pedido["contents"]
        assert all(fonte not in pedido["contents"] for caso in manifesto["casos"]
                   for fonte in caso["fontes_locais"].values())
        assert pedido["model"] == config["modelo"]
        assert pedido["config"].temperature == config["temperature"]
        assert pedido["config"].max_output_tokens == config["max_output_tokens"]
        assert pedido["config"].response_mime_type == config["response_mime_type"]
        assert pedido["config"].response_schema == config["schema"]
        assert pedido["config"].system_instruction == config["prompt"]


def test_aprovacao_antiga_rejeita_texto_alterado_antes_de_cliente(manifesto, tmp_path, monkeypatch):
    digest = avaliacao.hash_lote(manifesto)
    manifesto["casos"][0]["evidencias"][0]["texto"] += " Alterado."
    monkeypatch.setattr(avaliacao, "_criar_gerador", lambda: pytest.fail("cliente criado"))
    saida = tmp_path / "novo.jsonl"
    with pytest.raises(ValueError, match="Hash"):
        avaliacao.executar(manifesto, aprovacao_sha256=digest, previsao=0, saida=saida)
    assert not saida.exists()


def test_loader_rejeita_chaves_duplicadas(manifesto, tmp_path):
    caminho = tmp_path / "manifesto.json"
    bruto = json.dumps(manifesto)
    bruto = bruto.replace('"id": "E01"', '"id": "E02", "id": "E01"', 1)
    caminho.write_text(bruto, encoding="utf-8")
    with pytest.raises(ValueError, match="Chave repetida"):
        avaliacao.carregar_manifesto(caminho)


def test_hash_canonico_preserva_chaves_mas_registra_ordem_de_casos(manifesto):
    original = avaliacao.hash_lote(manifesto)
    def inverter_chaves(valor):
        if isinstance(valor, dict):
            return {k: inverter_chaves(v) for k, v in reversed(list(valor.items()))}
        if isinstance(valor, list):
            return [inverter_chaves(v) for v in valor]
        return valor
    assert avaliacao.hash_lote(inverter_chaves(manifesto)) == original
    manifesto["casos"] = list(reversed(manifesto["casos"]))
    assert avaliacao.hash_lote(manifesto) != original
