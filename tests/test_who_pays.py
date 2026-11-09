"""aios-harness#83 (Stage 4): who pays, and VAT, against docs/hand-example-who-pays.md."""
import pytest

from billtocome import model, who_pays
from billtocome.scenario import Scenario


@pytest.fixture(scope="module")
def both():
    return model.run(), model.run(split=False)


def test_households_share_2025():
    assert who_pays.households_share(2030) == pytest.approx(0.34911, abs=1e-5)
    assert who_pays.households_share(2026, "EEP") == pytest.approx(0.349, abs=0.001)
    assert who_pays.households_share(2050, "EEP") == pytest.approx(0.283, abs=0.001)
    assert who_pays.households_share(2070, "EEP") == who_pays.households_share(2050, "EEP")


def test_shares_add_to_each_whole(both):
    split, whole = both
    a = split.table[split.table.line != "VAT"].groupby(["line", "year"]).cash.sum()
    b = whole.table.groupby(["line", "year"]).cash.sum()
    assert (a - b).abs().max() < 1.0  # pounds


def test_vat_is_five_percent_of_households(both):
    t = both[0].table
    hh = t[(t.payer == "households") & (t.line != "VAT")].groupby("year").cash.sum()
    vat = t[t.line == "VAT"].groupby("year").cash.sum()
    assert ((vat - 0.05 * hh).abs() < 1.0).all()
    assert set(t[t.line == "VAT"].payer) == {"households"}


def test_exemption_moves_only_between_businesses_and_taxpayers(both):
    t = both[0].table
    e = t[t.item == "Manufacturers' exemption (BICS)"]
    assert set(e.payer) == {"businesses", "taxpayers"} and set(e.line) == set(who_pays.BICS_LINES)
    assert abs(e.cash.sum()) < 1.0
    assert e.year.min() == 2026 and e.year.max() == 2035  # back payment for 2026-27; to March 2035


def test_hand_example_ro_2028(both):
    t = both[0].table
    ro = t[(t.line == "RO") & (t.year == 2028)].groupby("payer").cash.sum() / 1e6
    assert ro["households"] == pytest.approx(577.8, abs=0.1)
    assert ro["businesses"] == pytest.approx(3054.3, abs=0.1)
    assert ro["taxpayers"] == pytest.approx(2004.7, abs=0.1)
    vat = t[(t.line == "VAT") & (t.item.str.startswith("RO|")) & (t.year == 2028)].cash.sum() / 1e6
    assert vat == pytest.approx(28.9, abs=0.1)


def test_ro_splits_on_desnz_41_every_other_line_on_34_9(both):
    """Point 27 (Richard, 9 Nov): the RO on DESNZ's domestic share of RO costs, all else on DUKES 34.9%."""
    t = both[0].table
    t = t[(t.year == 2040) & (t.line != "VAT")]  # after the Exchequer window and the exemption
    share = t[t.payer == "households"].groupby("line").cash.sum() / t.groupby("line").cash.sum()
    assert share["FiT"] == pytest.approx(0.34911, abs=1e-5)
    assert share["CfD renewables"] == pytest.approx(0.34911, abs=1e-5)
    t30 = both[0].table.query("year == 2036 and line == 'RO'")
    assert t30[t30.payer == "households"].cash.sum() / t30.cash.sum() == pytest.approx(0.41, abs=1e-9)


def test_exchequer_ro_window(both):
    t = both[0].table
    x = t[t.item.str.startswith("Exchequer") & (t.payer == "taxpayers")]
    assert x.year.min() == 2026 and x.year.max() == 2029


def test_projected_share_lowers_households():
    lo = model.run(Scenario(households="EEP")).table
    assert lo[lo.payer == "households"].cash.sum() < model.run().table.query("payer == 'households'").cash.sum()
