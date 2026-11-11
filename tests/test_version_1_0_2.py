"""aios-harness#229: version 1.0.2 corrects three written check notes and saves seven more sources; it
changes no figure. Tested at the seam the paper reads: the frozen results file, by key. From 1.1.0 (whose
Green Book present values move, aios-harness#255) the check reads the frozen 1.0.2 file, saved as a fixture."""
import hashlib
import json
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"
V101 = FIXTURES / "figures-1.0.1.json"  # results/figures.json at tag v1.0.1
V102 = FIXTURES / "figures-1.0.2.json"  # results/figures.json at tag v1.0.2


def test_the_fixture_is_the_frozen_1_0_1_file():
    assert hashlib.sha256(V101.read_bytes()).hexdigest().startswith("e79c8e9229cbc652")  # model-register.yaml


def test_every_1_0_1_key_and_figure_is_unchanged():
    old, new = json.loads(V101.read_text())["figures"], json.loads(V102.read_text())["figures"]
    assert sorted(new) == sorted(old)  # no key added or lost
    assert [k for k in old if new[k] != old[k]] == []  # exactly equal, not approximately


def test_only_the_version_and_the_saved_sources_fingerprint_move_in_the_meta():
    old, new = json.loads(V101.read_text())["meta"], json.loads(V102.read_text())["meta"]
    assert (old["version"], new["version"]) == ("1.0.1", "1.0.2")
    assert {k for k in old if new[k] != old[k]} == {"version", "manifest_sha256"}
