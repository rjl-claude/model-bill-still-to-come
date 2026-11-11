# Changelog

Each version is a git tag; its `results/figures.json` is the file products read by key. A version never changes an older one.

## 1.2.2 (11 Nov 2026), keys only

Adds the keys Report No. 2's outline lists as missing from this model (`report-series/price-of-the-climate-bill/outline-beats.md`, "Missing figures": S1, S2, S4, S5, S6; aios-harness#235, plan step 19). Each is read from what the model already holds or summed from what it already computes. A patch number, as 1.0.1: **no figure moves**. `tests/test_keys_1_2_2.py` checks the 7,102 keys of the frozen 1.2.1 file (`tests/fixtures/figures-1.2.1.json`, sha256 c96c950e…) are all present and exactly equal, and that the 82 added keys are only these. The key-by-key comparison is saved as `docs/figures-1.2.1-vs-1.2.2.csv` (every key: its 1.2.1 value, its 1.2.2 value, `same` or `added`). In the meta only `version` and `key_units` move (units for the new keys). Same inputs (MANIFEST unchanged) and dates; in `results/` only `figures.json` changes (written with `tools/results.py --reuse-tornado`).

- **S1, the rates:** `discount.green_book.years_1_30` 3.00%, `.years_31_75` 2.50% (`present_value.GREEN_BOOK`); `discount.hurdle.<technology>` for solar, onshore wind, fixed and floating offshore wind, tidal, geothermal, hydro, small wind, nuclear and other firm plant (`present_value.hurdle_rate` on a technology the model holds, `figures.HURDLE_TECHNOLOGIES`); `sizewell_c.allowed_return.central` 6.73% (the licence IWACC, `szc.IWACC`) and `.low_after_2039` 3.00% (the return bracket's low end).
- **S2, the bracket settings:** `bracket.<name>.setting.<low|central|high>` for all seventeen brackets: the one input each bracket moves (`scenario.BRACKETS`), at each end and central; a one-sided bracket's other end is central. A number where the Scenario holds one the reader can use (Hinkley's strike, £/MWh 2012 prices; its start, years from expected; Sizewell C's build cost and return after 2039; the Capacity Market share; the RO recycle value), else words (`figures.SETTING_WORDS`, written from each input's own notes): these words are new in this version and are labels, not sources.
- **S4, last years:** `<line>.last_year`, the last year each line's cash is not zero: renewable CfDs 2052, Hinkley Point C 2064, Sizewell C 2099, RO 2037, FiT 2042, Capacity Market 2044, biomass bridging 2031 (VAT 2099).
- **S5, negative years:** `<line|bill>.negative_years.cash`, the sum of the years a line (or the whole bill) is below zero, read from its year keys, and `.years`, those years as words: renewable CfDs −£573.2m in "2042, 2045-2052"; Sizewell C −£18.07bn in "2072-2099"; VAT −£315.4m and the whole bill −£18.39bn in the same years. Only lines with such years have the keys.
- **S6, without nuclear:** `bill.without_nuclear.total.cash` £110.23bn: the bill without Hinkley Point C, Sizewell C and the VAT on households' part of them (the VAT rows name their line).

## 1.2.1 (11 Nov 2026), self-contained

A clean copy of the tag, plus the saved inputs `data/raw/MANIFEST.jsonl` lists out of git, now reruns on any machine (spec user story 24). At 1.2.0 the Capacity Market line (`src/billtocome/cm.py`) read its net-zero shares from another model's working folder by absolute path (`/srv/aios/projects/model-bill-already-paid/reference/engine/v4-s43.json`), so a clean copy failed on the Mac Mini (found in aios-harness#231). A patch number: **no figure moves**.

- **The Capacity Market shares** are read from the model's own saved copy, `data/raw/model-bill-already-paid/v4-s43.json`: the Clock export of Report No. 1's engine release v4-s43, as model-bill-already-paid keeps it (`reference/engine/v4-s43.json`), fetched by commit (cc9866b4) and listed in `MANIFEST.jsonl` with its sha256, e1cf23af…, the fingerprint `report-series/model-register.yaml` pins. Byte for byte the file 1.2.0 read. A new engine release is never applied by itself: it is saved here, cut as a new version, and the pin moves on Richard's yes.
- **One test read outside the model:** `tests/test_manifest.py` checked copied files against model-ending-subsidy-contracts' checksum list by absolute path. That list is saved as `tests/fixtures/model-ending-subsidy-contracts-SHA256SUMS` (sha256 8e65c005…, checked).
- New test `tests/test_self_contained.py`: no file in `src/`, `tools/` or `tests/` names a path outside the model, and the shares load from the saved copy at the pinned fingerprint.
- `tests/test_version_1_2_1.py` checks the 7,102 keys and values are exactly 1.2.0's (`tests/fixtures/figures-1.2.0.json`, sha256 0ef2f7e4…); only `meta.version` and `meta.manifest_sha256` move (MANIFEST gains one file). In `results/` only `figures.json` and `run.json` change, in those two meta fields (written with `tools/results.py --reuse-tornado`; the full rebuild from a clean copy on the Mac Mini gives the same file).

## 1.2.0 (11 Nov 2026), Sizewell C's low return at the Green Book 2026 rate

The low end of the Sizewell C return bracket after 2039 moves from 3.5% to **3.00%**. Richard set that range on 5 Nov as "the Green Book rate" to 6.73%; the Green Book 2026 (revised 28 Oct 2026, para 6.54; saved in `data/raw/hmt/`) sets that rate at 3.00%, so the low end follows it. Found in aios-harness#255; Richard's ruling, choice 1, 11 Nov 2026 (aios-harness#257). It is a cash input (the allowed return on Sizewell C's asset base after 2039), not a discount rate. A minor number, by the reasoning of 1.1.0: patch versions keep every figure, and this version's figures differ.

**Only the keys built from that low end change**: `tests/test_version_1_2_0.py` checks the 7,102 keys are 1.1.0's and that exactly seven keys differ from the frozen 1.1.0 file (`tests/fixtures/figures-1.1.0.json`, sha256 af2634cf…): the bracket's low ends and swings in cash, Green Book and hurdle present value, and the low end of the cash range. Only `meta.version` moves in the meta (same saved sources, same dates). In `results/` only `figures.json` and the Sizewell C row of `tornado.csv` change (full rebuild, `tools/results.py`, brackets rerun).

- Sizewell C return bracket, low end: cash **£126.74bn** (was £132.87bn); Green Book £126.81bn (was £129.33bn); hurdle £104.29bn (was £105.27bn). Swing: cash £45.71bn (was £39.58bn); Green Book £18.79bn (was £16.27bn); hurdle £7.27bn (was £6.30bn). Still second by cash swing, after the Annex M prices.
- Cash range £126.74bn to £221.89bn (was £132.87bn to £221.89bn).
- Unchanged: the cash headline £172.45bn, every central figure, the Green Book range £124.48bn to £173.31bn and the hurdle range £96.53bn to £127.24bn (their low ends are the Annex M prices bracket's), every other bracket, check and count.

## 1.1.0 (11 Nov 2026), the Green Book 2026 discount rates

The Green Book present values move to the rates of the Green Book as published at the cut-off (2026 edition, revised 28 Oct 2026, para 6.54; saved in `data/raw/hmt/`): **3.00% real for years 1 to 30, 2.50% for years 31 to 75** (2.25% from year 76 is past the model's end, year 73). They were 3.5% and 3.0% in 1.0.0 to 1.0.2. Found in the input audit (aios-harness#229); Richard's ruling, choice 1, 11 Nov 2026 (aios-harness#255). Year 0 is still 2026, not discounted; the factors match the Green Book's Table 8 (para 6.57). A minor number, not a patch: 1.0.1 and 1.0.2 each kept every 1.0.0 figure, and this is the first version whose figures differ.

**Only the Green Book present values change**: `tests/test_version_1_1_0.py` checks the 7,102 keys are 1.0.2's and every key not ending `.pv_green_book` is exactly equal to the frozen 1.0.2 file (`tests/fixtures/figures-1.0.2.json`, sha256 e7bf817e…). 2,222 of the 2,281 Green Book keys move; the other 59 are 2026's, not discounted. Only `meta.version` moves in the meta (same saved sources, same dates). In `results/` only `figures.json` and `tornado.csv` change, and in `tornado.csv` only its four Green Book columns; every other CSV is byte for byte as 1.0.2 (full rebuild, `tools/results.py`, brackets rerun).

- Whole bill 2026-2099, Green Book present value: **£145.60bn** (was £141.23bn). Built £83.35bn (was £81.87bn); not yet built £62.25bn (was £59.36bn). Range £124.48bn to £173.31bn (was £120.80bn to £166.86bn). Hinkley Point C £19.25bn (was £17.99bn); Sizewell C £28.62bn (was £27.49bn).
- Unchanged: the cash headline £172.45bn, the cash range £132.87bn to £221.89bn, every hurdle-rate present value, every check and count.
- The Sizewell C return bracket's low end stays at 3.5% as Richard set it on 5 Nov (the Green Book's rate before the revision); it is a cash input, not a discount rate, and is not changed here.

## 1.0.2 (11 Nov 2026), notes and saved sources only

From the input audit (aios-harness#229; Richard's yes, choice 1, 11 Nov 2026). **No key or figure changes**: `tests/test_version_1_0_2.py` checks the 7,102 keys are the 1.0.1 keys and every value is exactly equal to the frozen 1.0.1 file (`tests/fixtures/figures-1.0.1.json`, sha256 e79c8e92…). Only `meta.version` and `meta.manifest_sha256` move. Same cut-off and valuation dates; every CSV in `results/` byte for byte as in 1.0.1 (written with `tools/results.py --reuse-tornado`).

- **Three check notes corrected** in `explanations.yaml` (typed on 5 Nov, before the freeze re-fetched the registers): the LCCC gap now reads 2.33 (was 2.28); the LCCC rerun at £114.50 reads 1.02, "within 3%" (was 0.93, "within 7%"); the Capacity Market Clock join reads 1.60 (was 0.84), and its first reason (the Clock's older 27.7% share) is gone, since the Clock's 2025 (£201m) already counts the 14.6% share. New test `tests/test_explanations.py`: each figure a note types equals its key.
- **Seven sources added to the saved sources** (`data/raw/`, each in `MANIFEST.jsonl` with its fingerprint, and in `tools/fetch.py`): the Department's results of CfD allocation rounds 1 to 7a (eight files, `desnz/cfd-round-results/`); the AR7 reforms government response, July 2025 (20-year terms, para 2.3); the BEIS *Electricity Generation Costs* 2016 report (Table 4); Staffell and Green 2014 (wind decline, 1.6% a year); EDF's 2025 annual results release (Hinkley Point C in 2030; `docs/facts.md` fact 6 now cites it); HM Treasury's Green Book (2026 edition); the VAT Act 1994, Schedule 7A. No figure reads them.

Found, not changed (for Richard): the Green Book as published at the cut-off (revised 28 Oct 2026, para 6.54) sets 3.00% for years 1 to 30, 2.50% for 31 to 75 and 2.25% after. `present_value.py` uses the earlier 3.5% and 3.0%, so the Green Book present values in 1.0.0 to 1.0.2 are on the old rates. The cash figures, the headline included, do not depend on it.

## 1.0.1 (9 Nov 2026), keys only

Adds the keys Report No. 2's paper needs that 1.0.0 held only in its CSVs or check notes (aios-harness#221; spec "Gaps in the bill still to come's keys", Richard's yes 9 Nov). **No 1.0.0 key or value changes**: `tests/test_keys_1_0_1.py` checks every 1.0.0 figure is exactly equal to the frozen 1.0.0 file (`tests/fixtures/figures-1.0.0.json`, sha256 9b80cfb0…). Same inputs (MANIFEST unchanged), same cut-off and valuation dates; every CSV in `results/` is byte for byte as in 1.0.0.

Added (units in the file's `meta.key_units`):

- **The price path:** `price_path.<low|reference|high>.<year>`, 2024 to 2050: DESNZ Annex M baseload, £/MWh in 2024 prices (CPIH), the fossil-price cases FFP_Low, Reference and FFP_High. Reference equals `results/prices.csv`.
- **Contract counts by line:** `<line>.contracts`, `<line>.built.contracts`, `<line>.not_yet_built.contracts`, contracts, accreditations and agreements paying from 1 Jan 2026. FiT counts installations. VAT and the rows that move cost between payers (the Exchequer's RO share, the manufacturers' exemption) are not contracts.
- **The checks:** `check.<check>.<line>.<period>.<model|reference|gap|ratio>` for every row of `checks.check` (OBR, LCCC, the Clock join, the Budget; 33 rows).
- **The written explanations' figures:** `check.obr.cfd.<year>.matching_price` (the flat market price at which the CfD lines meet the OBR), `check.obr.cfd.<year>.not_yet_built_share`, and `check.lccc.cfd_renewables.2026_10_to_2027_03.at_forward_price.ratio` (the model against LCCC at LCCC's winter price).

Found, not changed (for the input audit, aios-harness#229): three figures typed in `explanations.yaml` date from 5 Nov and do not match the frozen model. The LCCC gap reads 2.28 (the model gives 2.33); the LCCC rerun reads 0.93 (1.02; "within 7%" still holds); the Capacity Market Clock join reads 0.84 (1.60, so its first reason no longer applies). Annex E reads the keys, not that prose.

Tools: `tools/results.py --reuse-tornado` rewrites the results from one central run, reading the brackets from `results/tornado.csv` (1.0.1 changed no input, so the 34 bracket runs are not repeated).

## 1.0.0 (9 Nov 2026)

The freeze on the cut-off date (aios-harness#86, #91): every register re-fetched, results in git, tag `v1.0.0`.
