import pytest

from billtocome.contracts import load


@pytest.fixture(scope="module")
def c():
    return load()


def test_every_contract_has_a_strike_and_a_start(c):
    assert c.strike_2024.notna().all(), c[c.strike_2024.isna()][["cfd_id", "name"]]
    assert c.start.notna().all(), c[c.start.isna()][["cfd_id", "name"]]


def test_hinkley_point_c_is_two_reactors(c):
    h = c[c.technology == "Nuclear"]
    assert len(h) == 2
    assert h.strike_2024.iloc[0] == pytest.approx(124.71, abs=0.01)


def test_hand_example_contract(c):
    r = c[c.cfd_id == "CAA-EAS-167"].iloc[0]
    assert r.strike_2024 == pytest.approx(163.68, abs=0.01) and r.term_years == 15 and r.built


def test_auction_price_raised_to_2024_agrees_with_what_was_paid(c):
    # Check on the conversion: for live auction contracts, the 2012 price raised to 2024 prices
    # should be close to the strike actually paid in 2024. It runs about 2% above, because each
    # year's indexation uses an earlier month's CPI (recorded as a known difference).
    live = c[(c.strike_source == "paid 2024") & c.auction_strike_2024.notna()]
    gap = (live.auction_strike_2024 / live.strike_2024 - 1).abs()
    assert len(live) >= 25
    assert gap.median() < 0.03, gap.describe()
