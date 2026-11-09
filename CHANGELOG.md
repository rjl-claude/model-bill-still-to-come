# Changelog

Each version is a git tag; its `results/figures.json` is the file products read by key. A version never changes an older one.

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
