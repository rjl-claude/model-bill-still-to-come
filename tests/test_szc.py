"""aios-harness#82 (Stage 3): the Sizewell C line, against docs/hand-example-szc.md."""
import pytest

from billtocome import szc
from billtocome.scenario import Scenario


@pytest.fixture(scope="module")
def ln():
    return szc.build()


def test_licence_and_notice_figures():
    assert szc.DAY1_RAB == 5_197_977_481.50 and szc.FIRST_CY_AR == 1_443_625_216.26
    assert szc.LRT == 40_509_000_000 and szc.HRT == 47_720_000_000 and szc.IWACC == 0.0673


def test_first_charging_year_fits_the_secretary_of_states_allowed_revenue():
    k = szc.other_share()
    c = szc.charging_years(szc.LRT).set_index("charging_year").loc[[2025, 2026]]
    vv = szc.variable_values()
    pi = vv.loc[[2025, 2026], "CPIHt+forecast"] / szc.cpih_fy(2024)
    ar = ((c.roc * (1 + k) + c.opex + c.sbc + c.cda + c.fdp) * pi).sum()
    assert ar == pytest.approx(szc.FIRST_CY_AR, rel=1e-9)
    assert k == pytest.approx(-0.0766, abs=0.0005)


def test_hand_example_2030_31(ln):
    c = ln.tables["szc_charging_years"].set_index("charging_year").loc[2030]
    assert c.opening_rab / 1e9 == pytest.approx(16.192, abs=0.001)
    assert c.closing_rab / 1e9 == pytest.approx(18.686, abs=0.001)
    assert c.roc / 1e6 == pytest.approx(1173.6, abs=0.1)
    assert c.opex / 1e6 == pytest.approx(165.3, abs=0.1)
    assert c.allowed / 1e6 == pytest.approx(1259.6, abs=0.1)


def test_rab_reaches_the_build_cost_at_cod(ln):
    c = ln.tables["szc_charging_years"]
    assert c.closing_rab.iloc[-1] == pytest.approx(szc.LRT, rel=1e-9)


def test_levy_runs_both_ways_and_ends_2099(ln):
    y = ln.tables["szc_years"]
    assert y.year.max() == 2099 and (y.payment < 0).any()
    assert (y[y.year < 2040].market == 0).all()


def test_build_cost_bracket_moves_the_levy():
    lo = szc.build(Scenario(szc_cost=38e9)).rows.cash.sum()
    hi = szc.build(Scenario(szc_cost=47.72e9)).rows.cash.sum()
    assert lo < szc.build().rows.cash.sum() < hi
