"""The checks (design: Checks; build plan checks 2-4, point 14): `check(results) -> Report`.

Each line in each year against the Clock (the join), the OBR (calendarised) and LCCC. A gap over 15%
fails unless `explanations.yaml` holds an entry for that check, line and period. Worked by hand in
docs/hand-example-checks.md.
"""
import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import pandas as pd
import yaml

from .prices import cpih

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
# the bill already paid: one day's results file of model-bill-already-paid (aios-harness#140), frozen at the
# freeze (aios-harness#91): the robot's file of 9 Nov 2026, saved in data/raw/ and recorded in MANIFEST
# (tools/fetch.py, pinned by commit; its fingerprint checked by tests/test_manifest.py and model-register.yaml)
CLOCK = RAW / "model-bill-already-paid" / "clock.json"
MARGIN = 0.15
GROUPS = {"CfD": ("CfD renewables", "Hinkley Point C", "Biomass bridging"), "RO": ("RO",), "FiT": ("FiT",),
          "Capacity Market": ("Capacity Market",), "Sizewell C": ("Sizewell C",)}
# The OBR forecasts no FiT after 2025-26 (Table 4.20 shows 0), so FiT has no OBR check. The Capacity
# Market is checked as the whole levy, before net zero's share (point 9).
OBR_ROWS = {"CfD": "Contracts for difference", "RO": "Renewables obligation",
            "Capacity Market (whole levy)": "Capacity market1", "Sizewell C": "Sizewell C RAB levy1"}
# Table 4.20 note 1: the ONS's outturn leaves the Capacity Market out; "If they were included, they would
# have been £1.6 billion and £0.5 billion respectively in 2025-26" (the second is Sizewell C's RAB levy).
# Sizewell C's levy began on 1 December 2025, so its £0.5bn is four months (December-March): an annual
# rate of £1.5bn, of which calendarise() then puts the January-March part (three quarters of £0.5bn) in 2026.
OBR_OVERRIDE = {"Capacity Market (whole levy)": {2025: 1.6e9}, "Sizewell C": {2025: 0.5e9 * 12 / 4}}
CLOCK_LINES = {"CfD": "cfd_renewable", "RO": "ro", "FiT": "fit", "Capacity Market": "capacity_market"}
OBR_YEARS = range(2026, 2032)
# Budget 2025 policy costings p.12 (fact 13): Exchequer cost of 75% of the RO's domestic share, £ cash, by
# financial year (keyed by its starting year)
BUDGET_EXCHEQUER_RO = {2025: 0.0, 2026: 2_580e6, 2027: 2_100e6, 2028: 2_195e6, 2029: 0.0}  # 2031 needs 2031-32, the OBR's last year


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


@cache
def _clock_lines() -> dict[str, list[dict]]:
    doc = json.loads(CLOCK.read_bytes())
    if doc["meta"]["model"] != "model-bill-already-paid":
        raise ValueError(f"{CLOCK} is not model-bill-already-paid's results file")
    return {s["scheme_id"]: s["annual"]["rows"] for s in doc["model"]["schemes"]}


def _clock(group: str) -> tuple[int, float]:
    rows = [r for r in _clock_lines()[CLOCK_LINES[group]] if r["year"] <= 2025]
    last = max(rows, key=lambda r: r["year"])  # the Clock's last measured year (2026 on is its carry-forward)
    # to the penny, as the Clock publishes it (its CSVs carry 2 dp)
    return int(last["year"]), round(float(last["cost_gbp_2024"]), 2)


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
        if not real[g].sum() or g not in CLOCK_LINES:
            continue  # a line this run does not have, or one the Clock does not count (Sizewell C)
        y, c = _clock(g)
        add("Clock join", g, f"{first} vs {y}", float(real[g].get(first, 0.0)), c)
    for g in OBR_ROWS:
        if g in real and real[g].sum():
            for yr, ref in obr(g).items():
                add("OBR", g, str(yr), float(real[g].get(yr, 0.0)) * cpih(yr), ref)
    x = t[t.item.str.startswith("Exchequer") & (t.payer == "taxpayers")].groupby("year").cash.sum()
    if x.sum():
        for yr in range(2026, 2030):
            add("Budget", "RO (Exchequer share)", str(yr), float(x.get(yr, 0.0)) * cpih(yr),
                calendarise(BUDGET_EXCHEQUER_RO, yr))
    r = t[t.line == "CfD renewables"].groupby("year").cash.sum()
    if r.sum():
        add("LCCC", "CfD renewables", "2026-10 to 2027-03",
            0.25 * (r.get(2026, 0.0) * cpih(2026) + r.get(2027, 0.0) * cpih(2027)), _lccc())
    return Report(pd.DataFrame(rows))
