import pytest

from billtocome.contracts import load
from billtocome.output import measured, new_farm_lf, yearly_mwh


@pytest.fixture(scope="module")
def c():
    return load()


@pytest.fixture(scope="module")
def lf(c):
    return measured(c)


def test_hand_example_farm_load_factor(lf):
    # 1,122,200 MWh a year on 283.369 MW
    assert lf["CAA-EAS-167"] == pytest.approx(1_122_200 / (283.369 * 8760), rel=0.002)


def test_moray_east_is_low_because_it_is_switched_off(lf):
    # Not a data error: the most curtailed farm in Britain; its record nets off the hours switched off.
    assert 0.15 < lf["AR2-MRY-107"] < 0.25


def test_new_offshore_farms_take_the_recent_british_median(c, lf):
    new = new_farm_lf(c, lf)
    assert 0.38 < new["Offshore Wind"] < 0.47
    assert new["Nuclear"] == 0.90


def test_decline_with_age():
    base = yearly_mwh(100, 0.40, start_year=2020, year=2024)
    assert yearly_mwh(100, 0.40, start_year=2020, year=2034) == pytest.approx(base * 0.984 ** 10)
    # a farm not yet built starts at its full level
    assert yearly_mwh(100, 0.40, start_year=2030, year=2030) == pytest.approx(100 * 8760 * 0.40)
