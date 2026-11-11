"""Present value to the valuation date (aios-harness#84; build plan points 4, 8; facts 7, 11, 30).

`present_value(results, rate) -> table`: the results table with a `pv` column, £ 2024 prices, real.
- "green_book": the STPR, 3.00% real for years 1 to 30, 2.50% for years 31 to 75 (HM Treasury Green Book
  2026, revised 28 Oct 2026, para 6.54; aios-harness#255). Its 2.25% from year 76 is past the model's end.
- "hurdle": each row at its technology's DESNZ hurdle rate (real pre-tax; *Electricity Generation
  Costs 2025*, Table 6 and Annex A, medium, 2035 on). A technology with no 2025 rate takes the nearest
  (Richard, 5 Nov): nuclear at Sizewell C's licence WACC, 6.73% real; hydro and small wind and solar
  7.6%; every other fuelled or firm technology 8.9% (gas).
Year 0 is the valuation year, 2026, not discounted (the Green Book's convention; Richard, 5 Nov).
Rows with no technology take their line's rate: VAT's present value is 5% of households' part of
its line, year by year; the Exchequer and exemption rows take their line's cash-weighted factor.
"""
import pandas as pd

from .model import VALUATION_DATE, Results
from .who_pays import VAT

GREEN_BOOK = ((30, 0.030), (75, 0.025))  # (last year at this rate, rate); the model ends at year 73
NUCLEAR = 0.0673  # Sizewell C licence IWACC, real CPIH (facts 7, 30)
RULES = (  # first match on the technology's name, lower case
    ("floating", 0.101), ("tidal", 0.101), ("geothermal", 0.101),
    ("offshore", 0.089), ("nuclear", NUCLEAR),
    ("wind", 0.076), ("solar", 0.076), ("photovoltaic", 0.076), ("hydro", 0.076),
)
FIRM = 0.089  # gas CCGT, the rate for every other fuelled or firm technology


def hurdle_rate(technology: str) -> float:
    t = technology.lower()
    return next((r for key, r in RULES if key in t), FIRM)


def green_book_factor(year: int) -> float:
    t, f, start = year - VALUATION_DATE.year, 1.0, 0
    if t > GREEN_BOOK[-1][0]:
        raise ValueError(f"{year}: past year {GREEN_BOOK[-1][0]}, the Green Book's next step (2.25%) is not in")
    for end, rate in GREEN_BOOK:
        n = min(t, end) - start
        if n <= 0:
            break
        f /= (1 + rate) ** n
        start = end
    return f


def present_value(results: Results, rate: str) -> pd.DataFrame:
    t = results.table.copy()
    t0 = VALUATION_DATE.year
    if rate == "green_book":
        t["pv"] = t.cash * t.year.map(green_book_factor)
        return t
    if rate != "hurdle":
        raise ValueError(f"rate {rate!r}: 'green_book' or 'hurdle'")
    tech = t.technology.fillna("")
    own = tech != ""
    factor = pd.Series(float("nan"), index=t.index)
    factor[own] = (1 + tech[own].map(hurdle_rate)) ** -(t.year[own] - t0)
    t["pv"] = t.cash * factor
    # Exchequer and exemption rows: their line's own rows' factor that year, weighted by cash.
    w = t[own].assign(w=t.cash[own].abs(), wf=t.cash[own].abs() * factor[own]).groupby(["line", "year"])[["w", "wf"]].sum()
    line_factor = (w.wf / w.w).to_dict()
    moved = ~own & (t.line != "VAT")
    t.loc[moved, "pv"] = t.cash[moved] * [line_factor[k] for k in zip(t.line[moved], t.year[moved])]
    # VAT: 5% of households' part of its line, built or not, that year.
    hh = t[(t.payer == "households") & (t.line != "VAT")]
    hh_pv = hh.assign(built=hh.built.map({True: "built", False: "not yet built"})).groupby(["line", "built", "year"]).pv.sum()
    vat = t.line == "VAT"
    keys = [tuple(item.split("|")) + (y,) for item, y in zip(t.item[vat], t.year[vat])]
    t.loc[vat, "pv"] = [VAT * hh_pv.get(k, 0.0) for k in keys]
    return t
