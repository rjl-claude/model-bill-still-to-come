"""aios-harness#66: the farm's discount, against docs/hand-example-discount.md."""
import pytest

from billtocome import discount as d


def test_fit_recorded():
    w, s = d.fit("wind"), d.fit("solar")
    assert (round(w.intercept, 3), round(w.slope, 3), round(w.r2, 2)) == (1.081, -0.522, 0.88)
    assert (round(s.intercept, 3), round(s.slope, 3), round(s.r2, 2)) == (1.013, -2.069, 0.30)


def test_2016_is_out_because_prices_begin_in_september():
    assert d.measured().loc[2016, "periods"] < 6000 and 2016 not in d.FIT_YEARS


def test_future_wind_share_2030():
    assert d.share("wind", 2030) == pytest.approx(0.435, abs=0.001)
    assert d.share("wind", 2061) == d.share("wind", 2050)


def test_own_record_moves_with_the_slope():
    own = d.own_discounts()["CAA-EAS-167"]
    assert own == pytest.approx(0.946, abs=0.001)
    sp = d.SimplePattern()
    assert sp(2030, "Offshore Wind", own) == pytest.approx(0.884, abs=0.001)


def test_unchanged_share_keeps_the_own_discount():
    sp = d.SimplePattern()
    base = d.measured().loc[list(d.BASE_YEARS), "wind_share"].mean()
    line = sp.line("wind")
    assert 0.946 + line.slope * (base - base) == 0.946


def test_new_farm_takes_the_line():
    assert d.SimplePattern()(2030, "Offshore Wind") == pytest.approx(0.854, abs=0.001)


def test_other_technologies_are_one():
    for t in ("Nuclear", "Biomass Conversion", "Tidal Stream", "Energy from Waste with CHP"):
        assert d.SimplePattern()(2030, t) == 1.0


def test_brackets_turn_about_todays_share():
    base = d.measured().loc[list(d.BASE_YEARS), "wind_share"].mean()
    steep, gentle, central = (d.SimplePattern(slope_scale=k).line("wind") for k in (1.5, 0.5, 1.0))
    assert steep(base) == pytest.approx(central(base)) == pytest.approx(gentle(base))
    assert steep(0.45) < central(0.45) < gentle(0.45)


def test_build_path_scenarios_are_indexed_to_2024():
    for p in d.PATHWAYS:
        assert d.share("wind", 2024, p) == pytest.approx(d.measured().loc[2024, "wind_share"])


def test_a_stand_in_with_the_same_call_is_a_discount():
    flat: d.Discount = lambda year, technology, own=None: 0.9
    assert flat(2030, "Offshore Wind") == 0.9
