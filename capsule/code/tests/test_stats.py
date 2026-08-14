"""Unit tests for the statistics helpers (no data, no network)."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from stats_util import wilson, prf, kappa_pabak, linear_trend_z  # noqa: E402


def test_wilson_known():
    p, lo, hi = wilson(92, 388)
    assert abs(p - 0.2371) < 1e-3
    assert abs(lo - 0.197) < 2e-3
    assert abs(hi - 0.282) < 2e-3


def test_wilson_zero_n():
    p, lo, hi = wilson(0, 0)
    assert math.isnan(p) and math.isnan(lo) and math.isnan(hi)


def test_prf_perfect():
    prec, rec, f1 = prf(10, 0, 0)
    assert prec == 1.0 and rec == 1.0 and f1 == 1.0


def test_kappa_perfect_agreement():
    k, pk = kappa_pabak(20, 0, 0, 20)
    assert abs(k - 1.0) < 1e-9
    assert abs(pk - 1.0) < 1e-9


def test_kappa_chance():
    # equal marginals, agreement at chance -> kappa ~ 0
    k, _ = kappa_pabak(25, 25, 25, 25)
    assert abs(k) < 1e-9


def test_trend_monotone_positive():
    x = [1, 1, 2, 2, 3, 3, 4, 4]
    y = [0, 0, 0, 1, 1, 1, 1, 1]
    assert linear_trend_z(x, y) > 0
