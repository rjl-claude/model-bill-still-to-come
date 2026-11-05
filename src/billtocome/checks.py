"""The checks (design: Checks; build plan checks 2-4, point 14): `check(results) -> Report`.

Each line in each year against the Clock (the join), the OBR (calendarised) and LCCC. A gap over 15%
fails unless `explanations.yaml` holds an entry for that check, line and period. Worked by hand in
docs/hand-example-checks.md.
"""
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import pandas as pd
import yaml

from .prices import cpih

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
CLOCK = Path("/srv/aios/projects/web-subsidy-clock/site/data")  # the released Clock's data files
MARGIN = 0.15
GROUPS = {"CfD": ("CfD renewables", "Hinkley Point C", "Biomass bridging"), "RO": ("RO",), "FiT": ("FiT",),
          "Capacity Market": ("Capacity Market",)}
# The OBR forecasts no FiT after 2025-26 (Table 4.20 shows 0), so FiT has no OBR check. The Capacity
# Market is checked as the whole levy, before net zero's share (point 9).
OBR_ROWS = {"CfD": "Contracts for difference", "RO": "Renewables obligation",
            "Capacity Market (whole levy)": "Capacity market1"}
# Table 4.20 note 1: the ONS's outturn leaves the Capacity Market out; "If they were included, they would
# have been £1.6 billion [...] in 2025-26."
OBR_OVERRIDE = {"Capacity Market (whole levy)": {2025: 1.6e9}}
CLOCK_FILES = {"CfD": "cfd.csv", "RO": "renewables-obligation.csv", "FiT": "feed-in-tariffs.csv",
               "Capacity Market": "capacity-market.csv"}
OBR_YEARS = range(2026, 2032)  # 2031 needs 2031-32, the OBR's last year


@dataclass
class Report:
    rows: pd.DataFrame

    @property
    def passed(self) -> bool:
        return bool(self.rows.ok.all())


def load_explanations(path: Path = ROOT / "explanations.yaml") -> list[dict]:
    return yaml.safe_load(path.read_text()) or []


def calendarise(fy: dict[int, float], year: int) -> float:
    """Calendar `year` from financial years keyed by their starting year (point 4)."""
    return 0.25 * fy[year - 1] + 0.75 * fy[year]


@cache
def _obr_fy(row: str) -> dict[int, float]:
    d = pd.read_excel(RAW / "obr" / "october-2026-efo-detailed-forecast-tables-receipts.xlsx",
                      sheet_name="4.20", header=None)
    head = d.iloc[4]
    r = d[d[1].astype(str).str.strip() == row].iloc[0]
    return {int(str(head[c])[:4]): float(r[c]) * 1e9 for c in d.columns if str(head[c])[:4].isdigit()}


def obr(group: str) -> dict[int, float]:
    """OBR October 2026 Table 4.20, calendarised, £ cash."""
    fy = {**_obr_fy(OBR_ROWS[group]), **OBR_OVERRIDE.get(group, {})}
    return {y: calendarise(fy, y) for y in OBR_YEARS}


def _clock(group: str) -> tuple[int, float]:
    c = pd.read_csv(CLOCK / CLOCK_FILES[group], comment="#")
    last = c[c.year <= 2025].iloc[-1]  # the Clock's last measured year (2026 on is its carry-forward)
    return int(last.year), float(last.cost_real)


def _lccc() -> float:
    return float(pd.read_csv(RAW / "lccc" / "forecast_cfd_payments.csv").Forecast_CFD_Payments_GBP.sum())


def check(results, explanations: list[dict] | None = None) -> Report:
    ex = load_explanations() if explanations is None else explanations
    known = {(e["check"], e["line"], e["period"]) for e in ex}
    t = results.table
    real = {g: t[t.line.isin(lines)].groupby("year").cash.sum() for g, lines in GROUPS.items()}
    if "cm_agreement_years" in results.tables:
        real["Capacity Market (whole levy)"] = results.tables["cm_agreement_years"].groupby("year").whole_real.sum()
    rows = []

    def add(name, line, period, model, ref):
        gap = model / ref - 1 if ref else float("inf")
        explained = (name, line, period) in known
        rows.append(dict(check=name, line=line, period=period, model=model, reference=ref, gap=gap,
                         explained=explained, ok=abs(gap) <= MARGIN or explained))

    first = int(t.year.min())
    for g in GROUPS:
        if not real[g].sum():
            continue  # a line this run does not have
        y, c = _clock(g)
        add("Clock join", g, f"{first} vs {y}", float(real[g].get(first, 0.0)), c)
    for g in OBR_ROWS:
        if g in real and real[g].sum():
            for yr, ref in obr(g).items():
                add("OBR", g, str(yr), float(real[g].get(yr, 0.0)) * cpih(yr), ref)
    r = t[t.line == "CfD renewables"].groupby("year").cash.sum()
    add("LCCC", "CfD renewables", "2026-10 to 2027-03",
        0.25 * (r.get(2026, 0.0) * cpih(2026) + r.get(2027, 0.0) * cpih(2027)), _lccc())
    return Report(pd.DataFrame(rows))
