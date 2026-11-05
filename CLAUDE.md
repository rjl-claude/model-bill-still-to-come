<!-- Reviewed with Richard, 5 Nov 2026 (aios-harness#88) -->

# model-bill-still-to-come

The model behind Report No. 2, *The Price of the Climate Bill*. It builds only **the bill still to come**: what contracts already signed oblige Britain's bill-payers and taxpayers to pay for climate policy on electricity, from 1 Jan 2026 to each contract's end, in 2024 prices. The bill already paid (2002 to 2025) comes from the Subsidy Clock, not from here. It is chapter 12 of `/srv/aios/projects/report-series/price-of-the-climate-bill/outline.md`.

## Who uses it (Richard, 5 Nov 2026)

- The Report 2 paper: every figure read from the frozen results by key, never typed in.
- Report 3: takes Report 2's contracted total unchanged, as one line of its own total.
- Richard's questions, including figures he quotes in his own writing.

## Rules for using it (Richard, 5 Nov 2026)

- Quotable figures come from the frozen version only, and the answer names that version. "What if" runs are allowed but labelled **not the published figure**.
- Until the freeze (build stage 7) there is no frozen version: every figure is provisional and is called that.
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
