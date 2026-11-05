"""Brackets run and the tornado (aios-harness#85; design: Brackets).

Each bracket's two ends are run in turn, every other input central. `tornado()` gives one row per
bracket: the whole bill (2026 to the end, £ 2024 prices) at each end, its swing, ranked by swing, plus
the same at present value. `range_of(t)` is the lowest and highest bill of any bracket run.
"""
import pandas as pd

from .model import Results, run
from .present_value import present_value
from .scenario import BRACKETS, Scenario

MEASURES = ("cash", "pv_green_book", "pv_hurdle")


def run_one(s: Scenario) -> Results:
    return run(s)


def headline(r: Results, measure: str = "cash") -> float:
    if measure == "cash":
        return float(r.table.cash.sum())
    return float(present_value(r, measure.removeprefix("pv_")).pv.sum())


def tornado(brackets=BRACKETS, measures=MEASURES) -> pd.DataFrame:
    central = run_one(Scenario())
    c = {m: headline(central, m) for m in measures}
    rows = []
    for b in brackets:
        lo, hi = (central if s == Scenario() else run_one(s) for s in (b.low, b.high))  # one-sided: reuse central
        row = dict(bracket=b.name)
        for m in measures:
            sfx = "" if m == "cash" else f"_{m}"
            row |= {f"central{sfx}": c[m], f"low_bill{sfx}": headline(lo, m), f"high_bill{sfx}": headline(hi, m)}
            row[f"swing{sfx}"] = abs(row[f"high_bill{sfx}"] - row[f"low_bill{sfx}"])
        rows.append(row)
    return pd.DataFrame(rows).sort_values("swing", ascending=False, ignore_index=True)


def range_of(t: pd.DataFrame, measure: str = "cash") -> tuple[float, float]:
    sfx = "" if measure == "cash" else f"_{measure}"
    ends = pd.concat([t[f"low_bill{sfx}"], t[f"high_bill{sfx}"]])
    return float(ends.min()), float(ends.max())
