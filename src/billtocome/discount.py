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


class MarketResponse(Protocol):
    """The seam (design: Market response): for one contract-year, the share of the average price the
    farm earns and the share of its output in hours its rule leaves unpaid. `SimpleFit` now; Grid Sim later."""
    def for_contract(self, year: int, technology: str, rule: str, own: float | None = None) -> tuple[float, float]: ...


T95_6DF = 2.4469  # Student's t, 97.5th percentile, 6 degrees of freedom (eight fitted years less two)


def bounded_slope(ln: "Line", bound: int, n: int = 8) -> float:
    """The fitted slope (bound 0), or the end of its 95% confidence interval (bound -1 gentler, +1 steeper).
    A gentler end past zero is held at zero (flat), not turned round."""
    if bound == 0:
        return ln.slope
    se = abs(ln.slope) * ((1 - ln.r2) / (ln.r2 * (n - 2))) ** 0.5
    b = ln.slope + bound * T95_6DF * se * (1 if ln.slope >= 0 else -1)
    return b if b * ln.slope > 0 else 0.0


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
    slope_scale: float = 1.0  # steeper (>1) or gentler (<1) slope
    slope_bound: int = 0  # bracket: -1 gentler, +1 steeper end of the slope's 95% interval

    def line(self, kind: str) -> Line:
        f = fit(kind)
        base = measured().loc[list(BASE_YEARS)]
        pivot = float(base[f"{kind}_share"].mean())  # steeper/gentler turns the line about today's share
        slope = bounded_slope(f, self.slope_bound) * self.slope_scale
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


# --- Hours of negative price (build plan point 12; aios-harness#67) --------------------------------
# A CfD's rule decides which negative-price hours it is not paid for (docs/facts.md 8-10):
#   "none": AR1 and the Investment Contracts (paid through negative hours);
#   "6h":   AR2 and AR3, runs of six or more consecutive hours (12 half-hours);
#   "any":  AR4 to AR7, every negative hour.
# Measured on the half-hourly MID price, a stand-in for the hourly day-ahead price the contracts use.
RULE_BY_ROUND = {"Allocation Round 1": "none", "Investment Contract": "none", "Bespoke": "none",
                 "Allocation Round 2": "6h", "Allocation Round 3": "6h"}


def rule_for(round_: str) -> str:
    return RULE_BY_ROUND.get(round_, "any")


@cache
def negative_measured() -> pd.DataFrame:
    """Per year: share of wind (and solar) output in negative half-hours, any and in 6-hour runs,
    and the output-weighted negative price."""
    rows = []
    for y in range(2017, 2026):
        e = pd.read_csv(RAW / "halfhourly" / f"elexon_{y}.csv")
        d = pd.read_csv(RAW / "halfhourly" / f"demanddata_{y}.csv")
        d["date"] = pd.to_datetime(d.SETTLEMENT_DATE, format="mixed", dayfirst=True).dt.strftime("%Y-%m-%d")
        e["settlement_date"] = pd.to_datetime(e.settlement_date).dt.strftime("%Y-%m-%d")
        m = (e.merge(d, left_on=["settlement_date", "settlement_period"], right_on=["date", "SETTLEMENT_PERIOD"])
             .sort_values(["settlement_date", "settlement_period"]))
        m = m[m.price.notna()].reset_index(drop=True)
        neg = m.price < 0
        run = neg.groupby((neg != neg.shift()).cumsum()).transform("size")
        neg6 = neg & (run >= 12)
        row = {"year": y}
        for kind, q in (("wind", m.wind_tx_mw + m.EMBEDDED_WIND_GENERATION), ("solar", m.EMBEDDED_SOLAR_GENERATION)):
            row[f"{kind}_any"] = (q * neg).sum() / q.sum()
            row[f"{kind}_6h"] = (q * neg6).sum() / q.sum()
            row[f"{kind}_price"] = (m.price[neg] * q[neg]).sum() / q[neg].sum()
        rows.append(row)
    return pd.DataFrame(rows).set_index("year")


@cache
def negative_fit(kind: str, rule: str) -> Line:
    """Share of output in excluded negative hours against the kind's share; 2017-25 without 2022."""
    n, m = negative_measured().loc[list(FIT_YEARS)], measured().loc[list(FIT_YEARS)]
    x, y = m[f"{kind}_share"], n[f"{kind}_{rule}"]
    b, a = np.polyfit(x, y, 1)
    return Line(float(a), float(b), float(np.corrcoef(x, y)[0, 1] ** 2))


def negative_price(kind: str) -> float:
    """Output-weighted price in negative hours, 2023-25 average, £/MWh (cash; small and held flat)."""
    return float(negative_measured().loc[list(BASE_YEARS), f"{kind}_price"].mean())


@dataclass(frozen=True)
class NegativeHours:
    """The share of a contract's output in hours its rule leaves unpaid. Same inputs as the discount."""
    path: str = "EEP"
    slope_scale: float = 1.0  # steeper or gentler, turned about today's share
    slope_bound: int = 0  # bracket: -1 gentler, +1 steeper end of the slope's 95% interval

    def __call__(self, year: int, technology: str, rule: str) -> float:
        kind = "wind" if technology in WIND else "solar" if technology in SOLAR else None
        if kind is None or rule == "none":
            return 0.0
        f = negative_fit(kind, rule)
        pivot = float(measured().loc[list(BASE_YEARS), f"{kind}_share"].mean())
        slope = bounded_slope(f, self.slope_bound) * self.slope_scale
        v = f(pivot) + slope * (share(kind, year, self.path) - pivot)
        return float(min(max(v, 0.0), 1.0))


@dataclass(frozen=True)
class SimpleFit:
    """The Market response today: the British fit for the discount and for unpaid negative hours, on one
    build path (EEP, or a NESO FES pathway). Each slope can be set to either end of its 95% interval."""
    path: str = "EEP"
    discount_bound: int = 0
    negative_bound: int = 0

    def for_contract(self, year: int, technology: str, rule: str, own: float | None = None) -> tuple[float, float]:
        d = SimplePattern(self.path, slope_bound=self.discount_bound)(year, technology, own)
        n = NegativeHours(self.path, slope_bound=self.negative_bound)(year, technology, rule)
        return d, n
