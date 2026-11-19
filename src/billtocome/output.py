"""What each CfD contract will generate, year by year (MWh).

Level: the farm's own measured output (LCCC payment records, full calendar years 2023-25), which
already nets off the hours it was switched off. Farms not yet generating take the median of the
British CfD farms of their technology that started in 2019 or later. Technologies with no British
record take DESNZ's assumption (Electricity Generation Costs 2023), labelled.
Decline with age: 1.6% a year, relative (Staffell & Green, Renewable Energy 66, 2014), central.
"""
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parents[2] / "data" / "raw" / "lccc"
HOURS = 8760
DECLINE = 0.016
# Decline with age by technology, the same in every scheme (build plan point 17): wind 1.6%/yr
# (Staffell & Green 2014), solar PV 0.5%/yr (Jordan & Kurtz 2013), everything else flat.
WIND_TECH = {"Offshore Wind", "Onshore Wind", "Floating Offshore Wind", "Remote Island Wind"}


# Point 17's brackets, the same in every scheme (facts 22, 33, 34): (wind, solar PV) per year.
DECLINES = {"gentler": (0.0017, 0.005),  # Hamilton et al. 2020, newer plants; solar: no gentler source
            "central": (DECLINE, 0.005),  # Staffell & Green 2014; Jordan & Kurtz median
            "steeper": (0.018, 0.008)}  # Staffell & Green 2014's upper bound, 1.6 + 0.2%/yr (1.4.0); J&K mean

# The output bracket's high end (build plan "Output"; fact 35): DESNZ Electricity Generation Costs 2023,
# Annex A, average net load factor by commissioning year. CfD wind and solar only (Richard, 5 Nov).
DESNZ_2023 = {
    "Onshore Wind": {2025: 0.45, 2030: 0.48, 2035: 0.48, 2040: 0.48},
    "Offshore Wind": {2025: 0.61, 2030: 0.65, 2035: 0.69, 2040: 0.69},
    "Floating Offshore Wind": {2025: 0.56, 2030: 0.64, 2035: 0.68, 2040: 0.69},
    "Solar PV": {2025: 0.11, 2030: 0.11, 2035: 0.11, 2040: 0.11},
}
DESNZ_2023["Remote Island Wind"] = DESNZ_2023["Onshore Wind"]


def desnz_2023_lf(technology: str, start_year: int) -> float | None:
    """DESNZ's 2023 load factor for the commissioning year nearest `start_year` (2025 for any earlier)."""
    t = DESNZ_2023.get(technology)
    if t is None:
        return None
    return t[min(t, key=lambda y: abs(y - max(start_year, 2025)))]


def decline_for(technology: str, wind: float = DECLINE, solar: float = 0.005) -> float:
    if technology in WIND_TECH:
        return wind
    if technology == "Solar PV":
        return solar
    return 0.0


# No British CfD record yet: DESNZ Electricity Generation Costs 2023 (floating offshore, tidal stream);
# nuclear 90% (stated assumption, a bracket step); geothermal 80% (stated; 12 MW in all).
ASSUMED_LF = {"Floating Offshore Wind": 0.56, "Tidal Stream": 0.38, "Nuclear": 0.90, "Geothermal": 0.80}
# No record of its own: treated as its nearest measured technology.
LIKE = {"Remote Island Wind": "Onshore Wind", "Biomass Conversion": "Biomass Conversion",
        "Advanced Conversion Technology": "Energy from Waste"}  # waste gasification: nearest is EfW
BASE_YEARS = (2023, 2024, 2025)


def measured(contracts: pd.DataFrame, raw: Path = RAW) -> pd.Series:
    """Each farm's load factor over its full calendar years in BASE_YEARS."""
    a = pd.read_csv(raw / "actual_cfd_generation_and_avoided_ghg_emissions.csv",
                    usecols=["Settlement_Date", "CfD_ID", "CFD_Generation_MWh"], parse_dates=["Settlement_Date"])
    a["y"] = a.Settlement_Date.dt.year
    a = a[a.y.isin(BASE_YEARS)]
    d = a.groupby(["CfD_ID", "y"]).agg(days=("Settlement_Date", "nunique"), mwh=("CFD_Generation_MWh", "sum")).reset_index()
    d = d[d.days >= 360]
    cap = contracts.set_index("cfd_id").capacity_mw
    d["mwh_cap"] = d.CfD_ID.map(cap) * HOURS
    g = d.groupby("CfD_ID")[["mwh", "mwh_cap"]].sum()
    return (g.mwh / g.mwh_cap).rename("lf")


def new_farm_lf(contracts: pd.DataFrame, lf: pd.Series) -> dict:
    """Median measured load factor of farms that started 2019 or later, by technology."""
    c = contracts.set_index("cfd_id").join(lf, how="inner")
    recent = c[c.start.dt.year >= 2019]
    out = recent.groupby("technology").lf.median().to_dict()
    for tech, like in LIKE.items():
        out.setdefault(tech, out.get(like))
    out.update({k: v for k, v in ASSUMED_LF.items() if k not in out})
    return out


def load_factor(row, lf: pd.Series, new: dict) -> tuple[float, str]:
    """A contract's load factor and where it came from."""
    if row.cfd_id in lf.index:
        return float(lf[row.cfd_id]), "own record"
    if row.technology in ASSUMED_LF:
        return ASSUMED_LF[row.technology], "assumed"
    return new[row.technology], "recent farms"


def yearly_mwh(capacity_mw: float, lf: float, start_year: int, year: int, base_year: int = 2024,
               decline: float = DECLINE) -> float:
    """Generation in `year`. A measured load factor is that of base_year's age; it declines from there."""
    age_now, age_then = base_year - start_year, year - start_year
    return capacity_mw * HOURS * lf * (1 - decline) ** max(0, age_then - max(0, age_now))
