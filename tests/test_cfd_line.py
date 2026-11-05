"""aios-harness#68: the CfD line, against docs/hand-example-cfd-line.md."""
import pytest

from billtocome import cfd_line as L


@pytest.fixture(scope="module")
def o():
    return L.build().tables["cfd_contract_years"]


def test_hand_example_ea1_2030(o):
    r = o[(o.cfd_id == "CAA-EAS-167") & (o.year == 2030)].iloc[0]
    assert r.mwh == pytest.approx(1_018_691, rel=1e-4)
    assert r.strike == pytest.approx(162.54, abs=0.01)
    assert r.market == pytest.approx(57.91, abs=0.01)
    assert r.capture == pytest.approx(0.8837, abs=0.0001)
    assert r.payment / 1e6 == pytest.approx(113.4, abs=0.1)


def test_drax_bridging_2028(o):
    r = o[(o.cfd_id == "LCD-DRX") & (o.year == 2028)].iloc[0]
    assert r.mwh == pytest.approx(6_102_216, rel=1e-6)
    assert r.payment / 1e6 == pytest.approx(569.3, abs=0.2)
    assert (o[o.line == "Biomass bridging"].payment >= 0).all()


def test_three_lines_and_built_apart(o):
    assert set(o.line) == {"CfD renewables", "Hinkley Point C", "Biomass bridging"}
    assert set(o.built) == {True, False}
    assert o.year.min() == 2026


def test_payments_run_both_ways(o):
    assert (o.payment < 0).any()


def test_nothing_paid_after_a_contract_ends(o):
    from billtocome.contracts import load
    end = load().set_index("cfd_id").end
    last = o.groupby("cfd_id").year.max()
    assert (last <= end.reindex(last.index).dt.year).all()


def test_hinkley_cap_not_binding_at_central(o):
    assert o[o.line == "Hinkley Point C"].mwh.sum() < 910_000_000
