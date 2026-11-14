# What 1.2.6 changes (Northern Ireland's VAT window), 14 Nov 2026

1.2.5 sized the VAT the model leaves out for Northern Ireland as if Northern Ireland paid 5% from 1 October 2026 to 30 June 2027. The order (SI 2026/987) keeps Northern Ireland at 5% only to 31 March 2027, and Budget 2026 says "Extended VAT relief is expected to apply in Northern Ireland from April 2027" (para 3.4) and "This is expected to apply UK-wide from April 2027" (para 6.210). The model counts the Budget's extension for Great Britain, so it counts it for Northern Ireland too. 1.2.6 sizes the Northern Ireland figure over 1 October 2026 to 31 March 2027 only and rewords it. Nothing else changes.

Every key, old and new: `docs/figures-1.2.5-vs-1.2.6.csv`, from the 1.2.5 file (`tests/fixtures/figures-1.2.5.json`) and the 1.2.6 file (`results/figures.json`, full run on the Mac Mini from a clean copy, 14 Nov 2026).

## Counts

- 7,197 keys in 1.2.5 and 7,197 in 1.2.6. None added, none removed.
- **2 moved**: the Northern Ireland upper bound and its words.
- **7,195 unchanged**, every one identical (both runs are the Mac Mini's).
- Every other file in `results/` is byte-identical to 1.2.5's.
- In the file's meta only the version (1.2.5 to 1.2.6) and the Northern Ireland key's unit in `key_units` change.

## The two keys (old → new)

- `vat.zero_rate.northern_ireland_upper_bound.cash`: £5.92m → £4.00m (5,923,100.86 → 3,996,218.40; −£1.93m). 5% on households' part of the Renewables Obligation's Northern Ireland stations over 92 days of 2026 and 90 days of 2027, in place of 92 and 181.
- `vat.zero_rate.northern_ireland_upper_bound.words`: rewritten to say what the order does and to when, what Budget 2026 says (paragraphs 3.4 and 6.210), that the model does not split households by area, and the full reason the figure is an upper bound (Northern Ireland's stations were issued 5.6 million certificates in the year to March 2025, Northern Ireland's suppliers had to present 1.4 million, and most of the rest were presented by suppliers in Great Britain, where the zero rate applies).

## What does not move

- Every headline figure: the whole bill (£172.34bn cash), both present values, the range, households, businesses, taxpayers, the VAT line (£2.71bn) and the "zero rate in law only" keys (£34.8m).
- Every scheme line, split, check, count, rank, setting, bracket and year.

## Why the figure is still an upper bound, not a central estimate

Northern Ireland's households pay for the certificates Northern Ireland's suppliers must present: 0.192 per MWh on 7.26 TWh in the year to March 2025, about 1.39 million (Ofgem RO annual report SY23, Figure 5.1 and para 5.3). Northern Ireland's stations were issued 5.61 million certificates for that year (the RO certificates register), and 6.09 million Northern Ireland certificates were redeemed against it (the compliance certificates register). So at least 4.7 million of them went to suppliers in Great Britain, where the zero rate applies. Northern Ireland's real share is well under £4.0m.
