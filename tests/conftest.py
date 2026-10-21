import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture(autouse=True)
def cache_vetores_temporario(tmp_path, monkeypatch):
    # Nenhum teste grava vetores sintéticos no cache real de data/processed.
    from src import demo
    monkeypatch.setattr(demo, "CACHE_VETORES", tmp_path / "cache" / "emb_busca_minilm.npy",
                        raising=False)
