# What 1.3.0 changes (the price of power after 2050), 17 Nov 2026

Richard's ruling 11b (16 Nov 2026, Report No. 2 rulings sheet, point 11): a case that does not hold the price of power after 2050 at its 2050 level. DESNZ's central path (Annex M) stops at 2050, and the model holds 2050's price, £105.32/MWh, the highest on the path, to 2099. Sizewell C's paybacks, £18.07bn in 2072 to 2099, rest on that. The new case holds instead the average of DESNZ's central path over 2026 to 2050, £75.59/MWh, every year from 2051 to 2099. It is the eighteenth bracket, "Price after 2050", one-sided: its low end is central, its high end the case (lower prices raise the bill). Ruling 16b needs no model change (Richard, 17 Nov 2026: no fair published basis for a return above 6.73% after 2039), so 1.3.0 is 11b only.

Every key, old and new: `docs/figures-1.2.6-vs-1.3.0.csv`, from the 1.2.6 file (`tests/fixtures/figures-1.2.6.json`) and the 1.3.0 run (`results/figures.json`, full run on the Mac Mini, 17 Nov 2026).

## Counts

- 7,197 keys in 1.2.6 and 7,222 in 1.3.0. **25 added**, none removed.
- **16 moved**: the rank of every bracket the new one passes, each down one place (Sizewell C's return after 2039 from 2nd to 3rd, Sizewell C's build cost 3rd to 4th, and so on to households' share, 17th to 18th). Only the price of power (DESNZ's paths), 1st, keeps its rank.
- **7,181 unchanged**, every one identical (both runs are the Mac Mini's).
- In `results/` only `figures.json` and `tornado.csv` (one more row) change.
- In the file's meta only the version (1.2.6 to 1.3.0) and the new keys' units in `key_units` change.

## The case's effect (central → case, cash, 2024 prices)

- The bill still to come: £172.34bn → £221.57bn, **£49.22bn more** (`price_after_2050.path_average.bill.difference.cash`). Green Book present value £145.50bn → £160.43bn (+£14.93bn); commercial rates £111.46bn → £115.26bn (+£3.80bn).
- Sizewell C: £31.08bn → £68.76bn. Its paybacks: **£18.07bn in 2072 to 2099 → £2.85bn in 2089 to 2099**.
- Hinkley Point C (its contract runs to 2064): £30.07bn → £40.53bn. CfD renewables (to 2052): £38.67bn → £38.91bn. VAT on households' part rises with them.
- The range does not move: £221.57bn is just under its high end, £221.78bn (DESNZ's low path), and its low end stays £126.63bn (Sizewell C's return at the Green Book rate). The new bracket's swing, £49.22bn, is the second largest, after the price of power on DESNZ's paths (£74.57bn).

## The 25 added keys

- `brackets.count` (18) and `brackets.count_in_words` ("eighteen"): the paper types "seventeen" today.
- `price_after_2050.held.price` (£105.32/MWh) and `price_after_2050.path_average.price` (£75.59/MWh).
- `price_after_2050.path_average.` `bill.total.cash`, `bill.difference.cash`, `sizewell_c.total.cash`, `sizewell_c.negative_years.cash`, `sizewell_c.negative_years.years` ("2089-2099"), `hinkley_point_c.total.cash`, `cfd_renewables.total.cash`, and `.words`, the case in plain words.
- `bracket.price_after_2050.` `low`, `high` and `swing` at each of the three measures, `rank.cash` (2), and `setting.low`, `setting.central`, `setting.high` (words).

## What does not move

- Every central figure: the whole bill, both present values, the range, households, businesses, taxpayers, every scheme line, split, check, count, setting, year and every other bracket's ends and swing.
