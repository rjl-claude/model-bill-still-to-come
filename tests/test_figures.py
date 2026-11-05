"""aios-harness#84 (Stage 5): the results file, read by key; no printed figure outside it."""
import json

import pandas as pd
import pytest

from billtocome import figures, model
from billtocome.model import Results
from billtocome.scenario import Scenario


def small():
    rows = [
        ("CfD renewables", "A", "Offshore Wind", True, "households", 2026, 10e6),
        ("CfD renewables", "A", "Offshore Wind", True, "businesses", 2027, 20e6),
        ("CfD renewables", "B", "Solar PV", False, "businesses", 2027, 4e6),
        ("Hinkley Point C", "HPC", "Nuclear", False, "households", 2028, -5e6),
    ]
    return Results(table=pd.DataFrame(rows, columns=model.COLUMNS), scenario=Scenario())


def test_keys_are_built_from_the_table():
    f = figures.build(small())
    assert f["bill.total.cash"] == pytest.approx(29e6)
    assert f["cfd_renewables.2027.cash"] == pytest.approx(24e6)
    assert f["cfd_renewables.not_yet_built.total.cash"] == pytest.approx(4e6)
    assert f["bill.households.total.cash"] == pytest.approx(5e6)
    assert f["cfd_renewables.built.businesses.2027.cash"] == pytest.approx(20e6)
    assert f["hinkley_point_c.total.pv_green_book"] == pytest.approx(-5e6 / 1.035 ** 2)
    assert f["hinkley_point_c.total.pv_hurdle"] == pytest.approx(-5e6 / 1.0673 ** 2)
    assert "hinkley_point_c.built.total.cash" not in f  # no rows, no key


def test_the_file_carries_the_run_and_reads_back(tmp_path):
    r = small()
    r.save(tmp_path)
    data = json.loads((tmp_path / "figures.json").read_text())
    assert data["meta"]["valuation_date"] == "2026-01-01"
    assert data["meta"]["units"].startswith("£, 2024 prices")
    assert {"cut_off_date", "manifest_sha256", "scenario"} <= set(data["meta"])
    assert figures.figure("bill.total.cash", tmp_path / "figures.json") == pytest.approx(29e6)
    with pytest.raises(KeyError):
        figures.figure("bill.total.nothing", tmp_path / "figures.json")


def test_a_typed_figure_is_caught():
    f = figures.build(small())
    ok = "The bill still to come is {{bill.total.cash}} from 2026, {{bill.households.total.cash}} of it on households."
    assert figures.typed(ok) == []
    assert figures.render(ok, f) == "The bill still to come is £29.0m from 2026, £5.0m of it on households."
    bad = "The bill is £172.3bn, 34.9% on households, or 57.0 billion pounds; 209 contracts in AR7 (2026)."
    assert figures.typed(bad) == ["£172.3bn", "34.9%", "57.0 billion"]
    with pytest.raises(KeyError):
        figures.render("{{bill.total.cahs}}", f)


def test_central_bill_by_key():
    f = figures.build(model.run())
    assert f["cfd_renewables.total.cash"] / 1e9 == pytest.approx(38.7, abs=0.05)
    assert f["ro.total.cash"] / 1e9 == pytest.approx(47.8, abs=0.05)
    assert f["bill.households.total.cash"] / 1e9 == pytest.approx(57.0, abs=0.05)
    assert f["bill.total.cash"] == pytest.approx(sum(f[f"{s}.total.cash"] for s in figures.LINE_KEYS.values()))
    assert f["bill.total.pv_hurdle"] < f["bill.total.pv_green_book"] < f["bill.total.cash"]
