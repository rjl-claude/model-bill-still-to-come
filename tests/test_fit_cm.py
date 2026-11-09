"""aios-harness#81 (Stage 2): the FiT and Capacity Market lines, against docs/hand-example-fit-cm.md."""
import pandas as pd
import pytest

from billtocome import cm, fit
from billtocome.scenario import Scenario


@pytest.fixture(scope="module")
def f():
    return fit.build().tables["fit_group_years"]


@pytest.fixture(scope="module")
def c():
    return cm.build().tables["cm_agreement_years"]


def test_all_installations_read():
    assert len(fit.installations()) == 869_279


def test_fit_capacity_by_technology_matches_ofgem():
    mw = fit.groups().groupby("technology").kw.sum() / 1000  # Ofgem SY15 report Fig 2.1
    for t, v in {"Photovoltaic": 5149, "Wind": 772, "Hydro": 268, "Anaerobic digestion": 302}.items():
        assert mw[t] == pytest.approx(v, abs=1)


def test_every_code_has_a_rate_and_most_dates_fall_inside_it():
    r, n = fit.code_rates(), fit.installations().groupby("code").size()
    assert r.rate.notna().all()
    assert (r.inside * n).sum() / n.sum() > 0.95


def test_fit_hand_example_2030(f):
    g = fit.groups()
    assert g.attrs["scale"] == pytest.approx(0.90143, abs=1e-5)
    r = f[(f.group == "PV-R/0-4/06H-2|export|2035-12") & (f.year == 2030)].iloc[0]
    assert r.kwh == pytest.approx(37_396_085, rel=1e-5)
    assert r.generation / 1e6 == pytest.approx(8.119, abs=0.001)
    assert r.export / 1e6 == pytest.approx(0.638, abs=0.001)
    assert (r.generation + r.export) / 1e6 / 1.18035 == pytest.approx(7.42, abs=0.01)


def test_fit_sy15_payments_against_ofgem():
    g = fit.groups()
    a = (g.first_eligible <= pd.Timestamp("2025-03-31")) & (g.end >= pd.Timestamp("2024-04-01"))
    kwh = (g.kw * g.kwh_per_kw)[a]
    at_sy15 = 1 / ((1 + fit.CPI_UPLIFT_2026) * 1.035)  # 2026-27 tariffs back to 2024-25: CPI 3.4%, RPI Dec 2024 3.5%
    gen = (kwh * g.rate[a] / 100).sum() * at_sy15
    exp = (kwh * g.export_share[a] * g.export_rate[a] / 100).sum() * at_sy15
    assert abs(gen / fit.SY15_GENERATION - 1) < 0.10, gen
    assert abs(exp / fit.SY15_EXPORT - 1) < 0.10, exp


def test_fit_nothing_after_march_2042(f):
    assert f.year.max() == 2042
    assert (fit.groups().end <= fit.LAST_DAY).all()


def test_ro_migrated_end_march_2027():
    assert fit.end_of("PV/EXGEN/01", "Photovoltaic", pd.Timestamp("2010-04-01")) == pd.Timestamp("2027-03-31")
    assert fit.end_of("PV-R/0-4/02", "Photovoltaic", pd.Timestamp("2011-11-29")) == pd.Timestamp("2036-11-28")
    assert fit.end_of("WD/0-1.5/06", "Wind", pd.Timestamp("2015-06-01")) == pd.Timestamp("2035-05-31")


def test_cm_winter_cpi_by_hand():
    assert cm.winter_cpi(2022) == pytest.approx(115.857, abs=0.001)
    assert cm.winter_cpi(2026) == pytest.approx(140.300, abs=0.001)


def test_cm_hand_example_ifa_2026(c):
    r = c[c.agreement == "CAN-2026-IFA_19-001|2026-27 (T-4)"]
    assert r.whole_cash.sum() / 1e6 == pytest.approx(96.13, abs=0.01)
    r26 = r[r.year == 2026].iloc[0]
    assert r26.whole_cash / 1e6 == pytest.approx(26.31, abs=0.01)
    assert r26.payment / 1e6 == pytest.approx(3.59, abs=0.01)


def test_cm_share_by_point_9():
    assert cm.SHARE_CENTRAL == pytest.approx(0.146, abs=0.0005)
    assert cm.SHARE_LOW == pytest.approx(0.136, abs=0.0005) and cm.SHARE_HIGH == pytest.approx(0.156, abs=0.0005)


def test_cm_t1_not_indexed():
    assert cm.payment_cash(20.0, 1.0, 2025, pd.NA) == 20_000.0


def test_cm_only_awarded_live_agreements():
    a = cm.agreements()
    assert set(a.type) <= set(cm.AUCTIONS) and (a.mw >= 0).all()


def test_cm_share_scales_the_line():
    lo = cm.build(Scenario(cm_share=cm.SHARE_LOW)).rows.cash.sum()
    hi = cm.build(Scenario(cm_share=cm.SHARE_HIGH)).rows.cash.sum()
    assert hi / lo == pytest.approx(cm.SHARE_HIGH / cm.SHARE_LOW)


def test_cm_reads_the_newest_register():
    """The freeze (aios-harness#91): the newest NESO CMU register on disk, not a fixed day's."""
    assert cm.register_file().name == "cmu_20261104.csv"
