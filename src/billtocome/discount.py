"""The farm's discount: the share of the average power price a wind or solar farm earns.

One swappable part (build plan points 6, 7): `Discount(year, technology, own)` -> factor. No. 2 uses
`SimplePattern`, a straight line fitted to Britain's own half-hourly record; a hardened Grid Sim, or a
subset of it, can replace it later with the same call.

- Fit: each year's output-weighted price / time-average price (Elexon MID, APX) against the share of
  wind (transmission + embedded) or solar (embedded) in national demand plus embedded output (NESO).
  Years 2017-2025 without 2022 (the gas crisis). 2016 is out: MID prices begin mid-September 2016.
- Future shares (point 25): DESNZ EEP Annex J total renewables, split into wind and solar by NESO
  FES 2025 ("Falling Behind", the pathway nearest EEP's policy projection), as a share of EEP's total
  supply. Because these sources define a share differently from the fit, the path is indexed to the
  measured 2024 share: share(y) = measured_2024 x path(y) / path(2024). Other FES pathways are
  build-path scenarios, indexed the same way. Shares after 2050 are 2050's.
- A farm with its own record starts from its own 2023-25 discount and moves with the slope:
  own + slope x (share(y) - mean measured share 2023-25). A farm without one takes the line.
- Technologies that are not wind or solar (baseload reference price, or too small to matter): 1.0.
"""
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Protocol

import numpy as np
import pandas as pd

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
FIT_YEARS = tuple(y for y in range(2017, 2026) if y != 2022)
BASE_YEARS = (2023, 2024, 2025)
WIND = {"Offshore Wind", "Onshore Wind", "Floating Offshore Wind", "Remote Island Wind"}
SOLAR = {"Solar PV"}
PATHWAYS = ("Falling Behind", "Holistic Transition", "Electric Engagement", "Hydrogen Evolution")


class Discount(Protocol):
    def __call__(self, year: int, technology: str, own: float | None = None) -> float: ...


@cache
def measured() -> pd.DataFrame:
    """Per year: wind and solar share, and their value factors (output-weighted / average price)."""
    rows = []
    for y in range(2016, 2026):
        e = pd.read_csv(RAW / "halfhourly" / f"elexon_{y}.csv")
        d = pd.read_csv(RAW / "halfhourly" / f"demanddata_{y}.csv")
        # NESO writes dates as 01-JAN-2016 in some years and 01-Jan-23 in others
        d["date"] = pd.to_datetime(d.SETTLEMENT_DATE, format="mixed", dayfirst=True).dt.strftime("%Y-%m-%d")
        e["settlement_date"] = pd.to_datetime(e.settlement_date).dt.strftime("%Y-%m-%d")
        m = e.merge(d, left_on=["settlement_date", "settlement_period"], right_on=["date", "SETTLEMENT_PERIOD"])
        m = m[m.price.notna()]
        wind = m.wind_tx_mw + m.EMBEDDED_WIND_GENERATION
        solar = m.EMBEDDED_SOLAR_GENERATION
        total = m.ND + m.EMBEDDED_WIND_GENERATION + m.EMBEDDED_SOLAR_GENERATION
        avg = m.price.mean()
        rows.append(dict(year=y, periods=len(m), wind_share=wind.sum() / total.sum(),
                         wind_vf=(m.price * wind).sum() / wind.sum() / avg,
                         solar_share=solar.sum() / total.sum(),
                         solar_vf=(m.price * solar).sum() / solar.sum() / avg,
                         avg_price=avg))
    return pd.DataFrame(rows).set_index("year")


@dataclass(frozen=True)
class Line:
    intercept: float
    slope: float
    r2: float

    def __call__(self, share: float) -> float:
        return self.intercept + self.slope * share


@cache
def fit(kind: str, years: tuple = FIT_YEARS) -> Line:
    m = measured().loc[list(years)]
    x, y = m[f"{kind}_share"], m[f"{kind}_vf"]
    b, a = np.polyfit(x, y, 1)
    return Line(float(a), float(b), float(np.corrcoef(x, y)[0, 1] ** 2))


@cache
def _eep_path(kind: str) -> pd.Series:
    j = pd.read_excel(RAW / "desnz" / "Annex_J_All_Power_Producer_Generation.ods", sheet_name="Reference",
                      header=None, engine="odf")
    years = [int(v) for v in j.iloc[2, 3:]]
    row = {str(j.iloc[i, 0]): pd.Series(j.iloc[i, 3:].astype(float).values, index=years) for i in range(3, j.shape[0])}
    supply = [k for k in row if k.startswith("Total supplied (net of")][-1]
    split = _fes_split(kind, "Falling Behind")
    return (row["Renewables"] * split / row[supply]).loc[2024:2050]


@cache
def _fes(pathway: str) -> pd.DataFrame:
    f = pd.read_csv(RAW / "neso-fes" / "fes2025_es1_v006.csv")
    g = f[(f.Variable == "Generation (TWh)") & (f.Pathway == pathway)]
    return g.set_index(["Category", "Type"])[[str(y) for y in range(2024, 2051)]].T.rename(index=int)


def _fes_kind(g: pd.DataFrame, kind: str) -> pd.Series:
    types = g.columns.get_level_values(1)
    cols = [c for c, t in zip(g.columns, types) if ("Wind" in t if kind == "wind" else t == "Solar PV")]
    return g[cols].T.groupby(level=[0, 1]).sum().sum()


@cache
def _fes_split(kind: str, pathway: str) -> pd.Series:
    """Wind (or solar) as a share of renewables (renewable category plus biomass), FES pathway."""
    g = _fes(pathway)
    ren = [c for c in g.columns if c[0] == "Renewable" or c[1] in ("Biomass", "CCS Biomass")]
    return _fes_kind(g, kind) / g[ren].T.groupby(level=[0, 1]).sum().sum()


@cache
def _fes_share(kind: str, pathway: str) -> pd.Series:
    g = _fes(pathway)
    return _fes_kind(g, kind) / g.T.groupby(level=[0, 1]).sum().sum()


@cache
def share(kind: str, year: int, path: str = "EEP") -> float:
    """Wind or solar share in `year`, on the fit's definition (indexed to the measured 2024 share)."""
    p = _eep_path(kind) if path == "EEP" else _fes_share(kind, path)
    y = min(max(year, 2024), 2050)
    return float(measured().loc[2024, f"{kind}_share"] * p[y] / p[2024])


@dataclass(frozen=True)
class SimplePattern:
    path: str = "EEP"
    slope_scale: float = 1.0  # bracket: steeper (>1) or gentler (<1) slope

    def line(self, kind: str) -> Line:
        f = fit(kind)
        base = measured().loc[list(BASE_YEARS)]
        pivot = float(base[f"{kind}_share"].mean())  # steeper/gentler turns the line about today's share
        slope = f.slope * self.slope_scale
        return Line(f(pivot) - slope * pivot, slope, f.r2)

    def __call__(self, year: int, technology: str, own: float | None = None) -> float:
        kind = "wind" if technology in WIND else "solar" if technology in SOLAR else None
        if kind is None:
            return 1.0
        ln = self.line(kind)
        s = share(kind, year, self.path)
        if own is None:
            return ln(s)
        base = float(measured().loc[list(BASE_YEARS), f"{kind}_share"].mean())
        return own + ln.slope * (s - base)


def own_discounts(raw: Path = RAW) -> pd.Series:
    """Each live farm's 2023-25 discount: output-weighted reference price / average MID price."""
    a = pd.read_csv(raw / "lccc" / "actual_cfd_generation_and_avoided_ghg_emissions.csv",
                    usecols=["Settlement_Date", "CfD_ID", "Reference_Type", "CFD_Generation_MWh",
                             "Weighted_IMRP_GBP_Per_MWh"], parse_dates=["Settlement_Date"])
    a = a[a.Settlement_Date.dt.year.isin(BASE_YEARS) & (a.Reference_Type == "IMRP") & (a.CFD_Generation_MWh > 0)]
    w = (a.Weighted_IMRP_GBP_Per_MWh * a.CFD_Generation_MWh).groupby(a.CfD_ID).sum() / a.groupby("CfD_ID").CFD_Generation_MWh.sum()
    hh = pd.concat([pd.read_csv(raw / "halfhourly" / f"elexon_{y}.csv") for y in BASE_YEARS])
    return (w / hh.price.mean()).rename("own")
