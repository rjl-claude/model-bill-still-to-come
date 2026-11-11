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
    # 1.2.2 (aios-harness#235)
    r"discount\.(green_book\.years_\d+_\d+|hurdle\.[a-z_]+)": "discount rate a year, real (0 to 1)",
    r"sizewell_c\.allowed_return\.[a-z0-9_]+": "allowed return a year on the asset base, real CPIH (0 to 1)",
    r"bracket\.(annex_m_prices|build_path|decline_with_age|discount_slope|forward_prices_then_annex_m|hinkley_term"
    r"|households_share|negative_hours_slope|output_level|unbuilt_abandoned|unbuilt_start_late)\.setting\.(low|central|high)":
        "the bracket's input at that end, in words",
    r"bracket\.hinkley_strike\.setting\.(low|central|high)": "£/MWh, 2012 prices",
    r"bracket\.hinkley_start\.setting\.(low|central|high)": "years from the expected start",
    r"bracket\.sizewell_c_build_cost\.setting\.(low|central|high)": "£, real CPIH 2024/25, with the Day-1 RAB (licence SC28)",
    r"bracket\.sizewell_c_return_after_2039\.setting\.(low|central|high)": "allowed return a year, real CPIH (0 to 1)",
    r"bracket\.capacity_market_share\.setting\.(low|central|high)": "net zero's share of the Capacity Market (0 to 1)",
    r"bracket\.ro_recycle_value\.setting\.(low|central|high)": "recycle value, share of the buy-out price (0 to 1)",
    r"[a-z_]+\.last_year": "calendar year",
    r"[a-z_]+\.negative_years\.cash": "£, 2024 prices (CPIH), summed over the years in .years",
    r"[a-z_]+\.negative_years\.years": "calendar years, as words",
    r"bill\.without_nuclear\.total\.cash": "£, 2024 prices (CPIH)",
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


# A technology the model holds for each commercial-rate key (version 1.2.2, aios-harness#235)
HURDLE_TECHNOLOGIES = {
    "solar": "Solar PV", "onshore_wind": "Onshore Wind", "offshore_wind_fixed": "Offshore Wind",
    "offshore_wind_floating": "Floating Offshore Wind", "tidal": "Tidal Stream", "geothermal": "Geothermal",
    "hydro": "Hydro", "small_wind": "Wind with a DNC of 50kW or less", "nuclear": "Nuclear",
    "other_firm": "Combined Cycle Gas Turbine (CCGT)",
}


def rate_keys() -> dict[str, float]:
    """`discount.green_book.years_<a>_<b>`, `discount.hurdle.<technology>` and Sizewell C's allowed return,
    `sizewell_c.allowed_return.<central|low_after_2039>`: the rates the model holds (version 1.2.2, aios-harness#235)."""
    from .present_value import GREEN_BOOK, hurdle_rate
    from .scenario import BRACKETS
    from .szc import IWACC
    out, start = {}, 0
    for end, rate in GREEN_BOOK:
        out[f"discount.green_book.years_{start + 1}_{end}"] = rate
        start = end
    out |= {f"discount.hurdle.{k}": hurdle_rate(t) for k, t in HURDLE_TECHNOLOGIES.items()}
    szc = next(b for b in BRACKETS if b.name == "Sizewell C return after 2039")
    out |= {"sizewell_c.allowed_return.central": IWACC, "sizewell_c.allowed_return.low_after_2039": szc.low.szc_ops_return}
    return out


# Words for a bracket input that is not a number the reader can use: (input, setting) -> label
# (version 1.2.2, aios-harness#235). The words follow the model's own notes on each input (scenario.py and the
# modules it names); every other input is printed as the number the Scenario holds.
SETTING_WORDS = {
    ("case", "FFP_Low"): "DESNZ's low price path", ("case", "Reference"): "DESNZ's central price path",
    ("case", "FFP_High"): "DESNZ's high price path",
    ("prices", None): "DESNZ's central price path",
    ("prices", "forward"): "season-ahead prices to March 2027, then DESNZ's central price path",
    **{(b, v): w for b in ("discount_bound", "negative_bound") for v, w in
       ((-1, "low end of the 95% interval"), (0, "central fit"), (1, "high end of the 95% interval"))},
    ("path", "Falling Behind"): "NESO FES 2025 Falling Behind", ("path", "EEP"): "DESNZ's EEP build path",
    ("path", "Holistic Transition"): "NESO FES 2025 Holistic Transition",
    ("abandonment", False): "every unbuilt contract built",
    ("abandonment", True): "unbuilt renewables cut by their technology's termination rate",
    ("late_starts", False): "LCCC's expected start dates",
    ("late_starts", True): "unbuilt contracts start late by their round's measured delay",
    ("hpc_term", "contract"): "35 years from the earlier of start and the window's end",
    ("hpc_term", "from_start"): "35 years from start",
    ("households", "held"): "households' 2025 share held", ("households", "EEP"): "DESNZ's projected share",
    ("decline", "gentler"): "gentler decline", ("decline", "central"): "central decline",
    ("decline", "steeper"): "steeper decline",
    ("output", "measured"): "each farm's own record", ("output", "DESNZ 2023"): "DESNZ 2023 load factors",
}


def _setting(s, name: str):
    if name in ("path", "discount_bound", "negative_bound"):
        v = getattr(s.market, name)
    else:
        v = getattr(s, name)
    if name == "prices" and v is not None:
        v = "forward"
    return SETTING_WORDS.get((name, v), v)


def setting_keys() -> dict:
    """`bracket.<name>.setting.<low|central|high>`: the input each bracket moves, at each end and central; a number
    where the Scenario holds one, else words (`SETTING_WORDS`). A one-sided bracket's other end is central."""
    from dataclasses import fields

    from .scenario import BRACKETS, Scenario
    c, out = Scenario(), {}
    for b in BRACKETS:
        names = [f.name for f in fields(Scenario) if getattr(b.low, f.name) != getattr(b.high, f.name)]
        if names == ["market"]:
            names = [n for n in ("path", "discount_bound", "negative_bound") if getattr(b.low.market, n) != getattr(b.high.market, n)]
        (name,) = names
        for end, s in (("low", b.low), ("central", c), ("high", b.high)):
            out[f"bracket.{slug(b.name)}.setting.{end}"] = _setting(s, name)
    return out


def line_year_keys(results) -> dict:
    """`<line>.last_year`: the last calendar year each line pays (a non-zero year's cash) (version 1.2.2,
    aios-harness#235)."""
    t = results.table
    by = t.groupby([t.line.map(LINE_KEYS), "year"]).cash.sum()
    by = by[by != 0]
    return {f"{line}.last_year": int(g.index.get_level_values("year").max()) for line, g in by.groupby(level=0)}


def _spans(years: list[int]) -> str:
    """[2042, 2045, 2046, 2047] -> "2042, 2045-2047"."""
    spans: list[list[int]] = []
    for y in years:
        if spans and y == spans[-1][1] + 1:
            spans[-1][1] = y
        else:
            spans.append([y, y])
    return ", ".join(str(a) if a == b else f"{a}-{b}" for a, b in spans)


def negative_year_keys(figs: dict) -> dict:
    """`<line|bill>.negative_years.cash` and `.years`: the sum of the years in which a line, or the whole bill, pays
    back (its year's cash below zero), read from its year keys, and those years; only where there are any
    (version 1.2.2, aios-harness#235)."""
    year = re.compile(r"([a-z_]+)\.(\d{4})\.cash")
    by: dict[str, dict[int, float]] = {}
    for k, v in figs.items():
        m = year.fullmatch(k)
        if m and v < 0:
            by.setdefault(m[1], {})[int(m[2])] = v
    out: dict = {}
    for head, ys in by.items():
        years = sorted(ys)
        out[f"{head}.negative_years.cash"] = sum(ys[y] for y in years)
        out[f"{head}.negative_years.years"] = _spans(years)
    return out


NUCLEAR = ("Hinkley Point C", "Sizewell C")


def without_nuclear_keys(results) -> dict[str, float]:
    """`bill.without_nuclear.total.cash`: the bill without Hinkley Point C and Sizewell C and the VAT on households'
    part of them, whose VAT rows name the line (`who_pays.split`) (version 1.2.2, aios-harness#235)."""
    t = results.table
    vat_on = t.item.str.split("|").str[0].where(t.line == "VAT")
    keep = ~t.line.isin(NUCLEAR) & ~vat_on.isin(NUCLEAR)
    return {"bill.without_nuclear.total.cash": float(t.cash[keep].sum())}


def write(results, path: Path, tornado: pd.DataFrame | None = None, checks: bool = False) -> None:
    """The results file. With `tornado` (from `brackets.tornado()`), its bracket and range keys too; with
    `checks`, the check keys (`check_keys`), as the frozen release writes them."""
    meta = dict(model="model-bill-still-to-come", version=version("billtocome"),
                units=UNITS, key_units=KEY_UNITS, scenario=repr(results.scenario), valuation_date=results.valuation_date.isoformat(),
                cut_off_date=results.cut_off_date.isoformat() if results.cut_off_date else None,
                manifest_sha256=results.manifest_sha256)
    figs = build(results) | price_path_keys() | contract_keys(results) | (bracket_keys(tornado) if tornado is not None else {}) \
        | (check_keys(results) if checks else {}) | rate_keys() | setting_keys() | line_year_keys(results) | without_nuclear_keys(results)
    figs |= negative_year_keys(figs)
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
