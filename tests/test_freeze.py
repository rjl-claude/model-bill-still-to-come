"""aios-harness#86/#91 (Stage 7): the freeze on the cut-off date. The results file the paper reads is in git,
names the model's version, the valuation date and the cut-off date, and was written from today's inputs."""
import hashlib
import json
import tomllib
from pathlib import Path

from billtocome import figures, model

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_results_file_names_version_and_both_dates():
    meta = json.loads(figures.FILE.read_text())["meta"]
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    assert (meta["model"], meta["version"]) == ("model-bill-still-to-come", version) and version == "1.2.4"  # 1.2.4: the households' share words, no number moves (aios-harness#235)
    assert meta["valuation_date"] == "2026-01-01"
    assert meta["cut_off_date"] == "2026-11-09"  # the day every register was re-fetched (point 15)


def test_frozen_results_file_is_from_these_inputs():
    meta = json.loads(figures.FILE.read_text())["meta"]
    assert meta["manifest_sha256"] == hashlib.sha256(model.MANIFEST.read_bytes()).hexdigest()


def test_results_are_kept_in_git():
    assert "results/" not in (ROOT / ".gitignore").read_text().split()
