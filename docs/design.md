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
| **Brackets** | `BRACKETS`: name, low Scenario, high Scenario | every bracket in the build plan, declared once; a test fails if any bracket moves nothing | built: 17 declared, `LATER` empty; run and ranked by `brackets.tornado()` |
| **Scheme line** (seam, 5 adapters) | `build(scenario) -> rows` | CfD (renewables, Hinkley, bridging), RO, FiT, Capacity Market, Sizewell C | all five on the seam (`model.Line`) |
| **Prices** | `annex_m_path(case)` and `forward_then_annex_m()` give price tables for Scenario; `cpih`, `cpi_to_cpih` | data, not a seam: any price path is just another table | built (`prices.annex_m_path`, `prices.forward_then_annex_m`) |
| **Market response** (seam, 2 adapters) | `for_contract(year, technology, rule, own) -> (discount, unpaid share)` | simple British fit now; Grid Sim later (point 7) | one interface (`MarketResponse.for_contract`, adapter `SimpleFit`) |
| **Who pays** | `split(rows, scenario) -> rows` | households/businesses/taxpayers, VAT line, RO taxpayer share, manufacturers' exemption | built (`who_pays.py`) |
| **Present value** | `present_value(results, rate) -> table` | Green Book (3.00%/2.50%, since 1.1.0), hurdle rate by technology, to 1 Jan 2026 | built (`present_value.py`) |
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
| 4 | Who pays (split, VAT, RO taxpayer share, exemption) | shares add to each whole; VAT = 5% of households' share (from 1.2.5, the year's rate) | Sonnet |
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

- Every row split households 34.9% / businesses (point 18, 19), except the RO, split on DESNZ's 41% domestic share of RO costs in every scenario (point 27, Richard 9 Nov); Exchequer 75% of households' RO share Apr 2026-Mar 2029; BICS £600m a year Apr 2027-Mar 2035 plus the 2026-27 back payment, shared by businesses' part of RO, FiT and the whole CM levy; VAT 5% of households' part, its own line (from 1.2.5, 0% from 1 Oct 2026 to 30 Jun 2027: see the 1.2.5 section). Each scheme line's whole unchanged.
- Totals 2026-2099 (2024 prices), frozen 1.0.0 (cut-off 9 Nov 2026): households £59.2bn, businesses £103.8bn, taxpayers £9.5bn; whole bill £172.5bn cash, £141.2bn Green Book, £111.6bn hurdle; range £132.9bn to £221.9bn (from 1.2.0, £126.7bn to £221.9bn: Sizewell C's low return at 3.00%, aios-harness#257). Point 27 moved households from £57.0bn and the whole from £172.3bn (VAT on the RO moved to households); the range ends were £132.8bn and £221.8bn before point 27 and the re-fetch. The re-fetch moved no central total at one decimal place. Before point 27: households £57.0bn (incl. VAT £2.7bn), businesses £106.6bn, taxpayers £8.7bn.
- The Budget's Exchequer cost uses DESNZ's 41% domestic share of the RO, as the model now does (point 27); the model's is 4-13% lower, from its RO being below the OBR's (within 15%, no explanation needed). Before point 27 it was 18-26% lower.

## Stage 5 (5 Nov): present values and the results file

- Year 0 is 2026, not discounted (Green Book convention; Richard, 5 Nov). Green Book 3.5% to 2056, 3.0% from 2057 in 1.0.0 to 1.0.2; from 1.1.0, 3.00% to 2056 and 2.50% from 2057 (Green Book 2026, revised 28 Oct 2026, para 6.54; Richard, 11 Nov, aios-harness#255). The figures below are 1.0.0's.
- Hurdle rates (point 8, DESNZ 2025 medium): solar, onshore 7.6%; fixed offshore, gas 8.9%; floating, tidal, geothermal 10.1%. No 2025 rate, nearest (Richard, 5 Nov): nuclear 6.73% (Sizewell C licence WACC); hydro, small wind and solar 7.6%; other fuelled or firm 8.9%. VAT's PV is 5% (from 1.2.5, the year's rate) of households' PV of its line; Exchequer and exemption rows take their line's factor.
- Keys `line[.built][.payer].period.measure` (measures cash, pv_green_book, pv_hurdle), every combination with rows; `tools/results.py` writes `results/figures.json` with the run's dates and MANIFEST hash (`results/` in git from the freeze, 9 Nov 2026; `meta` names the model, version, valuation and cut-off dates and MANIFEST hash). Paper source writes `{{key}}`; `figures.typed` lists any money or % typed outside a key.
- Central, 2026-2099, £bn 2024 prices (cash / Green Book / hurdle): whole bill 172.3 / 141.1 / 111.5; built 93.3 / 81.8 / 69.6; not yet built 79.1 / 59.4 / 41.9.

## Stage 6 (5 Nov): brackets and the tornado

- Five brackets added, each one Scenario input: forward prices to Mar 2027 then Annex M (2026 £81.59, 2027 £72.84/MWh vs Annex M £75.26, £62.66); decline with age as one setting (gentler: wind 0.17%/yr, Hamilton 2020; steeper: wind 5.4%/yr, Hughes 2012, solar 0.8%/yr, Jordan & Kurtz mean; facts 33-34); output level high end, CfD wind and solar at DESNZ 2023 load factors by commissioning year (fact 35; RO and FiT on their own records, Richard 5 Nov); build path, ends Falling Behind (lowest) and Holistic Transition (highest) of the four FES pathways, all above central EEP; Sizewell C return after 2039, 3.5% to 6.73% (Richard 5 Nov: the Green Book rate to 6.73%; from 1.2.0 the low end is the Green Book 2026 rate, 3.00%, para 6.54; Richard, 11 Nov, aios-harness#257).
- `brackets.tornado()`: each bracket's ends run, the rest central; whole bill at each end, swing, ranked; also at both present values. `figures.bracket_keys`: `bracket.<name>.<low|high|swing|rank>.<measure>`, `range.<low|high>.<measure>`; `tools/results.py` writes them into `results/figures.json` (about five minutes).
- Central £172.3bn cash; range £132.8bn (Sizewell C return 3.5%; £126.74bn at 3.00% from 1.2.0) to £221.8bn (Annex M low prices); Green Book £120.7-166.8bn; hurdle £96.5-127.2bn. Largest swings: Annex M prices £74.6bn, Sizewell C return £39.6bn, Sizewell C cost £33.9bn, decline £19.7bn, output £15.1bn.

## Version 1.2.5 (13 Nov 2026): VAT's zero rate

- `who_pays.vat_rate(year)`: 0% (`VAT_ZERO`) for the days of the calendar year inside `VAT_ZERO_WINDOW`, 1 Oct 2026 to 30 Jun 2027 (end exclusive, 1 Jul 2027), 5% (`VAT`, VAT Act 1994 Sch. 7A) for the rest, by days as the Exchequer's and BICS windows are (`share_of_year`). 2026: 5% x 273/365; 2027: 5% x 184/365; 5% from 2028. The VAT line's cash and both present values use it.
- Period in law (`VAT_ZERO_IN_LAW`, 1 Oct 2026 to 31 Mar 2027): SI 2026/987 art. 1(2), Great Britain only (art. 3; Northern Ireland stays at the reduced rate, art. 4). The extension to 30 Jun 2027: Budget 2026 (para 2.48, Box 3.A; policy costings p.12, "until 1 July 2027"), announced, not law at the cut-off; counted as the model counts the Budget's other announced measures (conductor's ruling, 11 Nov 2026). legislation.gov.uk showed only SI 2026/987 on 13 Nov 2026: no extending order.
- Keys (`figures.vat_keys`): the rates; each period's words and source; the VAT line and bill had the zero rate ended on 31 Mar 2027 (each VAT row times its year's rate in law over its rate as modelled; £34.8m more); and the Northern Ireland upper bound.
- Northern Ireland (conductor's ruling, 13 Nov 2026): the model has no payer area and zero-rates every household's part. All lines but the RO are Great Britain only; the RO line holds the NIRO stations. So `vat.zero_rate.northern_ireland_upper_bound.cash` (£5.9m) is 5% x the days zero-rated x households' part of the Northern Ireland stations' rows: an upper bound on the overstatement, because their certificates can be presented in Great Britain. (From 1.2.6, £4.0m over 1 Oct 2026 to 31 Mar 2027 only, with the full reason: see the 1.2.6 section.)
- Central effect: whole bill £172.45bn to £172.34bn cash (−£110.3m), households £59.20bn to £59.09bn; nothing else in the split moves. Every key: `docs/figures-1.2.4-vs-1.2.5.csv` and `.md`.

## Version 1.2.6 (14 Nov 2026): Northern Ireland's VAT window

- The fault (checker of 1.2.5, 14 Nov 2026, section D): the Northern Ireland bound counted 5% to 30 Jun 2027. SI 2026/987 keeps Northern Ireland at the reduced rate only for supplies from 1 Oct 2026 to 31 Mar 2027 (art. 1(2), art. 4; its explanatory note: "to maintain the reduced rate of VAT on the supply of domestic electricity in Northern Ireland"). Budget 2026 para 3.4 (printed p.43, pdf p.49): "To support households in Northern Ireland, the government is providing funding for the Northern Ireland Executive to provide comparable support with household electricity bills. Extended VAT relief is expected to apply in Northern Ireland from April 2027." Para 6.210 (printed p.132, pdf p.138): the zero rate "will be extended for a further three months, to 1 July 2027. This is expected to apply UK-wide from April 2027." The model counts the Budget's announced extension for Great Britain (conductor's ruling, 11 Nov 2026), so on the same basis Northern Ireland is at 0% from 1 Apr 2027 to 30 Jun 2027.
- `figures.vat_keys`: `ni_kept` is 5% less `vat_rate(y, VAT_ZERO_IN_LAW)` (the order's window) on households' part of the Northern Ireland stations' RO rows: 2026 on 92 of 365 days, 2027 on 90. £5.92m to £4.00m cash. The Budget's "comparable support" for Northern Ireland from October 2026 to March 2027 is funding to the Executive, not VAT, and is not part of this bill.
- Why it is an upper bound, from the model's saved data: Northern Ireland households pay through their suppliers' NIRO obligation (Northern Ireland's supply times its obligation level), not for the certificates Northern Ireland's stations happen to make, and certificates cross the border: the NIRO 2009's "renewables obligation certificate" includes a GBROC (art. 2, `legislation/nisr-2009-154-NIRO-2009-latest.xml`), and the registers below show Northern Ireland certificates presented far beyond Northern Ireland's obligation. In the year to March 2025 Northern Ireland's obligation was 0.192 ROCs/MWh on 7.26 TWh, about 1.39 million certificates (`ofgem/RO_24-25_SY23_Annual_Report.pdf`, Figure 5.1 and para 5.3, pdf p.52-53); Northern Ireland's stations were issued 5.61 million certificates for that year (`ofgem-rer/RO_Certificates_09-11-2026_04-10.csv`, Country Northern Ireland, compliance period 2024/2025); and 6.09 million Northern Ireland certificates were redeemed against that year (`ofgem-rer/RO_Compliance_Certificates_09-11-2026_04-50.csv`, compliance period 23). So at least 4.7 million (77%) were presented by suppliers in Great Britain, where the zero rate applies, and Northern Ireland's own share of these stations' cost is well under the bound. The key stays an upper bound, not a central estimate.
- **ASSUMPTION: the zero rate is spread over each year by days, not by households' use in each month.** 2026 pays 5% on 273 of 365 days and 2027 on 184 of 365, as if households' climate levies fell evenly through the year. Households use more electricity in winter, and the zero-rated months are October to June, so a spread by use could make the cut a few £m larger (the checker of 1.2.5, section C). The size and direction depend on when each levy falls in the year, which is not sourced. The same holds for the Northern Ireland bound and the "zero rate in law only" keys.
- Only the two Northern Ireland keys and that key's unit in `key_units` move; every other key equals 1.2.5 (`tests/test_version_1_2_6.py`, `docs/figures-1.2.5-vs-1.2.6.csv` and `.md`).
