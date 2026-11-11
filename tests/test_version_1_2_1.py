"""Version 1.2.1, a patch: the model is self-contained (the Capacity Market shares read from its own saved copy of
the v4-s43 Clock export, the old checksum list saved as a fixture; found in aios-harness#231). No figure moves.
Tested at the seam the paper reads: the frozen results file, by key, against the frozen 1.2.0 file. From 1.2.2 (keys
only, aios-harness#235, tests/test_keys_1_2_2.py) the check reads the frozen 1.2.1 file, a fixture."""
import json
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"
V120 = FIXTURES / "figures-1.2.0.json"  # results/figures.json at tag v1.2.0
V121 = FIXTURES / "figures-1.2.1.json"  # results/figures.json at tag v1.2.1


def test_every_key_and_value_is_1_2_0s():
    old, new = json.loads(V120.read_text())["figures"], json.loads(V121.read_text())["figures"]
    assert new == old  # no key added or lost, every value exactly equal
    assert new["bill.total.cash"] == 172451822345.21866  # £172.45bn, 1.0.0's headline


def test_only_the_version_and_the_manifest_fingerprint_move_in_the_meta():
    old, new = json.loads(V120.read_text())["meta"], json.loads(V121.read_text())["meta"]
    assert (old["version"], new["version"]) == ("1.2.0", "1.2.1")
    assert sorted(new) == sorted(old)
    assert {k for k in old if new[k] != old[k]} == {"version", "manifest_sha256"}  # MANIFEST gains one file
