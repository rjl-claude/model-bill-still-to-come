"""The CfD top-up, tested first against the hand-worked example (docs/hand-example-cfd.md)."""
from datetime import date

import pytest

from billtocome.cfd import contract_end, in_term, top_up


def test_hand_example_east_anglia_one_phase_2_2030():
    # strike £163.68 (2024 prices), Annex M 2030 baseload £60.30, discount 0.945, 1,122,200 MWh
    assert top_up(strike=163.68, market=60.30, capture=0.945, mwh=1_122_200) == pytest.approx(119.7e6, rel=1e-3)


def test_brackets_cheap_power_means_bigger_top_up():
    low = top_up(strike=163.68, market=46.50, capture=0.945, mwh=1_122_200)
    high = top_up(strike=163.68, market=76.60, capture=0.945, mwh=1_122_200)
    assert low == pytest.approx(134.3e6, rel=1e-3)
    assert high == pytest.approx(102.4e6, rel=1e-3)


def test_market_above_strike_is_paid_back():
    # The contract runs both ways: the generator pays the difference back.
    assert top_up(strike=50.0, market=80.0, capture=1.0, mwh=1000) == pytest.approx(-30_000)


def test_term_fifteen_years_from_start():
    assert contract_end(date(2020, 3, 31), years=15) == date(2035, 3, 31)
    assert in_term(2030, date(2020, 3, 31), years=15)
    assert not in_term(2036, date(2020, 3, 31), years=15)


def test_part_year_at_the_end_counts_its_share():
    # Ends 31 Mar 2035: a quarter of 2035 is still inside the term.
    assert in_term(2035, date(2020, 3, 31), years=15) == pytest.approx(90 / 365, abs=0.01)
