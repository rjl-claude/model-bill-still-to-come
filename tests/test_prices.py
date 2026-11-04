"""aios-harness#64: prices in 2024 CPIH money, checked against docs/hand-example-prices.md."""
import pytest

from billtocome import prices


def test_annex_m_2027_reference_baseload():
    assert prices.power_price(2027, "Reference") == pytest.approx(62.655, abs=0.01)


def test_annex_m_after_obr_horizon_holds_the_2031_factor():
    assert prices.power_price(2035, "Reference") == pytest.approx(62.087, abs=0.01)
    assert prices.gdp_to_cpih(2040) == pytest.approx(prices.gdp_to_cpih(2031), rel=1e-12)


def test_cpi_indexed_value_2027():
    assert 163.68 * prices.cpi_to_cpih(2027) == pytest.approx(162.919, abs=0.01)
    assert prices.cpi_to_cpih(2045) == pytest.approx(prices.cpi_to_cpih(2031), rel=1e-12)


def test_after_2050_equals_2050():
    p2050 = prices.power_price(2050, "Reference")
    assert prices.power_price(2051, "Reference") == p2050
    assert prices.power_price(2064, "FFP_High") == prices.power_price(2050, "FFP_High")
    assert p2050 == pytest.approx(105.32, abs=0.01)


def test_2024_is_unchanged():
    assert prices.gdp_to_cpih(2024) == 1.0 and prices.cpi_to_cpih(2024) == 1.0


def test_low_and_high_cases_bracket_the_reference_to_2049():
    for y in range(2026, 2050):
        assert prices.power_price(y, "FFP_Low") < prices.power_price(y, "Reference") < prices.power_price(y, "FFP_High")


def test_annex_m_2050_high_case_is_below_reference():
    """As published: in 2050 (so in every year held flat after it) the high fossil-price case's power
    price is below the reference case's. Recorded, not corrected; the tornado takes the extremes."""
    assert prices.power_price(2050, "FFP_High") < prices.power_price(2050, "Reference")
