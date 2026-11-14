"""Who pays (aios-harness#83; build plan points 18-20, 22; docs/facts.md 13, 18-20).

`split(table, scenario)` turns every scheme row into its households' and businesses' parts, then moves
money between payers on rows of their own (each scheme line's whole is unchanged), and adds VAT:
- Households' share (point 18, 19): households' share of UK final electricity consumption, 2025, held
  (DUKES 5.1: 96,188.8 of 275,527.5 GWh = 34.9%); bracket: DESNZ's projected share by year (EEP
  2024-2050 Reference, Annex F: residential electricity over total electricity; 2050's after 2050).
- The RO's households' share (point 27, Richard 9 Nov): DESNZ's domestic share of RO costs, "approximately
  41 per cent" (Budget 2025 policy costings, p.12; fact 13), the share the Exchequer's 75% is costed on.
  Held in every scenario: the households' share bracket moves the other lines only.
- Taxpayers' RO share (fact 13): the Exchequer funds 75% of the domestic share of the RO from 1 April
  2026 to 31 March 2029; moved from households to taxpayers.
- Manufacturers' exemption, BICS (point 20, 22; fact 20): eligible firms exempt from the RO, FiT and
  Capacity Market from 1 April 2027, "up to £600 million per year, operating between 2027 and 2035"
  (taken as cash, to 31 March 2035), plus a first-year back payment for 2026-27 that "approximately
  doubles the first year's total benefit" (taken as a further £600m, against 2026-27's costs). Not
  CfD. Shared across the three schemes in proportion to businesses' part of each (the Capacity Market
  at its whole levy, of which only net zero's share is in the line); moved from businesses to
  taxpayers.
- VAT (point 18): 5%, the reduced rate on domestic fuel and power (VAT Act 1994, Sch. 7A), on what households
  pay of each line, its own line ("VAT"), item = the scheme; 0% from 1 October 2026 to 30 June 2027 (version 1.2.5).
  The Value Added Tax (Supplies of Domestic Electricity) Order 2026 (SI 2026/987, made 7 Sep 2026) zero-rates
  supplies made 1 October 2026 to 31 March 2027; Budget 2026 (28 Oct 2026, para 2.48; policy costings p.12:
  "effective from 1 October 2026 until 1 July 2027") extends it, announced, not yet law at the cut-off; the model
  counts it, as it counts the Budget's other announced measures (conductor's ruling, aios-harness#236). Applied
  by days in each calendar year, as the Exchequer's and BICS windows are (`share_of_year`).
"""
from functools import cache
from pathlib import Path

import pandas as pd

from .prices import cpih

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
HOUSEHOLDS_2025 = 96_188.8 / 275_527.5  # DUKES 5.1, 2025 (fact 18)
RO_HOUSEHOLDS = 0.41  # DESNZ's domestic share of RO costs (point 27, fact 13)
VAT = 0.05  # the reduced rate (VAT Act 1994, Sch. 7A)
VAT_ZERO = 0.0
VAT_ZERO_IN_LAW = (pd.Timestamp("2026-10-01"), pd.Timestamp("2027-04-01"))  # SI 2026/987, art. 1(2)
VAT_ZERO_WINDOW = (pd.Timestamp("2026-10-01"), pd.Timestamp("2027-07-01"))  # with Budget 2026's extension
EXCHEQUER_RO = 0.75
EXCHEQUER_WINDOW = (pd.Timestamp("2026-04-01"), pd.Timestamp("2029-04-01"))
BICS_WINDOW = (pd.Timestamp("2027-04-01"), pd.Timestamp("2035-04-01"))
BICS_BACK = (pd.Timestamp("2026-04-01"), pd.Timestamp("2027-04-01"))
BICS_LINES = ("RO", "FiT", "Capacity Market")
# The rows that move cost between payers, not contracts of their own (their item names)
EXCHEQUER_ITEM = "Exchequer: 75% of households' share, Apr 2026-Mar 2029"
BICS_ITEM = "Manufacturers' exemption (BICS)"
MOVES = (EXCHEQUER_ITEM, BICS_ITEM)


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


def vat_rate(year: int, window: tuple[pd.Timestamp, pd.Timestamp] = VAT_ZERO_WINDOW) -> float:
    """VAT on households' part in calendar `year`: 0% for the days in `window`, 5% for the rest."""
    f = share_of_year(year, window)
    return VAT_ZERO * f + VAT * (1 - f)


def bics_real(year: int, a_year: float) -> float:
    """The exemption in calendar `year`, £ in 2024 prices (cash £600m a year, plus the back payment)."""
    return a_year * (share_of_year(year, BICS_WINDOW) + share_of_year(year, BICS_BACK)) / cpih(year)


def split(table: pd.DataFrame, s) -> pd.DataFrame:
    t = table.drop(columns=[c for c in ("payer",) if c in table])
    h = t.year.map(lambda y: households_share(y, s.households)).where(t.line != "RO", RO_HOUSEHOLDS)
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
            move("RO", EXCHEQUER_ITEM, y, "households", "taxpayers",
                 EXCHEQUER_RO * f * by[("RO", "households", y)])
        e = bics_real(y, s.bics_a_year)
        if e:
            base = {ln: by.get((ln, "businesses", y), 0.0) for ln in BICS_LINES}
            base["Capacity Market"] /= s.cm_share  # the whole levy is what firms are exempted from
            total = sum(base.values())
            for ln, b in base.items():
                if b:
                    amount = e * b / total * (s.cm_share if ln == "Capacity Market" else 1.0)
                    move(ln, BICS_ITEM, y, "businesses", "taxpayers", amount)
    out = pd.concat([out, pd.DataFrame(moves)], ignore_index=True)
    hh = out[out.payer == "households"].groupby(["line", "built", "year"]).cash.sum().reset_index()
    vat = hh.assign(item=hh.line + ("|" + hh.built.map({True: "built", False: "not yet built"})),
                    line="VAT", technology="", payer="households", cash=hh.cash * hh.year.map(vat_rate))
    return pd.concat([out, vat[out.columns]], ignore_index=True)
