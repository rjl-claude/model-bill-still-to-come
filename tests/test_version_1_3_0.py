"""aios-harness#243: version 1.3.0, Richard's rulings of 16 Nov 2026 (Report No. 2 rulings sheet, points 11 and 16).

11b: a case that does not hold the price of power after 2050 at its 2050 level. DESNZ's Annex M stops at 2050 and
the model holds 2050's price to 2099 (build plan point 3). Sizewell C's paybacks, 2072 to 2099, rest on that. The
new case puts every year from 2051 at the average of DESNZ's central path over 2026 to 2050 (ASSUMPTION, design.md
"Version 1.3.0"); it is the eighteenth bracket, "Price after 2050". 16b needs no
model change (Richard, 17 Nov 2026: no fair published basis for a Sizewell C return above 6.73% after 2039).

Tested at the seams the paper reads: the price path and the brackets the model declares, and the frozen results
file, by key, against the frozen 1.2.6 file."""
import hashlib
import json
import math

from billtocome import figures, prices

ROOT = figures.FILE.parent.parent
V126 = ROOT / "tests" / "fixtures" / "figures-1.2.6.json"  # results/figures.json at tag v1.2.6


def old() -> dict:
    return json.loads(V126.read_text())["figures"]


def test_the_fixture_is_the_frozen_1_2_6_file():
    assert hashlib.sha256(V126.read_bytes()).hexdigest() == \
        "92c1b5c106ff9fe136f49b3606185537fed95338e17c2e4386df37ff02272893"  # git show v1.2.6:results/figures.json


def test_after_2050_the_price_is_the_average_of_desnzs_central_path_over_2026_to_2050():
    """By the frozen 1.2.6 keys, not the code: DESNZ's central path to 2050 unchanged, then from 2051 to 2099 the
    mean of its 25 years 2026 to 2050."""
    o = old()
    mean = sum(o[f"price_path.reference.{y}"] for y in range(2026, 2051)) / 25
    assert 75.5 < mean < 75.7
    path = prices.path_average_after_2050()
    assert sorted(path) == list(range(2024, 2100))
    for y in range(2024, 2051):
        assert math.isclose(path[y], o[f"price_path.reference.{y}"], rel_tol=1e-10)
    for y in range(2051, 2100):
        assert math.isclose(path[y], mean, rel_tol=1e-10)


def test_the_price_after_2050_is_the_eighteenth_bracket_one_sided_towards_a_higher_bill():
    """Its low end is central (2050's price held); its high end the average path, the only input it moves. Lower
    prices raise the bill, so the case is the bracket's high end."""
    from billtocome.scenario import BRACKETS, Scenario
    assert len(BRACKETS) == 18
    b = next(b for b in BRACKETS if b.name == "Price after 2050")
    assert b.low == Scenario()
    assert dict(b.high.prices) == prices.path_average_after_2050()
    assert b.high == Scenario(prices=b.high.prices)


NO_SEMICOLONS_OR_DASHES = (";", " - ", "–", "—")


def test_the_price_after_2050_settings_are_words_fit_to_print():
    s = figures.setting_keys()
    held = "DESNZ's central price path to 2050, then its 2050 price held to 2099"
    assert s["bracket.price_after_2050.setting.low"] == held
    assert s["bracket.price_after_2050.setting.central"] == held
    assert s["bracket.price_after_2050.setting.high"] == \
        "DESNZ's central price path to 2050, then its average over 2026 to 2050 held to 2099"
    for end in ("low", "central", "high"):
        assert not any(x in s[f"bracket.price_after_2050.setting.{end}"] for x in NO_SEMICOLONS_OR_DASHES)
    # the forward-prices bracket's words, which share the central Scenario, do not move
    o = old()
    for end in ("low", "central", "high"):
        k = f"bracket.forward_prices_then_annex_m.setting.{end}"
        assert s[k] == o[k]


CASE = "price_after_2050.path_average"


def frozen() -> dict:
    return json.loads(figures.FILE.read_text())["figures"]


def test_the_brackets_are_counted_in_figures_and_words():
    f = frozen()
    assert f["brackets.count"] == 18
    assert f["brackets.count_in_words"] == "eighteen"


def test_the_two_prices_after_2050_are_keys():
    f, o = frozen(), old()
    assert math.isclose(f["price_after_2050.held.price"], o["price_path.reference.2050"], rel_tol=1e-10)
    mean = sum(o[f"price_path.reference.{y}"] for y in range(2026, 2051)) / 25
    assert math.isclose(f[f"{CASE}.price"], mean, rel_tol=1e-10)


def test_the_case_gives_the_bill_and_sizewell_cs_paybacks():
    """The case's own run gives the bill the tornado's run of the bracket's high end gives (two runs); Sizewell C
    pays back far less and from later (by the exploration run of 17 Nov 2026 on the Mac Mini: about £2.85bn, 2089
    to 2099, against 1.2.6's £18.07bn, 2072 to 2099); Hinkley Point C costs more, as its contract runs past 2050."""
    f, o = frozen(), old()
    assert math.isclose(f[f"{CASE}.bill.total.cash"], f["bracket.price_after_2050.high.cash"], rel_tol=1e-10)
    assert math.isclose(f[f"{CASE}.bill.difference.cash"], f[f"{CASE}.bill.total.cash"] - f["bill.total.cash"],
                        rel_tol=1e-10)
    assert 49.0e9 < f[f"{CASE}.bill.difference.cash"] < 49.5e9
    assert math.isclose(f["sizewell_c.negative_years.cash"], o["sizewell_c.negative_years.cash"], rel_tol=1e-10)
    assert -2.9e9 < f[f"{CASE}.sizewell_c.negative_years.cash"] < -2.8e9
    assert f[f"{CASE}.sizewell_c.negative_years.years"] == "2089-2099"
    assert 68.7e9 < f[f"{CASE}.sizewell_c.total.cash"] < 68.8e9
    assert 40.5e9 < f[f"{CASE}.hinkley_point_c.total.cash"] < 40.6e9
    assert f[f"{CASE}.hinkley_point_c.total.cash"] > o["hinkley_point_c.total.cash"]


def test_the_case_is_described_in_words_fit_to_print():
    w = frozen()[f"{CASE}.words"]
    assert w == (
        "DESNZ's price path stops at 2050, and the central case holds its 2050 price, the highest on the path, to "
        "2099. This case holds instead the average of the path over 2026 to 2050 from 2051. Lower prices after 2050 "
        "mean larger top-ups for Hinkley Point C and the other contracts that run past 2050, and a larger Sizewell C "
        "charge, and Sizewell C pays back less.")
    assert not any(x in w for x in NO_SEMICOLONS_OR_DASHES)


import csv
import re

COMPARE = ROOT / "docs" / "figures-1.2.6-vs-1.3.0.csv"
ADDED = {
    "brackets.count", "brackets.count_in_words", "price_after_2050.held.price", f"{CASE}.price", f"{CASE}.words",
    f"{CASE}.bill.total.cash", f"{CASE}.bill.difference.cash", f"{CASE}.sizewell_c.total.cash",
    f"{CASE}.hinkley_point_c.total.cash", f"{CASE}.cfd_renewables.total.cash",
    f"{CASE}.sizewell_c.negative_years.cash", f"{CASE}.sizewell_c.negative_years.years",
    *(f"bracket.price_after_2050.{end}.{m}" for end in ("low", "high", "swing")
      for m in ("cash", "pv_green_book", "pv_hurdle")),
    "bracket.price_after_2050.rank.cash",
    *(f"bracket.price_after_2050.setting.{end}" for end in ("low", "central", "high")),
}


def _same(a, b) -> bool:
    """Exactly equal, or numbers equal to 10 significant figures (the no-move test of 1.2.2: holds on any machine)."""
    return a == b or (isinstance(a, float) and isinstance(b, float) and math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-6))


def _moved() -> set:
    o, f = old(), frozen()
    return {k for k in o if not _same(o[k], f[k])}


def test_keys_are_added_and_none_removed():
    o, f = old(), frozen()
    assert set(o) <= set(f)
    assert set(f) - set(o) == ADDED


def test_only_the_ranks_the_new_bracket_passes_move_each_down_one_place():
    """The new bracket enters the tornado at its swing's rank; every bracket it passes moves down one place. No other
    1.2.6 key moves: not the central bill, not the range (its ends stay Sizewell C's return and DESNZ's low path)."""
    o, f = old(), frozen()
    moved = _moved()
    assert moved and all(re.fullmatch(r"bracket\.[a-z0-9_]+\.rank\.cash", k) for k in moved), sorted(moved)
    new = f["bracket.price_after_2050.rank.cash"]
    for k in moved:
        assert f[k] == o[k] + 1 and o[k] >= new
    assert {k for k in o if re.fullmatch(r"bracket\.[a-z0-9_]+\.rank\.cash", k) and o[k] >= new} == moved


def test_the_new_keys_have_units():
    """Exactly one unit pattern for each new key (the rule of tests/test_keys_1_0_1.py for every key after 1.0.0)."""
    for k in ADDED:
        assert sum(bool(re.fullmatch(p, k)) for p in figures.KEY_UNITS if p != "default") == 1, k


def test_only_the_version_and_new_units_move_in_the_meta():
    o, n = json.loads(V126.read_text())["meta"], json.loads(figures.FILE.read_text())["meta"]
    assert (o["version"], n["version"]) == ("1.2.6", "1.3.0")
    assert {k for k in o if n[k] != o[k]} == {"version", "key_units"}
    assert set(n) == set(o)
    ku_o, ku_n = o["key_units"], n["key_units"]
    assert set(ku_o) < set(ku_n)
    assert all(ku_n[k] == ku_o[k] for k in ku_o)


def test_the_saved_comparison_lists_every_key_and_its_move():
    """docs/figures-1.2.6-vs-1.3.0.csv: every key, its old and new value (empty where it has none) and `same`
    (exactly), `digits` (the same to 10 significant figures), `moved` or `added`; the committed file's values exactly."""
    rows = list(csv.DictReader(COMPARE.open()))
    o, f = old(), frozen()
    assert sorted(r["key"] for r in rows) == sorted(set(o) | set(f))
    for r in rows:
        k = r["key"]
        assert r["v1.2.6"] == (repr(o[k]) if k in o else "")
        assert r["v1.3.0"] == repr(f[k])
        assert r["status"] == ("added" if k not in o else "same" if o[k] == f[k] else
                               "digits" if _same(o[k], f[k]) else "moved")
    assert {r["key"] for r in rows if r["status"] == "moved"} == _moved()
    assert {r["key"] for r in rows if r["status"] == "added"} == ADDED
