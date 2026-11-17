"""Prices in 2024 consumer money (2024 CPIH prices), the price base of every figure.

Rule (build plan point 5, Richard 3 Nov 2026): ONS CPIH and CPI to 2025; the OBR's latest forecast
(October 2026) for 2026-2031, its last full calendar year; after 2031 every measure rises at the same
rate, so the gaps between them stop growing. DESNZ's Annex M is in 2024 prices by the GDP deflator
(its note 15); it is turned back into cash by Annex M's own deflator path, then into 2024 CPIH prices.
Annex M stops at 2050; later years take 2050's prices (point 3).
"""
import csv
from functools import cache
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
BASE, LAST_ONS, LAST_OBR, LAST_ANNEX_M = 2024, 2025, 2031, 2050
CASES = ("Reference", "FFP_Low", "FFP_High")


def _ons(name: str) -> dict[int, float]:
    out = {}
    with open(RAW / "ons" / name, newline="") as f:
        for row in csv.reader(f):
            if len(row) == 2 and row[0].isdigit():
                out[int(row[0])] = float(row[1])
    return out


@cache
def _obr() -> pd.DataFrame:
    """OBR October 2026, Table 1.7: calendar-year means of the quarterly CPI and CPIH indices."""
    d = pd.read_excel(RAW / "obr" / "october-2026-efo-detailed-forecast-tables-economy.xlsx",
                      sheet_name="1.7", header=None)
    assert list(d.iloc[3, [14, 15]]) == ["CPI", "CPIH"], "OBR Table 1.7 layout changed"
    q = d.iloc[4:, [1, 14, 15]].dropna(subset=[1])
    q.columns = ["q", "cpi", "cpih"]
    q = q[q.q.astype(str).str.fullmatch(r"\d{4}Q\d")]
    q["y"] = q.q.str[:4].astype(int)
    full = q.groupby("y").filter(lambda g: len(g) == 4)
    return full.groupby("y")[["cpi", "cpih"]].mean().astype(float)


@cache
def _annex_m(case: str) -> pd.DataFrame:
    d = pd.read_excel(RAW / "desnz" / "Annex_M_assumptions_growth_price.ods", sheet_name=case,
                      header=None, engine="odf")
    years = [int(c) for c in d.iloc[2, 5:]]
    rows = {str(d.iloc[i, 0]) + "|" + str(d.iloc[i, 2]): d.iloc[i, 5:].astype(float).values
            for i in range(3, d.shape[0])}
    out = pd.DataFrame({"gdp_growth": rows["GDP deflator|nan"],
                        "baseload_p_kwh": rows["Price - Wholesale|Electricity (baseload)"],
                        "gas_p_therm": rows["Price - Wholesale|Natural gas"]}, index=years)
    return out


def _chain(start: dict[int, float], growth: dict[int, float], year: int) -> float:
    """Index (2024 = 1) from ONS levels to LAST_ONS, then year-on-year growth factors."""
    if year <= LAST_ONS:
        return start[year] / start[BASE]
    v = start[LAST_ONS] / start[BASE]
    for y in range(LAST_ONS + 1, year + 1):
        v *= growth[y]
    return v


@cache
def _gdp(year: int) -> float:
    g = _annex_m("Reference").gdp_growth  # the same in every fossil-price case (Annex M note 6)
    v = 1.0
    for y in range(BASE + 1, min(year, LAST_ANNEX_M) + 1):
        v *= 1 + g[y]
    for _ in range(LAST_ANNEX_M + 1, year + 1):
        v *= 1 + g[LAST_ANNEX_M]
    return v


def _consumer(series: str, ons_file: str, year: int) -> float:
    obr = _obr()[series]
    growth = {y: obr[y] / obr[y - 1] for y in range(LAST_ONS + 1, LAST_OBR + 1)}
    for y in range(LAST_OBR + 1, year + 1):  # after the OBR: the same rate as the GDP deflator
        growth[y] = _gdp(y) / _gdp(y - 1)
    return _chain(_ons(ons_file), growth, year)


@cache
def cpih(year: int) -> float:
    return _consumer("cpih", "cpih-index-l522.csv", year)


@cache
def cpi(year: int) -> float:
    return _consumer("cpi", "cpi-index-d7bt.csv", year)


def gdp_to_cpih(year: int) -> float:
    """Multiply a 2024-prices (GDP deflator) figure for `year` by this to get 2024 CPIH prices."""
    return _gdp(year) / cpih(year)


def cpi_to_cpih(year: int) -> float:
    """Multiply a value indexed by CPI from its 2024 cash level by this to get 2024 CPIH prices."""
    return cpi(year) / cpih(year)


def power_price(year: int, case: str = "Reference") -> float:
    """Annex M baseload wholesale power price, £/MWh, 2024 CPIH prices; 2050's after 2050."""
    if case not in CASES:
        raise ValueError(case)
    y = min(year, LAST_ANNEX_M)
    return _annex_m(case).baseload_p_kwh[y] * 10 * gdp_to_cpih(y)


def annex_m_path(case: str = "Reference") -> dict[int, float]:
    """The price path as a table: Annex M baseload, £/MWh in 2024 CPIH prices, 2024 to 2050.
    A Scenario holds any such table; later years take the last year's price (point 3)."""
    return {y: power_price(y, case) for y in range(BASE, LAST_ANNEX_M + 1)}


# Fact 21: the season-ahead baseload prices (LCCC BMRP, £/MWh cash) for the months to March 2027.
FORWARD_MONTHS = {2026: [84.75] * 3 + [75.30] * 6 + [114.50] * 3, 2027: [114.50] * 3}


def forward_then_annex_m(case: str = "Reference") -> dict[int, float]:
    """Point 26's bracket: the market's season-ahead prices to March 2027, then Annex M. Each calendar
    year is the mean of its months, forward months deflated by that year's CPIH, the rest Annex M's."""
    path = annex_m_path(case)
    for y, months in FORWARD_MONTHS.items():
        rest = 12 - len(months)
        path[y] = (sum(months) / cpih(y) + rest * path[y]) / 12
    return path


AVERAGE_FROM, LAST_YEAR = 2026, 2099  # 1.3.0: the average's first year (the valuation year); the last year paid


def path_average_after_2050(case: str = "Reference") -> dict[int, float]:
    """Ruling 11b's case (version 1.3.0, aios-harness#243): Annex M to 2050, then every year to 2099 at the average
    of Annex M's path over 2026 to 2050 in place of 2050's price (ASSUMPTION, design.md "Version 1.3.0")."""
    path = annex_m_path(case)
    mean = sum(path[y] for y in range(AVERAGE_FROM, LAST_ANNEX_M + 1)) / (LAST_ANNEX_M + 1 - AVERAGE_FROM)
    return path | {y: mean for y in range(LAST_ANNEX_M + 1, LAST_YEAR + 1)}
