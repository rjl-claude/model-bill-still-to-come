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
# The unit of each kind of key 1.0.1 added (a regex on the key); every other key is in UNITS
KEY_UNITS = {
    "default": UNITS,
    r"price_path\.(low|reference|high)\.\d{4}": "£/MWh, 2024 prices (CPIH)",
    r"[a-z_]+\.(built\.|not_yet_built\.)?contracts": "number (FiT: installations)",
    r"check(\.[a-z0-9_]+){3}\.(model|reference)": "£ cash; the Clock join in 2024 prices",
    r"check(\.[a-z0-9_]+){3}\.(gap|ratio)": "gap: model / reference - 1; ratio: model / reference",
    r"check\.obr\.cfd\.\d{4}\.matching_price": "£/MWh, 2024 prices (CPIH)",
    r"check\.obr\.cfd\.\d{4}\.not_yet_built_share": "share of the model's CfD that year (0 to 1)",
    r"check\.lccc(\.[a-z0-9_]+){2}\.at_forward_price\.ratio": "model / LCCC, 2026-27 at LCCC's winter price",
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


PRICE_CASES = {"low": "FFP_Low", "reference": "Reference", "high": "FFP_High"}


def price_path_keys() -> dict[str, float]:
    """`price_path.<low|reference|high>.<year>`: DESNZ Annex M baseload, £/MWh in 2024 prices (CPIH),
    2024 to 2050 (later years take 2050's), for each fossil-price case (version 1.0.1, aios-harness#221)."""
    from .prices import annex_m_path
    return {f"price_path.{name}.{y}": float(p) for name, case in PRICE_CASES.items()
            for y, p in annex_m_path(case).items()}


def contract_keys(results) -> dict[str, int]:
    """`<line>.contracts`, `<line>.built.contracts`, `<line>.not_yet_built.contracts`: how many contracts,
    accreditations and agreements pay from the valuation date, by line (version 1.0.1, aios-harness#221).
    The FiT line counts installations (its tariff groups' `n`); VAT and the rows moving cost between
    payers are not contracts."""
    from .who_pays import MOVES
    t = results.table
    t = t[~t.item.isin(MOVES) & (t.line != "VAT")]
    fit_n = results.tables["fit_groups"].set_index("group").n if "fit_groups" in results.tables else None
    out: dict[str, int] = {}
    for (line, built), g in t.groupby(["line", "built"]):
        key = LINE_KEYS[line]
        items = g.item.unique()
        n = int(fit_n.reindex(items).sum()) if key == "fit" and fit_n is not None else len(items)
        out[f"{key}.{BUILT[built]}.contracts"] = n
        out[f"{key}.contracts"] = out.get(f"{key}.contracts", 0) + n
    return out


def check_keys(results) -> dict[str, float]:
    """`check.<check>.<line>.<period>.<model|reference|gap|ratio>` for each row of `checks.check(results)`:
    model and reference in £ cash (OBR, LCCC, Budget) or 2024 prices (Clock join); gap = model / reference - 1;
    ratio = model / reference; and the figures the written explanations print (`checks.notes`)
    (version 1.0.1, aios-harness#221)."""
    from .checks import check, notes
    out: dict[str, float] = notes(results)
    for r in check(results).rows.itertuples():
        k = f"check.{slug(r.check)}.{slug(r.line)}.{slug(r.period)}"
        out |= {f"{k}.model": float(r.model), f"{k}.reference": float(r.reference),
                f"{k}.gap": float(r.gap), f"{k}.ratio": float(r.model / r.reference)}
    return out


def write(results, path: Path, tornado: pd.DataFrame | None = None, checks: bool = False) -> None:
    """The results file. With `tornado` (from `brackets.tornado()`), its bracket and range keys too; with
    `checks`, the check keys (`check_keys`), as the frozen release writes them."""
    meta = dict(model="model-bill-still-to-come", version=version("billtocome"),
                units=UNITS, key_units=KEY_UNITS, scenario=repr(results.scenario), valuation_date=results.valuation_date.isoformat(),
                cut_off_date=results.cut_off_date.isoformat() if results.cut_off_date else None,
                manifest_sha256=results.manifest_sha256)
    figs = build(results) | price_path_keys() | contract_keys(results) | (bracket_keys(tornado) if tornado is not None else {}) \
        | (check_keys(results) if checks else {})
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
