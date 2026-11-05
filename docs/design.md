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
| **Brackets** | `BRACKETS`: name, low Scenario, high Scenario | every bracket in the build plan, declared once; a test fails if any bracket moves nothing | built: 12 declared; 5 more in `LATER` with their stage |
| **Scheme line** (seam, 5 adapters) | `build(scenario) -> rows` | CfD (renewables, Hinkley, bridging), RO, FiT, Capacity Market, Sizewell C | all five on the seam (`model.Line`) |
| **Prices** | `annex_m_path(case)` and `forward_then_annex_m()` give price tables for Scenario; `cpih`, `cpi_to_cpih` | data, not a seam: any price path is just another table | `annex_m_path` built; forward-then-Annex M in stage 6 |
| **Market response** (seam, 2 adapters) | `for_contract(year, technology, rule, own) -> (discount, unpaid share)` | simple British fit now; Grid Sim later (point 7) | one interface (`MarketResponse.for_contract`, adapter `SimpleFit`) |
| **Who pays** | `split(rows, scenario) -> rows` | households/businesses/taxpayers, VAT line, RO taxpayer share, manufacturers' exemption | built (`who_pays.py`) |
| **Present value** | `present_value(results, rate) -> table` | Green Book (3.5%/3.0%), hurdle rate by technology, to 1 Jan 2026 | built (`present_value.py`) |
| **Figures** | `figure(key) -> number`, keys built from the table (line.year.measure, line.total.measure ...), not a fixed list | the one results file the paper reads by key | built (`figures.py`, `results/figures.json`) |
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

## Stage 2 (5 Nov): FiT and Capacity Market

- FiT on the Clock's measure (scheme value: generation + export + qualifying costs), not the levelisation fund; 869,279 installations in 6,914 groups; total £16.35bn 2026-42 (2024 prices). Output: DUKES load factors scaled to Ofgem's 7.97 TWh; payments at SY15 tariffs about 5% under Ofgem's.
- Capacity Market: 7,669 live awarded agreements; whole levy within 6% of the OBR 2026-29; net-zero share 14.6% (point 9): £2.99bn 2026-44. 2030-31 below the OBR: auctions not yet held (explained).
- Found: the Clock's published CM data predates its own v4-s43 pin (27.7% share, not 14.6%).

## Stage 3 (5 Nov): Sizewell C

- The levy from the licence: RAB from the Day-1 RAB to £40.509bn at COD (29 Dec 2039), spend spread evenly (not published); return 6.73%; opex, social benefits, cost of debt and FDP from the licence and Ofgem's 2026 values; tax and the other blocks fitted to the First Charging Year's Allowed Revenue (-7.7% of the return).
- 2040-2099 (Richard: choice a): return 6.73% held, 60-year straight-line write-off, BEIS 2016 nuclear running costs, power sold at the Scenario price, tax left out; the levy runs both ways (Sizewell C pays back from 2072 at Annex M prices).
- £31.1bn 2026-2099 (2024 prices): £22.8bn to 2039, £8.3bn after. OBR within 11% 2026 and 2028-31; 2027 explained.

## Stage 4 (5 Nov): who pays

- Every row split households 34.9% / businesses (point 18, 19); Exchequer 75% of households' RO share Apr 2026-Mar 2029; BICS £600m a year Apr 2027-Mar 2035 plus the 2026-27 back payment, shared by businesses' part of RO, FiT and the whole CM levy; VAT 5% of households' part, its own line. Each scheme line's whole unchanged.
- Totals 2026-2099 (2024 prices): households £57.0bn (incl. VAT £2.7bn), businesses £106.6bn, taxpayers £8.7bn.
- The Budget's Exchequer cost uses DESNZ's 41% domestic share of the RO; the model's is 18-26% lower (explained).

## Stage 5 (5 Nov): present values and the results file

- Year 0 is 2026, not discounted (Green Book convention; Richard, 5 Nov). Green Book 3.5% to 2056, 3.0% from 2057.
- Hurdle rates (point 8, DESNZ 2025 medium): solar, onshore 7.6%; fixed offshore, gas 8.9%; floating, tidal, geothermal 10.1%. No 2025 rate, nearest (Richard, 5 Nov): nuclear 6.73% (Sizewell C licence WACC); hydro, small wind and solar 7.6%; other fuelled or firm 8.9%. VAT's PV is 5% of households' PV of its line; Exchequer and exemption rows take their line's factor.
- Keys `line[.built][.payer].period.measure` (measures cash, pv_green_book, pv_hurdle), every combination with rows; `tools/results.py` writes `results/figures.json` with the run's dates and MANIFEST hash (`results/` not in git until the stage 7 freeze). Paper source writes `{{key}}`; `figures.typed` lists any money or % typed outside a key.
- Central, 2026-2099, £bn 2024 prices (cash / Green Book / hurdle): whole bill 172.3 / 141.1 / 111.5; built 93.3 / 81.8 / 69.6; not yet built 79.1 / 59.4 / 41.9.
