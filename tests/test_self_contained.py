"""Version 1.2.1: the model is self-contained. A clean copy of its tag, plus the saved inputs MANIFEST.jsonl lists
out of git, reruns on any machine (spec user story 24). At 1.2.0 the Capacity Market line read another model's
working folder by absolute path, so a clean copy failed on the Mac Mini (found in aios-harness#231)."""
import hashlib
import json
import re
from pathlib import Path

from billtocome import cm

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
# The Clock export of Report No. 1's engine release v4-s43, as model-bill-already-paid keeps it
# (reference/engine/v4-s43.json); report-series/model-register.yaml pins it by this fingerprint.
V4_S43 = "e1cf23af9fd6129cc7e4b1dc7b1a5b058c9f20d0e1a64077d6817decea3828cf"
OUTSIDE = re.compile(r"""["'](?:/(?:srv|home|vault|var|tmp|mnt|opt|Users|root)\b|~/|\.\./)""")


def _latest(rel: str) -> dict:
    out = {}
    for line in (RAW / "MANIFEST.jsonl").read_text().splitlines():
        rec = json.loads(line)
        out[rec["file"]] = rec  # later lines are later fetches
    return out[rel]


def test_no_source_tool_or_test_names_a_path_outside_the_model():
    found = [f"{p.relative_to(ROOT)}:{n}" for d in ("src", "tools", "tests") for p in sorted((ROOT / d).rglob("*"))
             if p.suffix in (".py", ".sh") for n, line in enumerate(p.read_text().splitlines(), 1) if OUTSIDE.search(line)]
    assert found == []


def test_the_capacity_market_shares_load_from_the_models_own_saved_copy():
    assert cm.ENGINE.resolve().is_relative_to(RAW)
    rel = cm.ENGINE.relative_to(RAW).as_posix()
    assert hashlib.sha256(cm.ENGINE.read_bytes()).hexdigest() == _latest(rel)["sha256"] == V4_S43


def test_the_shares_are_the_v4_s43_shares():
    # docs/facts.md 28: 2025 14.61%; 2021-25 lowest 13.60% (2022), highest 15.55% (2024)
    assert (round(cm.SHARE_CENTRAL, 4), round(cm.SHARE_LOW, 4), round(cm.SHARE_HIGH, 4)) == (0.1461, 0.1360, 0.1555)
