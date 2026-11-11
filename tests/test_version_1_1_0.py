"""aios-harness#255: version 1.1.0 puts the Green Book present values on the Green Book 2026's rates (revised
28 Oct 2026, para 6.54: 3.00% for years 1 to 30, 2.50% for 31 to 75; Richard's ruling 11 Nov 2026). Only the
Green Book present values move. Tested at the seam the paper reads: the frozen results file, by key. From 1.2.0
(whose Sizewell C low return moves, aios-harness#257) the check reads the frozen 1.1.0 file, saved as a fixture."""
import hashlib
import json
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"
V102 = FIXTURES / "figures-1.0.2.json"  # results/figures.json at tag v1.0.2
V110 = FIXTURES / "figures-1.1.0.json"  # results/figures.json at tag v1.1.0
MOVES = ".pv_green_book"  # the only keys allowed to differ from 1.0.2: every key whose measure is the Green Book present value


def test_the_fixture_is_the_frozen_1_0_2_file():
    assert hashlib.sha256(V102.read_bytes()).hexdigest().startswith("e7bf817e623a6eea")  # model-register.yaml


def test_only_green_book_present_values_differ_from_1_0_2():
    old, new = json.loads(V102.read_text())["figures"], json.loads(V110.read_text())["figures"]
    assert sorted(new) == sorted(old)  # no key added or lost
    assert [k for k in old if new[k] != old[k] and not k.endswith(MOVES)] == []  # exactly equal, not approximately


def test_the_green_book_present_values_rise_and_the_cash_headline_holds():
    old, new = json.loads(V102.read_text())["figures"], json.loads(V110.read_text())["figures"]
    assert new["bill.total.cash"] == old["bill.total.cash"] == 172451822345.21866  # £172.45bn, 1.0.0's headline
    assert new["bill.total.pv_green_book"] > old["bill.total.pv_green_book"]  # lower rates, a larger present value
    assert new["bill.total.pv_green_book"] < new["bill.total.cash"]


def test_only_the_version_moves_in_the_meta():
    old, new = json.loads(V102.read_text())["meta"], json.loads(V110.read_text())["meta"]
    assert (old["version"], new["version"]) == ("1.0.2", "1.1.0")
    assert {k for k in old if new[k] != old[k]} == {"version"}  # same saved sources (MANIFEST), same dates
