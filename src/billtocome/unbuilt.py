"""Two brackets for contracts not yet built (build plan point 16; aios-harness#69).

Abandonment: each unbuilt renewable contract's payments are cut by its technology's measured
termination rate in the mature rounds AR1-AR4 (LCCC portfolio: terminated / awarded). A technology
with fewer than 10 contracts in those rounds takes the rate for all of them (25%). Hinkley Point C
and the bridging contracts are left alone.

Late starts: each unbuilt contract starts as late as its round's measured delay implies: the
average gap between first payment and 1 April of the delivery year bid for, among contracts already
generating. Rounds with fewer than 10 measured contracts take the mature rounds' average (AR1, AR2,
AR4). The start never moves earlier than LCCC's expected date; the term is unchanged.
"""
from functools import cache
from pathlib import Path

import pandas as pd

from . import contracts as C

RAW = C.RAW
MATURE = tuple(f"Allocation Round {i}" for i in (1, 2, 3, 4))
MIN_COUNT = 10


@cache
def termination_rates(raw: Path = RAW) -> tuple[dict, float]:
    p = pd.read_csv(raw / "cfd_contract_portfolio_status.csv")
    p = p[p.Allocation_Round.isin(MATURE)]
    t = p.Status == "Terminated"
    overall = float(t.mean())
    g = t.groupby(p.Technology_Type).agg(["mean", "count"])
    return {k: float(v["mean"]) for k, v in g.iterrows() if v["count"] >= MIN_COUNT}, overall


def termination_rate(technology: str) -> float:
    by, overall = termination_rates()
    return by.get(technology, overall)


def _delivery_year(c: pd.DataFrame, raw: Path = RAW) -> pd.Series:
    o = pd.read_csv(raw / "auction_outcomes.csv")
    o["n"] = o.Project_Name.map(C._norm)
    key = {(a, n): int(d) for a, n, d in zip(o.Auction, o.n, o.Delivery_Year)}
    return c.apply(lambda r: key.get((C.ROUND.get(r["round"]), C._norm(r["name"]))), axis=1)


@cache
def delays() -> tuple[dict, float]:
    """Average measured delay in years by round, and the mature rounds' average."""
    c = C.load()
    c = c[c.built & c["round"].str.startswith("Allocation")].copy()
    c["dy"] = _delivery_year(c)
    c = c.dropna(subset=["dy"])
    c["delay"] = (c.start - pd.to_datetime(c.dy.astype(int).astype(str) + "-04-01")).dt.days / 365.25
    g = c.groupby("round").delay.agg(["mean", "count"])
    mature = c[c["round"].isin(MATURE)].delay.mean()
    return {k: float(v["mean"]) for k, v in g.iterrows() if v["count"] >= MIN_COUNT}, float(mature)


def delay_for(round_: str) -> float:
    by, mature = delays()
    return by.get(round_, mature)


def late_starts(c: pd.DataFrame) -> pd.DataFrame:
    """The contract list with each unbuilt allocation-round contract started as late as its round implies."""
    c = c.copy()
    k = ~c.built & c["round"].str.startswith("Allocation")
    dy = _delivery_year(c[k])
    for i in c.index[k]:
        d = dy.get(i)
        if d is None or pd.isna(d):
            continue
        target = pd.Timestamp(f"{int(d)}-04-01") + pd.Timedelta(days=round(delay_for(c.at[i, "round"]) * 365.25))
        shift = max(pd.Timedelta(0), target - c.at[i, "start"])
        c.at[i, "start"] += shift
        c.at[i, "end"] += shift
    return c
