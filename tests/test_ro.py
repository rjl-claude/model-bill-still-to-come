"""aios-harness#70: the RO line, against docs/hand-example-ro.md."""
import pandas as pd
import pytest

from billtocome import ro


@pytest.fixture(scope="module")
def o():
    return ro.build().tables["ro_station_years"]


def test_end_dates_in_law():
    assert ro.end_of(pd.Timestamp("2008-06-25")) == pd.Timestamp("2027-03-31")
    assert ro.end_of(pd.Timestamp("2016-10-17")) == pd.Timestamp("2036-10-17")
    assert ro.end_of(pd.Timestamp("2017-03-31")) == pd.Timestamp("2037-03-31")


def test_recycle_by_hand():
    assert ro.RECYCLE_CENTRAL == pytest.approx((4.42 / 50.05 + 7.44 / 50.80 + 6.88 / 52.88 + 5.95 / 59.01 + 8.04 / 64.73) / 5)
    assert ro.RECYCLE_LOW == pytest.approx(4.42 / 50.05) and ro.RECYCLE_HIGH == pytest.approx(7.44 / 50.80)


def test_hand_example_pen_y_cymoedd_2030(o):
    r = o[(o.station == "R00210RQWA") & (o.year == 2030)].iloc[0]
    assert r.rocs == pytest.approx(497_428, rel=1e-4)
    assert r.value == pytest.approx(72.64, abs=0.01)
    assert r.payment / 1e6 == pytest.approx(36.1, abs=0.1)


def test_nothing_after_march_2037(o):
    assert o.year.max() == 2037
    assert o[o.year == 2037].payment.sum() < o[o.year == 2036].payment.sum() * 0.3


def test_pre_2008_stations_stop_in_2027(o):
    s = ro.stations()
    old = s.index[s.accredited <= ro.CUTOFF_2008]
    assert o[o.station.isin(old)].year.max() == 2027


def test_ro_reads_the_newest_register_by_date_not_name(tmp_path):
    """Ofgem names its files DD-MM-YYYY: 01-12-2026 is newer than 09-11-2026, though it sorts first."""
    from billtocome import ro
    (tmp_path / "ofgem-rer").mkdir()
    for n in ("RO_Certificates_09-11-2026_04-10.csv", "RO_Certificates_01-12-2026_04-10.csv",
              "RO_Certificates_04-11-2026_04-10.csv"):
        (tmp_path / "ofgem-rer" / n).write_text("")
    assert ro._latest("RO_Certificates_", tmp_path).name == "RO_Certificates_01-12-2026_04-10.csv"
