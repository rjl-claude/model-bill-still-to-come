# What 1.2.5 changes (VAT's zero rate), 13 Nov 2026

1.2.4 charged 5% VAT on households' part of the bill in every year. 1.2.5 charges 0% from 1 October 2026 to 30 June 2027 and 5% otherwise, by days in each calendar year (2026: 5% on 273 of 365 days; 2027: 5% on 184 of 365 days). The zero rate in law runs to 31 March 2027 (SI 2026/987); Budget 2026 announced it runs to 1 July 2027, and the model counts announced Budget measures (conductor's ruling, 11 Nov 2026, aios-harness#236).

Every key, old and new: `docs/figures-1.2.4-vs-1.2.5.csv`, from the 1.2.4 file (`tests/fixtures/figures-1.2.4.json`) and the 1.2.5 file (`results/figures.json`, full run on the Mac Mini from a clean copy, 13 Nov 2026).

## Counts

- 7,184 keys in 1.2.4; 7,197 in 1.2.5.
- **256 moved.**
- **13 added**: the two rates, the six period, source and basis words, the three "had the zero rate ended on 31 March 2027" keys, and the Northern Ireland upper bound (a number and its words).
- **6,928 unchanged**: 6,031 identical, and 897 the same to 10 significant figures. Those 897 differ only in their last binary digits, because the Mac Mini's chip (arm64) rounds differently from this machine's (x86_64); see 1.2.2.

## The headline figures (£bn, 2024 prices; old → new, difference)

- Whole bill, cash: 172.45 → 172.34 (−£110.3m)
- Range, cash: low 126.74 → 126.63 (−£110.3m); high 221.89 → 221.78 (−£119.1m)
- Whole bill, Green Book present value: 145.60 → 145.50 (−£108.3m); range 124.48 → 124.39 (−£94.4m) to 173.31 → 173.19 (−£116.9m)
- Whole bill, hurdle-rate present value: 111.57 → 111.46 (−£105.0m); range 96.53 → 96.44 (−£91.6m) to 127.24 → 127.13 (−£113.3m)
- Households: 59.20 → 59.09 (−£110.3m). Businesses (103.76) and taxpayers (9.49) do not move.
- VAT line: 2.82 → 2.71 (−£110.3m); in 2026, 0.163 → 0.122 (−£41.1m); in 2027, 0.140 → 0.070 (−£69.2m). Green Book 2.35 → 2.25; hurdle 1.76 → 1.66.
- Bill in 2026: 13.16 → 13.12 (−£41.1m); in 2027: 12.44 → 12.37 (−£69.2m).
- Built: 93.38 → 93.28 (−£97.5m); not yet built: 79.07 → 79.06 (−£12.8m).
- Bill without the two nuclear stations: 110.23 → 110.13 (−£98.3m).
- Each bracket's ends move down by £91.6m to £123.6m; each swing by at most £23.0m. No bracket's rank changes.
- The model has no per-household key, so there is no per-household figure to move.

## New figures

- Had the zero rate ended on 31 March 2027, as in law: the bill would be £34.8m higher, £172.38bn, and the VAT line £2.74bn.
- Northern Ireland: the order leaves Northern Ireland at 5%. The model has no split of payers by area, so it charges 0% on every household. The Renewables Obligation (RO) line includes the Northern Ireland stations. At most £5.9m (`vat.zero_rate.northern_ireland_upper_bound.cash`) is VAT that 5% on households' part of those stations would have kept. It is an upper bound, because Northern Ireland's certificates can be presented in Great Britain. The other lines (Contracts for Difference, Feed-in Tariffs, Capacity Market, Hinkley Point C, Sizewell C) cover Great Britain only (conductor's ruling, 13 Nov 2026).

## What does not move

- Every scheme line's own whole: the CfD, the RO, FiT, the Capacity Market, Hinkley Point C, Sizewell C and biomass bridging.
- Every split between households and businesses before VAT, the Exchequer's share, the manufacturers' exemption, all checks, counts, ranks, last years, price paths, rates and bracket settings.
- VAT's and the bill's negative years (those years are 2042 and later).
- VAT from 2028 on.

## Sources for the period

- In law: the Value Added Tax (Supplies of Domestic Electricity) Order 2026, SI 2026/987, made 7 Sep 2026 (`data/raw/legislation/`, art. 1(2)). On 13 Nov 2026, legislation.gov.uk listed no other order with that title, so no extending order had been made.
- Announced: Budget 2026, 28 Oct 2026 (`data/raw/hmt/budget-2026.pdf`, para 2.48 and Box 3.A: "until July 2027"); policy costings (`data/raw/hmt/AB26_Policy_Costing.pdf`, p.12: "effective from 1 October 2026 until 1 July 2027", Exchequer −£755m in 2026-27 and −£305m in 2027-28).
