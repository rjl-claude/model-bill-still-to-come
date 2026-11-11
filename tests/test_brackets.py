"""aios-harness#85 (Stage 6): the last five brackets and the tornado, against docs/hand-example-brackets.md."""
import pytest

from billtocome import brackets, output, prices, szc
from billtocome.discount import PATHWAYS, SimpleFit
from billtocome.scenario import BRACKETS, LATER, Scenario


def test_every_bracket_in_the_build_plan_is_declared():
    assert LATER == ()
    assert {b.name for b in BRACKETS} >= {"Forward prices, then Annex M", "Decline with age", "Output level",
                                          "Build path", "Sizewell C return after 2039"}


def test_forward_then_annex_m():
    f, a = prices.forward_then_annex_m(), prices.annex_m_path()
    assert f[2026] == pytest.approx(81.59, abs=0.01)
    assert f[2027] == pytest.approx(72.84, abs=0.01)
    assert all(f[y] == a[y] for y in a if y >= 2028) and set(f) == set(a)


def test_decline_ends():
    for d, wind, solar in (("gentler", 0.0017, 0.005), ("central", 0.016, 0.005), ("steeper", 0.054, 0.008)):
        s = Scenario(decline=d)
        assert (s.wind_decline, s.solar_decline) == (wind, solar)
    assert output.yearly_mwh(1, 0.40, 2020, 2034, decline=0.054) / 8760 == pytest.approx(0.2296, abs=1e-4)


@pytest.mark.parametrize("technology, start, lf", [
    ("Offshore Wind", 2028, 0.65), ("Offshore Wind", 2033, 0.69), ("Onshore Wind", 2024, 0.45),
    ("Remote Island Wind", 2027, 0.45), ("Solar PV", 2031, 0.11), ("Floating Offshore Wind", 2040, 0.69),
])
def test_desnz_2023_load_factor(technology, start, lf):
    assert output.desnz_2023_lf(technology, start) == lf


def test_desnz_2023_level_is_cfd_wind_and_solar_only():
    assert output.desnz_2023_lf("Tidal Stream", 2028) is None and output.desnz_2023_lf("Dedicated Biomass", 2020) is None


def test_sizewell_c_return_low_end():
    # The low end is the Green Book rate (Richard, 5 Nov): 3.00% in the Green Book 2026, para 6.54 (Richard, 11 Nov, aios-harness#257)
    b = next(b for b in BRACKETS if b.name == "Sizewell C return after 2039")
    assert (b.low.szc_ops_return, b.high.szc_ops_return) == (0.030, 0.0673)
    y = szc.build(b.low).tables["szc_years"].set_index("year")
    c = szc.build(Scenario()).tables["szc_years"].set_index("year")
    dep = 40.509e9 / 60
    assert c.allowed_2425[2040] - dep == pytest.approx(2.704e9, rel=1e-3)
    assert y.allowed_2425[2040] - dep == pytest.approx(1.205e9, rel=1e-3)
    assert (y.allowed_2425.loc[:2039] == c.allowed_2425.loc[:2039]).all()


def test_build_path_ends_are_fes_pathways():
    b = next(b for b in BRACKETS if b.name == "Build path")
    assert {b.low.market.path, b.high.market.path} <= set(PATHWAYS)


@pytest.fixture(scope="module")
def tornado():
    return brackets.tornado()


def test_no_bracket_moves_nothing(tornado):
    t = tornado.set_index("bracket")
    assert list(t.index) == list(t.sort_values("swing", ascending=False).index)  # ranked
    assert set(t.index) == {b.name for b in BRACKETS}
    dead = t[(t.low_bill - t.high_bill).abs() < 1e6]
    assert dead.empty, list(dead.index)


def test_range_is_the_extremes(tornado):
    lo, hi = brackets.range_of(tornado)
    assert lo == min(tornado.low_bill.min(), tornado.high_bill.min())
    assert hi == max(tornado.low_bill.max(), tornado.high_bill.max())
    assert lo < tornado.central.iloc[0] < hi


def test_build_path_ends_are_the_extreme_pathways(tornado):
    b = next(b for b in BRACKETS if b.name == "Build path")
    runs = {p: brackets.headline(brackets.run_one(Scenario(market=SimpleFit(path=p)))) for p in PATHWAYS}
    t = tornado.set_index("bracket").loc["Build path"]
    assert t.low_bill == min(runs.values()) == runs[b.low.market.path]
    assert t.high_bill == max(runs.values()) == runs[b.high.market.path]


def test_tornado_figures_are_keys_in_the_results_file(tornado):
    from billtocome import figures
    f = figures.bracket_keys(tornado)
    t = tornado.set_index("bracket")
    assert f["bracket.annex_m_prices.low.cash"] == t.loc["Annex M prices", "low_bill"]
    assert f["bracket.sizewell_c_return_after_2039.high.pv_hurdle"] == t.loc["Sizewell C return after 2039", "high_bill_pv_hurdle"]
    assert f["bracket.households_share.swing.cash"] == t.loc["Households' share", "swing"]
    assert f["bracket.forward_prices_then_annex_m.rank.cash"] == 1 + list(t.index).index("Forward prices, then Annex M")
    assert (f["range.low.cash"], f["range.high.cash"]) == brackets.range_of(tornado)
    assert (f["range.low.pv_green_book"], f["range.high.pv_green_book"]) == brackets.range_of(tornado, "pv_green_book")
