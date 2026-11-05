# The bill still to come: model design (agreed with Richard, 4 Nov 2026, after a roast)

Delivers the agreed report design (build plan points 1-26). Vocabulary: Matt Pocock's codebase-design (module, interface, seam, adapter, depth).

## One call

```python
results = run(Scenario())          # central
results = run(Scenario(case="FFP_High"))   # one bracket
```

`run` is the deep module: every scheme line, every year from the valuation date, one tidy table back. Everything a report figure needs is computed from that table; nothing else is called by the paper.

**Results** (one row per item-year; `run` also saves the in-between tables behind them: contracts, output, prices, discounts, for open data, paper ch. 11): `line` (CfD renewables, Hinkley Point C, biomass bridging, RO, FiT, Capacity Market, Sizewell C, VAT), `item` (contract, station or group), `technology`, `built`, `payer` (households, businesses, taxpayers), `year`, `cash` (£, 2024 CPIH prices). Plus the run's `Scenario`, valuation date, cut-off date and the MANIFEST hash.

## The modules

| Module | Interface | Behind it | State |
|---|---|---|---|
| **Scenario** | one frozen record of every contested choice, central by default, including the price path as a table (year -> £/MWh) | the 26 rulings as defaults | built (`scenario.py`) |
| **Brackets** | `BRACKETS`: name, low Scenario, high Scenario | every bracket in the build plan, declared once; a test fails if any bracket moves nothing | built: 9 declared; 7 more in `LATER` with their stage |
| **Scheme line** (seam, 5 adapters) | `build(scenario) -> rows` | CfD (renewables, Hinkley, bridging), RO, FiT, Capacity Market, Sizewell C | CfD, RO on the seam (`model.Line`); FiT, CM, SZC to build |
| **Prices** | `annex_m_path(case)` and `forward_then_annex_m()` give price tables for Scenario; `cpih`, `cpi_to_cpih` | data, not a seam: any price path is just another table | `annex_m_path` built; forward-then-Annex M in stage 6 |
| **Market response** (seam, 2 adapters) | `for_contract(year, technology, rule, own) -> (discount, unpaid share)` | simple British fit now; Grid Sim later (point 7) | one interface (`MarketResponse.for_contract`, adapter `SimpleFit`) |
| **Who pays** | `split(rows, scenario) -> rows` | households/businesses/taxpayers, VAT line, RO taxpayer share, manufacturers' exemption | to build |
| **Present value** | `present_value(results, rate) -> table` | Green Book (3.5%/3.0%), hurdle rate by technology, to 1 Jan 2026 | to build |
| **Figures** | `figure(key) -> number`, keys built from the table (line.year.measure, line.total.measure ...), not a fixed list | the one results file the paper reads by key | to build |
| **Checks** | `check(results) -> report`; fails on an unexplained gap over 15% | Clock 2025 join, OBR (calendarised), LCCC; `explanations.yaml` | built (`checks.py`) |

Inputs stay as now: `tools/fetch.py`, MANIFEST with sha256, `docs/facts.md`.

## Seams that earn their place

- **Scheme line**: five adapters, one interface. A new scheme (No. 4's changes) is one more adapter; `run` and everything after it do not change.
- **Market response**: two adapters (fit, stand-in today; Grid Sim later).
- Not seams: Prices (data), Who pays, Present value, Figures, Checks (one adapter each).

## What changes in the built code

`cfd_line.Settings` and the keyword arguments on `contracts.load` and `ro.build` fold into `Scenario`; `discount.SimplePattern` and `NegativeHours` sit behind one Market response interface. No method changes: central totals must not move (CfD £71.4bn, RO £47.8bn, 2024 prices).

## Stages (one short session each; stop for Richard's check at each ✓)

| Stage | Builds | Test that ends it | Model |
|---|---|---|---|
| 0 | Every fact still open, saved with its source: households' share now and projected, the manufacturers' exemption size, a forward price curve, solar decline 0.5%/yr, Capacity Market indexation | each in `docs/facts.md` with saved source and page | Sonnet, run alone |
| 1 | Scenario (price path as a table), Brackets list, Scheme line interface, `run`, Results and in-between tables; Checks (Clock 2025 join, OBR calendarised, LCCC, `explanations.yaml`); CfD and RO moved onto it | central totals unchanged (CfD £71.4bn, RO £47.8bn); checks run on CfD and RO; 65 tests pass ✓ | Opus |
| 2 | FiT line, Capacity Market line | hand examples; checks pass or explained ✓ | Opus (FiT: 869,000 installations) |
| 3 | Sizewell C line from the licence formula | one year by hand from the licence; checks ✓ | Opus |
| 4 | Who pays (split, VAT, RO taxpayer share, exemption) | shares add to each whole; VAT = 5% of households' share | Sonnet |
| 5 | Present value and Figures (keys from the table) | three-year stream by hand; no printed figure outside the file ✓ | Sonnet |
| 6 | Brackets run and the tornado (incl. forward-then-Annex M) | each bracket moves only its input; none moves nothing; range = extremes ✓ | Sonnet |
| 7 | Freeze on the cut-off date | re-fetch; MANIFEST and results carry both dates; all checks pass or explained ✓ | Sonnet |

Each stage starts from map #61 and this file, reads only the modules it touches, and ends with `tools/test.sh` passing, a commit, and a one-line entry on the map.

## Roast (4 Nov): what changed

Checks moved to stage 1 (not last); a fact stage 0 so no build stage researches; prices as data, not a seam; a dead-bracket test; figure keys built from the table; FiT on Opus; in-between tables saved for open data. Kept: one `run`, one Scheme line seam, one Scenario.

## Stage 1 (5 Nov): what it settled in the code

- Slope brackets (discount, negative hours): each end of the fitted slope's 95% interval (eight years, t = 2.447); a gentler end past zero is held flat.
- The Clock's RO record ends in 2024, so the RO join sets the model's 2026 against 2024.
- Checks, central: RO within 7% of the OBR every year 2026-31; CfD joins the Clock within 2%; CfD runs 1.3-2.5 x the OBR and 2.3 x LCCC, each explained by the market price (`explanations.yaml`).
- Still missing for stage 6: the steeper decline rate from Hughes (REF 2012) is not in `docs/facts.md`.
