"""aios-harness#84 (Stage 5): present values, against docs/hand-example-present-value.md."""
import pandas as pd
import pytest

from billtocome import model, present_value as pv
from billtocome.model import Results
from billtocome.scenario import Scenario


def stream(technology="Offshore Wind", line="CfD renewables"):
    rows = [dict(line=line, item="A farm", technology=technology, built=True, payer="households", year=y, cash=c)
            for y, c in ((2026, 10e6), (2027, 20e6), (2028, -5e6))]
    return Results(table=pd.DataFrame(rows, columns=model.COLUMNS), scenario=Scenario())


def test_three_year_stream_green_book():
    t = pv.present_value(stream(), "green_book")
    assert list(t.pv / 1e6) == pytest.approx([10.0, 19.417, -4.713], abs=1e-3)
    assert t.pv.sum() / 1e6 == pytest.approx(24.704, abs=1e-3)


def test_three_year_stream_hurdle():
    t = pv.present_value(stream(), "hurdle")
    assert list(t.pv / 1e6) == pytest.approx([10.0, 18.365, -4.216], abs=1e-3)
    assert t.pv.sum() / 1e6 == pytest.approx(24.149, abs=1e-3)
    assert pv.present_value(stream("Nuclear", "Hinkley Point C"), "hurdle").pv.sum() / 1e6 == pytest.approx(24.350, abs=1e-3)


def test_green_book_2026_table_8_factors():
    """The Green Book 2026, para 6.57, Table 8: years 0 to 5 at 3.00%."""
    assert [round(pv.green_book_factor(2026 + t), 4) for t in range(6)] == [1.0, 0.9709, 0.9426, 0.9151, 0.8885, 0.8626]


def test_green_book_step_after_year_30():
    """Para 6.54 (revised 28 Oct 2026): 3.00% for years 1 to 30, 2.50% for years 31 to 75 (aios-harness#255)."""
    assert pv.green_book_factor(2026) == 1.0
    assert pv.green_book_factor(2056) == pytest.approx(0.411987, abs=1e-6)
    assert pv.green_book_factor(2057) == pytest.approx(0.401938, abs=1e-6)
    assert pv.green_book_factor(2099) == pytest.approx(0.142481, abs=1e-6)


@pytest.mark.parametrize("technology, rate", [
    ("Solar PV", 0.076), ("Photovoltaic with a DNC of 50kW or less", 0.076), ("Onshore Wind", 0.076),
    ("Remote Island Wind", 0.076), ("Wind", 0.076), ("Hydro with a DNC of 20MW or less", 0.076),
    ("Offshore Wind", 0.089), ("Offshore wind - demonstration turbines", 0.089),
    ("Floating Offshore Wind", 0.101), ("Offshore wind - floating turbines", 0.101),
    ("Tidal Stream", 0.101), ("Geothermal", 0.101), ("Nuclear", 0.0673),
    ("Dedicated Biomass", 0.089), ("Fuelled", 0.089), ("Storage - Pumped", 0.089), ("Interconnector", 0.089),
    ("Anaerobic digestion", 0.089), ("Combined Cycle Gas Turbine (CCGT)", 0.089),
])
def test_hurdle_rate_by_technology(technology, rate):
    assert pv.hurdle_rate(technology) == rate


@pytest.fixture(scope="module")
def central():
    r = model.run()
    return r, pv.present_value(r, "green_book"), pv.present_value(r, "hurdle")


def test_every_row_has_a_present_value(central):
    r, gb, h = central
    for t in (gb, h):
        assert len(t) == len(r.table) and t.pv.notna().all()
        assert (t.drop(columns="pv") == r.table).all().all()


def test_vat_present_value_follows_the_zero_rate(central):
    """Version 1.2.5: VAT's present value is its year's rate times households' present value of its line: 5% on 273
    of 2026's 365 days and 184 of 2027's (0% 1 Oct 2026 to 30 Jun 2027), 5% after."""
    _, gb, h = central
    rate = {2026: 0.05 * 273 / 365, 2027: 0.05 * 184 / 365}
    for t in (gb, h):
        hh = t[(t.payer == "households") & (t.line != "VAT")].groupby("year").pv.sum()
        vat = t[t.line == "VAT"].groupby("year").pv.sum()
        assert ((vat - hh * [rate.get(y, 0.05) for y in hh.index]).abs() < 1.0).all()


def test_transfers_still_net_to_zero(central):
    _, gb, h = central
    for t in (gb, h):
        moved = t[t.technology.fillna("").eq("") & (t.line != "VAT")]
        assert abs(moved.groupby(["line", "item", "year"]).pv.sum()).max() < 1.0


def test_present_value_below_cash(central):
    r, gb, h = central
    cash = r.table.cash.sum()
    assert h.pv.sum() < gb.pv.sum() < cash
