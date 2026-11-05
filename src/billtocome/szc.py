"""The Sizewell C line (aios-harness#82; build plan points 2, 10, 11; Richard 5 Nov: choice (a)).

The levy is Sizewell C's Allowed Revenue less what its power sells for (zero until it runs), from the
licence's formula (Nuclear RAB licence, special conditions v7):
- Regulated Asset Base (SC27): the Day-1 RAB £5,197,977,481.50 (real CPIH 2024/25; DESNZ notice of
  23 Oct 2025) on 4 Nov 2025, plus capital spend up to the build cost, which the licence measures
  "when aggregated with the Day-1 RAB" (SC28): central the Original Lower Regulatory Threshold
  £40.509bn, high the Higher Regulatory Threshold £47.72bn, low the FID estimate (about £38bn);
  nothing above the HRT (point 11). The spend is not published: it is spread evenly over the days
  from 4 Nov 2025 to Scheduled COD, 29 Dec 2039 (stated).
- Pre-PCR Allowed Revenue (SC30): Return on Capital (SC31) = average RAB x ((1 + IWACC)^share - 1),
  IWACC 6.73% real CPIH; plus Opex (Original Opex Pre-PCR Allowance £2.341bn, spread as the spend),
  Social Benefits (£10.4m a year), Cost of Debt Adjustment and FDP allowance (Ofgem's 2026 PCFM
  variable values, 2025-26 to 2027-28; none after, stated); plus the Tax Building Block and the
  other blocks, taken as one share of the Return on Capital fitted to the Secretary of State's
  Allowed Revenue for the First Charging Year (£1,443,625,216.26 nominal, 4 Nov 2025-31 Mar 2027).
- Operations Phase, 2040 to 2099 (60 years from Scheduled COD; Richard's choice (a), stated
  settings): the return, depreciation and running costs are set by the Authority at the Post
  Construction Review (SC49, SC53, SC54), not in the licence. Stated: the return held at 6.73%; the
  RAB written off evenly over 60 years; running costs from BEIS Electricity Generation Costs 2016,
  Nuclear PWR FOAK (2014 prices: fixed O&M £72,900/MW/yr, insurance £10,000/MW/yr, connection
  £500/MW/yr; variable O&M £5, fuel £5, decommissioning £2 per MWh; DESNZ's later editions keep
  nuclear costs confidential); the tax and other blocks left out (not set; so a floor); output 2 x 1,639 MW
  (licence Original Baseline Target Capacity) at 90% (VfM assessment), sold at the Scenario's power
  price. The levy runs both ways: above the Allowed Revenue, Sizewell C pays back.
"""
from functools import cache
from pathlib import Path

import pandas as pd

from .prices import cpih

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
DAY1_RAB = 5_197_977_481.50  # real CPIH 2024/25
FIRST_CY_AR = 1_443_625_216.26  # nominal, 4 Nov 2025 - 31 Mar 2027
START, COD, END = pd.Timestamp("2025-11-04"), pd.Timestamp("2039-12-29"), pd.Timestamp("2099-12-29")
LRT, HRT, FID_ESTIMATE = 40_509_000_000, 47_720_000_000, 38_000_000_000
IWACC = 0.0673
OPEX_PRE_PCR = 2_341_000_000
SBC_A_YEAR = 10_400_000
MW = 2 * 1639
LOAD_FACTOR = 0.90
OPS_2014 = dict(fixed_per_mw=72_900 + 10_000 + 500, per_mwh=5 + 5 + 2)  # BEIS EGC 2016, Table 19 and Table 4


@cache
def variable_values() -> pd.DataFrame:
    """Ofgem, Sizewell C PCFM variable values, 2026 Annual Revenue Setting (Oct 2026), by charging year."""
    d = pd.read_excel(RAW / "sizewell-c" / "Annex-Sizewell-C-variable-value-proposal-to-modify.xlsx",
                      header=None, engine="calamine")
    years = [int(str(v)[:4]) for v in d.iloc[5, 5:8]]
    # keyed by the term, except two rows Ofgem both label "SBCAt": social benefits (£m) and the structures
    # and buildings capital allowance rate (%); the first is kept as "SBCAt", the second as "SBAt"
    rows = {}
    for i in range(6, d.shape[0]):
        term = str(d.iat[i, 3]).strip()
        if term == "SBCAt" and str(d.iat[i, 2]).startswith("Structures"):
            term = "SBAt"
        rows[term] = [float(v) if v != "-" else 0.0 for v in d.iloc[i, 5:8]]
    return pd.DataFrame(rows, index=years)


@cache
def _cpih_monthly() -> dict[tuple[int, str], float]:
    import csv
    out = {}
    with open(RAW / "ons" / "cpih-index-l522.csv", newline="") as f:
        for row in csv.reader(f):
            if len(row) == 2 and len(row[0]) == 8 and row[0][:4].isdigit() and row[0][5:].isalpha():
                out[(int(row[0][:4]), row[0][5:])] = float(row[1])
    return out


def cpih_fy(start_year: int) -> float:
    """ONS CPIH, mean of April `start_year` to March `start_year + 1`."""
    m = _cpih_monthly()
    months = [(start_year, x) for x in ("APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")]
    months += [(start_year + 1, x) for x in ("JAN", "FEB", "MAR")]
    return sum(m[k] for k in months) / 12


def to_2024(value_2425: float) -> float:
    """Real CPIH 2024/25 -> 2024 CPIH prices (calendar 2024 = 1)."""
    m = _cpih_monthly()
    cal24 = sum(v for (y, _), v in m.items() if y == 2024) / 12
    return value_2425 * cal24 / cpih_fy(2024)


def charging_years(cost: float) -> pd.DataFrame:
    """Pre-PCR charging years (1 April - 31 March, the first from 4 Nov 2025, the last to Scheduled COD),
    real CPIH 2024/25, before the other building blocks."""
    days_total = (COD - START).days
    spend_a_day = (cost - DAY1_RAB) / days_total
    opex_a_day = OPEX_PRE_PCR / days_total
    vv = variable_values()
    rows, rab = [], DAY1_RAB
    for cy in range(2025, 2040):
        lo, hi = max(START, pd.Timestamp(f"{cy}-04-01")), min(COD, pd.Timestamp(f"{cy + 1}-04-01"))
        days = (hi - lo).days
        share = days / (pd.Timestamp(f"{cy + 1}-04-01") - pd.Timestamp(f"{cy}-04-01")).days
        opening, closing = rab, rab + spend_a_day * days
        roc = (opening + closing) / 2 * ((1 + IWACC) ** share - 1)
        cda = vv.at[cy, "CDAt"] * 1e6 if cy in vv.index else 0.0
        fdp = vv.at[cy, "FDPt"] * 1e6 if cy in vv.index else vv["FDPt"].iloc[-1] * 1e6 * share
        sbc = vv.at[cy, "SBCAt"] * 1e6 if cy in vv.index else SBC_A_YEAR * share
        rows.append(dict(charging_year=cy, start=lo, end=hi, share=share, opening_rab=opening,
                         closing_rab=closing, roc=roc, opex=opex_a_day * days, sbc=sbc, cda=cda, fdp=fdp))
        rab = closing
    return pd.DataFrame(rows)


def other_share() -> float:
    """The Tax Building Block and the other blocks, as a share of the Return on Capital, fitted to the
    Allowed Revenue for the First Charging Year (charging years 2025-26 and 2026-27)."""
    c = charging_years(LRT).set_index("charging_year").loc[[2025, 2026]]
    vv = variable_values()
    pi = vv.loc[[2025, 2026], "CPIHt+forecast"] / cpih_fy(2024)
    known = c.roc + c.opex + c.sbc + c.cda + c.fdp
    # nominal AR = sum over the two periods of (known + k x RoC) x PI  ->  solve for k
    return float((FIRST_CY_AR - (known * pi).sum()) / (c.roc * pi).sum())


def _calendarise(cy: pd.DataFrame, col: str) -> dict[int, float]:
    out: dict[int, float] = {}
    for r in cy.itertuples():
        days = (r.end - r.start).days
        for y in range(r.start.year, r.end.year + 1):
            a, b = max(r.start, pd.Timestamp(f"{y}-01-01")), min(r.end, pd.Timestamp(f"{y + 1}-01-01"))
            if b > a:
                out[y] = out.get(y, 0.0) + getattr(r, col) * (b - a).days / days
    return out


def build(s=None, first: int = 2026):
    """The Sizewell C scheme-line adapter: one row per year, the levy in 2024 prices."""
    from .model import Line
    from .scenario import Scenario
    s = s or Scenario()
    k = other_share()
    cy = charging_years(s.szc_cost)
    cy["other"] = k * cy.roc
    cy["allowed"] = cy[["roc", "opex", "sbc", "cda", "fdp", "other"]].sum(axis=1)
    pre = _calendarise(cy, "allowed")
    ops_cost_2024 = (OPS_2014["fixed_per_mw"] * MW + OPS_2014["per_mwh"] * MW * LOAD_FACTOR * 8766) / cpih(2014)
    rows = []
    for y in range(first, 2100):
        hours = (pd.Timestamp(f"{y + 1}-01-01") - pd.Timestamp(f"{y}-01-01")).days * 24
        if y < 2040:
            rows.append(dict(year=y, phase="construction", allowed_2425=pre.get(y, 0.0), mwh=0.0, market=0.0))
            continue
        n = y - 2040
        dep = s.szc_cost / 60
        opening = s.szc_cost - dep * n
        avg = opening - dep / 2
        roc = avg * s.szc_ops_return
        mwh = MW * LOAD_FACTOR * hours
        # other blocks (chiefly tax) after 2039 are not set and are left out (stated; a floor)
        rows.append(dict(year=y, phase="operation", allowed_2425=roc + dep, running_2024=ops_cost_2024,
                         mwh=mwh, market=mwh * s.power(y)))
    out = pd.DataFrame(rows).fillna({"running_2024": 0.0})
    out["allowed"] = out.allowed_2425.map(to_2024) + out.running_2024
    out["payment"] = out.allowed - out.market
    tidy = out.assign(line="Sizewell C", item="Sizewell C", technology="Nuclear", built=False,
                      cash=out.payment)[["line", "item", "technology", "built", "year", "cash"]]
    return Line(tidy, {"szc_charging_years": cy.assign(other_share=k), "szc_years": out})
