import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import demo
from src.retrieval import cache as cache_vetores


class ModeloContador:
    """Encoder determinístico sem rede; conta só a codificação do corpus."""

    def __init__(self):
        self.lotes = []

    def encode(self, textos, **kwargs):
        def vetor(texto):
            v = np.zeros(384, dtype=np.float32)
            v[0 if "atras" in texto.lower() else 1] = 1
            return v
        if isinstance(textos, str):
            return vetor(textos)
        self.lotes.append(list(textos))
        return np.stack([vetor(t) for t in textos])


def _ids(saida):
    return [f["review_id"] for f in saida["fontes"]]


def test_cache_reaproveitado_nao_codifica_o_corpus_de_novo(tmp_path):
    modelo, caminho = ModeloContador(), tmp_path / "emb.npy"
    primeira = demo.recuperar(demo.corpus_sintetico(), "atraso", modelo, cache_vetores=caminho)
    segunda = demo.recuperar(demo.corpus_sintetico(), "atraso", modelo, cache_vetores=caminho)
    assert len(modelo.lotes) == 1
    assert _ids(primeira) == _ids(segunda)
    assert primeira["fontes"] == segunda["fontes"]


def test_cache_e_execucao_sem_cache_devolvem_o_mesmo_contexto(tmp_path):
    corpus = demo.corpus_sintetico()
    sem_cache = demo.recuperar(corpus, "atraso", ModeloContador(), situacao_entrega="atrasado")
    demo.recuperar(corpus, "atraso", ModeloContador(), cache_vetores=tmp_path / "emb.npy")
    lendo = demo.recuperar(corpus, "atraso", ModeloContador(), situacao_entrega="atrasado",
                           cache_vetores=tmp_path / "emb.npy")
    assert lendo["fontes"] == sem_cache["fontes"]


def test_sem_caminho_nada_e_gravado(tmp_path):
    demo.recuperar(demo.corpus_sintetico(), "atraso", ModeloContador())
    assert not demo.CACHE_VETORES.exists()
    assert not any(tmp_path.rglob("*.npy"))


def test_texto_alterado_regenera(tmp_path):
    modelo, caminho = ModeloContador(), tmp_path / "emb.npy"
    corpus = demo.corpus_sintetico()
    demo.recuperar(corpus, "atraso", modelo, cache_vetores=caminho)
    corpus.loc[2, "texto"] = "A entrega atrasou muito."
    saida = demo.recuperar(corpus, "atraso", modelo, k=3, cache_vetores=caminho)
    assert len(modelo.lotes) == 2
    assert "sintetico-03" in _ids(saida)


def test_ordem_alterada_regenera(tmp_path):
    modelo, caminho = ModeloContador(), tmp_path / "emb.npy"
    corpus = demo.corpus_sintetico()
    demo.recuperar(corpus, "atraso", modelo, cache_vetores=caminho)
    demo.recuperar(corpus.iloc[::-1].reset_index(drop=True), "atraso", modelo,
                   cache_vetores=caminho)
    assert len(modelo.lotes) == 2


def test_modelo_configurado_diferente_regenera(tmp_path, monkeypatch):
    modelo, caminho = ModeloContador(), tmp_path / "emb.npy"
    demo.recuperar(demo.corpus_sintetico(), "atraso", modelo, cache_vetores=caminho)
    monkeypatch.setattr(demo, "MODELO", "outro-modelo")
    demo.recuperar(demo.corpus_sintetico(), "atraso", modelo, cache_vetores=caminho)
    assert len(modelo.lotes) == 2


@pytest.mark.parametrize("dano", ["truncado", "digest", "sem_manifesto"])
def test_cache_danificado_regenera_com_aviso(tmp_path, dano, caplog):
    modelo, caminho = ModeloContador(), tmp_path / "emb.npy"
    demo.recuperar(demo.corpus_sintetico(), "atraso", modelo, cache_vetores=caminho)
    manifesto = caminho.with_suffix(".json")
    if dano == "truncado":
        caminho.write_bytes(caminho.read_bytes()[:100])
    elif dano == "digest":
        dados = json.loads(manifesto.read_text(encoding="utf-8"))
        dados["vetores_sha256"] = "0" * 64
        manifesto.write_text(json.dumps(dados), encoding="utf-8")
    else:
        manifesto.unlink()
    saida = demo.recuperar(demo.corpus_sintetico(), "atraso", modelo, cache_vetores=caminho)
    assert len(modelo.lotes) == 2
    assert "cache" in caplog.text.lower()
    assert _ids(saida)


def test_interrupcao_na_gravacao_nao_deixa_cache_valido(tmp_path, monkeypatch):
    modelo, caminho = ModeloContador(), tmp_path / "emb.npy"
    substituir = cache_vetores.os.replace
    chamadas = []

    def falha_no_manifesto(origem, destino):
        chamadas.append(destino)
        if str(destino).endswith(".json"):
            raise KeyboardInterrupt
        substituir(origem, destino)

    monkeypatch.setattr(cache_vetores.os, "replace", falha_no_manifesto)
    with pytest.raises(KeyboardInterrupt):
        demo.recuperar(demo.corpus_sintetico(), "atraso", modelo, cache_vetores=caminho)
    monkeypatch.setattr(cache_vetores.os, "replace", substituir)
    demo.recuperar(demo.corpus_sintetico(), "atraso", modelo, cache_vetores=caminho)
    assert len(modelo.lotes) == 2
    assert not list(tmp_path.glob("*.tmp*"))


def test_gravacao_completa_nao_deixa_temporario(tmp_path):
    demo.recuperar(demo.corpus_sintetico(), "atraso", ModeloContador(),
                   cache_vetores=tmp_path / "emb.npy")
    assert sorted(p.name for p in tmp_path.iterdir()) == ["emb.json", "emb.npy"]


def test_encoder_invalido_falha_sem_gravar(tmp_path):
    class ModeloQuebrado(ModeloContador):
        def encode(self, textos, **kwargs):
            if isinstance(textos, str):
                return super().encode(textos)
            return np.zeros((len(textos), 384), dtype=np.float32)
    with pytest.raises(ValueError, match="encoder"):
        demo.recuperar(demo.corpus_sintetico(), "atraso", ModeloQuebrado(),
                       cache_vetores=tmp_path / "emb.npy")
    assert not any(tmp_path.iterdir())


@pytest.mark.parametrize("acao", [["--acao", "buscar"],
                                  ["--acao", "responder", "--gerador", "falso"]])
def test_cli_usa_o_cache_entre_comandos(monkeypatch, acao):
    modelo = ModeloContador()
    monkeypatch.setattr(demo, "carregar_corpus", lambda caminho: demo.corpus_sintetico())
    monkeypatch.setattr(demo, "carregar_modelo", lambda: modelo)
    args = acao + ["--pergunta", "atraso"]
    assert demo.main(args) == 0
    assert demo.main(args) == 0
    assert len(modelo.lotes) == 1
    assert demo.CACHE_VETORES.exists()


def test_ensaio_sintetico_nao_usa_cache(monkeypatch):
    monkeypatch.setattr(demo, "carregar_modelo", ModeloContador)
    assert demo.main(["--acao", "ensaio-sintetico"]) == 0
    assert not demo.CACHE_VETORES.exists()
