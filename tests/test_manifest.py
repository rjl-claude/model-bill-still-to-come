"""aios-harness#62: every official file is recorded with its source and checksum."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
# The 16 Oct fetch's checksum list (model-ending-subsidy-contracts data/raw/SHA256SUMS, Gitea commit 760c84c), saved
# here from 1.2.1 so the test reads nothing outside the model
OLD_SUMS = ROOT / "tests" / "fixtures" / "model-ending-subsidy-contracts-SHA256SUMS"
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
            sums = OLD_SUMS.read_text()
            assert rec["sha256"] in sums, f"{rel}: copied, but not in the old checksum list"
        else:
            assert rec["url"].startswith("https://"), rel
        assert hashlib.sha256(path.read_bytes()).hexdigest() == rec["sha256"], f"{rel} changed since fetch"


def test_ro_registers_present():
    latest = _latest()
    assert any(k.startswith("ofgem-rer/RO_Accredited_Stations_") for k in latest)
    assert any(k.startswith("ofgem-rer/RO_Certificates_") for k in latest)


# The input audit (aios-harness#229) found seven sources the model relies on that were not saved here.
AUDIT_229 = [
    *(f"desnz/cfd-round-results/{r}.pdf" for r in ("AR1", "AR2", "AR3", "AR4", "AR5", "AR6", "AR7", "AR7a")),
    "desnz/cfd-ar7-consultation-final-government-response.pdf",  # 20-year AR7 wind and solar contracts, para 2.3
    "desnz/BEIS_Electricity_Generation_Cost_Report_2016.pdf",  # Table 4, p.26: nuclear fuel and decommissioning
    "decline/staffell-green-2014-wind-farm-performance-decline-with-age.pdf",  # 1.6% a year
    "edf/edf-2025-annual-results-2026-02-20.html",  # Hinkley Point C Unit 1 production in 2030
    "hmt/The_Green_Book_2026.pdf",  # discount rates
    "legislation/ukpga-1994-23-VATA-schedule-7A-latest.xml",  # VAT at the reduced rate on household power
]


def test_the_sources_the_input_audit_found_unsaved_are_saved():
    latest = _latest()
    assert [rel for rel in AUDIT_229 if rel not in latest or not (RAW / rel).is_file()] == []
    assert set(AUDIT_229) <= set(_fetch_module().FILES)  # fetched again with the rest


def test_the_old_checksum_list_is_the_saved_copy():
    assert hashlib.sha256(OLD_SUMS.read_bytes()).hexdigest().startswith("8e65c005afa95bbb")
