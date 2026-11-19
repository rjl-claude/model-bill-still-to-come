"""The Renewables Obligation line (aios-harness#70).

Each accredited station: certificates a year from its own 2023-25 record (Ofgem RER certificate
register, revoked and refused batches left out), declining with age by technology (point 17), to its
end in law (RO Order 2015 art. 44; ROS 2009 art. 17A; NIRO 2009 art. 18A; docs/facts.md 12):
first accredited on or before 25 June 2008 -> no certificates after 31 March 2027; later -> to the
20th anniversary of accreditation or 31 March 2037, whichever is first. Additional capacity on its
own clock is not modelled (stated).
Each certificate costs bill-payers the buy-out price plus the recycle value (Ofgem: SY23 £64.73 +
£8.04 = £72.77; scheme value = ROCs presented x that). Buy-out: £67.06 (2025-26), £69.34 (2026-27),
then CPI-indexed by the previous calendar year (DESNZ, 28 Jan 2026). Recycle value: its average share
of the buy-out price over SY19-SY23 (Ofgem SY23 annual report, Figure A4.1), with the lowest and
highest of those years as the bracket.
"""
import re
from functools import cache
from pathlib import Path

import pandas as pd

from .output import decline_for
from .prices import cpi, cpih

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
BASE_YEARS = (2023, 2024, 2025)
CUTOFF_2008, END_2027, END_2037 = pd.Timestamp("2008-06-25"), pd.Timestamp("2027-03-31"), pd.Timestamp("2037-03-31")
BUYOUT = {2025: 67.06, 2026: 69.34}  # scheme year starting 1 April of the key, £/ROC cash
# Ofgem SY23 annual report, Figure A4.1: recycle value per ROC and buy-out price by scheme year.
RECYCLE = {"SY19": (4.42, 50.05), "SY20": (7.44, 50.80), "SY21": (6.88, 52.88), "SY22": (5.95, 59.01), "SY23": (8.04, 64.73)}
RECYCLE_SHARE = {k: r / b for k, (r, b) in RECYCLE.items()}
RECYCLE_CENTRAL = sum(RECYCLE_SHARE.values()) / len(RECYCLE_SHARE)
RECYCLE_LOW, RECYCLE_HIGH = min(RECYCLE_SHARE.values()), max(RECYCLE_SHARE.values())
WIND = {"Onshore wind", "Offshore wind", "Wind with a DNC of 50kW or less", "Offshore wind - floating turbines"}


def _tech(t: str) -> str:
    if t in WIND:
        return "Onshore Wind"  # any wind: the wind decline
    if t.startswith("Photovoltaic"):
        return "Solar PV"
    return t


def _latest(prefix: str, raw: Path) -> Path:
    """Ofgem's newest file by the date in its name (DD-MM-YYYY_HH-MM), not by the name's own order."""
    def when(p: Path) -> tuple:
        d, m, y, hh, mm = re.search(r"(\d\d)-(\d\d)-(\d{4})_(\d\d)-(\d\d)\.csv$", p.name).groups()
        return (y, m, d, hh, mm)
    return max((raw / "ofgem-rer").glob(prefix + "*.csv"), key=when)


@cache
def stations(raw: Path = RAW) -> pd.DataFrame:
    s = pd.read_csv(_latest("RO_Accredited_Stations_", raw), thousands=",")
    s["accredited"] = pd.to_datetime(s["Effective date"], dayfirst=True)
    c = pd.read_csv(_latest("RO_Certificates_", raw), thousands=",",
                    usecols=["Accreditation reference", "Output period", "Number of certificates", "Cert status"])
    c = c[~c["Cert status"].isin(["Revoked", "Refused"])]
    c["y"] = pd.to_datetime(c["Output period"], format="%b %Y").dt.year
    rocs = c[c.y.isin(BASE_YEARS)].groupby("Accreditation reference")["Number of certificates"].sum() / len(BASE_YEARS)
    out = s.set_index("Accreditation reference").join(rocs.rename("rocs_a_year"), how="inner")
    out["end"] = out.accredited.map(end_of)
    return out[["Station name", "Technology", "Country", "accredited", "end", "rocs_a_year"]]


def end_of(accredited: pd.Timestamp) -> pd.Timestamp:
    if accredited <= CUTOFF_2008:
        return END_2027
    return min(accredited + pd.DateOffset(years=20), END_2037)


def buyout_cash(scheme_year: int) -> float:
    """Buy-out price for the scheme year starting 1 April `scheme_year`, cash."""
    if scheme_year in BUYOUT:
        return BUYOUT[scheme_year]
    last = max(BUYOUT)
    return BUYOUT[last] * cpi(scheme_year - 1) / cpi(last - 1)


def roc_value(year: int, recycle: float = RECYCLE_CENTRAL) -> float:
    """Cost to bill-payers of one certificate generated in calendar `year`, 2024 CPIH prices."""
    cash = 0.25 * buyout_cash(year - 1) + 0.75 * buyout_cash(year)
    return cash * (1 + recycle) / cpih(year)


def share_of_year(year: int, end: pd.Timestamp) -> float:
    y0, y1 = pd.Timestamp(f"{year}-01-01"), pd.Timestamp(f"{year + 1}-01-01")
    return max(0.0, (min(y1, end + pd.Timedelta(days=1)) - y0).days) / (y1 - y0).days


def build(s=None, first: int = 2026, last: int = 2037):
    """The RO scheme-line adapter: one row per station-year (design: Scheme line)."""
    from .model import Line
    from .scenario import Scenario
    s = s or Scenario()
    st = stations()
    rows = []
    for station, r in st.iterrows():
        d = decline_for(_tech(r.Technology), s.wind_decline, s.solar_decline)
        for y in range(first, last + 1):
            f = share_of_year(y, r.end)
            if f == 0:
                continue
            rocs = r.rocs_a_year * (1 - d) ** (y - 2024) * f
            v = roc_value(y, s.ro_recycle)
            rows.append(dict(station=station, technology=r.Technology, country=r.Country, year=y, rocs=rocs,
                             value=v, payment=rocs * v))
    out = pd.DataFrame(rows)
    tidy = out.rename(columns={"station": "item", "payment": "cash"}).assign(line="RO", built=True)
    return Line(tidy[["line", "item", "technology", "built", "year", "cash"]],
                {"ro_stations": st.reset_index(), "ro_station_years": out})
