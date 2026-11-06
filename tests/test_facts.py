"""aios-harness#79 (Stage 0): every fact the later stages need is in docs/facts.md with its saved source and page.

A fact is a numbered line `N. **Label.** ...`. Each one named in STAGE_0 must cite at least one saved file
(a backticked path under data/raw/, recorded in MANIFEST.jsonl) and say where in it (page, paragraph,
table, clause, regulation, rule or sheet). None of them may still be listed under "Open".
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
FACTS = (ROOT / "docs" / "facts.md").read_text()

STAGE_0 = [
    "Households' share now",
    "Households' share projected",
    "Manufacturers' exemption size",
    "Forward prices 2026-27",
    "Solar decline",
    "Capacity Market indexation",
]
WHERE = re.compile(r"\b(p\.|pp\.|page|para|Table|cl\.|reg\.|rule|Rule|sheet|Sheet|art\.|section|s\.)\s*[\w.]", re.I)


def _manifest() -> set[str]:
    return {json.loads(line)["file"] for line in (RAW / "MANIFEST.jsonl").read_text().splitlines()}


def _fact(label: str) -> str:
    m = re.search(rf"^\d+\. \*\*{re.escape(label)}[.:]?\*\*.*$", FACTS, re.M)
    assert m, f"no fact headed **{label}.** in docs/facts.md"
    return m.group(0)


def _open_section() -> str:
    return FACTS.split("## Open", 1)[1] if "## Open" in FACTS else ""


def test_each_stage_0_fact_cites_a_saved_file_and_where_in_it():
    saved = _manifest()
    for label in STAGE_0:
        line = _fact(label)
        cited = [p for p in re.findall(r"`([^`*]+\.[A-Za-z0-9]+)`", line) if p in saved]
        assert cited, f"{label}: cites no file recorded in MANIFEST"
        for p in cited:
            assert (RAW / p).is_file(), f"{label}: {p} is in MANIFEST but not on disk"
        assert WHERE.search(line), f"{label}: says no page, table, clause or rule"


def test_no_stage_0_fact_is_still_open():
    rest = _open_section().lower()
    for word in ("solar decline", "capacity market", "households' share", "exemption", "forward price"):
        assert word not in rest, f"'{word}' is still listed under Open"


def test_every_cited_file_is_saved():
    saved = _manifest()
    for p in re.findall(r"`([a-z0-9-]+/[^`*/]+\.[A-Za-z0-9]+)`", FACTS):
        if p.startswith("model-ending-subsidy-contracts/"):
            continue  # the 16 Oct fetch, kept in its own project
        assert p in saved, f"{p} is cited but not in MANIFEST"
