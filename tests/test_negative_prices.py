"""aios-harness#67: hours of negative price, against docs/hand-example-negative-prices.md."""
import pytest

from billtocome import discount as d
from billtocome.cfd import top_up, top_up_with_rule


def test_rules_by_round():
    assert d.rule_for("Allocation Round 1") == d.rule_for("Investment Contract") == "none"
    assert d.rule_for("Allocation Round 2") == d.rule_for("Allocation Round 3") == "6h"
    assert all(d.rule_for(f"Allocation Round {i}") == "any" for i in (4, 5, 6, 7))


def test_fits_recorded():
    a, h = d.negative_fit("wind", "any"), d.negative_fit("wind", "6h")
    assert (round(a.intercept, 4), round(a.slope, 4), round(a.r2, 2)) == (-0.0508, 0.2936, 0.92)
    assert (round(h.intercept, 4), round(h.slope, 4), round(h.r2, 2)) == (-0.0204, 0.115, 0.82)
    assert d.negative_price("wind") == pytest.approx(-11.87, abs=0.01)


def test_wind_2030():
    nh = d.NegativeHours()
    assert nh(2030, "Offshore Wind", "any") == pytest.approx(0.0769, abs=0.0001)
    assert nh(2030, "Offshore Wind", "6h") == pytest.approx(0.0296, abs=0.0001)
    assert nh(2030, "Offshore Wind", "none") == 0.0
    assert nh(2030, "Nuclear", "any") == 0.0


def test_payments_hand_example():
    args = dict(strike=100, market=57.91, capture=0.854, mwh=1_000_000)
    assert top_up(**args) / 1e6 == pytest.approx(50.54, abs=0.01)
    assert top_up_with_rule(**args, neg_share=0.0296, neg_price=-11.87) / 1e6 == pytest.approx(47.23, abs=0.01)
    assert top_up_with_rule(**args, neg_share=0.0769, neg_price=-11.87) / 1e6 == pytest.approx(41.94, abs=0.01)
    assert top_up_with_rule(**args, neg_share=0.0, neg_price=-11.87) == top_up(**args)


def test_never_below_zero_or_above_one():
    steep = d.NegativeHours(slope_scale=3.0)
    for y in range(2026, 2051):
        assert 0.0 <= steep(y, "Solar PV", "any") <= 1.0
        assert 0.0 <= d.NegativeHours(slope_scale=0.1)(y, "Onshore Wind", "6h") <= 1.0
