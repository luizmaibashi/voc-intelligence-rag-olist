"""O executor E05 antigo pertence ao contrato da tag; novo schema bloqueia replay."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.eval import reavaliar_e05 as foco


def test_hash_historico_e05_nao_libera_contrato_novo(tmp_path, monkeypatch):
    monkeypatch.setattr(foco.lote, "version", lambda _: "1.75.0")
    monkeypatch.setattr(foco.lote, "_criar_gerador", lambda: pytest.fail("cliente criado"))
    manifesto = foco.lote.carregar_manifesto(
        Path(__file__).resolve().parents[1] / "data/eval/geracao_casos.json")
    assert foco.lote.hash_lote(manifesto, repetir_transitorios=True) != foco.HASH_ORIGEM
    saida = tmp_path / "e05.jsonl"
    with pytest.raises(ValueError, match="divergem"):
        foco.executar(manifesto, aprovacao_sha256=foco.HASH_ORIGEM,
                      previsao=1, saida=saida, gerar=lambda *_: pytest.fail("chamada"))
    assert not saida.exists()
