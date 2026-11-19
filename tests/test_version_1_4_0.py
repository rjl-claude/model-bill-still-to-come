"""aios-harness#268: version 1.4.0, Richard's ruling of 19 Nov 2026. The steep end of "Decline with age" is
Staffell and Green's upper bound, wind 1.8% a year (Renewable Energy 66 (2014): "Wind turbines are found to lose
1.6 ± 0.2% of their output per year"), in place of an estimate from a 2012 report, no longer used or saved. Solar's
steep end (Jordan and Kurtz's mean, 0.8%), the gentle end and the central settings do not move.

Tested at the seams the paper reads: the Scenario's bracket ends, the setting words the figures file prints, the
facts file, and the frozen results file, by key, against the frozen 1.3.0 file."""
import re

from billtocome import figures, model
from billtocome.scenario import BRACKETS, Scenario

ROOT = figures.FILE.parent.parent
STAFFELL = "decline/staffell-green-2014-wind-farm-performance-decline-with-age.pdf"


def test_the_steep_end_is_wind_1_8_a_year_and_solar_0_8():
    s = Scenario(decline="steeper")
    assert (s.wind_decline, s.solar_decline) == (0.018, 0.008)
    b = next(b for b in BRACKETS if b.name == "Decline with age")
    assert b.high == Scenario(decline="steeper") and b.low == Scenario(decline="gentler")
    assert (Scenario().wind_decline, Scenario().solar_decline) == (0.016, 0.005)
    assert (Scenario(decline="gentler").wind_decline, Scenario(decline="gentler").solar_decline) == (0.0017, 0.005)


def test_the_steep_end_is_sourced_to_staffell_and_green_s_saved_paper():
    """Fact 34 quotes the paper's 1.6 ± 0.2% with its page, and cites the saved copy, which is in the MANIFEST."""
    facts = (ROOT / "docs" / "facts.md").read_text()
    m = re.search(r"^34\. \*\*Decline with age, steeper end\.\*\*.*$", facts, re.M)
    assert m
    fact = m.group(0)
    assert "Staffell" in fact and "Green" in fact and "1.6 ± 0.2%" in fact and "1.8%" in fact
    assert f"`{STAFFELL}`" in fact and re.search(r"p\.\s*775", fact)
    assert STAFFELL in model.MANIFEST.read_text()
    assert (model.MANIFEST.parent / STAFFELL).is_file()


def test_the_setting_words_print_the_new_steep_end():
    s = figures.setting_keys()
    assert s["bracket.decline_with_age.setting.high"] == "wind 1.8% a year, solar PV 0.8%"
    assert s["bracket.decline_with_age.setting.central"] == "wind 1.6% a year, solar PV 0.5%"
    assert s["bracket.decline_with_age.setting.low"] == "wind 0.17% a year, solar PV 0.5%"


import csv
import hashlib
import json
import math

V130 = ROOT / "tests" / "fixtures" / "figures-1.3.0.json"  # results/figures.json at tag v1.3.0
COMPARE = ROOT / "docs" / "figures-1.3.0-vs-1.4.0.csv"
DECLINE_ENDS = {f"bracket.decline_with_age.{end}.{m}" for end in ("high", "swing")
                for m in ("cash", "pv_green_book", "pv_hurdle")}


def old() -> dict:
    return json.loads(V130.read_text())["figures"]


def frozen() -> dict:
    return json.loads(figures.FILE.read_text())["figures"]


def _same(a, b) -> bool:
    """Exactly equal, or numbers equal to 10 significant figures (holds on any machine)."""
    return a == b or (isinstance(a, float) and isinstance(b, float) and math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-6))


def _moved() -> set:
    o, f = old(), frozen()
    return {k for k in o if not _same(o[k], f[k])}


def test_the_fixture_is_the_frozen_1_3_0_file():
    assert hashlib.sha256(V130.read_bytes()).hexdigest() == \
        "4e2d025130280b032cdce74b19cf8d1806a958c4c92e285b072b8f9e1c718276"  # git show v1.3.0:results/figures.json


def test_no_key_is_added_or_removed():
    assert set(frozen()) == set(old())


def test_only_the_decline_bracket_s_steep_end_its_swing_and_the_ranks_move():
    """The central run is unchanged, so the bill does not move; the gentle end does not move; the steep end now costs
    more than before (less output lost, so fewer top-ups lost), so the swing shrinks and the bracket falls in rank."""
    o, f = old(), frozen()
    moved = _moved()
    ranks = {k for k in moved if re.fullmatch(r"bracket\.[a-z0-9_]+\.rank\.cash", k)}
    assert moved == DECLINE_ENDS | {"bracket.decline_with_age.setting.high"} | ranks
    assert all(_same(o[k], f[k]) for k in o if k.startswith(("bill.total.", "range.")))
    assert all(_same(o[k], f[k]) for k in o if k.startswith("bracket.decline_with_age.low."))
    assert f["bracket.decline_with_age.high.cash"] > o["bracket.decline_with_age.high.cash"]
    assert math.isclose(f["bracket.decline_with_age.swing.cash"], abs(
        f["bracket.decline_with_age.low.cash"] - f["bracket.decline_with_age.high.cash"]), rel_tol=1e-10)
    assert 7.0e9 < f["bracket.decline_with_age.swing.cash"] < 7.1e9
    assert f["bracket.decline_with_age.rank.cash"] > o["bracket.decline_with_age.rank.cash"]
    # the ranks stay one to eighteen, each once
    assert sorted(f[k] for k in f if re.fullmatch(r"bracket\.[a-z0-9_]+\.rank\.cash", k)) == list(range(1, 19))


def test_only_the_version_and_the_manifest_fingerprint_move_in_the_meta():
    """The saved copy of the 2012 report leaves data/raw and the MANIFEST, so its fingerprint moves."""
    o, n = json.loads(V130.read_text())["meta"], json.loads(figures.FILE.read_text())["meta"]
    assert (o["version"], n["version"]) == ("1.3.0", "1.4.0")
    assert {k for k in o if n[k] != o[k]} == {"version", "manifest_sha256"}
    assert set(n) == set(o)


def test_the_saved_comparison_lists_every_key_and_its_move():
    rows = list(csv.DictReader(COMPARE.open()))
    o, f = old(), frozen()
    assert sorted(r["key"] for r in rows) == sorted(set(o) | set(f))
    for r in rows:
        k = r["key"]
        assert r["v1.3.0"] == repr(o[k]) and r["v1.4.0"] == repr(f[k])
        assert r["status"] == ("same" if o[k] == f[k] else "digits" if _same(o[k], f[k]) else "moved")
    assert {r["key"] for r in rows if r["status"] == "moved"} == _moved()
