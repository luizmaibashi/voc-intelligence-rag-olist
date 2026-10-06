import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.eval import pool_candidatos as pool
from src.eval import calibrar_recusa as calibracao


class EncoderSintetico:
    def __init__(self):
        self.chamadas = []

    def get_sentence_embedding_dimension(self):
        return 2

    def encode(self, textos, **kwargs):
        self.chamadas.append(list(textos))
        return np.array([[1., 0.] if t.endswith("antigo") else [0., 1.] for t in textos], dtype=np.float32)


@pytest.fixture
def ambiente(tmp_path, monkeypatch):
    monkeypatch.setattr(pool, "RAIZ", tmp_path)
    (tmp_path / "data/processed").mkdir(parents=True)
    return tmp_path, EncoderSintetico()


def test_cache_reutiliza_mesma_entrada(ambiente):
    _, modelo = ambiente
    esperado = pool.embeddings_docs("minilm", modelo, "", ["antigo", "novo"])
    np.testing.assert_array_equal(pool.embeddings_docs("minilm", modelo, "", ["antigo", "novo"]), esperado)
    assert len(modelo.chamadas) == 1


@pytest.mark.parametrize("textos", [["novo", "novo"], ["novo", "antigo"]])
def test_cache_rejeita_conteudo_ou_ordem_alterados(ambiente, textos):
    _, modelo = ambiente
    pool.embeddings_docs("minilm", modelo, "", ["antigo", "novo"])
    obtido = pool.embeddings_docs("minilm", modelo, "", textos)
    esperado = np.array([[1., 0.] if t == "antigo" else [0., 1.] for t in textos])
    np.testing.assert_array_equal(obtido, esperado)
    assert len(modelo.chamadas) == 2


def test_cache_rejeita_prefixo_alterado(ambiente):
    _, modelo = ambiente
    pool.embeddings_docs("minilm", modelo, "", ["antigo"])
    pool.embeddings_docs("minilm", modelo, "passage: ", ["antigo"])
    assert modelo.chamadas == [["antigo"], ["passage: antigo"]]


def test_cache_rejeita_modelo_configurado_alterado(ambiente, monkeypatch):
    _, modelo = ambiente
    pool.embeddings_docs("minilm", modelo, "", ["antigo"])
    monkeypatch.setitem(pool.MODELOS, "minilm", ("outro-modelo", "", ""))
    pool.embeddings_docs("minilm", modelo, "", ["antigo"])
    assert len(modelo.chamadas) == 2


def test_cache_rejeita_versao_da_biblioteca_alterada(ambiente, monkeypatch):
    _, modelo = ambiente
    pool.embeddings_docs("minilm", modelo, "", ["antigo"])
    monkeypatch.setattr(pool, "version", lambda nome: "outra-versao")
    pool.embeddings_docs("minilm", modelo, "", ["antigo"])
    assert len(modelo.chamadas) == 2


def test_cache_rejeita_dimensao_alterada(ambiente):
    _, modelo = ambiente
    pool.embeddings_docs("minilm", modelo, "", ["antigo"])
    class Encoder3(EncoderSintetico):
        def get_sentence_embedding_dimension(self):
            return 3
        def encode(self, textos, **kwargs):
            return np.pad(super().encode(textos, **kwargs), ((0, 0), (0, 1)))
    novo = Encoder3()
    assert pool.embeddings_docs("minilm", novo, "", ["antigo"]).shape == (1, 3)
    assert len(novo.chamadas) == 1


@pytest.mark.parametrize("invalido", [np.zeros((1, 2)), np.ones((1, 3)), np.array([[np.nan, 0.]])])
def test_encoder_invalido_falha_sem_salvar_cache(ambiente, monkeypatch, invalido):
    raiz, modelo = ambiente
    monkeypatch.setattr(modelo, "encode", lambda *args, **kwargs: invalido)
    with pytest.raises(ValueError, match="encoder"):
        pool.embeddings_docs("minilm", modelo, "", ["antigo"])
    assert not (raiz / "data/processed/emb_minilm.npy").exists()


@pytest.mark.parametrize("dano", ["legado", "manifesto", "vetores", "arquivo"])
def test_cache_incompleto_ou_corrompido_regenera_com_aviso(ambiente, dano, caplog):
    raiz, modelo = ambiente
    cache = raiz / "data/processed/emb_minilm.npy"
    manifesto = cache.with_suffix(".json")
    pool.embeddings_docs("minilm", modelo, "", ["antigo"])
    if dano == "legado":
        manifesto.unlink(missing_ok=True)
    elif dano == "manifesto":
        manifesto.write_text("{invalido", encoding="utf-8")
    elif dano == "vetores":
        np.save(cache, np.array([[0., 1.]], dtype=np.float32))
    else:
        cache.write_bytes(b"arquivo corrompido")
    obtido = pool.embeddings_docs("minilm", modelo, "", ["antigo"])
    np.testing.assert_array_equal(obtido, [[1., 0.]])
    assert len(modelo.chamadas) == 2
    assert "cache" in caplog.text.lower()


def test_calibracao_usa_textos_distintos_e_cache_validado(ambiente, monkeypatch):
    raiz, modelo = ambiente
    class Encoder384(EncoderSintetico):
        def get_sentence_embedding_dimension(self):
            return 384
        def encode(self, textos, **kwargs):
            return np.pad(super().encode(textos, **kwargs), ((0, 0), (0, 382)))
    modelo = Encoder384()
    corpus = pd.DataFrame({"review_id": ["a", "b", "c"], "texto": ["antigo", "ANTIGO", "novo"],
                           "nota": [1, 5, 4], "freq_texto": [2, 2, 1]})
    corpus.to_parquet(raiz / "data/processed/corpus_reviews.parquet", index=False)
    (raiz / "data/eval").mkdir()
    pd.DataFrame({"id_pergunta": ["P01", "P15"], "pergunta": ["antigo", "novo"],
                  "tem_resposta": ["1", "0"]}).to_csv(raiz / "data/eval/perguntas.csv", sep=";", index=False)
    monkeypatch.setattr(calibracao, "RAIZ", raiz)
    monkeypatch.setattr(calibracao, "SentenceTransformer", lambda nome: modelo)
    # Evita reconfigurar o stream do pytest; preserva a saída para conferência.
    class Saida(io.StringIO):
        def reconfigure(self, **kwargs):
            pass
    saida = Saida()
    monkeypatch.setattr(calibracao.sys, "stdout", saida)
    calibracao.main()
    assert modelo.chamadas[0] == ["antigo", "novo"]
    assert (raiz / "data/processed/emb_minilm.json").exists()
    assert "P15" in saida.getvalue()
