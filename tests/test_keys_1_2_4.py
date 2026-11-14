"""aios-harness#235: version 1.2.4, text keys only. The households' share bracket's words say the RO is at DESNZ's 41%
in every scenario (who_pays.RO_HOUSEHOLDS), not held at 2025's share (the recheck's finding, 11 Nov 2026); no other
key changes. Tested at the seam the paper reads: the frozen results file, by key, against the frozen 1.2.3 file. From
1.2.5 (VAT's zero rate, aios-harness#236, tests/test_version_1_2_5.py) these checks read the frozen 1.2.4 file, a
fixture."""
import json
from pathlib import Path

from billtocome import figures

V123 = Path(__file__).resolve().parent / "fixtures" / "figures-1.2.3.json"  # results/figures.json at tag v1.2.3
V124 = Path(__file__).resolve().parent / "fixtures" / "figures-1.2.4.json"  # results/figures.json at tag v1.2.4
KEYS = {f"bracket.households_share.setting.{end}" for end in ("low", "central", "high")}


def frozen() -> dict:
    return json.loads(V124.read_text())["figures"]


def test_the_fixture_is_the_frozen_1_2_3_file():
    import hashlib
    assert hashlib.sha256(V123.read_bytes()).hexdigest().startswith("7b7f10f09aa8998c")


def test_the_households_share_words_give_both_shares():
    """DUKES 5.1, 2025: 96,188.8 of 275,527.5 GWh = 34.9%; the RO's domestic share, DESNZ's 41% (who_pays.py)."""
    f = frozen()
    assert f["bracket.households_share.setting.low"] == "DESNZ's projected share by year (the RO at DESNZ's 41% throughout)"
    assert f["bracket.households_share.setting.central"] == f["bracket.households_share.setting.high"] \
        == "households' 2025 share, 34.9%, held (the RO at DESNZ's 41% throughout)"


def test_only_the_households_share_words_change_from_1_2_3():
    from test_keys_1_2_2 import same
    old, new = json.loads(V123.read_text())["figures"], frozen()
    assert sorted(new) == sorted(old)
    assert {k for k in old if not same(new[k], old[k])} == KEYS  # every number to 10 figures on any machine


def test_the_saved_proof_shows_only_the_three_keys_changed_in_the_committed_file():
    import csv
    rows = list(csv.DictReader((figures.FILE.parent.parent / "docs" / "figures-1.2.3-vs-1.2.4.csv").open()))
    old = json.loads(V123.read_text())["figures"]
    assert sorted(r["key"] for r in rows) == sorted(old)
    assert all(r["v1.2.3"] == repr(old[r["key"]]) for r in rows)
    assert {r["key"] for r in rows if r["status"] != "same"} == KEYS
    assert all(r["v1.2.4"] == r["v1.2.3"] for r in rows if r["status"] == "same")


def test_only_the_version_moves_in_the_meta():
    old, new = json.loads(V123.read_text())["meta"], json.loads(V124.read_text())["meta"]
    assert (old["version"], new["version"]) == ("1.2.3", "1.2.4")
    assert {k for k in old if new[k] != old[k]} == {"version"}
