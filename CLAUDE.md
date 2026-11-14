<!-- Reviewed with Richard, 5 Nov 2026 (aios-harness#88) -->

# model-bill-still-to-come

The model behind Report No. 2, *The Price of the Climate Bill*. It builds only **the bill still to come**: what contracts already signed oblige Britain's bill-payers and taxpayers to pay for climate policy on electricity, from 1 Jan 2026 to each contract's end, in 2024 prices. The bill already paid (2002 to 2025) comes from `/srv/aios/projects/model-bill-already-paid` (the Subsidy Clock's sums; its results file `results/clock.json`), not from here. It is chapter 12 of `/srv/aios/projects/report-series/price-of-the-climate-bill/outline.md`.

## Who uses it (Richard, 5 Nov 2026)

- The Report 2 paper: every figure read from the frozen results by key, never typed in.
- Report 3: takes Report 2's contracted total unchanged, as one line of its own total.
- Richard's questions, including figures he quotes in his own writing.

## Rules for using it (Richard, 5 Nov 2026)

- Quotable figures come from the frozen version only, and the answer names that version. "What if" runs are allowed but labelled **not the published figure**.
- The frozen version is **1.2.6** (git tag `v1.2.6`; 1.2.6 the Northern Ireland VAT bound over 1 Oct 2026 to 31 Mar 2027 only, as Budget 2026 expects the relief there from April 2027, every other key as 1.2.5; 1.2.5 VAT on households' electricity at 0% from 1 Oct 2026 to 30 Jun 2027, SI 2026/987 with Budget 2026's announced extension, 5% otherwise; 1.2.4 the households' share words, every number as 1.2.3; 1.2.3 the bracket settings' words corrected, every number as 1.2.2; 1.2.2 keys only, every figure as 1.2.1, adding the keys Report No. 2's outline lists as missing: the rates, the bracket settings, each line's last year, the negative years, the bill without the two nuclear stations; 1.2.1 self-contained, every figure as 1.2.0: the Capacity Market shares read from its own saved copy of the v4-s43 Clock export; 1.2.0 put Sizewell C's low return after 2039 at the Green Book 2026 rate, 3.00%, every other figure as 1.1.0; 1.1.0 put the Green Book present values on the Green Book 2026's rates, 3.00% then 2.50%, every other figure as 1.0.2; 1.0.2 corrected three check notes and saved seven sources; 1.0.1 added keys to 1.0.0's figures; see `CHANGELOG.md`; cut-off date 9 Nov 2026, valuation date 1 Jan 2026; `results/figures.json`, pinned in `report-series/model-register.yaml`). Figures from any later uncommitted run are provisional and are called that.
- Answer by running the model, never from memory or sums in chat. Name the version and the lines covered (for example: CfD renewables plus Hinkley, central case, 2024 prices).
- Report 3 pins the frozen version it uses (version and file fingerprint), as `report-series/model-register.yaml` does for Report 1's model. It moves only when Richard moves the pin.
- A mistake found after the freeze is fixed in a new numbered version with a note of what changed and by how much. The old version stays as it was. Richard decides on any correction notice in the paper.

## Commands

- Run Python here: `uv run --frozen python`
- All tests: `tools/test.sh` (every test must pass). One file: `tools/test.sh tests/test_cfd.py`

## Outside this folder

- Rulings behind every choice (points 1 to 26): `/srv/aios/projects/report-series/price-of-the-climate-bill/bill-still-to-come-build-plan.md`
- Terms: `/srv/aios/projects/report-series/GLOSSARY.md`. Decisions: `/srv/aios/projects/report-series/docs/adr/`
- Build progress and build rules: map #61 on GitHub `richardjlyon/aios-harness`
