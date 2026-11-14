"""aios-harness#236: version 1.2.6, Northern Ireland's VAT window. The checker of 1.2.5 (14 Nov 2026) found that the
Northern Ireland upper bound assumed Northern Ireland pays 5% until 30 June 2027. SI 2026/987 keeps Northern Ireland
at the reduced rate for supplies from 1 October 2026 to 31 March 2027 (art. 1(2), art. 4), and Budget 2026 says
"Extended VAT relief is expected to apply in Northern Ireland from April 2027" (data/raw/hmt/budget-2026.pdf, para
3.4, pdf p.49) and "This is expected to apply UK-wide from April 2027" (para 6.210, pdf p.138). The model counts the
Budget's extension for Great Britain, so on the same basis Northern Ireland is at 0% from April 2027 and the window
the model overstates is 1 October 2026 to 31 March 2027 only. 1.2.6 moves only the two Northern Ireland keys.

Tested at the seam the paper reads: the frozen results file, by key, against the frozen 1.2.5 file."""
import csv
import hashlib
import json
import math

import pandas as pd

from billtocome import figures

ROOT = figures.FILE.parent.parent
V125 = ROOT / "tests" / "fixtures" / "figures-1.2.5.json"  # results/figures.json at tag v1.2.5
COMPARE = ROOT / "docs" / "figures-1.2.5-vs-1.2.6.csv"
NI_KEY = "vat.zero_rate.northern_ireland_upper_bound.cash"
NI_WORDS = "vat.zero_rate.northern_ireland_upper_bound.words"
NI_UNITS = r"vat\.zero_rate\.northern_ireland_upper_bound\.cash"
MAY_MOVE = {NI_KEY, NI_WORDS}


def _same(a, b) -> bool:
    """Exactly equal, or numbers equal to 10 significant figures (the no-move test of 1.2.2: holds on any machine)."""
    return a == b or (isinstance(a, float) and isinstance(b, float) and math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-6))


def frozen() -> dict:
    return json.loads(figures.FILE.read_text())["figures"]


def old() -> dict:
    return json.loads(V125.read_text())["figures"]


def test_the_fixture_is_the_frozen_1_2_5_file():
    assert hashlib.sha256(V125.read_bytes()).hexdigest() == \
        "c7ed3a41b92a5b5ef7391733c23f47ab0f955535d4ac4e48fd758309a3fa9fd6"  # git show v1.2.5:results/figures.json


def test_the_northern_ireland_bound_covers_october_2026_to_march_2027_only():
    """By hand from the frozen run's own rows, not from the code: Northern Ireland's stations are those
    results/ro_stations.csv places there; households' part of their RO rows in results/results.csv; 5% on 92 of 365
    days of 2026 (1 Oct to 31 Dec) and 90 of 365 days of 2027 (1 Jan to 31 Mar). The checker's own figure is £3.996m."""
    st = pd.read_csv(ROOT / "results" / "ro_stations.csv", usecols=["Accreditation reference", "Country"])
    ni = set(st.loc[st.Country == "Northern Ireland", "Accreditation reference"])
    t = pd.read_csv(ROOT / "results" / "results.csv", usecols=["line", "item", "payer", "year", "cash"])
    hh = t[(t.line == "RO") & (t.payer == "households") & t.item.isin(ni)].groupby("year").cash.sum()
    by_hand = 0.05 * (92 / 365 * hh[2026] + 90 / 365 * hh[2027])
    f = frozen()
    assert abs(f[NI_KEY] - by_hand) < 1.0
    assert 3.99e6 < f[NI_KEY] < 4.00e6  # the checker's £3.996m (14 Nov 2026)


def test_the_northern_ireland_words_are_fit_to_print():
    words = frozen()[NI_WORDS]
    assert words == (
        "At most the VAT that 5% on households' part of the Renewables Obligation's Northern Ireland stations would "
        "have raised from 1 October 2026 to 31 March 2027. The order (SI 2026/987) zero-rates households' electricity "
        "in Great Britain only and keeps Northern Ireland at 5% to 31 March 2027. Budget 2026 says the extended relief "
        "is expected to apply in Northern Ireland from April 2027 (paragraphs 3.4 and 6.210), so the model counts "
        "Northern Ireland at 0% from then, as it counts the extension for Great Britain. The model does not split "
        "households by area, so before April 2027 it zero-rates Northern Ireland's households too. The figure is an "
        "upper bound because Northern Ireland's households do not pay for all of these stations. Northern Ireland's "
        "stations make far more certificates than Northern Ireland's suppliers must present, and most are presented "
        "by suppliers in Great Britain, where the zero rate applies. In the year to March 2025 Northern Ireland's "
        "stations were issued 5.6 million certificates, and Northern Ireland's suppliers had to present 1.4 million.")
    assert ";" not in words and " - " not in words and "–" not in words and "—" not in words


def test_the_northern_ireland_units_say_the_window():
    assert figures.KEY_UNITS[NI_UNITS] == (
        "£, 2024 prices (CPIH): at most the VAT the model leaves out for Northern Ireland, at 5% from 1 October 2026 "
        "to 31 March 2027")


def test_no_other_key_moves():
    """Every key of 1.2.5 is in 1.2.6 and none is added; every key but the two Northern Ireland keys is the same,
    exactly for text and to 10 significant figures for numbers."""
    o, f = old(), frozen()
    assert set(f) == set(o)
    moved = {k for k in o if not _same(o[k], f[k])}
    assert moved == MAY_MOVE, sorted(moved ^ MAY_MOVE)


def test_only_the_version_and_the_northern_ireland_units_move_in_the_meta():
    o, n = json.loads(V125.read_text())["meta"], json.loads(figures.FILE.read_text())["meta"]
    assert (o["version"], n["version"]) == ("1.2.5", "1.2.6")
    assert {k for k in o if n[k] != o[k]} == {"version", "key_units"}
    assert set(n) == set(o)
    ku_o, ku_n = o["key_units"], n["key_units"]
    assert set(ku_n) == set(ku_o)
    assert {k for k in ku_o if ku_n[k] != ku_o[k]} == {NI_UNITS}


def test_the_saved_comparison_lists_every_key_and_its_move():
    """docs/figures-1.2.5-vs-1.2.6.csv: every key, its old and new value and `same` (exactly), `digits` (the same to
    10 significant figures) or `moved`; the committed file's values exactly."""
    rows = list(csv.DictReader(COMPARE.open()))
    o, f = old(), frozen()
    assert sorted(r["key"] for r in rows) == sorted(set(o) | set(f))
    for r in rows:
        k = r["key"]
        assert r["v1.2.5"] == repr(o[k])
        assert r["v1.2.6"] == repr(f[k])
        assert r["status"] == ("same" if o[k] == f[k] else "digits" if _same(o[k], f[k]) else "moved")
    assert {r["key"] for r in rows if r["status"] == "moved"} == MAY_MOVE
