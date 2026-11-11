# Changelog

Each version is a git tag; its `results/figures.json` is the file products read by key. A version never changes an older one.

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
