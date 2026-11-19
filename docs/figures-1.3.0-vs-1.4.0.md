# What 1.4.0 changes (the steep end of output's decline with age), 19 Nov 2026

Richard's ruling of 19 Nov 2026 (aios-harness#268). The "Decline with age" bracket's steep end for wind is now Staffell and Green's upper bound, 1.8% a year (*Renewable Energy* 66 (2014): "Wind turbines are found to lose 1.6 ± 0.2% of their output per year", abstract, p.775), in place of 5.4% a year from a 2012 report the model no longer uses or saves. Solar's steep end (0.8%), the gentle end and the central settings do not change.

Every key, old and new: `docs/figures-1.3.0-vs-1.4.0.csv`, from the 1.3.0 file (`tests/fixtures/figures-1.3.0.json`) and the 1.4.0 run (`results/figures.json`, full run on the Mac Mini, 19 Nov 2026).

## Counts

- 7,222 keys in 1.3.0 and in 1.4.0. None added, none removed.
- **9 moved**, all in the tornado: the decline bracket's steep end and swing at each of the three measures (6), its rank, its steep-end words, and the output level bracket's rank.
- **7,213 unchanged**, every one identical (both runs are the Mac Mini's).
- In `results/` `figures.json`, `tornado.csv` (the decline row) and `run.json` (the MANIFEST fingerprint) change.
- In the file's meta only the version (1.3.0 to 1.4.0) and the MANIFEST fingerprint change (the 2012 report's copy left the saved sources).

## What moved (1.3.0 → 1.4.0)

- `bracket.decline_with_age.high.cash` £158.52bn → £171.24bn; `.pv_green_book` £133.79bn → £144.56bn; `.pv_hurdle` £102.65bn → £110.74bn. Faster decline means less output and so smaller top-ups: the steep end is below the central £172.34bn, now by much less.
- `bracket.decline_with_age.swing.cash` £19.76bn → **£7.04bn**; `.pv_green_book` £16.71bn → £5.94bn; `.pv_hurdle` £12.54bn → £4.45bn.
- `bracket.decline_with_age.rank.cash` 5 → **6**; `bracket.output_level.rank.cash` 6 → 5. No other rank moves.
- `bracket.decline_with_age.setting.high` "wind 5.4% a year, solar PV 0.8%" → "wind 1.8% a year, solar PV 0.8%".

## What does not move

- The bill still to come (`bill.total.*`: £172.34bn cash, £145.50bn Green Book, £111.46bn commercial rates) and every line and year.
- The range (`range.low.*`, `range.high.*`: £126.63bn to £221.78bn cash): its ends are Sizewell C's return after 2039 and DESNZ's low path, not this bracket.
- The decline bracket's gentle end (£178.28bn cash) and its low and central words.
