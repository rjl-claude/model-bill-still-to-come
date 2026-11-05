"""The Feed-in Tariff line (aios-harness#81; build plan FiT row, points 17, 4).

Measure: the Clock's, Ofgem's "scheme value" = generation payments + export payments + licensees'
qualifying costs (SY15, 2024-25: £1,732m + £94m + £17.5m = £1.84bn; Ofgem FIT annual report SY15
Figs 3.5, 3.6; Clock reference/ref_totals.yaml). Ofgem's levelisation fund nets the market value of
exported power out of the export payments (SY15 £1,726m); it is kept beside, not counted.

Groups: every installation in Ofgem's installation report (Sep 2026, 869,279 rows), grouped by tariff
code, export status and end month.
- Tariff: each code's 2026-27 rate (Ofgem CPI-adjusted tariff table), matched once per code by
  technology, PV type, energy-efficiency rate, capacity band and the code's median eligibility date.
- Eligibility date: the later of application and commissioning date (Ofgem glossary: the date FIT
  payments commence). End: 20 years; PV eligible before 1 Aug 2012 25 years; micro-CHP 10 years
  (SY15 report para 2.2); installations migrated from the RO 31 Mar 2027 (17 years, para 2.17); none
  after 31 Mar 2042 (para 7.1).
- Output: DESNZ load factor by technology (DUKES 6.3, 2023-25 mean: solar PV, onshore wind, small
  hydro, anaerobic digestion), scaled by one factor so the installations active in SY15 generate
  Ofgem's 7.97 TWh (para 3.6). Decline with age by point 17 from 2024.
- Export: Ofgem's 1.47 TWh exported in SY15 as one share of exporting installations' output, paid at
  the export tariff for the eligibility date (Ofgem table, 2026-27: 5.43p before 1 Aug 2012 PV /
  1 Dec 2012 non-PV, 7.64p after).
- Prices: 2026-27 tariffs as published; each later scheme year (from 1 April) indexed by CPI of the
  previous calendar year (indexation moved from RPI to CPI from April 2026); 2025-26 is 2026-27 less
  the 3.4% CPI uplift. A calendar year is 1/4 of the scheme year before and 3/4 of its own.
- Qualifying costs: £17.5m (SY15), CPI-indexed, in proportion to the installations still paid.
- Micro-CHP (64 installations, 0.1 MW) is left out: DUKES gives it no load factor; all end by 2029.
"""
from functools import cache
from pathlib import Path

import numpy as np
import pandas as pd

from .output import decline_for
from .prices import cpi, cpih

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
PARTS = [f"ofgem/Feed-in-Tariff-Installation-Report-Part-{i}-092026.xlsx" for i in (1, 2, 3)]
RATES = "ofgem/fit_rates_cpi_update_26_27.xlsx"
SY15_TWH, SY15_EXPORT_TWH = 7.97, 1.47
SY15_GENERATION, SY15_EXPORT, SY15_QUALIFYING = 1_732_082_151, 94_088_277, 17_538_180  # Figs 3.5, 3.6
CPI_UPLIFT_2026 = 0.034  # Ofgem tariff table, Introduction: "adjusted by the annual CPI rate of 3.4 percent"
LAST_DAY = pd.Timestamp("2042-03-31")
RO_MIGRATED_END = pd.Timestamp("2027-03-31")
EXPORT_RATE = {"early": 5.43, "late": 7.64}  # p/kWh, 2026-27
DUKES_ROW = {"Photovoltaic": "Solar photovoltaics", "Wind": "Onshore", "Hydro": "Small scale",
             "Anaerobic digestion": "Anaerobic digestion"}
TECH_FOR_DECLINE = {"Photovoltaic": "Solar PV", "Wind": "Onshore Wind"}  # others flat (point 17)


@cache
def installations() -> pd.DataFrame:
    d = pd.concat([pd.read_excel(RAW / p, header=4, engine="calamine") for p in PARTS], ignore_index=True)
    d.columns = [c.strip() for c in d.columns]
    d = d.rename(columns={"Installed capacity": "kw", "TariffCode": "code", "Technology": "technology"})
    d["code"] = d.code.astype(str).str.strip()
    for c in ("Application date", "Commissioning date"):
        d[c] = pd.to_datetime(d[c], dayfirst=True, errors="coerce", format="mixed")
    d["eligible"] = d[["Application date", "Commissioning date"]].max(axis=1)
    d["exports"] = ~d["Export status"].astype(str).str.startswith("No Export")
    return d[["code", "technology", "kw", "eligible", "exports"]]


@cache
def rate_table() -> pd.DataFrame:
    x = pd.ExcelFile(RAW / RATES, engine="calamine")
    sheets = [s for s in x.sheet_names if s.startswith("April ")]
    r = pd.concat([pd.read_excel(x, sheet_name=s) for s in sheets], ignore_index=True)
    r.columns = [" ".join(c.split()) for c in r.columns]
    r = r.rename(columns={"Technology Type": "technology", "Solar PV Installation Type": "pv_type",
                          "Minimum Capacity (kW)": "lo", "Maximum Capacity (kW)": "hi",
                          "Energy Efficiency Requirement rating": "eff", "Tariff": "rate",
                          "Tariff Start Date": "start", "Tariff End Date": "end"})
    r["start"], r["end"] = pd.to_datetime(r.start), pd.to_datetime(r.end.astype(str).str.replace("9999", "2262"))
    return r


def _ro_migrated_rate() -> float:
    m = pd.read_excel(RAW / RATES, sheet_name="RO Migrated ", engine="calamine")
    return float(m.Tariff.iloc[0])


def _pv_type(code: str) -> str | None:
    if code.startswith("PV-R/"):
        return "Retrofit"
    if code.startswith("PV-N/"):
        return "New Build"
    if code.startswith(("PV/SA/", "PV/ST/")):
        return "Standalone"
    return "Standard" if code.startswith("PV/") else None


def _eff(code: str) -> str | None:
    tail = code.split("/")[-1]
    for letter, name in (("H", "Higher"), ("M", "Middle"), ("L", "Lower")):
        if letter in tail[2:4]:
            return name
    return None


@cache
def code_rates() -> pd.DataFrame:
    """One 2026-27 rate per tariff code, and the share of the code's installations whose eligibility
    date falls inside the matched tariff's dates (a check on the match)."""
    d, r = installations(), rate_table()
    out = []
    for code, g in d.groupby("code"):
        tech = g.technology.iloc[0]
        if "EXGEN" in code:
            out.append(dict(code=code, rate=_ro_migrated_rate(), inside=1.0, matched="RO migrated"))
            continue
        cand = r[(r.technology == tech) & (r.lo <= g.kw.median()) & (g.kw.median() <= r.hi)]
        pv = _pv_type(code)
        if pv:
            cand = cand[cand.pv_type == pv]
        eff = _eff(code)
        if eff and cand.eff.notna().any():
            cand = cand[cand.eff == eff]
        elif cand.eff.notna().any():
            cand = cand[cand.eff.isna() | (cand.eff == "Higher")]
        day = g.eligible.median()
        hit = cand[(cand.start <= day) & (day <= cand.end)]
        if hit.empty:  # e.g. a date after the code's own tariff period: nearest tariff period before it
            hit = cand[cand.start <= day].sort_values("start").tail(1)
        if hit.empty:  # band or rate letter not in the table for that date: any band of the PV type
            loose = r[(r.technology == tech) & ((r.pv_type == pv) if pv else True)]
            hit = loose[(loose.start <= day) & (day <= loose.end)]
            hit = hit[hit.eff == eff] if eff and (hit.eff == eff).any() else hit
            hit = hit.iloc[(hit.lo - g.kw.median()).abs().argsort()[:1]] if len(hit) else hit
        if hit.empty:
            raise ValueError(f"FiT tariff code {code}: no tariff matched")
        h = hit.iloc[0]
        inside = float(((g.eligible >= h.start) & (g.eligible <= h.end)).mean())
        out.append(dict(code=code, rate=float(h.rate), inside=inside, matched=f"{h.start.date()}..{h.end.date()}"))
    return pd.DataFrame(out).set_index("code")


def end_of(code: str, technology: str, eligible: pd.Timestamp) -> pd.Timestamp:
    if "EXGEN" in code:
        return RO_MIGRATED_END
    if technology == "Micro CHP":
        years = 10
    elif technology == "Photovoltaic" and eligible < pd.Timestamp("2012-08-01"):
        years = 25
    else:
        years = 20
    return min(eligible + pd.DateOffset(years=years) - pd.Timedelta(days=1), LAST_DAY)


@cache
def load_factors() -> dict[str, float]:
    t = pd.read_excel(RAW / "desnz" / "DUKES_6.3.xlsx", sheet_name="6.3", header=None, engine="calamine")
    head = t.iloc[4]
    cols = [c for c in t.columns if str(head[c])[:4] in ("2023", "2024", "2025")]
    rows = {str(t.iloc[i, 0]).strip(): t.iloc[i, cols].astype(float).mean() / 100 for i in range(5, 21)}
    return {tech: rows[name] for tech, name in DUKES_ROW.items()}


@cache
def groups() -> pd.DataFrame:
    d = installations()
    d = d[d.technology != "Micro CHP"].copy()
    d["end"] = [end_of(c, t, e) for c, t, e in zip(d.code, d.technology, d.eligible)]
    late = np.where(d.technology == "Photovoltaic", d.eligible >= pd.Timestamp("2012-08-01"),
                    d.eligible >= pd.Timestamp("2012-12-01"))
    d["export_rate"] = np.where(late, EXPORT_RATE["late"], EXPORT_RATE["early"])
    d["end_month"] = d.end.dt.to_period("M")
    g = (d.groupby(["code", "technology", "exports", "export_rate", "end_month"])
         .agg(n=("kw", "size"), kw=("kw", "sum"), first_eligible=("eligible", "min"), end=("end", "max"))
         .reset_index())
    g = g.join(code_rates().rate, on="code")
    lf = load_factors()
    g["kwh_per_kw_raw"] = g.technology.map(lf) * 8760
    active = (g.first_eligible <= pd.Timestamp("2025-03-31")) & (g.end >= pd.Timestamp("2024-04-01"))
    scale = SY15_TWH * 1e9 / (g.kw * g.kwh_per_kw_raw)[active].sum()
    g["kwh_per_kw"] = g.kwh_per_kw_raw * scale
    exp_gen = (g.kw * g.kwh_per_kw)[active & g.exports].sum()
    g["export_share"] = np.where(g.exports, SY15_EXPORT_TWH * 1e9 / exp_gen, 0.0)
    g.attrs.update(scale=scale, export_share=SY15_EXPORT_TWH * 1e9 / exp_gen)
    g["group"] = g.code + "|" + np.where(g.exports, "export", "no export") + "|" + g.end_month.astype(str)
    return g


def index_cash(scheme_year: int) -> float:
    """Tariff in the scheme year starting 1 April `scheme_year`, as a multiple of its 2026-27 rate."""
    if scheme_year <= 2025:
        return 1 / (1 + CPI_UPLIFT_2026)
    return cpi(scheme_year - 1) / cpi(2025)


def calendar_index(year: int) -> float:
    return 0.25 * index_cash(year - 1) + 0.75 * index_cash(year)


def share_of_year(year: int, end: pd.Timestamp) -> float:
    y0, y1 = pd.Timestamp(f"{year}-01-01"), pd.Timestamp(f"{year + 1}-01-01")
    return max(0.0, (min(y1, end + pd.Timedelta(days=1)) - y0).days) / (y1 - y0).days


def build(s=None, first: int = 2026, last: int = 2042):
    """The FiT scheme-line adapter: one row per group-year (design: Scheme line)."""
    from .model import Line
    from .scenario import Scenario
    s = s or Scenario()
    g = groups()
    n_sy15 = g.loc[(g.first_eligible <= pd.Timestamp("2025-03-31")) & (g.end >= pd.Timestamp("2024-04-01")), "n"].sum()
    rows = []
    for r in g.itertuples(index=False):
        dec = decline_for(TECH_FOR_DECLINE.get(r.technology, r.technology), s.wind_decline, s.solar_decline)
        for y in range(first, last + 1):
            f = share_of_year(y, r.end)
            if f == 0:
                continue
            kwh = r.kw * r.kwh_per_kw * (1 - dec) ** (y - 2024) * f
            idx = calendar_index(y)
            gen_pay = kwh * r.rate / 100 * idx
            exp_pay = kwh * r.export_share * r.export_rate / 100 * idx
            qual = SY15_QUALIFYING * (r.n / n_sy15) * f * cpi(y) / cpi(2024)
            rows.append(dict(group=r.group, code=r.code, technology=r.technology, year=y, kwh=kwh,
                             generation=gen_pay, export=exp_pay, qualifying=qual,
                             payment=(gen_pay + exp_pay + qual) / cpih(y)))
    out = pd.DataFrame(rows)
    tidy = out.rename(columns={"group": "item", "payment": "cash"}).assign(line="FiT", built=True)
    return Line(tidy[["line", "item", "technology", "built", "year", "cash"]],
                {"fit_groups": g.assign(end_month=g.end_month.astype(str)), "fit_group_years": out,
                 "fit_code_rates": code_rates().reset_index()})
