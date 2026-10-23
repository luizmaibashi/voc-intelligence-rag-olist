import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import demo


class ModeloFalso:
    def encode(self, textos, **kwargs):
        def vetor(texto):
            v = np.zeros(384, dtype=np.float32)
            v[0 if "atras" in texto.lower() else 1] = 1
            return v
        return vetor(textos) if isinstance(textos, str) else np.stack([vetor(t) for t in textos])


def test_recuperar_preserva_filtro_e_fontes():
    corpus = demo.corpus_sintetico()
    corpus.loc[2, "texto"] = corpus.loc[0, "texto"]
    corpus.loc[0, "situacao_entrega"] = "no_prazo"
    corpus.loc[2, "situacao_entrega"] = "atrasado"
    saida = demo.recuperar(corpus, "atraso", ModeloFalso(), k=10, situacao_entrega="atrasado")
    assert {f["review_id"] for f in saida["fontes"]} == {"sintetico-02", "sintetico-03"}
    assert saida["filtros"]["situacao_entrega"] == "atrasado"
    for f in saida["fontes"]:
        assert f["texto"] == corpus.set_index("review_id").loc[f["review_id"], "texto"]
    assert "resposta_simulada" not in saida


@pytest.mark.parametrize("filtro", [{"k": 0}, {"k": True}, {"nota_min": 0},
                                    {"nota_max": 6}, {"situacao_entrega": "atrasadoo"}])
def test_filtro_invalido_falha(filtro):
    with pytest.raises(ValueError):
        demo.recuperar(demo.corpus_sintetico(), "atraso", ModeloFalso(), **filtro)


@pytest.mark.parametrize("pergunta", ["", " ", None])
def test_pergunta_invalida_falha(pergunta):
    with pytest.raises(ValueError):
        demo.recuperar(demo.corpus_sintetico(), pergunta, ModeloFalso())


def test_contagem_independe_de_fontes_topk():
    corpus = demo.corpus_sintetico()
    demo.recuperar(corpus, "atraso", ModeloFalso(), k=1)
    saida = demo.quantificar(corpus)
    assert saida["resultado"]["atrasadas"] == 2
    assert saida["resultado"]["entregues"] == 3
    assert saida["resultado"]["proporcao"] == pytest.approx(2 / 3)
    assert "2 de 3" in saida["resumo"]
    assert "IC95%" in saida["resumo"] and "2018-01-01" in saida["resumo"]


def test_ensaio_e_simulacao_com_citacoes_validas_e_recusa():
    saida = demo.ensaio_sintetico(ModeloFalso())
    positiva, negativa = saida["consultas"]
    assert positiva["resposta_simulada"]["status"] == "respondida"
    assert {f["review_id"] for f in positiva["fontes_citadas"]} == set(
        positiva["resposta_simulada"]["review_ids"])
    assert negativa["resposta_simulada"]["status"] == "sem_evidencia"
    assert negativa["fontes_citadas"] == []
    assert saida["gerador"] == "falso_local" and saida["gate_demo"] == "bloqueado"


def test_modelo_so_offline(monkeypatch):
    chamadas = []
    monkeypatch.setattr(demo, "SentenceTransformer", lambda *a, **k: chamadas.append((a, k)))
    demo.carregar_modelo()
    assert chamadas == [((demo.MODELO,), {"local_files_only": True})]


def test_cli_contar_sem_encoder_gerador_ou_rede(tmp_path, monkeypatch, capsys):
    corpus = tmp_path / "corpus.parquet"
    demo.corpus_sintetico().to_parquet(corpus, index=False)
    monkeypatch.setattr(demo, "carregar_modelo", lambda: pytest.fail("modelo não necessário"))
    assert demo.main(["--acao", "contar", "--corpus", str(corpus)]) == 0
    assert json.loads(capsys.readouterr().out)["resultado"]["entregues"] == 3


def test_cli_ensaio_ignora_corpus_real_e_nao_altera_arquivo(monkeypatch, tmp_path, capsys):
    corpus = tmp_path / "corpus.parquet"
    corpus.write_bytes(b"preservar")
    monkeypatch.setattr(demo, "carregar_modelo", lambda: ModeloFalso())
    assert demo.main(["--acao", "ensaio-sintetico", "--corpus", str(corpus)]) == 0
    assert json.loads(capsys.readouterr().out)["modo"] == "simulacao_sintetica"
    assert corpus.read_bytes() == b"preservar"


@pytest.mark.parametrize("args", [["--acao", "buscar"], ["--acao", "contar", "--nota-min", "1"],
                                  ["--acao", "ensaio-sintetico", "--pergunta", "x"]])
def test_cli_rejeita_entrada_ignorada(args):
    with pytest.raises(SystemExit) as erro:
        demo.main(args)
    assert erro.value.code == 2


def test_cli_arquivo_ausente_falha(tmp_path, capsys):
    assert demo.main(["--acao", "contar", "--corpus", str(tmp_path / "ausente")]) == 2
    assert "Falha local" in capsys.readouterr().err


def test_filtro_de_periodo_e_categoria_aparecem_na_busca():
    corpus = demo.corpus_sintetico()
    saida = demo.recuperar(corpus, "atraso", ModeloFalso(), categoria="sintetica",
                          compra_de="2018-02-01", compra_ate="2018-02-01")
    assert [f["review_id"] for f in saida["fontes"]] == ["sintetico-02"]
    assert saida["filtros"]["compra_de"] == "2018-02-01"


def test_recorte_sem_resultado_recusa_local_sem_gerador(monkeypatch):
    monkeypatch.setattr(demo, "_criar_gerador", lambda: pytest.fail("não criar cliente"))
    saida = demo.responder_cli(demo.corpus_sintetico(), "atraso", ModeloFalso(),
                               categoria="moveis", executar=True, aprovacao_sha256="qualquer")
    assert saida["modo"] == "recusa_local_sem_api"
    assert saida["resposta"]["status"] == "sem_evidencia"


def test_filtros_ausentes_preservam_chaves_historicas_do_hash():
    saida = demo.recuperar(demo.corpus_sintetico(), "atraso", ModeloFalso())
    assert set(saida["filtros"]) == {"k", "nota_min", "nota_max", "situacao_entrega"}


def test_corpus_sem_data_aceita_busca_antiga_mas_recusa_filtro_temporal():
    corpus = demo.corpus_sintetico().drop(columns="data_compra")
    assert demo.recuperar(corpus, "atraso", ModeloFalso())["fontes"]
    with pytest.raises(ValueError, match="data_compra"):
        demo.recuperar(corpus, "atraso", ModeloFalso(), compra_de="2018-01-01")
