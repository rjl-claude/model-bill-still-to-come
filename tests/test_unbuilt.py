"""aios-harness#69: unbuilt contracts, against docs/hand-example-unbuilt.md."""
import pytest

from billtocome.scenario import Scenario

from billtocome import cfd_line as L
from billtocome import unbuilt as U
from billtocome.contracts import load


def test_termination_rates_by_hand():
    assert U.termination_rate("Offshore Wind") == pytest.approx(4 / 40)
    assert U.termination_rate("Solar PV") == pytest.approx(13 / 69)
    assert U.termination_rate("Tidal Stream") == pytest.approx(41 / 164)


def test_delays_by_hand():
    assert U.delay_for("Allocation Round 4") == pytest.approx(1.97, abs=0.01)
    assert U.delay_for("Allocation Round 7") == pytest.approx(1.97, abs=0.01)


def test_late_starts_move_only_unbuilt_and_keep_the_term():
    c = load()
    late = U.late_starts(c)
    moved = late.start != c.start
    assert not (moved & c.built).any()
    assert ((late.end - late.start) == (c.end - c.start)).all()
    assert (late.start >= c.start).all()


@pytest.fixture(scope="module")
def central():
    return L.build(last_year=2030).tables["cfd_contract_years"]


def test_abandonment_changes_only_unbuilt_renewables(central):
    a = L.build(Scenario(abandonment=True), last_year=2030).tables["cfd_contract_years"]
    same = central.built | (central.line != "CfD renewables")
    assert (a.payment[same.values].values == central.payment[same.values].values).all()
    k = (~central.built) & (central.line == "CfD renewables") & (central.technology == "Offshore Wind")
    assert a.payment[k.values].values == pytest.approx(central.payment[k.values].values * 0.9)
