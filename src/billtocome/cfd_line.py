"""The CfD line: every contract, every calendar year from the valuation date to its end (aios-harness#68).

Each contract-year: top-up = (strike - market x discount) x output, less the unpaid negative-price
hours, both ways (a negative top-up is a payment back), all in 2024 CPIH prices. Three lines:
renewables (allocation rounds and Investment Contracts), Hinkley Point C, and the biomass bridging
contracts (top-up only; output at the 27% load-factor cap). Built and not yet built are kept apart.
"""
from datetime import date

import pandas as pd

from . import contracts as C
from . import discount as D
from . import output as O
from .cfd import top_up_with_rule
from .prices import cpi_to_cpih

VALUATION_YEAR = 2026  # valuation date 1 Jan 2026 (build plan point 4)


def share_of_year(year: int, start: pd.Timestamp, end: pd.Timestamp) -> float:
    y0, y1 = pd.Timestamp(date(year, 1, 1)), pd.Timestamp(date(year + 1, 1, 1))
    lo, hi = max(y0, start), min(y1, end)
    return max(0.0, (hi - lo).days) / (y1 - y0).days


def line_of(row) -> str:
    if row.technology == "Nuclear":
        return "Hinkley Point C"
    if row["round"] == "Bridging":
        return "Biomass bridging"
    return "CfD renewables"


def build(s: "Scenario | None" = None, last_year: int = 2066) -> "Line":
    """The CfD scheme-line adapter: three lines, one row per contract-year (design: Scheme line)."""
    from .model import Line
    from .scenario import Scenario
    s = s or Scenario()
    c = C.load(hpc_strike_2012=s.hpc_strike_2012, hpc_term=s.hpc_term, hpc_shift_years=s.hpc_shift_years)
    if s.late_starts:
        from .unbuilt import late_starts
        c = late_starts(c)
    lf = O.measured(c[c["round"] != "Bridging"])
    new = O.new_farm_lf(c, lf)
    own = D.own_discounts()
    neg_price = {"wind": D.negative_price("wind"), "solar": D.negative_price("solar")}
    rows = []
    for r in c.itertuples(index=False):
        r = pd.Series(r._asdict()).rename({"round_": "round"}) if hasattr(r, "round_") else pd.Series(r._asdict())
        ln = line_of(r)
        if ln == "Biomass bridging":
            load_f, lf_src = C.BRIDGING_LF, "bridging cap"
        else:
            load_f, lf_src = O.load_factor(r, lf, new)
        rule = D.rule_for(r["round"])
        kind = "wind" if r.technology in D.WIND else "solar" if r.technology in D.SOLAR else None
        for y in range(VALUATION_YEAR, last_year + 1):
            frac = share_of_year(y, r.start, r.end)
            if frac == 0:
                continue
            mwh = O.yearly_mwh(r.capacity_mw, load_f, r.start.year, y,
                               decline=O.decline_for(r.technology, s.wind_decline, s.solar_decline)) * frac
            strike = r.strike_2024 * cpi_to_cpih(y)
            market = s.power(y)
            capture, ns = s.market.for_contract(y, r.technology, rule, own.get(r.cfd_id)) if kind else (1.0, 0.0)
            pay = top_up_with_rule(strike, market, capture, mwh, ns, neg_price.get(kind, 0.0))
            if ln == "Biomass bridging":
                pay = max(pay, 0.0)  # top-up only
            rows.append(dict(cfd_id=r.cfd_id, name=r["name"], line=ln, technology=r.technology,
                             round=r["round"], built=bool(r.built), year=y, share_of_year=frac, mwh=mwh,
                             load_factor=load_f, lf_source=lf_src, strike=strike, market=market,
                             capture=capture, neg_share=ns, payment=pay))
    out = pd.DataFrame(rows)
    if s.abandonment:
        from .unbuilt import termination_rate
        k = ~out.built & (out.line == "CfD renewables")
        out.loc[k, "payment"] *= 1 - out.loc[k, "technology"].map(termination_rate)
    out = _apply_hpc_cap(out, c)
    tidy = out.rename(columns={"cfd_id": "item", "payment": "cash"})[["line", "item", "technology", "built", "year", "cash"]]
    return Line(tidy, {"cfd_contracts": c, "cfd_contract_years": out})


def _apply_hpc_cap(out: pd.DataFrame, c: pd.DataFrame) -> pd.DataFrame:
    """Hinkley's 910 TWh cap covers both reactors together, counted from first generation."""
    cap = c.loc[c.technology == "Nuclear", "cap_mwh"].dropna()
    if cap.empty:
        return out
    h = out[out.line == "Hinkley Point C"].groupby("year").mwh.sum().sort_index()
    left, scale = float(cap.iloc[0]), {}
    for y, m in h.items():
        scale[y] = min(1.0, max(0.0, left) / m) if m else 1.0
        left -= m
    k = out.line == "Hinkley Point C"
    f = out.loc[k, "year"].map(scale)
    out.loc[k, "mwh"] *= f
    out.loc[k, "payment"] *= f
    return out


def by_year(out: pd.DataFrame) -> pd.DataFrame:
    return out.pivot_table(index="year", columns=["line", "built"], values="payment", aggfunc="sum", fill_value=0.0)
