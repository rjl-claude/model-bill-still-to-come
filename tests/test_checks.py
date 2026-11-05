"""aios-harness#80 (Stage 1): the checks, against docs/hand-example-checks.md."""
import dataclasses

import pytest

from billtocome import checks, model
from billtocome.scenario import Scenario


@pytest.fixture(scope="module")
def results():
    return model.run(Scenario())


@pytest.fixture(scope="module")
def report(results):
    return checks.check(results)


def test_calendarise_by_hand():
    assert checks.calendarise({2025: 8.000, 2026: 8.465}, 2026) == pytest.approx(8.349, abs=0.001)


def test_obr_ro_2026_reference_by_hand():
    assert checks.obr("RO")[2026] == pytest.approx(8.349e9, rel=1e-3)


def test_every_check_runs_on_cfd_and_ro(report):
    r = report.rows
    for name in ("Clock join", "OBR", "LCCC"):
        assert (r.check == name).any(), name
    assert {"CfD", "RO"} <= set(r[r.check == "OBR"].line)
    assert set(r[r.check == "OBR"].period) >= {str(y) for y in range(2026, 2032)}


def test_central_passes_every_check_or_is_explained(report):
    bad = report.rows[~report.rows.ok]
    assert report.passed, bad.to_string()


def test_an_unexplained_gap_fails(results):
    doubled = dataclasses.replace(results, table=results.table.assign(cash=results.table.cash * 2))
    rep = checks.check(doubled, explanations=[])
    assert not rep.passed


def test_no_stale_explanations(report):
    keys = set(zip(report.rows.check, report.rows.line, report.rows.period))
    for e in checks.load_explanations():
        assert (e["check"], e["line"], e["period"]) in keys, e
