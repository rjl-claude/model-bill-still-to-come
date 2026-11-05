"""aios-harness#80 (Stage 1): one run, one Scenario, the Scheme line seam, Results and in-between tables."""
import dataclasses
import datetime as dt

import pandas as pd
import pytest

from billtocome import model, prices
from billtocome.scenario import BRACKETS, LATER, Scenario

CFD_LINES = {"CfD renewables", "Hinkley Point C", "Biomass bridging"}


@pytest.fixture(scope="module")
def central():
    return model.run(Scenario())


def test_central_totals_unchanged(central):
    t = central.table.groupby("line").cash.sum() / 1e9
    assert t[list(CFD_LINES)].sum() == pytest.approx(71.38, abs=0.01)
    assert t["CfD renewables"] == pytest.approx(38.67, abs=0.01)
    assert t["Hinkley Point C"] == pytest.approx(30.07, abs=0.01)
    assert t["Biomass bridging"] == pytest.approx(2.64, abs=0.01)
    assert t["RO"] == pytest.approx(47.83, abs=0.01)


def test_results_table_shape(central):
    r = central.table
    assert list(r.columns) == ["line", "item", "technology", "built", "payer", "year", "cash"]
    assert r.year.min() == 2026
    assert set(r.line) == CFD_LINES | {"RO"}
    assert set(r.built) == {True, False}
    assert set(r.payer) == {"all"}  # split by who pays in stage 4
    assert not r.duplicated(["line", "item", "payer", "year"]).any()


def test_results_carry_scenario_dates_and_manifest(central):
    assert central.scenario == Scenario()
    assert central.valuation_date == dt.date(2026, 1, 1)
    assert central.cut_off_date >= dt.date(2026, 11, 2)  # the day the registers were downloaded
    assert len(central.manifest_sha256) == 64


def test_in_between_tables_saved(central, tmp_path):
    for name in ("prices", "cfd_contracts", "cfd_contract_years", "ro_stations", "ro_station_years"):
        assert name in central.tables and len(central.tables[name]), name
    central.save(tmp_path)
    assert (tmp_path / "results.csv").exists() and (tmp_path / "run.json").exists()
    for name in central.tables:
        assert (tmp_path / f"{name}.csv").exists()


def test_scenario_is_frozen_and_central_by_default():
    s = Scenario()
    with pytest.raises(dataclasses.FrozenInstanceError):
        s.case = "FFP_High"  # type: ignore[misc]
    assert s.case == "Reference" and s.hpc_strike_2012 == 89.50 and s.wind_decline == 0.016


def test_price_path_is_a_table():
    path = Scenario().price_path()
    assert path[2027] == pytest.approx(prices.power_price(2027))
    assert Scenario(case="FFP_High").price_path()[2030] > path[2030]
    own = Scenario(prices=((2026, 100.0), (2027, 90.0)))
    assert own.power(2026) == 100.0 and own.power(2040) == 90.0  # the last year's price held flat after it


def test_a_new_scheme_line_needs_no_change_to_run():
    def fake(s):
        rows = pd.DataFrame(dict(line="Fake", item="x", technology="t", built=True, year=[2026, 2027], cash=1.0))
        return model.Line(rows, {"fake_detail": rows})
    r = model.run(Scenario(), lines=(fake,))
    assert r.table.cash.sum() == 2.0 and "fake_detail" in r.tables


def test_a_stand_in_market_response_runs_the_cfd_line():
    class Flat:
        def for_contract(self, year, technology, rule, own=None):
            return 0.9, 0.0
    from billtocome import cfd_line
    o = cfd_line.build(Scenario(market=Flat()), last_year=2027).tables["cfd_contract_years"]
    w = o[o.technology == "Offshore Wind"]
    assert (w.capture == 0.9).all() and (w.neg_share == 0.0).all()


def test_each_bracket_moves_one_input_only():
    central = dataclasses.asdict(Scenario())
    names = [b.name for b in BRACKETS]
    assert len(names) == len(set(names))
    for b in BRACKETS:
        moved = [[k for k, v in dataclasses.asdict(s).items() if v != central[k]] for s in (b.low, b.high)]
        assert all(len(m) <= 1 for m in moved), (b.name, moved)  # one side may be central (one-sided)
        assert len({k for m in moved for k in m}) == 1, (b.name, moved)  # and both move the same input


def test_brackets_still_to_come_are_listed_with_their_stage():
    assert all(stage in range(2, 7) for _, stage in LATER)
    assert not {n for n, _ in LATER} & {b.name for b in BRACKETS}
