"""aios-harness#221: version 1.0.1 adds the keys the paper needs that 1.0.0 held only in its CSVs or check
notes (the price path, contract counts, the checks against the OBR, LCCC, the Clock and the Budget), and
changes no 1.0.0 figure. Tested at the seam the paper reads: the frozen results file, by key."""
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from billtocome import figures

FIXTURES = Path(__file__).resolve().parent / "fixtures"
V100 = FIXTURES / "figures-1.0.0.json"  # results/figures.json as frozen at tag v1.0.0


def frozen() -> dict[str, float]:
    return json.loads(figures.FILE.read_text())["figures"]


def test_the_fixture_is_the_frozen_1_0_0_file():
    assert hashlib.sha256(V100.read_bytes()).hexdigest().startswith("9b80cfb0cfca8ea4")  # model-register.yaml


def test_every_1_0_0_figure_is_unchanged():
    old, new = json.loads(V100.read_text())["figures"], frozen()
    assert [k for k in old if k not in new] == []
    assert [k for k in old if new[k] != old[k]] == []  # exactly equal, not approximately


def test_the_price_path_is_read_by_key():
    """Annex M baseload, £/MWh in 2024 prices (CPIH), each case, 2024 to 2050: the reference case is the
    central run's prices.csv; the low and high cases are the Annex M prices bracket's two ends."""
    f = frozen()
    central = pd.read_csv(figures.FILE.parent / "prices.csv").set_index("year").price_2024
    for case in ("low", "reference", "high"):
        assert sorted(int(k.split(".")[2]) for k in f if k.startswith(f"price_path.{case}.")) == list(range(2024, 2051))
    assert all(f[f"price_path.reference.{y}"] == pytest.approx(p, rel=1e-12) for y, p in central.items())
    # as the written explanations print them (explanations.yaml), and test_prices' hand values
    assert [round(f[f"price_path.reference.{y}"], 1) for y in range(2026, 2032)] == [75.3, 62.7, 59.1, 57.2, 57.9, 57.7]
    assert f["price_path.reference.2050"] == pytest.approx(105.32, abs=0.01)
    for y in range(2026, 2050):
        assert f[f"price_path.low.{y}"] < f[f"price_path.reference.{y}"] < f[f"price_path.high.{y}"]
    assert f["price_path.high.2050"] < f["price_path.reference.2050"]  # as Annex M publishes it


def test_contract_counts_by_line_are_read_by_key():
    """`<line>[.built|.not_yet_built].contracts`: the contracts, accreditations and agreements paying from
    1 Jan 2026. FiT counts installations (results/fit_groups.csv `n`), not the model's tariff groups."""
    f = frozen()
    t = pd.read_csv(figures.FILE.parent / "results.csv")
    t = t[~t.item.isin(["Exchequer: 75% of households' share, Apr 2026-Mar 2029", "Manufacturers' exemption (BICS)"])]
    for line, key in figures.LINE_KEYS.items():
        rows = t[t.line == line]
        if key in ("vat", "fit"):
            assert f"{key}.contracts" not in f or key == "fit"
            continue
        assert f[f"{key}.contracts"] == rows.item.nunique()
        for built, name in ((True, "built"), (False, "not_yet_built")):
            n = rows[rows.built == built].item.nunique()
            assert f.get(f"{key}.{name}.contracts", 0) == n
    groups = pd.read_csv(figures.FILE.parent / "fit_groups.csv")
    paying = groups[groups.group.isin(t[t.line == "FiT"].item)]
    assert f["fit.contracts"] == paying.n.sum() == f["fit.built.contracts"]
    # by hand from the 1.0.0 CSVs (9 Nov 2026)
    assert (f["cfd_renewables.contracts"], f["cfd_renewables.built.contracts"]) == (556, 99)
    assert (f["hinkley_point_c.contracts"], f["sizewell_c.contracts"], f["biomass_bridging.contracts"]) == (2, 1, 2)
    assert (f["ro.contracts"], f["fit.contracts"], f["capacity_market.contracts"]) == (3597, 869_215, 3790)


@pytest.fixture(scope="module")
def central():
    from billtocome import model
    return model.run()


def test_every_check_is_read_by_key(central):
    """`check.<check>.<line>.<period>.<model|reference|gap|ratio>`, one set for each row of the checks
    (`checks.check`): the OBR (calendarised, cash), LCCC (cash), the Clock join (2024 prices), the Budget."""
    from billtocome import checks
    f = frozen()
    rows = checks.check(central).rows
    assert len(rows) == 33
    for r in rows.itertuples():
        k = f"check.{figures.slug(r.check)}.{figures.slug(r.line)}.{figures.slug(r.period)}"
        assert (f[k + ".model"], f[k + ".reference"]) == (pytest.approx(r.model, rel=1e-12), pytest.approx(r.reference, rel=1e-12))
        assert f[k + ".gap"] == pytest.approx(r.gap, rel=1e-12) and f[k + ".ratio"] == pytest.approx(r.gap + 1, rel=1e-12)
    # the ratios as the written explanations print them (explanations.yaml `gap`)
    assert [round(f[f"check.obr.cfd.{y}.ratio"], 2) for y in range(2026, 2032)] == [1.75, 2.54, 1.50, 1.32, 1.48, 1.67]
    assert [round(f[f"check.obr.capacity_market_whole_levy.{y}.ratio"], 2) for y in (2030, 2031)] == [0.60, 0.27]
    assert round(f["check.obr.sizewell_c.2027.ratio"], 2) == 1.18


def test_the_written_explanations_figures_are_read_by_key():
    """The figures explanations.yaml prints in prose (Annex E), each now a key: the market price at which the
    model meets the OBR's CfD figure, the not-yet-built share of the model's CfD that year, and the model
    against LCCC when run at LCCC's own winter price (fact 21)."""
    import re
    import yaml
    f = frozen()
    notes = {(e["check"], e["line"], e["period"]): e["explanation"] for e in yaml.safe_load(open(figures.ROOT / "explanations.yaml"))}
    for y in range(2026, 2032):
        text = notes[("OBR", "CfD", str(y))]
        assert f"£{f[f'check.obr.cfd.{y}.matching_price']:.1f}/MWh" in text
        assert f"£{f[f'price_path.reference.{y}']:.1f}/MWh" in text
        built = re.search(r"Contracts not yet built are (\d+)%", text)
        assert built is None or int(built.group(1)) == round(100 * f[f"check.obr.cfd.{y}.not_yet_built_share"])
    assert [round(100 * f[f"check.obr.cfd.{y}.not_yet_built_share"]) for y in range(2028, 2032)] == [12, 24, 37, 53]
    # The LCCC note's "model 0.93 x LCCC" (and its gap, 2.28) date from 5 Nov, before the freeze re-fetched
    # every register; on the frozen inputs the same method gives 1.02 (and 2.33). Its claim, "within 7%",
    # still holds. The stale prose goes to the input audit (aios-harness#229); Annex E reads the keys.
    ratio = f["check.lccc.cfd_renewables.2026_10_to_2027_03.at_forward_price.ratio"]
    assert "within 7% of LCCC" in notes[("LCCC", "CfD renewables", "2026-10 to 2027-03")] and abs(ratio - 1) < 0.07
    assert round(ratio, 2) == 1.02 and round(f["check.lccc.cfd_renewables.2026_10_to_2027_03.ratio"], 2) == 2.33


def test_the_matching_price_meets_the_obr(central):
    """Run the CfD lines at the 2026 matching price, flat: the model then meets the OBR's 2026 figure."""
    from dataclasses import replace
    from billtocome import cfd_line, model
    from billtocome.prices import cpih
    f = frozen()
    p = f["check.obr.cfd.2026.matching_price"]
    r = model.run(replace(central.scenario, prices=((2024, p),)), lines=(cfd_line.build,), split=False)
    assert r.table[r.table.year == 2026].cash.sum() * cpih(2026) == pytest.approx(f["check.obr.cfd.2026.reference"], rel=0.01)


def test_every_key_has_a_stated_unit():
    """The file's meta names the unit of each kind of key (`key_units`, pattern: unit); 1.0.0's keys keep
    `units`. Every key matches exactly one pattern."""
    import re
    data = json.loads(figures.FILE.read_text())
    units = data["meta"]["key_units"]
    assert units["default"] == data["meta"]["units"]
    pats = {p: re.compile(p) for p in units if p != "default"}
    v100 = json.loads(V100.read_text())["figures"]
    for k in data["figures"]:
        hits = [p for p, rx in pats.items() if rx.fullmatch(k)]
        assert len(hits) == (0 if k in v100 else 1), (k, hits)
