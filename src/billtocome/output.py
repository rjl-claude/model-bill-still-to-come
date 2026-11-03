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
# No British CfD record yet: DESNZ Electricity Generation Costs 2023 (floating offshore, tidal stream);
# nuclear 90% (stated assumption, a bracket step); geothermal 80% (stated; 12 MW in all).
ASSUMED_LF = {"Floating Offshore Wind": 0.56, "Tidal Stream": 0.38, "Nuclear": 0.90, "Geothermal": 0.80}
# No record of its own: treated as its nearest measured technology.
LIKE = {"Remote Island Wind": "Onshore Wind", "Biomass Conversion": "Biomass Conversion"}
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
