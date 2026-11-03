"""The CfD contract list: one row per contract not terminated, with its strike in 2024 prices,
start, term and whether it is built. Built from LCCC's published lists (data/raw/lccc/).

Sources of the strike price, in order:
1. Live contracts with payments: the contract's own strike in 2024, weighted by output (the
   CPI-indexed price actually paid; 2024's average is the 2024-prices strike).
2. Auction outcomes (LCCC): AR1-AR6 in 2012 prices, raised to 2024 prices by DESNZ's own ratio
   from AR7 (£91.20 in 2024 prices = £65.45 in 2012 prices); AR7 and AR7a already in 2024 prices.
3. Hinkley Point C: £92.50/MWh in 2012 prices (the 2013 agreement), raised the same way.
"""
import re
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parents[2] / "data" / "raw" / "lccc"
P2012_TO_2024 = 91.20 / 65.45  # DESNZ, AR7 results (Jan 2026): the same price in both bases
HPC_STRIKE_2012 = 92.50
# Hinkley Point C has no start date in LCCC's list. Central: 1 Apr 2030, the year the OBR's
# March 2026 forecast (Table 3.21) first pays it (£983m in 2030-31). The start date is a bracket step.
HPC_START = pd.Timestamp("2030-04-01")
ROUND = {f"Allocation Round {i}": f"AR{i}" for i in range(1, 8)}
# Units whose LCCC portfolio name differs from the auction list's (AR3 Dogger Bank).
NAME_OVERRIDE = {
    "Dogger Bank A": "Doggerbank Creyke Beck A P1",
    "Dogger Bank B": "Doggerbank Creyke Beck B P1",
    "Dogger Bank C": "Doggerbank Teeside A P1",
}
# Term in years by round and technology; AR7 wind and solar contracts run 20 years.
TWENTY_YEAR_AR7 = {"Offshore Wind", "Onshore Wind", "Solar PV", "Floating Offshore Wind"}


def _norm(s: str) -> str:
    s = re.sub(r"\(.*?\)", "", str(s).lower())
    s = re.sub(r"phase\s*\w+|unit\s*\w+|limited|ltd|wind farm|offshore|solar farm|solar park|solar|windfarm|project", "", s)
    return re.sub(r"[^a-z0-9]", "", s)


def _auction_strike(row, outcomes: pd.DataFrame) -> float | None:
    rnd = ROUND.get(row.Allocation_Round)
    if rnd is None:
        return None
    o = outcomes[outcomes.Auction == rnd]
    name = next((v for k, v in NAME_OVERRIDE.items() if row.Name_of_CFD_Unit.startswith(k)), None)
    hit = o[o.Project_Name == name] if name else o[o.n == _norm(row.Name_of_CFD_Unit)]
    if hit.empty:  # pay-as-clear: one price per round, technology and delivery year
        tech = o[o.Technology_Type.str.split(" ").str[0] == str(row.Technology_Type).split(" ")[0]]
        start = pd.to_datetime(row.Expected_Start_Date, errors="coerce")
        if tech.empty:
            return None
        if pd.notna(start):
            tech = tech.iloc[(tech.Delivery_Year.astype(int) - start.year).abs().argsort()]
        hit = tech.head(1)
    strike = float(hit.Strike_Price_GBP_Per_MWh.iloc[0])
    return strike if rnd == "AR7" else strike * P2012_TO_2024


def term_years(row) -> float:
    if row.Allocation_Round == "Bespoke":
        return 35
    if row.Allocation_Round == "Allocation Round 7" and row.Technology_Type in TWENTY_YEAR_AR7:
        return 20
    return 15


def load(raw: Path = RAW) -> pd.DataFrame:
    p = pd.read_csv(raw / "cfd_contract_portfolio_status.csv")
    p = p[p.Status != "Terminated"].copy()
    outcomes = pd.read_csv(raw / "auction_outcomes.csv")
    outcomes["n"] = outcomes.Project_Name.map(_norm)
    act = pd.read_csv(raw / "actual_cfd_generation_and_avoided_ghg_emissions.csv",
                      usecols=["Settlement_Date", "CfD_ID", "CFD_Generation_MWh", "Strike_Price_GBP_Per_MWh"],
                      parse_dates=["Settlement_Date"])
    first = act.groupby("CfD_ID").Settlement_Date.min()  # first settlement, with or without output
    act = act[act.CFD_Generation_MWh > 0]
    y24 = act[act.Settlement_Date.dt.year == 2024]
    paid24 = (y24.Strike_Price_GBP_Per_MWh * y24.CFD_Generation_MWh).groupby(y24.CfD_ID).sum() \
        / y24.groupby("CfD_ID").CFD_Generation_MWh.sum()

    rows = []
    for r in p.itertuples():
        auction = _auction_strike(r, outcomes)
        if r.CFD_ID in paid24.index:
            strike, source = float(paid24[r.CFD_ID]), "paid 2024"
        elif r.Allocation_Round == "Bespoke":
            strike, source = HPC_STRIKE_2012 * P2012_TO_2024, "HPC agreement"
        else:
            strike, source = auction, "auction"
        start = first.get(r.CFD_ID, pd.to_datetime(r.Expected_Start_Date, errors="coerce"))
        if pd.isna(start) and r.Allocation_Round == "Bespoke":
            start = HPC_START
        if pd.isna(start):  # no date in LCCC's list: 1 April of the auction's delivery year
            hit = outcomes[(outcomes.Auction == ROUND.get(r.Allocation_Round)) & (outcomes.n == _norm(r.Name_of_CFD_Unit))]
            if not hit.empty:
                start = pd.Timestamp(f"{int(hit.Delivery_Year.iloc[0])}-04-01")
        rows.append(dict(cfd_id=r.CFD_ID, name=r.Name_of_CFD_Unit, round=r.Allocation_Round,
                         technology=r.Technology_Type, status=r.Status, built=r.Status.startswith("Live"),
                         capacity_mw=r.Maximum_Contract_Capacity_MW, start=start, term_years=term_years(r),
                         strike_2024=strike, strike_source=source, auction_strike_2024=auction))
    return pd.DataFrame(rows)
