import copy
import hashlib
import json
import sys
from collections import Counter
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


def test_hash_do_gate_da_tag_nao_libera_schema_novo(manifesto, tmp_path, monkeypatch):
    hash_antigo = "8953bffc2db35a5ff48371763c97238bf04eb16ad4424564f30ba7c6afc9ccd0"
    monkeypatch.setattr(avaliacao, "_criar_gerador", lambda: pytest.fail("cliente criado"))
    caminho = tmp_path / "novo.jsonl"
    assert avaliacao.hash_lote(manifesto, repetir_transitorios=True) != hash_antigo
    with pytest.raises(ValueError, match="Hash"):
        avaliacao.executar(manifesto, aprovacao_sha256=hash_antigo, previsao=10,
                          previsao_falhas_contrato=4, saida=caminho,
                          repetir_transitorios=True)
    assert not caminho.exists()


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
        return {"status": status, "limitacao": "Texto não avaliado semanticamente.",
                "afirmacoes": [{"frase": "Texto não avaliado semanticamente.",
                                "review_ids": [alias]}] if status == "respondida" else []}
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
        return {"status": "respondida", "limitacao": "",
                "afirmacoes": [{"frase": "sem referência", "review_ids": ["inventado"]}]}
    saida = tmp_path / "resultados.jsonl"
    avaliacao.executar(manifesto, aprovacao_sha256=avaliacao.hash_lote(manifesto),
                      previsao=1, saida=saida, gerar=gerar)
    bruto = saida.read_text(encoding="utf-8")
    casos = [json.loads(l) for l in bruto.splitlines()][1:-1]
    assert "CHAVE_SECRETA" not in bruto
    assert len(chamadas) == 19
    assert casos[0]["erro_integracao"] == {"classe": "Falha", "codigo": 503, "fase": "gerador"}
    assert casos[0]["resposta_aplicacao"]["status"] == "erro_geracao"
    assert casos[1]["saida_provedor"]["afirmacoes"][0]["review_ids"] == ["inventado"]
    assert casos[1]["resposta_aplicacao"]["status"] == "erro_geracao"


def test_interrupcao_preserva_cabecalho_e_caso_anterior(manifesto, tmp_path):
    def gerar(pergunta, evidencias):
        if evidencias[0]["review_id"] == "caso-2":
            raise KeyboardInterrupt()
        return {"status": "sem_evidencia", "limitacao": "Limite", "afirmacoes": []}
    saida = tmp_path / "parcial.jsonl"
    with pytest.raises(KeyboardInterrupt):
        avaliacao.executar(manifesto, aprovacao_sha256=avaliacao.hash_lote(manifesto),
                          previsao=1, saida=saida, gerar=gerar)
    assert len(saida.read_text(encoding="utf-8").splitlines()) == 2


def test_status_malformado_preserva_saida_e_continua(manifesto, tmp_path):
    saida = tmp_path / "resultados.jsonl"
    avaliacao.executar(manifesto, aprovacao_sha256=avaliacao.hash_lote(manifesto), previsao=0,
                      saida=saida, gerar=lambda *_: {"status": [], "limitacao": "x", "afirmacoes": []})
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
                      saida=saida, gerar=lambda *_: {"status": "sem_evidencia", "limitacao": "Sem suporte", "afirmacoes": []})
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
        avaliacao.executar(manifesto, aprovacao_sha256=digest, previsao=0,
                          previsao_falhas_contrato=0, limiar_contrato=5, saida=existente,
                          ids_execucao=["E02"])


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
            return type("Saida", (), {"text": '{"status":"sem_evidencia","limitacao":"Limite","afirmacoes":[]}'})()
        def close(self):
            self.fechado = True
    monkeypatch.setattr(genai, "Client", Cliente)
    avaliacao.executar(manifesto, aprovacao_sha256=avaliacao.hash_lote(manifesto), previsao=0,
                      previsao_falhas_contrato=0, limiar_contrato=5, saida=tmp_path / "novo.jsonl",
                      registro_orcamento=tmp_path / "cota.jsonl",
                      ids_execucao=sorted(avaliacao.IDS_PAREAVEIS_BASELINE))
    assert len(chamadas) == 1
    assert chamadas[0].opcoes.timeout == 25000
    assert chamadas[0].opcoes.retry_options.attempts == 1
    assert chamadas[0].fechado is True
    assert len(chamadas[0].pedidos) == 13
    registros = [json.loads(l) for l in (tmp_path / "cota.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len([r for r in registros if r["tipo"] == "envio"]) == 13
    assert len([r for r in registros if r["tipo"] == "resultado"]) == 13
    assert len([r for r in registros if r["tipo"] == "resultado" and r["tentativas"] == 1]) == 13
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


def test_parada_por_contrato_preserva_parcial(manifesto, tmp_path):
    chamadas = []
    def gerar(_pergunta, evidencias):
        chamadas.append(evidencias[0]["review_id"])
        return {"_erro_contrato": "truncamento_observado", "_finish_reason": "MAX_TOKENS"}
    saida = tmp_path / "parada.jsonl"
    avaliacao.executar(manifesto, aprovacao_sha256=avaliacao.hash_lote(manifesto),
                      previsao=0, previsao_falhas_contrato=3, limiar_contrato=3,
                      saida=saida, gerar=gerar,
                      ids_execucao=sorted(avaliacao.IDS_PAREAVEIS_BASELINE))
    linhas = [json.loads(l) for l in saida.read_text(encoding="utf-8").splitlines()]
    assert len(chamadas) == 13
    assert [l["classe_operacional"] for l in linhas if l["tipo"] == "caso"] == [
        "truncamento_observado"] * 13
    assert any(l["tipo"] == "parada_contrato" for l in linhas)
    assert linhas[-1]["casos_registrados"] == 13
    assert linhas[-1]["lote_completo"] is True


def test_parada_pareada_conta_so_ids_julgaveis_no_baseline(manifesto, tmp_path):
    chamadas = []
    def gerar(_pergunta, evidencias):
        chamadas.append(evidencias[0]["review_id"])
        return {"status": "respondida", "limitacao": "",
                "afirmacoes": [{"frase": "x", "review_ids": ["inventado"]}]}
    saida = tmp_path / "pareado.jsonl"
    avaliacao.executar(manifesto, aprovacao_sha256=avaliacao.hash_lote(manifesto),
                      previsao=0, previsao_falhas_contrato=4, limiar_contrato=4,
                      saida=saida, gerar=gerar)
    linhas = [json.loads(l) for l in saida.read_text(encoding="utf-8").splitlines()]
    assert len(chamadas) == 18
    assert linhas[-2]["falhas_contrato"] == 18
    assert linhas[-2]["falhas_pareadas"] == 13


def test_ids_subset_e_previsoes_reais_bloqueiam_antes_do_cliente(manifesto, tmp_path, monkeypatch):
    monkeypatch.setattr(avaliacao, "_criar_gerador", lambda: pytest.fail("cliente criado"))
    digest = avaliacao.hash_lote(manifesto)
    for ids in (["E01", "E01"], ["E99"], []):
        with pytest.raises(ValueError):
            avaliacao.executar(manifesto, aprovacao_sha256=digest, previsao=0,
                              previsao_falhas_contrato=0, limiar_contrato=5,
                              ids_execucao=ids, saida=tmp_path / "bloqueado.jsonl")
    with pytest.raises(ValueError, match="Limiar"):
        avaliacao.executar(manifesto, aprovacao_sha256=digest, previsao=0,
                          previsao_falhas_contrato=0, limiar_contrato=0,
                          saida=tmp_path / "bloqueado.jsonl")
    assert not (tmp_path / "bloqueado.jsonl").exists()


def test_cota_real_compartilhada_para_antes_da_chamada_21(manifesto, tmp_path, monkeypatch):
    import httpx
    from src.rag import tentativas
    monkeypatch.setattr(tentativas.time, "sleep", lambda _: None)
    chamadas = []
    def gerar(_pergunta, evidencias):
        alias = evidencias[0]["review_id"]
        chamadas.append(alias)
        if len(chamadas) % 2:
            raise httpx.ReadTimeout("segredo")
        return {"status": "sem_evidencia", "limitacao": "sem suporte", "afirmacoes": []}
    class Cliente:
        def close(self):
            pass
    monkeypatch.setattr(avaliacao, "_criar_gerador", lambda: (gerar, Cliente()))
    saida = tmp_path / "lote.jsonl"
    cota = tmp_path / "cota.jsonl"
    avaliacao.executar(manifesto, aprovacao_sha256=avaliacao.hash_lote(
        manifesto, repetir_transitorios=True), previsao=0,
        previsao_falhas_contrato=0, saida=saida, repetir_transitorios=True,
        registro_orcamento=cota,
        ids_execucao=sorted(avaliacao.IDS_PAREAVEIS_BASELINE))
    linhas = [json.loads(l) for l in saida.read_text(encoding="utf-8").splitlines()]
    assert len(chamadas) == 20
    assert len([l for l in linhas if l["tipo"] == "caso"]) == 10
    assert any(l["tipo"] == "cota_esgotada" and l["id"] == "E14" for l in linhas)
    assert linhas[-1]["lote_completo"] is False
    assert linhas[-1]["casos_registrados"] == 10


def test_parada_pareada_acumula_entre_execucoes_e_bloqueia_reenvio(manifesto, tmp_path, monkeypatch):
    chamadas = []
    def gerar(_pergunta, evidencias):
        chamadas.append(evidencias[0]["review_id"])
        return {"status": "respondida", "limitacao": "",
                "afirmacoes": [{"frase": "x", "review_ids": ["inventado"]}]}
    class Cliente:
        def close(self):
            pass
    monkeypatch.setattr(avaliacao, "_criar_gerador", lambda: (gerar, Cliente()))
    digest = avaliacao.hash_lote(manifesto)
    cota = tmp_path / "cota.jsonl"
    kwargs = {"aprovacao_sha256": digest, "previsao": 0,
              "previsao_falhas_contrato": 3, "registro_orcamento": cota}
    avaliacao.executar(manifesto, saida=tmp_path / "dia1.jsonl",
                      ids_execucao=["E02", "E03"], **kwargs)
    with pytest.raises(ValueError, match="já enviados"):
        avaliacao.executar(manifesto, saida=tmp_path / "repetido.jsonl",
                          ids_execucao=["E02"], **kwargs)
    assert not (tmp_path / "repetido.jsonl").exists()
    restantes = sorted(avaliacao.IDS_PAREAVEIS_BASELINE - {"E02", "E03"})
    avaliacao.executar(manifesto, saida=tmp_path / "dia2.jsonl",
                      ids_execucao=restantes, **kwargs)
    linhas = [json.loads(l) for l in (tmp_path / "dia2.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(chamadas) == 13
    assert linhas[0]["falhas_pareadas_anteriores"] == 2
    assert linhas[-2]["tipo"] == "parada_contrato"
    assert linhas[-2]["falhas_pareadas"] == 13
    with pytest.raises(ValueError, match="Parada antecipada"):
        avaliacao.executar(manifesto, saida=tmp_path / "dia3.jsonl",
                          ids_execucao=["E01"], **kwargs)
    assert not (tmp_path / "dia3.jsonl").exists()


def test_sete_restantes_so_apos_treze_pareaveis_e_n_menor_que_tres(manifesto, tmp_path, monkeypatch):
    class Cliente:
        def close(self):
            pass
    def gerar(_pergunta, evidencias):
        return {"status": "sem_evidencia", "limitacao": "sem suporte", "afirmacoes": []}
    monkeypatch.setattr(avaliacao, "_criar_gerador", lambda: (gerar, Cliente()))
    digest = avaliacao.hash_lote(manifesto)
    kwargs = {"aprovacao_sha256": digest, "previsao": 17,
              "previsao_falhas_contrato": 3, "registro_orcamento": tmp_path / "cota.jsonl"}
    with pytest.raises(ValueError, match="13 casos pareáveis"):
        avaliacao.executar(manifesto, saida=tmp_path / "cedo.jsonl",
                          ids_execucao=["E01"], **kwargs)
    assert not (tmp_path / "cedo.jsonl").exists()
    avaliacao.executar(manifesto, saida=tmp_path / "fase1.jsonl",
                      ids_execucao=sorted(avaliacao.IDS_PAREAVEIS_BASELINE), **kwargs)
    avaliacao.executar(manifesto, saida=tmp_path / "fase2.jsonl",
                      ids_execucao=["E01"], **kwargs)
    linhas = [json.loads(l) for l in (tmp_path / "fase2.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [l["id"] for l in linhas if l["tipo"] == "caso"] == ["E01"]


def test_reavaliacao_local_preserva_captura_e_nao_permite_terceiro_envio(manifesto, tmp_path, monkeypatch):
    import httpx
    from src.rag import tentativas
    monkeypatch.setattr(tentativas.time, "sleep", lambda _: None)
    estado = {"falhar": True}
    class Cliente:
        def close(self):
            pass
    def gerar(_pergunta, _evidencias):
        if estado["falhar"]:
            raise httpx.ConnectError("bloqueio local")
        return {"status": "sem_evidencia", "limitacao": "sem suporte", "afirmacoes": []}
    monkeypatch.setattr(avaliacao, "_criar_gerador", lambda: (gerar, Cliente()))
    digest = avaliacao.hash_lote(manifesto, repetir_transitorios=True)
    monkeypatch.setattr(avaliacao, "HASH_REAVALIACAO_LOCAL", digest)
    origem = tmp_path / "origem.jsonl"
    monkeypatch.setattr(avaliacao, "CAPTURA_FALHA_LOCAL", origem)
    kwargs = {"aprovacao_sha256": digest, "previsao": 17,
              "previsao_falhas_contrato": 3, "registro_orcamento": tmp_path / "cota.jsonl",
              "repetir_transitorios": True, "ids_execucao": ["E02"]}
    avaliacao.executar(manifesto, saida=origem, **kwargs)
    original = origem.read_bytes()
    monkeypatch.setattr(avaliacao, "SHA256_CAPTURA_FALHA_LOCAL",
                        hashlib.sha256(original).hexdigest())
    with pytest.raises(ValueError, match="já enviados"):
        avaliacao.executar(manifesto, saida=tmp_path / "sem_optin.jsonl", **kwargs)
    origem.write_bytes(original + b"\n")
    with pytest.raises(ValueError, match="foi alterada"):
        avaliacao.executar(manifesto, saida=tmp_path / "captura_alterada.jsonl",
                          reavaliar_falhas_locais=True, **kwargs)
    assert not (tmp_path / "captura_alterada.jsonl").exists()
    origem.write_bytes(original)
    estado["falhar"] = False
    avaliacao.executar(manifesto, saida=tmp_path / "reavaliacao.jsonl",
                      reavaliar_falhas_locais=True, **kwargs)
    assert origem.read_bytes() == original
    ledger = [json.loads(l) for l in (tmp_path / "cota.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len([l for l in ledger if l["tipo"] == "envio"]) == 2
    with pytest.raises(ValueError, match="única falha local anterior"):
        avaliacao.executar(manifesto, saida=tmp_path / "terceira.jsonl",
                          reavaliar_falhas_locais=True, **kwargs)
    assert not (tmp_path / "terceira.jsonl").exists()


def test_reenvio_servico_autorizado_e_segundo_recusado(manifesto, tmp_path, monkeypatch):
    digest = avaliacao.hash_lote(manifesto, repetir_transitorios=True)
    monkeypatch.setattr(avaliacao, "HASH_REAVALIACAO_SERVICO", digest)
    for cid in ("E02", "E18"):
        caminho, _, quantidade = avaliacao.CAPTURAS_FALHA_SERVICO[cid]
        origem = Path(avaliacao.__file__).resolve().parents[2] / caminho
        linhas_origem = [json.loads(l) for l in origem.read_text(encoding="utf-8").splitlines()]
        linhas_origem[0]["hash_lote"] = digest
        copia = tmp_path / f"origem_{cid}.jsonl"
        conteudo = ("\n".join(json.dumps(l, ensure_ascii=False) for l in linhas_origem) + "\n").encode()
        copia.write_bytes(conteudo)
        monkeypatch.setitem(avaliacao.CAPTURAS_FALHA_SERVICO, cid,
                            (str(copia), hashlib.sha256(conteudo).hexdigest(), quantidade))
    cota = tmp_path / "cota.jsonl"
    linhas = []
    for cid, quantidade in (("E02", 2), ("E18", 1)):
        for indice in range(quantidade):
            execucao = f"{cid}-{indice}"
            linhas.extend([{"tipo": "envio", "execucao": execucao, "id": cid,
                            "origem": "avaliacao", "hash": digest, "utc": "2026-10-19T00:00:00+00:00"},
                           {"tipo": "resultado", "execucao": execucao, "id": cid,
                            "origem": "avaliacao", "hash": digest, "tentativas": 2,
                            "classe_operacional": "falha_servico"}])
    cota.write_text("\n".join(json.dumps(l) for l in linhas) + "\n", encoding="utf-8")
    class Cliente:
        def close(self):
            pass
    monkeypatch.setattr(avaliacao, "_criar_gerador", lambda: (
        lambda *_: {"status": "sem_evidencia", "limitacao": "", "afirmacoes": []}, Cliente()))
    kwargs = {"aprovacao_sha256": digest, "previsao": 17, "previsao_falhas_contrato": 3,
              "registro_orcamento": cota, "repetir_transitorios": True,
              "reavaliar_falha_servico": True}
    avaliacao.executar(manifesto, saida=tmp_path / "e02.jsonl", ids_execucao=["E02"], **kwargs)
    with pytest.raises(ValueError, match="Histórico"):
        avaliacao.executar(manifesto, saida=tmp_path / "e02_novo.jsonl", ids_execucao=["E02"], **kwargs)
    with pytest.raises(ValueError, match="13 casos pareáveis"):
        avaliacao.executar(manifesto, saida=tmp_path / "fase2.jsonl", ids_execucao=["E01"],
                          **{k: v for k, v in kwargs.items() if k != "reavaliar_falha_servico"})
    avaliacao.executar(manifesto, saida=tmp_path / "e18.jsonl", ids_execucao=["E18"], **kwargs)
    assert not (tmp_path / "e02_novo.jsonl").exists()


def test_opcoes_de_reenvio_incompativeis_antes_do_cliente(manifesto, tmp_path, monkeypatch):
    monkeypatch.setattr(avaliacao, "_criar_gerador", lambda: pytest.fail("cliente criado"))
    with pytest.raises(ValueError, match="incompatíveis"):
        avaliacao.executar(manifesto, aprovacao_sha256=avaliacao.hash_lote(manifesto),
                          previsao=17, previsao_falhas_contrato=3,
                          saida=tmp_path / "recusado.jsonl", ids_execucao=["E02"],
                          reavaliar_falhas_locais=True, reavaliar_falha_servico=True)
    assert not (tmp_path / "recusado.jsonl").exists()


def test_reenvio_servico_exige_ultimo_resultado_falha_antes_do_cliente(
        manifesto, tmp_path, monkeypatch):
    digest = avaliacao.hash_lote(manifesto, repetir_transitorios=True)
    monkeypatch.setattr(avaliacao, "HASH_REAVALIACAO_SERVICO", digest)
    caminho, _, quantidade = avaliacao.CAPTURAS_FALHA_SERVICO["E02"]
    origem = Path(avaliacao.__file__).resolve().parents[2] / caminho
    linhas_origem = [json.loads(l) for l in origem.read_text(encoding="utf-8").splitlines()]
    linhas_origem[0]["hash_lote"] = digest
    copia = tmp_path / "origem_e02.jsonl"
    conteudo = ("\n".join(json.dumps(l, ensure_ascii=False) for l in linhas_origem) + "\n").encode()
    copia.write_bytes(conteudo)
    monkeypatch.setitem(avaliacao.CAPTURAS_FALHA_SERVICO, "E02",
                        (str(copia), hashlib.sha256(conteudo).hexdigest(), quantidade))
    cota = tmp_path / "cota.jsonl"
    linhas = []
    for indice, classe in enumerate(("falha_servico", "respondida_pendente_julgamento")):
        execucao = f"E02-{indice}"
        linhas.extend([{"tipo": "envio", "execucao": execucao, "id": "E02",
                        "origem": "avaliacao", "hash": digest, "utc": "2026-10-19T00:00:00+00:00"},
                       {"tipo": "resultado", "execucao": execucao, "id": "E02",
                        "origem": "avaliacao", "hash": digest, "tentativas": 1,
                        "classe_operacional": classe}])
    cota.write_text("\n".join(json.dumps(l) for l in linhas) + "\n", encoding="utf-8")
    monkeypatch.setattr(avaliacao, "_criar_gerador", lambda: pytest.fail("cliente criado"))
    saida = tmp_path / "recusado.jsonl"
    with pytest.raises(ValueError, match="Histórico"):
        avaliacao.executar(manifesto, aprovacao_sha256=digest, previsao=17,
                          previsao_falhas_contrato=3, saida=saida,
                          registro_orcamento=cota, repetir_transitorios=True,
                          ids_execucao=["E02"], reavaliar_falha_servico=True)
    assert not saida.exists()


def test_fase2_so_depois_de_e02_e_e18_com_saida(manifesto, tmp_path, monkeypatch):
    digest = avaliacao.hash_lote(manifesto)
    cota = tmp_path / "cota.jsonl"
    linhas = []
    for cid in avaliacao.IDS_PAREAVEIS_BASELINE:
        if cid == "E18":
            continue
        classe = "falha_servico" if cid == "E02" else "recusa"
        linhas.extend([{"tipo": "envio", "execucao": cid, "id": cid, "origem": "avaliacao",
                        "hash": digest, "utc": "2026-10-19T00:00:00+00:00"},
                       {"tipo": "resultado", "execucao": cid, "id": cid, "origem": "avaliacao",
                        "hash": digest, "tentativas": 1, "classe_operacional": classe}])
    cota.write_text("\n".join(json.dumps(l) for l in linhas) + "\n", encoding="utf-8")
    class Cliente:
        def close(self):
            pass
    monkeypatch.setattr(avaliacao, "_criar_gerador", lambda: (
        lambda *_: {"status": "sem_evidencia", "limitacao": "", "afirmacoes": []}, Cliente()))
    kwargs = {"aprovacao_sha256": digest, "previsao": 17, "previsao_falhas_contrato": 3,
              "registro_orcamento": cota}
    with pytest.raises(ValueError, match="13 casos pareáveis"):
        avaliacao.executar(manifesto, saida=tmp_path / "cedo.jsonl", ids_execucao=["E01"], **kwargs)
    linhas.append({"tipo": "resultado", "execucao": "E02-novo", "id": "E02",
                  "origem": "avaliacao", "hash": digest, "classe_operacional": "recusa"})
    cota.write_text("\n".join(json.dumps(l) for l in linhas) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="13 casos pareáveis"):
        avaliacao.executar(manifesto, saida=tmp_path / "ainda_cedo.jsonl", ids_execucao=["E01"], **kwargs)
    linhas.append({"tipo": "resultado", "execucao": "E18-novo", "id": "E18",
                  "origem": "avaliacao", "hash": digest, "classe_operacional": "recusa"})
    cota.write_text("\n".join(json.dumps(l) for l in linhas) + "\n", encoding="utf-8")
    avaliacao.executar(manifesto, saida=tmp_path / "fase2.jsonl", ids_execucao=["E01"], **kwargs)


def test_guarda_reenvio_servico_recusa_desvios(tmp_path, monkeypatch):
    digest = avaliacao.HASH_REAVALIACAO_SERVICO
    envios = Counter({"E02": 2, "E18": 1})
    resultados = {cid: {"classe_operacional": "falha_servico"} for cid in envios}
    avaliacao.autorizar_reenvio_servico(["E02", "E18"], digest, envios, resultados)
    with pytest.raises(ValueError, match="autorização"):
        avaliacao.autorizar_reenvio_servico(["E03"], digest, envios, resultados)
    with pytest.raises(ValueError, match="Histórico"):
        avaliacao.autorizar_reenvio_servico(["E02"], digest, Counter({"E02": 3}), resultados)
    caminho, sha, n = avaliacao.CAPTURAS_FALHA_SERVICO["E02"]
    original = (Path(avaliacao.__file__).resolve().parents[2] / caminho).read_bytes().replace(b"\r\n", b"\n")
    for conteudo in (original, original.replace(b"\n", b"\r\n")):
        copia = tmp_path / "origem.jsonl"
        copia.write_bytes(conteudo)
        monkeypatch.setitem(avaliacao.CAPTURAS_FALHA_SERVICO, "E02", (str(copia), sha, n))
        avaliacao.autorizar_reenvio_servico(["E02"], digest, envios, resultados)
    copia.write_bytes(original + b"x")
    with pytest.raises(ValueError, match="alterada"):
        avaliacao.autorizar_reenvio_servico(["E02"], digest, envios, resultados)
    caso = json.loads(next(l for l in original.decode().splitlines()
                           if json.loads(l).get("tipo") == "caso" and json.loads(l).get("id") == "E02"))
    caso["saida_provedor"] = {"status": "respondida"}
    alterado = b"\n".join(json.dumps(caso if json.loads(l).get("tipo") == "caso" and
                                      json.loads(l).get("id") == "E02" else json.loads(l),
                                      ensure_ascii=False, separators=(",", ":")).encode()
                            for l in original.decode().splitlines()) + b"\n"
    copia.write_bytes(alterado)
    monkeypatch.setitem(avaliacao.CAPTURAS_FALHA_SERVICO, "E02", (
        str(copia), hashlib.sha256(alterado).hexdigest(), n))
    with pytest.raises(ValueError, match="Contrato"):
        avaliacao.autorizar_reenvio_servico(["E02"], digest, envios, resultados)


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


def test_previa_optin_muda_hash_e_hash_legado_bloqueia_execucao(manifesto, tmp_path, monkeypatch):
    antigo = avaliacao.hash_lote(manifesto)
    nova = avaliacao.previa(manifesto, repetir_transitorios=True)
    assert nova["hash_lote"] != antigo
    assert nova["configuracao"]["attempts"] == 1
    assert nova["configuracao"]["politica_repeticao"]["max_tentativas"] == 2
    monkeypatch.setattr(avaliacao, "_criar_gerador", lambda: pytest.fail("cliente criado"))
    saida = tmp_path / "bloqueado.jsonl"
    with pytest.raises(ValueError, match="Hash"):
        avaliacao.executar(manifesto, aprovacao_sha256=antigo, previsao=10,
                          saida=saida, repetir_transitorios=True)
    assert not saida.exists()
    assert avaliacao.hash_lote(manifesto, repetir_transitorios=False) == antigo


def test_rodada_optin_preserva_tentativas_e_numero_real(manifesto, tmp_path, monkeypatch):
    import httpx
    from src.rag import tentativas
    esperas = []
    monkeypatch.setattr(tentativas.time, "sleep", esperas.append)
    chamadas = {}

    def gerar(_pergunta, evidencias):
        alias = evidencias[0]["review_id"]
        chamadas[alias] = chamadas.get(alias, 0) + 1
        if alias in {"caso-1", "caso-2"} and (alias == "caso-2" or chamadas[alias] == 1):
            raise httpx.ReadTimeout("SEGREDO")
        return {"status": "respondida", "limitacao": "",
                "afirmacoes": [{"frase": "Texto sintético", "review_ids": [alias]}]}

    saida = tmp_path / "retry.jsonl"
    avaliacao.executar(manifesto, aprovacao_sha256=avaliacao.hash_lote(manifesto, repetir_transitorios=True),
                      previsao=10, saida=saida, gerar=gerar, repetir_transitorios=True)
    bruto = saida.read_text(encoding="utf-8")
    registros = [json.loads(l) for l in bruto.splitlines()]
    eventos = [r for r in registros if r["tipo"] == "tentativa"]
    casos = {r["id"]: r for r in registros if r["tipo"] == "caso"}
    assert len(eventos) == 21
    assert sum(chamadas.values()) == 21
    assert esperas == [2, 2]
    assert casos["E01"]["tentativa"] == 2
    assert casos["E01"]["erro_integracao"] is None
    assert casos["E01"]["resposta_aplicacao"]["status"] == "respondida"
    assert casos["E02"]["tentativa"] == 2
    assert casos["E02"]["erro_integracao"]["classe"] == "ReadTimeout"
    assert casos["E02"]["resposta_aplicacao"]["status"] == "erro_geracao"
    assert casos["E20"]["tentativa"] == 0
    assert not any(e["id"] == "E20" for e in eventos)
    assert eventos[0]["erro_integracao"]["classe"] == "ReadTimeout"
    assert registros[1]["tipo"] == registros[2]["tipo"] == "tentativa"
    assert registros[-1]["casos_registrados"] == 20
    assert "SEGREDO" not in bruto


def test_cli_previa_optin_sem_cliente(manifesto, tmp_path, monkeypatch, capsys):
    caminho = tmp_path / "manifesto.json"
    caminho.write_text(json.dumps(manifesto), encoding="utf-8")
    monkeypatch.setattr(avaliacao, "_criar_gerador", lambda: pytest.fail("cliente criado"))
    assert avaliacao.main(["--manifesto", str(caminho), "--repetir-transitorios"]) == 0
    previa = json.loads(capsys.readouterr().out)
    assert previa["hash_lote"] == avaliacao.hash_lote(manifesto, repetir_transitorios=True)


def test_falha_registro_optin_para_executor_sem_proximo_caso(manifesto, tmp_path, monkeypatch):
    import httpx
    chamadas = []
    caminho = tmp_path / "parcial.jsonl"
    original = Path.open

    class Arquivo:
        def __init__(self, real):
            self.real = real

        def __enter__(self):
            self.real.__enter__()
            return self

        def __exit__(self, *args):
            return self.real.__exit__(*args)

        def write(self, texto):
            if json.loads(texto)["tipo"] == "tentativa":
                raise OSError("Registro indisponível")
            return self.real.write(texto)

        def flush(self):
            return self.real.flush()

    def abrir(self, *args, **kwargs):
        arquivo = original(self, *args, **kwargs)
        modo = args[0] if args else kwargs.get("mode", "r")
        return Arquivo(arquivo) if self == caminho and modo == "x" else arquivo

    def gerar(*_args):
        chamadas.append(True)
        raise httpx.ReadTimeout("SEGREDO")

    monkeypatch.setattr(Path, "open", abrir)
    with pytest.raises(OSError, match="Registro"):
        avaliacao.executar(manifesto, aprovacao_sha256=avaliacao.hash_lote(manifesto, repetir_transitorios=True),
                          previsao=10, saida=caminho, gerar=gerar, repetir_transitorios=True)
    assert chamadas == [True]
    assert len(caminho.read_text(encoding="utf-8").splitlines()) == 1
