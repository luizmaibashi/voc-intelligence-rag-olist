import runpy
from pathlib import Path

import pytest


def test_eda_importa_sem_main_nem_alterar_relatorio():
    raiz = Path(__file__).resolve().parents[1]
    relatorio = raiz / "reports/eda_olist.md"
    original = relatorio.read_bytes()
    modulo = runpy.run_path(str(raiz / "src/eda/01_eda_reviews.py"), run_name="teste_importacao")
    assert callable(modulo["main"])
    assert relatorio.read_bytes() == original


@pytest.mark.parametrize("k,n", [(0, 10), (10, 10), (2, 3)])
def test_eda_wilson_concorda_com_contagem(k, n):
    from statsmodels.stats.proportion import proportion_confint
    from src.analytics.frequencia import _intervalo_wilson
    assert _intervalo_wilson(k, n) == pytest.approx(
        proportion_confint(k, n, method="wilson"), abs=1e-5)
