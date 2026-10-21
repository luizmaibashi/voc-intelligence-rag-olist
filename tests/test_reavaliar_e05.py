import copy
import json
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.eval import reavaliar_e05 as foco


@pytest.fixture
def manifesto(monkeypatch):
    monkeypatch.setattr(foco.lote, "version", lambda _: "1.75.0")
    monkeypatch.setattr("src.rag.tentativas.time.sleep", lambda _: None)
    return foco.lote.carregar_manifesto(
        Path(__file__).resolve().parents[1] / "data/eval/geracao_casos.json")


def executar(manifesto, tmp_path, gerar):
    saida = tmp_path / "e05.jsonl"
    foco.executar(manifesto, aprovacao_sha256=foco.HASH_ORIGEM,
                  previsao=1, saida=saida, gerar=gerar)
    return [json.loads(l) for l in saida.read_text(encoding="utf-8").splitlines()]


def boa():
    return {"status": "respondida", "texto": "Relato de divergência da foto.",
            "review_ids": ["candidato-e05"]}


def test_previa_sem_cliente_e_manifesto_intacto(manifesto, monkeypatch):
    original = copy.deepcopy(manifesto)
    monkeypatch.setattr(foco.lote, "_criar_gerador", lambda: pytest.fail("cliente"))
    p = foco.previa(manifesto)
    assert p["caso"]["id"] == "E05"
    assert p["hash_lote_origem"] == foco.HASH_ORIGEM
    assert manifesto == original
    assert p["configuracao"]["attempts"] == 1
    assert p["configuracao"]["politica_repeticao"]["max_tentativas"] == 2


def test_so_e05_com_previsao_antes_da_chamada(manifesto, tmp_path):
    caso = next(c for c in manifesto["casos"] if c["id"] == "E05")
    chamadas = []
    def gerar(pergunta, evidencias):
        cab = json.loads((tmp_path / "e05.jsonl").read_text(encoding="utf-8").splitlines()[0])
        assert cab["previsao"] == 1
        assert cab["caso"] == caso
        chamadas.append((pergunta, evidencias))
        assert pergunta == caso["pergunta"] and evidencias == caso["evidencias"]
        return boa()
    linhas = executar(manifesto, tmp_path, gerar)
    assert len(chamadas) == 1
    assert linhas[-2]["julgamento_semantico"] == "pendente"
    assert linhas[-1]["gate_demo"] == "bloqueado"
    assert linhas[-1]["chamadas_externas"] == 1
    assert len(linhas[0]["codigo_sha256"]) == 5


@pytest.mark.parametrize("defeito", ["texto", "modelo", "sdk", "caso_ausente", "hash"])
def test_drift_bloqueia_antes_de_arquivo_cliente(manifesto, tmp_path, monkeypatch, defeito):
    hash_aprovacao = foco.HASH_ORIGEM
    if defeito == "texto":
        manifesto["casos"][4]["evidencias"][0]["texto"] += " Mudou."
    elif defeito == "modelo":
        manifesto["modelo"] = "outro"
    elif defeito == "sdk":
        monkeypatch.setattr(foco.lote, "version", lambda _: "outra")
    elif defeito == "caso_ausente":
        manifesto["casos"].pop()
    else:
        hash_aprovacao = "0" * 64
    monkeypatch.setattr(foco.lote, "_criar_gerador", lambda: pytest.fail("cliente"))
    saida = tmp_path / "novo.jsonl"
    with pytest.raises(ValueError):
        foco.executar(manifesto, aprovacao_sha256=hash_aprovacao, previsao=1, saida=saida)
    assert not saida.exists()


@pytest.mark.parametrize("previsao", [True, None, "1", -1, 2])
def test_previsao_invalida_bloqueia(manifesto, tmp_path, previsao):
    saida = tmp_path / "novo.jsonl"
    with pytest.raises(ValueError):
        foco.executar(manifesto, aprovacao_sha256=foco.HASH_ORIGEM,
                      previsao=previsao, saida=saida, gerar=lambda *_: pytest.fail("API"))
    assert not saida.exists()


def test_arquivo_existente_preservado(manifesto, tmp_path):
    saida = tmp_path / "e05.jsonl"
    saida.write_text("preservar", encoding="utf-8")
    with pytest.raises(FileExistsError):
        executar(manifesto, tmp_path, lambda *_: pytest.fail("API"))
    assert saida.read_text() == "preservar"


@pytest.mark.parametrize("recupera", [True, False])
def test_transitorio_limite_e_historico(manifesto, tmp_path, recupera):
    chamadas = []
    def gerar(*_):
        chamadas.append(1)
        if len(chamadas) == 1 or not recupera:
            raise httpx.ReadTimeout("SEGREDO_NAO_GRAVAR")
        return boa()
    linhas = executar(manifesto, tmp_path, gerar)
    tentativas = [l for l in linhas if l["tipo"] == "tentativa"]
    assert len(chamadas) == len(tentativas) == 2
    assert tentativas[0]["erro_integracao"]["classe"] == "ReadTimeout"
    assert tentativas[0]["espera_planejada_s"] == 2
    assert tentativas[1]["havera_repeticao"] is False
    assert linhas[-2]["resposta_aplicacao"]["status"] == ("respondida" if recupera else "erro_geracao")
    assert "SEGREDO_NAO_GRAVAR" not in json.dumps(linhas)


@pytest.mark.parametrize("modo", ["permanente", "invalida", "recusa"])
def test_sem_repeticao_por_erro_local_saida_ou_recusa(manifesto, tmp_path, modo):
    chamadas = []
    def gerar(*_):
        chamadas.append(1)
        if modo == "permanente":
            raise ValueError("SEGREDO_NAO_GRAVAR")
        if modo == "invalida":
            return {**boa(), "review_ids": ["inventada"]}
        return {"status": "sem_evidencia", "texto": "Recusa.", "review_ids": []}
    linhas = executar(manifesto, tmp_path, gerar)
    assert len(chamadas) == 1
    assert linhas[-2]["status_esperado_compativel"] is False
    assert "SEGREDO_NAO_GRAVAR" not in json.dumps(linhas)


def test_falha_registro_para_sem_repetir(manifesto, tmp_path, monkeypatch):
    original_open = Path.open
    chamadas = []
    class ArquivoFalho:
        def __init__(self, arquivo):
            self.arquivo = arquivo
        def __enter__(self):
            return self
        def __exit__(self, *args):
            self.arquivo.close()
        def write(self, texto):
            if json.loads(texto)["tipo"] == "tentativa":
                raise OSError("disco")
            return self.arquivo.write(texto)
        def flush(self):
            self.arquivo.flush()
    def abrir(path, mode="r", *args, **kwargs):
        arquivo = original_open(path, mode, *args, **kwargs)
        return ArquivoFalho(arquivo) if mode == "x" else arquivo
    monkeypatch.setattr(Path, "open", abrir)
    def gerar(*_):
        chamadas.append(1)
        raise httpx.ReadTimeout("falha")
    with pytest.raises(OSError):
        executar(manifesto, tmp_path, gerar)
    assert len(chamadas) == 1


def test_interrupcao_preserva_cabecalho(manifesto, tmp_path):
    def gerar(*_):
        raise KeyboardInterrupt
    with pytest.raises(KeyboardInterrupt):
        executar(manifesto, tmp_path, gerar)
    linhas = (tmp_path / "e05.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(linhas) == 1
    assert json.loads(linhas[0])["previsao"] == 1
