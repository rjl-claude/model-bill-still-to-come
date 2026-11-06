"""aios-harness#62: every official file is recorded with its source and checksum."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OLD_SUMS = Path("/srv/aios/projects/model-ending-subsidy-contracts/data/raw/SHA256SUMS")
# MANIFEST records copies under the project's name at copy time, before the 6 Nov 2026 rename (aios-harness#101)
COPIED = "copied from model-subsidy-book"


def _latest() -> dict:
    out = {}
    for line in (RAW / "MANIFEST.jsonl").read_text().splitlines():
        rec = json.loads(line)
        out[rec["file"]] = rec  # later lines are later fetches
    return out


def _fetch_module():
    spec = importlib.util.spec_from_file_location("fetch", ROOT / "tools" / "fetch.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_every_named_file_was_fetched():
    latest = _latest()
    missing = [rel for rel in _fetch_module().FILES if rel not in latest]
    assert not missing, f"never fetched: {missing}"


def test_every_file_on_disk_matches_its_latest_record():
    latest = _latest()
    for path in RAW.rglob("*"):
        if not path.is_file() or path.name == "MANIFEST.jsonl" or "halfhourly" in path.parts:
            continue
        rel = path.relative_to(RAW).as_posix()
        assert rel in latest, f"{rel} is not in MANIFEST"
        rec = latest[rel]
        # Either fetched from its publisher, or copied from the 16 Oct fetch (now model-ending-subsidy-contracts), whose
        # own checksum list must then hold the same file.
        if rec["url"].startswith(COPIED):
            sums = OLD_SUMS.read_text() if OLD_SUMS.exists() else ""
            assert rec["sha256"] in sums, f"{rel}: copied, but not in the old checksum list"
        else:
            assert rec["url"].startswith("https://"), rel
        assert hashlib.sha256(path.read_bytes()).hexdigest() == rec["sha256"], f"{rel} changed since fetch"


def test_ro_registers_present():
    latest = _latest()
    assert any(k.startswith("ofgem-rer/RO_Accredited_Stations_") for k in latest)
    assert any(k.startswith("ofgem-rer/RO_Certificates_") for k in latest)
