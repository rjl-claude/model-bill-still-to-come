"""The Capacity Market line (aios-harness#81; build plan CM row, point 9).

Each agreement in NESO's register (28 Oct 2026) awarded in an auction (T-4, T-3, T-1, transitional),
not terminated: capacity obligation (MW) x its auction's clearing price (£/kW/yr), for each delivery
year (October to September) it is valid for that is still to come.
- Indexation (Electricity Capacity Regulations 2014, Sch. 1 para 3(5), (7); docs/facts.md 23): a T-4
  (and T-3) agreement's price x CPI of the winter (October-April) before the delivery year / CPI of the
  auction's base-period winter. T-1 and transitional auctions have no base period in NESO's auction
  data and the Regulations give them no formula: their price is not indexed.
- CPI by winter: ONS monthly index (D7BT) where published; later months from the OBR's October 2026
  quarterly CPI (Table 1.7), spliced to the last ONS month; after the OBR, the annual CPI path.
- Calendar years: each month's payment is weighted by its share of GB demand (Sch. 1 para 2); the
  October-December share of a delivery year is measured from NESO's demand record, delivery years
  2022/23-2024/25.
- The line counts net zero's share of the whole levy (point 9): the Clock's 2025 share, held flat; the
  whole levy is kept in the in-between table for the OBR check.
"""
import json
from functools import cache
from pathlib import Path

import pandas as pd

from .prices import cpi, cpih

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
# The Clock export of Report No. 1's engine release v4-s43, via model-bill-already-paid, saved here (MANIFEST,
# sha256 e1cf23af..., the file model-register.yaml pins). From 1.2.1 the model reads its own copy, not that
# model's folder; a new engine release is never applied by itself.
ENGINE = RAW / "model-bill-already-paid" / "v4-s43.json"
AUCTIONS = ("T-4", "T-3", "T-1", "TR")
WINTER_MONTHS = ("OCT", "NOV", "DEC", "JAN", "FEB", "MAR", "APR")


@cache
def netzero_shares() -> dict[int, float]:
    """Net zero's share of the Capacity Market levy by year, Clock engine v4-s43."""
    y = json.loads(ENGINE.read_text())["capacity_market"]["years"]
    return {int(k): v["netzero_gbp"] / v["cm_paid_gbp"] for k, v in y.items()}


SHARE_CENTRAL = netzero_shares()[2025]  # point 9: 14.6%
SHARE_LOW = min(netzero_shares()[y] for y in range(2021, 2026))  # 13.6% (2022)
SHARE_HIGH = max(netzero_shares()[y] for y in range(2021, 2026))  # 15.6% (2024)


@cache
def _ons_monthly() -> dict[tuple[int, str], float]:
    import csv
    out = {}
    with open(RAW / "ons" / "cpi-index-d7bt.csv", newline="") as f:
        for row in csv.reader(f):
            if len(row) == 2 and len(row[0]) == 8 and row[0][:4].isdigit() and row[0][5:].isalpha():
                out[(int(row[0][:4]), row[0][5:])] = float(row[1])
    return out


@cache
def _obr_quarterly() -> dict[tuple[int, int], float]:
    d = pd.read_excel(RAW / "obr" / "october-2026-efo-detailed-forecast-tables-economy.xlsx",
                      sheet_name="1.7", header=None, engine="calamine")
    assert d.iloc[3, 14] == "CPI", "OBR Table 1.7 layout changed"
    q = d.iloc[4:, [1, 14]].dropna()
    q = q[q[1].astype(str).str.fullmatch(r"\d{4}Q\d")]
    return {(int(s[:4]), int(s[5])): float(v) for s, v in zip(q[1].astype(str), q[14])}


MONTHS = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")


def cpi_month(year: int, month: str) -> float:
    ons = _ons_monthly()
    if (year, month) in ons:
        return ons[(year, month)]
    last = max(ons, key=lambda k: (k[0], MONTHS.index(k[1])))
    obr = _obr_quarterly()
    q_last = (last[0], MONTHS.index(last[1]) // 3 + 1)
    q = (year, MONTHS.index(month) // 3 + 1)
    if q in obr:
        return ons[last] * obr[q] / obr[q_last]
    q_end = max(obr)
    return ons[last] * obr[q_end] / obr[q_last] * cpi(year) / cpi(q_end[0])


def winter_cpi(april_year: int) -> float:
    """Mean CPI over October (april_year - 1) to April (april_year)."""
    months = [(april_year - 1, m) for m in WINTER_MONTHS[:3]] + [(april_year, m) for m in WINTER_MONTHS[3:]]
    return sum(cpi_month(y, m) for y, m in months) / len(months)


@cache
def autumn_share() -> float:
    """October-December share of a delivery year's GB demand, delivery years 2022/23-2024/25."""
    parts = []
    for y in range(2022, 2026):
        d = pd.read_csv(RAW / "halfhourly" / f"demanddata_{y}.csv", usecols=["SETTLEMENT_DATE", "ND"])
        d["date"] = pd.to_datetime(d.SETTLEMENT_DATE, format="mixed", dayfirst=True)
        parts.append(d)
    d = pd.concat(parts)
    d["dy"] = d.date.dt.year - (d.date.dt.month < 10)
    d = d[d.dy.isin([2022, 2023, 2024])]
    q4 = d[d.date.dt.month >= 10].groupby("dy").ND.sum()
    return float((q4 / d.groupby("dy").ND.sum()).mean())


def register_file() -> Path:
    """NESO's newest CMU register on disk (named cmu_YYYYMMDD.csv); the freeze's is the cut-off date's."""
    return sorted((RAW / "neso").glob("cmu_2*.csv"))[-1]


@cache
def agreements() -> pd.DataFrame:
    r = pd.read_csv(register_file(), low_memory=False)
    r = r[r.Type.isin(AUCTIONS) & (r["Capacity Agreement Awarded"] == "Yes")
          & (r["Capacity Agreement has been Terminated"] != "Yes")]
    s = pd.read_csv(RAW / "neso" / "capacity-market-auction-static-data.csv", encoding="utf-8-sig")
    s = s.set_index("Auction Name")
    out = pd.DataFrame({
        "agreement": r["Unique Agreement Identifier"].astype(str) + "|" + r["Auction Name"].str[:13],
        "auction": r["Auction Name"], "type": r.Type, "cmu": r["CMU ID"],
        "technology": r["Primary Fuel Type"].fillna(r["CMU Technology"]).fillna("unknown"),
        "category": r["CM Unit Category"], "mw": r["Auction Acquired Capacity Obligation"].astype(float),
        "years": r["Delivery Years for which Agreement Valid"].astype(str)})
    out["price"] = out.auction.map(s["Clearing Price_GBP per kW per year"]).astype(float)
    base = out.auction.map(s["Base Period for the Agreement"])
    out["base_april_year"] = base.str.extract(r"(\d{4})$")[0].astype("Int64")  # "Winter 2021/2022" -> 2022
    out["delivery_years"] = out.years.str.findall(r"(\d{4})/\d{4}").map(lambda v: [int(x) for x in v])
    out["first_year"] = out.delivery_years.map(min)
    out["built"] = ~(out.category.str.startswith("New Build") & (out.first_year >= 2026))
    return out.reset_index(drop=True)


def payment_cash(price: float, mw: float, delivery_year: int, base_april_year) -> float:
    """One delivery year's capacity payments, £ cash (Sch. 1 para 3(5))."""
    index = 1.0 if pd.isna(base_april_year) else winter_cpi(delivery_year) / winter_cpi(int(base_april_year))
    return mw * 1000 * price * index


def build(s=None, first: int = 2026):
    """The Capacity Market scheme-line adapter: one row per agreement-year (design: Scheme line)."""
    from .model import Line
    from .scenario import Scenario
    s = s or Scenario()
    a = agreements()
    w = autumn_share()
    rows = []
    for r in a.itertuples(index=False):
        for dy in r.delivery_years:
            if dy + 1 < first:
                continue
            cash = payment_cash(r.price, r.mw, dy, r.base_april_year)
            for y, part in ((dy, w), (dy + 1, 1 - w)):
                if y >= first:
                    rows.append(dict(agreement=r.agreement, technology=r.technology, built=r.built,
                                     delivery_year=dy, year=y, whole_cash=cash * part,
                                     whole_real=cash * part / cpih(y)))
    out = pd.DataFrame(rows)
    out["payment"] = out.whole_real * s.cm_share
    yearly = out.groupby(["agreement", "technology", "built", "year"], as_index=False).payment.sum()
    tidy = yearly.rename(columns={"agreement": "item", "payment": "cash"}).assign(line="Capacity Market")
    return Line(tidy[["line", "item", "technology", "built", "year", "cash"]],
                {"cm_agreements": a.drop(columns=["delivery_years"]), "cm_agreement_years": out})
