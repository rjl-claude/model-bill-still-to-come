"""One call (design: `run`): every scheme line, every year from the valuation date, one tidy table back.

    results = run(Scenario())                  # central
    results = run(Scenario(case="FFP_High"))   # one bracket

Each scheme line is an adapter at one seam: `build(scenario) -> Line(rows, tables)`, where `rows` has
line, item, technology, built, year, cash (£, 2024 CPIH prices) and `tables` are its in-between tables
(contracts, output, discounts ...), kept for open data (paper ch. 11). A new scheme is one more adapter
in LINES; nothing after it changes.
"""
import datetime as dt
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, NamedTuple

import pandas as pd

from .scenario import Scenario

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "data" / "raw" / "MANIFEST.jsonl"
VALUATION_DATE = dt.date(2026, 1, 1)  # point 4
REGISTER = "lccc/cfd_contract_portfolio_status.csv"  # its download day is the cut-off date (point 15)
COLUMNS = ["line", "item", "technology", "built", "payer", "year", "cash"]


class Line(NamedTuple):
    rows: pd.DataFrame
    tables: dict[str, pd.DataFrame]


@dataclass
class Results:
    table: pd.DataFrame
    scenario: Scenario
    tables: dict[str, pd.DataFrame] = field(default_factory=dict)
    valuation_date: dt.date = VALUATION_DATE
    cut_off_date: dt.date | None = None
    manifest_sha256: str = ""

    def save(self, folder: Path) -> None:
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        self.table.to_csv(folder / "results.csv", index=False)
        for name, t in self.tables.items():
            t.to_csv(folder / f"{name}.csv", index=False)
        (folder / "run.json").write_text(json.dumps(dict(
            scenario=repr(self.scenario), valuation_date=self.valuation_date.isoformat(),
            cut_off_date=self.cut_off_date.isoformat() if self.cut_off_date else None,
            manifest_sha256=self.manifest_sha256), indent=1))


def _cut_off() -> dt.date:
    days = [json.loads(line)["fetched"][:10] for line in MANIFEST.read_text().splitlines()
            if json.loads(line)["file"] == REGISTER]
    return dt.date.fromisoformat(max(days))


def _lines() -> tuple[Callable[[Scenario], Line], ...]:
    from . import cfd_line, ro
    return (cfd_line.build, ro.build)


def run(scenario: Scenario | None = None, lines: tuple[Callable[[Scenario], Line], ...] | None = None) -> Results:
    s = scenario or Scenario()
    rows, tables = [], {"prices": pd.DataFrame(sorted(s.price_path().items()), columns=["year", "price_2024"])}
    for build in lines or _lines():
        ln = build(s)
        r = ln.rows.copy()
        if "payer" not in r:
            r["payer"] = "all"  # split by who pays in stage 4
        rows.append(r[COLUMNS])
        tables.update(ln.tables)
    table = pd.concat(rows, ignore_index=True)
    table = table[table.year >= VALUATION_DATE.year].reset_index(drop=True)
    return Results(table=table, scenario=s, tables=tables, cut_off_date=_cut_off(),
                   manifest_sha256=hashlib.sha256(MANIFEST.read_bytes()).hexdigest())
