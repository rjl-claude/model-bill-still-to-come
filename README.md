# The bill still to come

The model behind the second half of Report No. 2, [*The Price of Climate Policy*](https://richardlyon.net/research/price-of-climate-policy/), by Richard Lyon: what obligations already granted (contracts, accreditations and entitlements) commit Britain's bill-payers and taxpayers to pay for climate policy on electricity, from 1 January 2026 to each obligation's end.

In the version the report uses, **1.4.0** (tag `v1.4.0`), the bill still to come is **£172.3bn** in 2024 prices before discounting. Changing each disputed assumption in turn moves it between £126.6bn and £221.8bn. It is modelled throughout, because it rests on prices and output that have not happened yet.

The first half of the report, the bill already paid from 2002, comes from a separate model: [model-bill-already-paid](https://github.com/rjl-claude/model-bill-already-paid).

## What it counts

| Line | What is owed |
|---|---|
| Renewables Obligation | certificates to accredited stations, to each station's last year |
| Contracts for Difference, renewable | top-ups under signed contracts, built and not yet built, net of money paid back |
| Hinkley Point C | its Contract for Difference |
| Sizewell C | the revenue its licence allows, to the end of its operating period |
| Feed-in Tariffs | tariffs to accredited installations |
| Capacity Market | the share of agreements counted as a cost of climate policy |
| Biomass bridging contracts | the bridging contracts |
| VAT | on households' share |

Every row is split by who pays (households, businesses, taxpayers) and by year. Eighteen disputed assumptions are each changed on their own to give the range.

## Run it

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/). The inputs are saved in `data/`, each with its source and checksum, so the model runs from a clone.

```sh
git checkout v1.4.0
tools/test.sh                              # every test passes
uv run --frozen python tools/results.py    # reruns every figure: results/figures.json (about five minutes)
```

`results/figures.json` is the one file the report reads, by key (7,222 keys in 1.4.0). No figure in the report is typed: each is printed from its key in this file, and the report names the version and the file's fingerprint.

## Where things are

```
src/billtocome/   the model: one call, run(Scenario()), and a module for each line
data/             the saved inputs
results/          the results at this version: figures.json and the tables behind it
docs/             the design (design.md), the facts and their sources (facts.md), a worked example
                  by hand for each line (hand-example-*.md), and what moved between versions
tests/            the test suite
CHANGELOG.md      every version and what changed
```

## Versions

A frozen version is never changed. A correction is a new numbered version, with a note in `CHANGELOG.md` of what changed and by how much. The archived copy of 1.4.0 is on Zenodo: [10.5281/zenodo.24449423](https://doi.org/10.5281/zenodo.24449423).

## Licence

MIT (see `LICENSE`). The saved inputs in `data/` are their publishers' own, kept here so the figures can be rerun; `docs/facts.md` names each source.
