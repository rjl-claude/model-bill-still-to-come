"""aios-harness#229: every figure a written explanation types equals its key in the frozen results file.

explanations.yaml goes into Annex E. Its `gap` line and the figures in its prose were typed by hand on 5 Nov
2026; the freeze (9 Nov) re-fetched every register and three of them went stale (found in aios-harness#221).
Tested at the seam the paper reads: the frozen results file, by key."""
import json
import re

import pandas as pd
import yaml

from billtocome import figures


def frozen() -> dict[str, float]:
    return json.loads(figures.FILE.read_text())["figures"]


def notes() -> list[dict]:
    return yaml.safe_load((figures.ROOT / "explanations.yaml").read_text())


def key(e: dict) -> str:
    return f"check.{figures.slug(e['check'])}.{figures.slug(e['line'])}.{figures.slug(e['period'])}"


def test_each_gap_line_is_the_ratio_key_to_two_places():
    f = frozen()
    for e in notes():
        typed = re.fullmatch(r"model (\d+\.\d\d) x \w+ \(.*\)", e["gap"])
        assert typed, e["gap"]
        assert float(typed.group(1)) == round(f[key(e) + ".ratio"], 2), (e["check"], e["line"], e["period"])


def test_the_lccc_note_prints_the_rerun_at_lcccs_price():
    f = frozen()
    text = next(e["explanation"] for e in notes() if e["check"] == "LCCC")
    ratio = f["check.lccc.cfd_renewables.2026_10_to_2027_03.at_forward_price.ratio"]
    assert f"(model {ratio:.2f} x LCCC)" in text
    within = int(re.search(r"within (\d+)% of LCCC", text).group(1))
    assert abs(ratio - 1) * 100 <= within < abs(ratio - 1) * 100 + 1  # the nearest whole per cent above the gap


def test_the_capacity_market_join_note_matches_the_frozen_join():
    """The model's 2026 is above the Clock's 2025: the note gives both figures as the keys hold them, and
    no longer gives the Clock's older net-zero share as a reason."""
    f = frozen()
    k = "check.clock_join.capacity_market.2026_vs_2025"
    text = next(e["explanation"] for e in notes() if e["check"] == "Clock join")
    assert "27.7%" not in text
    assert f"£{f[k + '.reference'] / 1e6:.0f}m" in text and f"£{f[k + '.model'] / 1e6:.0f}m" in text
    years = pd.read_csv(figures.FILE.parent / "cm_agreement_years.csv")
    autumn = years[(years.delivery_year == 2026) & (years.year == 2026)].whole_cash.sum()
    assert f"£{autumn / 1e9:.2f}bn" in text
