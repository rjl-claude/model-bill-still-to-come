"""aios-harness#236: version 1.2.5, VAT on households' electricity at 0% from 1 October 2026 to 30 June 2027.

The Value Added Tax (Supplies of Domestic Electricity) Order 2026 (SI 2026/987, made 7 Sep 2026, saved in
data/raw/legislation/) zero-rates supplies made from 1 October 2026 to 31 March 2027; Budget 2026 (28 Oct 2026,
data/raw/hmt/budget-2026.pdf para 2.48; AB26_Policy_Costing.pdf p.12, "effective from 1 October 2026 until 1 July
2027") extends it, announced, not yet law at the cut-off. The model counts the extension (the conductor's ruling,
11 Nov 2026), as it counts the Budget's other announced measures. 1.2.4 charged 5% throughout.

Tested at the seam the paper reads: the frozen results file, by key, against the frozen 1.2.4 file. From 1.2.6
(Northern Ireland's window, aios-harness#236, tests/test_version_1_2_6.py) these checks read the frozen 1.2.5 file, a
fixture, as 1.2.6 moves its two Northern Ireland keys; 1.2.5's mirror test of the Northern Ireland key was replaced by
a hand calculation from the run's own rows, and its meta test allows only what its name says (the checker, 14 Nov)."""
import csv
import hashlib
import json
import math
import re
from pathlib import Path

import pandas as pd

from billtocome import figures

ROOT = Path(__file__).resolve().parents[1]
V124 = ROOT / "tests" / "fixtures" / "figures-1.2.4.json"  # results/figures.json at tag v1.2.4
V125 = ROOT / "tests" / "fixtures" / "figures-1.2.5.json"  # results/figures.json at tag v1.2.5
COMPARE = ROOT / "docs" / "figures-1.2.4-vs-1.2.5.csv"
ADDED = {
    "vat.rate.reduced": 0.05,
    "vat.rate.zero": 0.0,
    "vat.zero_rate.in_law.period": "1 October 2026 to 31 March 2027",
    "vat.zero_rate.in_law.source": "the Value Added Tax (Supplies of Domestic Electricity) Order 2026 (SI 2026/987)",
    "vat.zero_rate.announced.period": "1 October 2026 to 30 June 2027",
    "vat.zero_rate.announced.source": "Budget 2026, 28 October 2026 (announced; not yet law at 9 November 2026)",
    "vat.zero_rate.modelled.period": "1 October 2026 to 30 June 2027",
    "vat.zero_rate.modelled.basis": "the zero rate in law with the extension Budget 2026 announced",
}
IN_LAW = ("vat.zero_rate_in_law_only.total.cash", "bill.zero_rate_in_law_only.total.cash",
          "bill.zero_rate_in_law_only.difference.cash")


def _same(a, b) -> bool:
    """Equal, or numbers equal to 10 significant figures (the no-move test of 1.2.2: holds on any machine)."""
    return a == b or (isinstance(a, float) and isinstance(b, float) and math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-6))


def frozen() -> dict:
    return json.loads(V125.read_text())["figures"]


def old() -> dict:
    return json.loads(V124.read_text())["figures"]


def test_the_fixture_is_the_frozen_1_2_4_file():
    assert hashlib.sha256(V124.read_bytes()).hexdigest().startswith("356e25ae")  # model-register.yaml


def test_the_rates_and_the_periods_are_read_by_key():
    f = frozen()
    assert {k: f[k] for k in ADDED} == ADDED


def test_vat_moves_only_in_2026_and_2027():
    """2026 pays 5% on 273 of 365 days (Jan-Sep), 2027 on 184 (Jul-Dec); 1.2.4 paid 5% on all of each."""
    f, o = frozen(), old()
    assert abs(f["vat.2026.cash"] / o["vat.2026.cash"] - 273 / 365) < 1e-9
    assert abs(f["vat.2027.cash"] / o["vat.2027.cash"] - 184 / 365) < 1e-9
    assert all(_same(f[f"vat.{y}.cash"], o[f"vat.{y}.cash"]) for y in range(2028, 2100))  # to 10 sf: any machine


def test_the_bill_had_the_zero_rate_ended_in_law_on_31_march_2027():
    """Ended on 31 March 2027, 2027's VAT is 5% on 91 more days (April to June): 5% x 91/365 of households' 2027
    part before VAT. Households' 2027 key includes their VAT, so it is taken off first."""
    f = frozen()
    hh_2027 = f["bill.households.2027.cash"] - f["vat.2027.cash"]
    extra = 0.05 * 91 / 365 * hh_2027
    assert abs(f["vat.zero_rate_in_law_only.total.cash"] - (f["vat.total.cash"] + extra)) < 1.0
    assert abs(f["bill.zero_rate_in_law_only.total.cash"] - (f["bill.total.cash"] + extra)) < 1.0
    assert abs(f["bill.zero_rate_in_law_only.difference.cash"] - extra) < 1.0
    assert 0 < extra < 0.1e9


def test_the_new_keys_have_units():
    for k in list(ADDED) + list(IN_LAW):
        assert any(re.fullmatch(p, k) for p in figures.KEY_UNITS if p != "default"), k


def test_only_the_version_the_manifest_fingerprint_and_new_units_move_in_the_meta():
    """The MANIFEST gained SI 2026/987's two files; key_units gained the new keys' units and changed none."""
    o, n = json.loads(V124.read_text())["meta"], json.loads(V125.read_text())["meta"]
    assert (o["version"], n["version"]) == ("1.2.4", "1.2.5")
    assert set(n) == set(o)
    assert {k for k in o if n[k] != o[k]} == {"version", "manifest_sha256", "key_units"}
    assert all(n["key_units"][k] == v for k, v in o["key_units"].items())


def test_the_saved_comparison_lists_every_key_and_its_move():
    """docs/figures-1.2.4-vs-1.2.5.csv: every key of either file, its old and new value and `same` (exactly),
    `digits` (the same to 10 significant figures: the last binary digits, as the Mac Mini's arm64 run differs from
    x86_64, see 1.2.2), `moved` or `added`; the committed file's numbers exactly."""
    rows = list(csv.DictReader(COMPARE.open()))
    o, f = old(), frozen()
    assert sorted(r["key"] for r in rows) == sorted(set(o) | set(f))
    for r in rows:
        k = r["key"]
        assert r["v1.2.4"] == (repr(o[k]) if k in o else "")
        assert r["v1.2.5"] == repr(f[k])
        assert r["status"] == ("added" if k not in o else "same" if o[k] == f[k] else "digits" if _same(o[k], f[k])
                               else "moved")
    assert {r["key"] for r in rows if r["status"] == "added"} == set(ADDED) | set(IN_LAW) | {NI_KEY, NI_WORDS}


MAY_MOVE = re.compile(
    r"(vat|bill)(\.(built|not_yet_built|households))*\.(2026|2027|total)\.(cash|pv_green_book|pv_hurdle)"  # VAT, and sums with it
    r"|bill\.without_nuclear\.total\.cash"  # less nuclear's VAT, the rest's VAT moves
    r"|bracket\.[a-z0-9_]+\.(low|high|swing)\.(cash|pv_green_book|pv_hurdle)|range\.(low|high)\.[a-z_]+")  # each bracket end's bill


def test_no_other_key_moves():
    """Only the VAT line, the sums that include it (in 2026, 2027 and the totals), the bill without nuclear and the
    brackets' ends, swings and ranges move; every scheme line, payer split, check, count, rank and setting stays."""
    o, f = old(), frozen()
    moved = {k for k in o if not _same(o[k], f[k])}
    assert moved and all(MAY_MOVE.fullmatch(k) for k in moved), sorted(k for k in moved if not MAY_MOVE.fullmatch(k))
    assert "vat.total.cash" in moved and "bill.total.cash" in moved and "range.low.cash" in moved


# Northern Ireland (conductor's ruling, 13 Nov 2026, choice 1): SI 2026/987 zero-rates Great Britain only and leaves
# Northern Ireland at 5%; the model has no payer area and zero-rates every household's part. The RO line holds the
# NIRO stations, so the overstatement is sized by a key: at most the VAT 5% on households' part of those stations'
# rows would have kept, by days (Oct-Dec 2026: 92 of 365; Jan-Jun 2027: 181 of 365). An upper bound, because NI
# stations' certificates can be presented in Great Britain.
NI_KEY = "vat.zero_rate.northern_ireland_upper_bound.cash"
NI_WORDS = "vat.zero_rate.northern_ireland_upper_bound.words"


def test_the_northern_ireland_overstatement_is_sized_by_key():
    """1.2.5's key, by hand from the run's own rows (results/results.csv and results/ro_stations.csv, which 1.2.6 does
    not change): 5% on households' part of the Northern Ireland stations' RO rows over 92 of 365 days of 2026 and 181
    of 365 of 2027. The checker's own figure is £5.923m. 1.2.6 sizes it over 1 Oct 2026 to 31 Mar 2027 only."""
    st = pd.read_csv(ROOT / "results" / "ro_stations.csv", usecols=["Accreditation reference", "Country"])
    ni = set(st.loc[st.Country == "Northern Ireland", "Accreditation reference"])
    t = pd.read_csv(ROOT / "results" / "results.csv", usecols=["line", "item", "payer", "year", "cash"])
    hh = t[(t.line == "RO") & (t.payer == "households") & t.item.isin(ni)].groupby("year").cash.sum()
    f = frozen()
    assert abs(f[NI_KEY] - 0.05 * (92 / 365 * hh[2026] + 181 / 365 * hh[2027])) < 1.0
    assert 5.92e6 < f[NI_KEY] < 5.93e6  # the checker's £5.923m (14 Nov 2026)
    assert f[NI_WORDS] == (
        "at most the VAT that 5% on households' part of the Renewables Obligation's Northern Ireland stations would "
        "have kept from 1 October 2026 to 30 June 2027; an upper bound, because Northern Ireland's certificates can "
        "be presented in Great Britain")
