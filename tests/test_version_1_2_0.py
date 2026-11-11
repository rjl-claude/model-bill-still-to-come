"""aios-harness#257: version 1.2.0 moves the low end of Sizewell C's return after 2039 from 3.5% to 3.00%. Richard
set the low end at "the Green Book rate" (5 Nov 2026); the Green Book 2026 (revised 28 Oct 2026, para 6.54) sets
that rate at 3.00%, so the low end follows it (Richard's ruling, choice 1, 11 Nov 2026). Only the keys built from
that bracket's low end move. Tested at the seam the paper reads: the frozen results file, by key."""
import hashlib
import json
from pathlib import Path

from billtocome import figures

V110 = Path(__file__).resolve().parent / "fixtures" / "figures-1.1.0.json"  # results/figures.json at tag v1.1.0
SZC = "bracket.sizewell_c_return_after_2039"
# The only keys allowed to differ from 1.1.0: the bracket's low ends and swings (its high end is the central
# run), and the low end of the cash range, which is that bracket's low end. The present-value ranges' low ends
# are the Annex M prices bracket's, and the bracket keeps its rank (2nd by cash swing).
MOVES = {f"{SZC}.{end}.{m}" for end in ("low", "swing") for m in ("cash", "pv_green_book", "pv_hurdle")} | {"range.low.cash"}


def test_the_fixture_is_the_frozen_1_1_0_file():
    assert hashlib.sha256(V110.read_bytes()).hexdigest().startswith("af2634cfca3cb335")  # model-register.yaml


def test_only_the_sizewell_c_low_return_keys_differ_from_1_1_0():
    old, new = json.loads(V110.read_text())["figures"], json.loads(figures.FILE.read_text())["figures"]
    assert sorted(new) == sorted(old)  # no key added or lost
    assert {k for k in old if new[k] != old[k]} == MOVES  # every other key exactly equal, not approximately


def test_a_lower_return_lowers_the_low_end_and_the_cash_headline_holds():
    old, new = json.loads(V110.read_text())["figures"], json.loads(figures.FILE.read_text())["figures"]
    assert new["bill.total.cash"] == old["bill.total.cash"] == 172451822345.21866  # £172.45bn, 1.0.0's headline
    assert new[f"{SZC}.low.cash"] < old[f"{SZC}.low.cash"]
    assert new["range.low.cash"] == new[f"{SZC}.low.cash"]
    assert new[f"{SZC}.rank.cash"] == old[f"{SZC}.rank.cash"] == 2


def test_only_the_version_moves_in_the_meta():
    old, new = json.loads(V110.read_text())["meta"], json.loads(figures.FILE.read_text())["meta"]
    assert (old["version"], new["version"]) == ("1.1.0", "1.2.0")
    assert {k for k in old if new[k] != old[k]} == {"version"}  # same saved sources (MANIFEST), same dates
