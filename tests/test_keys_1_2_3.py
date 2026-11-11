"""aios-harness#235: version 1.2.3, text keys only. The bracket settings' words (1.2.2's `bracket.*.setting.*`) are
corrected to say what the code does (the checker's findings, 11 Nov 2026); no number moves. Tested at the seam the
paper reads: the frozen results file, by key, against the frozen 1.2.2 file. From 1.2.4 (the households' share words,
aios-harness#235, tests/test_keys_1_2_4.py) these checks read the frozen 1.2.3 file, a fixture."""
import json
from pathlib import Path

from billtocome import figures

V122 = Path(__file__).resolve().parent / "fixtures" / "figures-1.2.2.json"  # results/figures.json at tag v1.2.2


V123 = Path(__file__).resolve().parent / "fixtures" / "figures-1.2.3.json"  # results/figures.json at tag v1.2.3


def frozen() -> dict:
    return json.loads(V123.read_text())["figures"]


def s(b: str) -> tuple:
    f = frozen()
    return tuple(f[f"bracket.{b}.setting.{end}"] for end in ("low", "central", "high"))


def test_the_slopes_are_named_by_their_gentler_and_steeper_ends_and_the_clamp_to_flat():
    """discount.bounded_slope: bound -1 the gentler end of the 95% interval, +1 the steeper; a gentler end past zero
    is held flat. Solar's discount slope is (-2.07, gentler end past zero); no negative-hours slope is."""
    lo, c, hi = s("discount_slope")
    assert "gentler end of the 95% interval" in lo and "solar" in lo and "flat" in lo
    assert "steeper end of the 95% interval" in hi and "fitted slope" in c
    lo, c, hi = s("negative_hours_slope")
    assert "gentler end of the 95% interval" in lo and "flat" not in lo
    assert "steeper end of the 95% interval" in hi and "fitted slope" in c


def test_the_output_level_says_where_a_farm_s_output_comes_from():
    """output.py: each farm's own record; farms not yet generating, the median of their technology's farms started in
    2019 or later; no British record, an assumption (DESNZ 2023). The bracket: DESNZ 2023 for CfD wind and solar."""
    lo, c, hi = s("output_level")
    assert lo == c and "own record" in c and "2019 or later" in c and "DESNZ 2023" in c
    assert "DESNZ 2023" in hi and "wind and solar" in hi


def test_hinkley_s_term_names_the_target_commissioning_window():
    lo, c, hi = s("hinkley_term")
    assert lo == c == "35 years from the earlier of start and the target commissioning window's end"
    assert hi == "35 years from start"


def test_decline_with_age_gives_its_rates():
    """output.DECLINES: wind 0.17%, 1.6%, 5.4% a year; solar PV 0.5%, 0.5%, 0.8%."""
    assert s("decline_with_age") == ("wind 0.17% a year, solar PV 0.5%", "wind 1.6% a year, solar PV 0.5%",
                                     "wind 5.4% a year, solar PV 0.8%")


def test_the_late_start_and_households_words_say_which_contracts_and_lines():
    """unbuilt.late_starts moves allocation-round contracts only; who_pays holds the RO's share in every scenario."""
    assert "allocation-round" in s("unbuilt_start_late")[2]
    assert all("RO" in v for v in s("households_share"))


def test_the_fixture_is_the_frozen_1_2_2_file():
    import hashlib
    assert hashlib.sha256(V122.read_bytes()).hexdigest().startswith("0cd2e1d3ddb70a5f")


def test_no_number_moves_from_1_2_2_and_only_setting_words_change():
    """On any machine: numbers to 10 significant figures (a rebuild on another kind of machine differs in the last
    binary digits only, CHANGELOG 1.2.2), whole numbers exactly; the words that change are setting keys only."""
    from test_keys_1_2_2 import same
    old, new = json.loads(V122.read_text())["figures"], frozen()
    assert sorted(new) == sorted(old)  # no key added or lost
    moved = {k for k in old if not same(new[k], old[k])}
    assert moved and all(k.startswith("bracket.") and ".setting." in k for k in moved)
    assert all(isinstance(old[k], str) and isinstance(new[k], str) for k in moved)  # words only, no number


def test_the_saved_proof_shows_every_number_exactly_unchanged_in_the_committed_file():
    """docs/figures-1.2.2-vs-1.2.3.csv, written from the committed 1.2.3 file: every key `same` (value and type exactly)
    or `words` (a setting's words changed); none `added` or `moved`."""
    import csv
    rows = list(csv.DictReader((figures.FILE.parent.parent / "docs" / "figures-1.2.2-vs-1.2.3.csv").open()))
    old = json.loads(V122.read_text())["figures"]
    assert sorted(r["key"] for r in rows) == sorted(old)
    for r in rows:
        assert r["v1.2.2"] == repr(old[r["key"]])
        if r["status"] == "same":
            assert r["v1.2.3"] == r["v1.2.2"]
        else:
            assert r["status"] == "words" and isinstance(old[r["key"]], str) and ".setting." in r["key"]


def test_only_the_version_moves_in_the_meta():
    old, new = json.loads(V122.read_text())["meta"], json.loads(V123.read_text())["meta"]
    assert (old["version"], new["version"]) == ("1.2.2", "1.2.3")
    assert {k for k in old if new[k] != old[k]} == {"version"}
