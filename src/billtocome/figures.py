"""The one results file the paper reads by key (aios-harness#84; build plan: "Every printed figure is read
from one results file by key: no typed numbers").

Keys are built from the results table, not a fixed list: `line[.built][.payer].period.measure`, where
- line: a scheme line (`LINE_KEYS`) or `bill`, every line together;
- built: `built` or `not_yet_built` (left out: both);
- payer: `households`, `businesses` or `taxpayers` (left out: all);
- period: a calendar year or `total` (2026 to the last year);
- measure: `cash` (£, 2024 prices), `pv_green_book`, `pv_hurdle` (present value to 1 Jan 2026).
Every combination with rows in the table has a key. E.g. `bill.total.cash`,
`cfd_renewables.not_yet_built.total.pv_hurdle`, `bill.households.2030.cash`.

`build(results) -> {key: £}`; `Results.save` writes it as `figures.json` with the run's dates and
MANIFEST hash; `figure(key)` reads it. The paper's source writes `{{key}}`; `render` fills each in,
and `typed` lists any money or percentage figure typed outside a key.
"""
import json
import re
from importlib.metadata import version
from itertools import product
from pathlib import Path

import pandas as pd

from .present_value import present_value

ROOT = Path(__file__).resolve().parents[2]
FILE = ROOT / "results" / "figures.json"
UNITS = "£, 2024 prices (CPIH); present values real, to 1 Jan 2026"
LINE_KEYS = {
    "CfD renewables": "cfd_renewables", "Hinkley Point C": "hinkley_point_c", "Biomass bridging": "biomass_bridging",
    "RO": "ro", "FiT": "fit", "Capacity Market": "capacity_market", "Sizewell C": "sizewell_c", "VAT": "vat",
}
BUILT = {True: "built", False: "not_yet_built"}
MEASURES = {"cash": None, "pv_green_book": "green_book", "pv_hurdle": "hurdle"}


def build(results) -> dict[str, float]:
    t = results.table.copy()
    for m, rate in MEASURES.items():
        if rate:
            t[m] = present_value(results, rate).pv
    t["line_key"] = t.line.map(LINE_KEYS)
    if t.line_key.isna().any():
        raise KeyError(f"lines with no key: {sorted(set(t.line[t.line_key.isna()]))}")
    t["built_key"] = t.built.map(BUILT)
    out: dict[str, float] = {}
    for line, built, payer in product((None, "line_key"), (None, "built_key"), (None, "payer")):
        dims = [d for d in (line, built, payer) if d]
        groups = t.groupby(dims) if dims else [((), t)]
        for k, g in groups:
            k = k if isinstance(k, tuple) else (k,)
            head = ([] if line else ["bill"]) + list(k)
            sums = g.groupby("year")[list(MEASURES)].sum()
            for m in MEASURES:
                out[".".join(head + ["total", m])] = float(sums[m].sum())
                for y, v in sums[m].items():
                    out[".".join(head + [str(y), m])] = float(v)
    return out


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower().replace("'", "")).strip("_")


def bracket_keys(tornado: pd.DataFrame) -> dict[str, float]:
    """`bracket.<name>.<low|high|swing|rank>.<measure>` and `range.<low|high>.<measure>` from `brackets.tornado()`.
    Low and high are the bill at each end of the bracket's input; rank is by swing in cash."""
    from .brackets import MEASURES, range_of
    out: dict[str, float] = {}
    for i, r in tornado.reset_index(drop=True).iterrows():
        for m in MEASURES:
            sfx = "" if m == "cash" else f"_{m}"
            for end, col in (("low", "low_bill"), ("high", "high_bill"), ("swing", "swing")):
                out[f"bracket.{slug(r.bracket)}.{end}.{m}"] = float(r[col + sfx])
        out[f"bracket.{slug(r.bracket)}.rank.cash"] = i + 1
    for m in MEASURES:
        out[f"range.low.{m}"], out[f"range.high.{m}"] = range_of(tornado, m)
    return out


def write(results, path: Path, tornado: pd.DataFrame | None = None) -> None:
    """The results file. With `tornado` (from `brackets.tornado()`), its bracket and range keys too."""
    meta = dict(model="model-bill-still-to-come", version=version("billtocome"),
                units=UNITS, scenario=repr(results.scenario), valuation_date=results.valuation_date.isoformat(),
                cut_off_date=results.cut_off_date.isoformat() if results.cut_off_date else None,
                manifest_sha256=results.manifest_sha256)
    figs = build(results) | (bracket_keys(tornado) if tornado is not None else {})
    Path(path).write_text(json.dumps(dict(meta=meta, figures=figs), indent=0, sort_keys=True))


def figure(key: str, path: Path = FILE) -> float:
    return json.loads(Path(path).read_text())["figures"][key]


def fmt(v: float) -> str:
    sign, a = ("-" if v < 0 else ""), abs(v)
    return f"{sign}£{a / 1e9:.1f}bn" if a >= 1e9 else f"{sign}£{a / 1e6:.1f}m"


KEY = re.compile(r"\{\{\s*([a-z0-9_.]+)\s*\}\}")
FIGURE = re.compile(r"£\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:bn|m|k|billion|million)\b)?"
                    r"|\d[\d,]*(?:\.\d+)?\s?(?:%|per ?cent\b|bn\b|billion\b|million\b)")


def render(text: str, figs: dict[str, float]) -> str:
    return KEY.sub(lambda m: fmt(figs[m.group(1)]), text)


def typed(text: str) -> list[str]:
    """Money and percentage figures typed in `text` outside a `{{key}}`."""
    return [m.group(0).strip() for m in FIGURE.finditer(KEY.sub("", text))]
