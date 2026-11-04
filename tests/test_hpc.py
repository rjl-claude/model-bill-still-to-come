"""aios-harness#65: Hinkley Point C as two reactors, checked against docs/hand-example-hpc.md."""
import pandas as pd
import pytest

from billtocome.contracts import load


def _hpc(**kw):
    c = load(**kw)
    return c[c.technology == "Nuclear"].sort_values("cfd_id").reset_index(drop=True)


def test_two_reactors_strike_capacity_starts_ends():
    h = _hpc()
    assert list(h.cfd_id) == ["NUC-HPC-198-R1", "NUC-HPC-198-R2"]
    assert h.strike_2024.round(2).tolist() == [124.71, 124.71]
    assert h.capacity_mw.round(2).tolist() == [1643.58, 1643.58]
    assert list(h.start) == [pd.Timestamp("2030-04-01"), pd.Timestamp("2031-04-01")]
    assert list(h.end) == [pd.Timestamp("2064-04-30"), pd.Timestamp("2064-10-31")]
    assert (h.cap_mwh == 910_000_000).all()


def test_strike_bracket():
    assert _hpc(hpc_strike_2012=92.50).strike_2024.round(2).tolist() == [128.89, 128.89]


def test_term_from_start_bracket():
    h = _hpc(hpc_term="from_start")
    assert list(h.end) == [pd.Timestamp("2065-04-01"), pd.Timestamp("2066-04-01")]


def test_late_start_shortens_the_paid_years():
    h = _hpc(hpc_shift_years=2)
    assert list(h.start) == [pd.Timestamp("2032-04-01"), pd.Timestamp("2033-04-01")]
    assert list(h.end) == [pd.Timestamp("2064-04-30"), pd.Timestamp("2064-10-31")]


def test_early_start_inside_reactor_one_window():
    h = _hpc(hpc_shift_years=-1)
    assert list(h.end) == [pd.Timestamp("2064-04-01"), pd.Timestamp("2064-10-31")]


def test_every_other_contract_ends_term_years_after_start():
    c = load()
    o = c[(c.technology != "Nuclear") & (c["round"] != "Bridging") & ~c.cfd_id.isin(["INV-DRX-001", "INV-LYN-001"])]
    assert (o.end == o.apply(lambda r: r.start + pd.DateOffset(years=int(r.term_years)), axis=1)).all()


def test_fixed_ends_and_bridging():
    c = load().set_index("cfd_id")
    assert c.loc["INV-DRX-001", "end"] == c.loc["INV-LYN-001", "end"] == pd.Timestamp("2027-03-31")
    b = c[c["round"] == "Bridging"]
    assert sorted(b.index) == ["LCD-DRX", "LCD-LYN"]
    assert (b.start == pd.Timestamp("2027-04-01")).all() and (b.end == pd.Timestamp("2031-03-31")).all()
    assert b.loc["LCD-DRX", "strike_2024"] == pytest.approx(153.14, abs=0.01)
