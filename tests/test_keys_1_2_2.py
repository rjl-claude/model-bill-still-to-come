"""aios-harness#235 (Report No. 2, plan step 19): version 1.2.2, keys only. It adds the keys the paper's outline
lists as missing (outline-beats.md, "Missing figures": S1 the rates, S2 the bracket settings, S4 each line's last
year, S5 the negative years, S6 the bill without the two nuclear stations), each read from what the model already
holds or a sum of what it already computes, and moves no 1.2.1 figure. Tested at the seam the paper reads: the
frozen results file, by key. From 1.2.3 (the settings' words corrected, aios-harness#235) these checks read the frozen
1.2.2 file, a fixture (tests/test_keys_1_2_3.py checks the current file against it)."""
import json

from billtocome import figures


V122 = figures.FILE.parent.parent / "tests" / "fixtures" / "figures-1.2.2.json"  # results/figures.json at tag v1.2.2


def frozen() -> dict:
    return json.loads(V122.read_text())["figures"]


def test_the_rates_are_read_by_key():
    """S1: the Green Book rates by period (HM Treasury Green Book 2026, para 6.54), the commercial (hurdle) rate by
    technology (DESNZ Electricity Generation Costs 2025, Table 6; Richard 5 Nov for those with no 2025 rate), and
    Sizewell C's allowed return: the licence IWACC, 6.73% real, central; the Green Book rate, 3.00%, after 2039 low."""
    f = frozen()
    assert (f["discount.green_book.years_1_30"], f["discount.green_book.years_31_75"]) == (0.030, 0.025)
    hurdle = dict(solar=0.076, onshore_wind=0.076, offshore_wind_fixed=0.089, offshore_wind_floating=0.101,
                  tidal=0.101, geothermal=0.101, hydro=0.076, small_wind=0.076, nuclear=0.0673, other_firm=0.089)
    assert {k: f[f"discount.hurdle.{k}"] for k in hurdle} == hurdle
    assert f["sizewell_c.allowed_return.central"] == 0.0673
    assert f["sizewell_c.allowed_return.low_after_2039"] == 0.030


BRACKETS = ("annex_m_prices", "build_path", "capacity_market_share", "decline_with_age", "discount_slope",
            "forward_prices_then_annex_m", "hinkley_start", "hinkley_strike", "hinkley_term", "households_share",
            "negative_hours_slope", "output_level", "ro_recycle_value", "sizewell_c_build_cost",
            "sizewell_c_return_after_2039", "unbuilt_abandoned", "unbuilt_start_late")  # the outline's seventeen


def test_each_bracket_s_settings_are_read_by_key():
    """S2: each bracket's input at its low end, central and high end, a number where the input is one, else words,
    for the tornado's labels. A one-sided bracket's other end is the central setting."""
    f = frozen()
    assert sorted({k.split(".")[1] for k in f if k.startswith("bracket.") and ".setting." in k}) == list(BRACKETS)
    s = lambda b: tuple(f[f"bracket.{b}.setting.{end}"] for end in ("low", "central", "high"))  # noqa: E731
    for b in BRACKETS:
        assert all(isinstance(v, (str, int, float)) and v != "" for v in s(b))
    # numbers, as the build plan and the licence set them (scenario.py, the build plan's points 10, 13, 23)
    assert s("hinkley_strike") == (89.50, 89.50, 92.50)  # £/MWh, 2012 prices
    assert s("hinkley_start") == (-1, 0, 2)  # years from the expected start
    assert s("sizewell_c_build_cost") == (38e9, 40.509e9, 47.72e9)
    assert s("sizewell_c_return_after_2039") == (0.030, 0.0673, 0.0673)
    assert [round(v, 3) for v in s("capacity_market_share")] == [0.136, 0.146, 0.156]  # the Clock's 2022, 2025, 2024
    lo, c, hi = s("ro_recycle_value")
    assert lo < c < hi and round(lo, 3) == round(4.42 / 50.05, 3)  # Ofgem SY19 to SY23 recycle shares
    # words: one-sided brackets keep the central words at their other end
    assert s("unbuilt_abandoned")[1:] == (s("unbuilt_abandoned")[1],) * 2 != s("unbuilt_abandoned")[:1] * 2
    assert s("unbuilt_start_late")[0] == s("unbuilt_start_late")[1] != s("unbuilt_start_late")[2]
    assert s("annex_m_prices")[1] == s("forward_prices_then_annex_m")[1] == s("forward_prices_then_annex_m")[2]
    assert len(set(s("annex_m_prices"))) == len(set(s("decline_with_age"))) == len(set(s("build_path"))) == 3


def test_each_line_s_last_year_of_payment_is_read_by_key():
    """S4: the last calendar year in which each line pays (by hand from results/results.csv at 1.2.1, 11 Nov 2026):
    the renewable CfDs to 2052, Hinkley Point C to 2064 (35 years), Sizewell C to 2099 (60 years from 2039)."""
    f = frozen()
    last = dict(cfd_renewables=2052, hinkley_point_c=2064, sizewell_c=2099, ro=2037, fit=2042, capacity_market=2044,
                biomass_bridging=2031)
    assert {k: f[f"{k}.last_year"] for k in last} == last
    assert all(f[f"{k}.{last[k]}.cash"] != 0 and f"{k}.{last[k] + 1}.cash" not in f for k in last)


def test_each_line_s_negative_years_are_read_by_key():
    """S5: the sum of the years in which a line (or the whole bill) pays back, and those years. By hand from
    results/results.csv at 1.2.1 (11 Nov 2026): the renewable CfDs in 2042 and 2045 to 2052, £573.2m; Sizewell C
    from 2072 to 2099, £18,071.1m; the whole bill, every line together, in Sizewell C's years."""
    f = frozen()
    assert round(f["cfd_renewables.negative_years.cash"] / 1e6, 1) == -573.2
    assert round(f["sizewell_c.negative_years.cash"] / 1e6, 1) == -18_071.1
    assert f["cfd_renewables.negative_years.years"] == "2042, 2045-2052"
    assert f["sizewell_c.negative_years.years"] == f["bill.negative_years.years"] == "2072-2099"
    for head in ("cfd_renewables", "sizewell_c", "bill"):
        years = [y for y in range(2026, 2100) if f.get(f"{head}.{y}.cash", 0) < 0]
        assert f[f"{head}.negative_years.cash"] == sum(f[f"{head}.{y}.cash"] for y in years)
    assert f["bill.negative_years.cash"] < f["sizewell_c.negative_years.cash"]  # VAT on the payback too


def test_the_bill_without_the_two_nuclear_stations_is_read_by_key():
    """S6: the bill still to come without Hinkley Point C and Sizewell C, and without the VAT on households' part of
    them (5%, point 18), which falls with them."""
    import pytest
    f = frozen()
    nuclear = ("hinkley_point_c", "sizewell_c")
    vat = 0.05 * sum(f[f"{k}.households.total.cash"] for k in nuclear)
    expected = f["bill.total.cash"] - sum(f[f"{k}.total.cash"] for k in nuclear) - vat
    assert f["bill.without_nuclear.total.cash"] == pytest.approx(expected, rel=1e-12)
    assert round(f["bill.without_nuclear.total.cash"] / 1e9, 1) == 110.2  # £172.5bn less £30.1bn and £31.1bn, less about £1.0bn of VAT


V121 = figures.FILE.parent.parent / "tests" / "fixtures" / "figures-1.2.1.json"  # results/figures.json at tag v1.2.1
NEW = (r"discount\.(green_book\.years_\d+_\d+|hurdle\.[a-z_]+)", r"sizewell_c\.allowed_return\.[a-z0-9_]+",
       r"bracket\.[a-z0-9_]+\.setting\.(low|central|high)", r"[a-z_]+\.last_year",
       r"[a-z_]+\.negative_years\.(cash|years)", r"bill\.without_nuclear\.total\.cash")


def test_the_fixture_is_the_frozen_1_2_1_file():
    import hashlib
    assert hashlib.sha256(V121.read_bytes()).hexdigest().startswith("c96c950e0598b662")


def same(a, b) -> bool:
    """Text, whole numbers and flags exactly; other numbers to 10 significant figures. A rebuild on another kind
    of machine (the Mac Mini, arm64) differs from this one's (x86_64) in the last binary digits only: at most
    7.9e-13 relative over 7,184 keys, 11 Nov 2026 (aios-harness#235)."""
    if isinstance(a, float) or isinstance(b, float):
        return not isinstance(a, bool) and not isinstance(b, bool) and abs(a - b) <= 1e-10 * max(abs(a), abs(b))
    return type(a) is type(b) and a == b


def test_no_1_2_1_figure_moves_and_only_the_new_keys_are_added():
    import re
    old, new = json.loads(V121.read_text())["figures"], frozen()
    assert [k for k in old if k not in new] == []
    assert [k for k in old if not same(new[k], old[k])] == []  # a rebuild on any machine
    added = set(new) - set(old)
    assert [k for k in added if not any(re.fullmatch(p, k) for p in NEW)] == []
    assert len(added) == 12 + 2 + 17 * 3 + 8 + 4 * 2 + 1


def test_only_the_version_and_the_key_units_move_in_the_meta():
    old, new = json.loads(V121.read_text())["meta"], json.loads(V122.read_text())["meta"]
    assert (old["version"], new["version"]) == ("1.2.1", "1.2.2")
    assert {k for k in old if new[k] != old[k]} == {"version", "key_units"}  # same saved sources, same dates
    assert set(old["key_units"]) < set(new["key_units"])
    import re
    for k in set(frozen()) - set(json.loads(V121.read_text())["figures"]):
        assert any(re.fullmatch(p, k) for p in new["key_units"] if p != "default"), k  # every new key has its unit


def test_the_saved_proof_shows_every_1_2_1_key_exactly_unchanged_in_the_committed_file():
    """docs/figures-1.2.1-vs-1.2.2.csv, written from the committed 1.2.2 file: every 1.2.1 key `same` (exactly
    equal, value and type), the rest `added`; its 1.2.1 column is the frozen 1.2.1 file."""
    import csv
    rows = list(csv.DictReader((figures.FILE.parent.parent / "docs" / "figures-1.2.1-vs-1.2.2.csv").open()))
    old = json.loads(V121.read_text())["figures"]
    assert {r["key"]: r["status"] for r in rows if r["key"] in old} == {k: "same" for k in old}
    assert sum(r["status"] == "added" for r in rows) == 82 and len(rows) == len(old) + 82
    assert all(r["v1.2.1"] == repr(old[r["key"]]) == r["v1.2.2"] for r in rows if r["key"] in old)
