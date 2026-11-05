"""Who pays (aios-harness#83; build plan points 18-20, 22; docs/facts.md 13, 18-20).

`split(table, scenario)` turns every scheme row into its households' and businesses' parts, then moves
money between payers on rows of their own (each scheme line's whole is unchanged), and adds VAT:
- Households' share (point 18, 19): households' share of UK final electricity consumption, 2025, held
  (DUKES 5.1: 96,188.8 of 275,527.5 GWh = 34.9%); bracket: DESNZ's projected share by year (EEP
  2024-2050 Reference, Annex F: residential electricity over total electricity; 2050's after 2050).
- Taxpayers' RO share (fact 13): the Exchequer funds 75% of the domestic share of the RO from 1 April
  2026 to 31 March 2029; moved from households to taxpayers.
- Manufacturers' exemption, BICS (point 20, 22; fact 20): eligible firms exempt from the RO, FiT and
  Capacity Market from 1 April 2027, "up to £600 million per year, operating between 2027 and 2035"
  (taken as cash, to 31 March 2035), plus a first-year back payment for 2026-27 that "approximately
  doubles the first year's total benefit" (taken as a further £600m, against 2026-27's costs). Not
  CfD. Shared across the three schemes in proportion to businesses' part of each (the Capacity Market
  at its whole levy, of which only net zero's share is in the line); moved from businesses to
  taxpayers.
- VAT (point 18): 5% on what households pay of each line, its own line ("VAT"), item = the scheme.
"""
from functools import cache
from pathlib import Path

import pandas as pd

from .prices import cpih

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
HOUSEHOLDS_2025 = 96_188.8 / 275_527.5  # DUKES 5.1, 2025 (fact 18)
VAT = 0.05
EXCHEQUER_RO = 0.75
EXCHEQUER_WINDOW = (pd.Timestamp("2026-04-01"), pd.Timestamp("2029-04-01"))
BICS_WINDOW = (pd.Timestamp("2027-04-01"), pd.Timestamp("2035-04-01"))
BICS_BACK = (pd.Timestamp("2026-04-01"), pd.Timestamp("2027-04-01"))
BICS_LINES = ("RO", "FiT", "Capacity Market")


@cache
def eep_households() -> dict[int, float]:
    d = pd.read_excel(RAW / "desnz" / "Annex_F_final_energy_demand_TWh.ods", sheet_name="Reference",
                      header=None, engine="odf")
    years = [int(float(v)) for v in d.iloc[2, 4:]]
    row = lambda cov: d[(d[0] == cov) & (d[1] == "Electricity")].iloc[0, 4:].astype(float).values  # noqa: E731
    res, tot = row("Residential"), row("Total excluding international aviation")
    return {y: float(r / t) for y, r, t in zip(years, res, tot)}


def households_share(year: int, path: str = "held") -> float:
    if path == "held":
        return HOUSEHOLDS_2025
    e = eep_households()
    return e[min(year, max(e))]


def share_of_year(year: int, window: tuple[pd.Timestamp, pd.Timestamp]) -> float:
    y0, y1 = pd.Timestamp(f"{year}-01-01"), pd.Timestamp(f"{year + 1}-01-01")
    lo, hi = max(y0, window[0]), min(y1, window[1])
    return max(0.0, (hi - lo).days) / (y1 - y0).days


def bics_real(year: int, a_year: float) -> float:
    """The exemption in calendar `year`, £ in 2024 prices (cash £600m a year, plus the back payment)."""
    return a_year * (share_of_year(year, BICS_WINDOW) + share_of_year(year, BICS_BACK)) / cpih(year)


def split(table: pd.DataFrame, s) -> pd.DataFrame:
    t = table.drop(columns=[c for c in ("payer",) if c in table])
    h = t.year.map(lambda y: households_share(y, s.households))
    parts = [t.assign(payer="households", cash=t.cash * h), t.assign(payer="businesses", cash=t.cash * (1 - h))]
    out = pd.concat(parts, ignore_index=True)
    by = out.groupby(["line", "payer", "year"]).cash.sum()
    moves = []

    def move(line, item, year, frm, to, amount):
        for payer, sign in ((frm, -1), (to, 1)):
            moves.append(dict(line=line, item=item, technology="", built=True, payer=payer, year=year, cash=sign * amount))

    for y in sorted(out.year.unique()):
        f = share_of_year(y, EXCHEQUER_WINDOW)
        if f and ("RO", "households", y) in by:
            move("RO", "Exchequer: 75% of households' share, Apr 2026-Mar 2029", y, "households", "taxpayers",
                 EXCHEQUER_RO * f * by[("RO", "households", y)])
        e = bics_real(y, s.bics_a_year)
        if e:
            base = {ln: by.get((ln, "businesses", y), 0.0) for ln in BICS_LINES}
            base["Capacity Market"] /= s.cm_share  # the whole levy is what firms are exempted from
            total = sum(base.values())
            for ln, b in base.items():
                if b:
                    amount = e * b / total * (s.cm_share if ln == "Capacity Market" else 1.0)
                    move(ln, "Manufacturers' exemption (BICS)", y, "businesses", "taxpayers", amount)
    out = pd.concat([out, pd.DataFrame(moves)], ignore_index=True)
    hh = out[out.payer == "households"].groupby(["line", "built", "year"]).cash.sum().reset_index()
    vat = hh.assign(item=hh.line + ("|" + hh.built.map({True: "built", False: "not yet built"})),
                    line="VAT", technology="", payer="households", cash=hh.cash * VAT)
    return pd.concat([out, vat[out.columns]], ignore_index=True)
