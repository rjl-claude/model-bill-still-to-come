# Hand example: who pays the RO in 2028 (aios-harness#83, Stage 4)

Rulings: points 18-20, 22. Facts: 13 (taxpayers' RO share), 18 (households' share), 20 (the exemption). All in 2024 prices.

1. **The whole.** The RO line in 2028: **£5,636.8m**; FiT £1,724.2m; Capacity Market (net zero's share) £460.2m, so its whole levy is 460.2 / 14.607% = £3,150.6m.
2. **Households' share** (point 18): 96,188.8 / 275,527.5 GWh = **34.911%** (DUKES 5.1, 2025). Households £1,967.8m, businesses £3,669.0m.
3. **Taxpayers' RO share** (fact 13): the Exchequer funds 75% of households' share through March 2029, so all of 2028: 0.75 x 1,967.8 = **£1,475.9m** moved from households to taxpayers.
4. **Manufacturers' exemption** (fact 20): £600m cash a year from April 2027, all of 2028: 600 / CPIH 1.13113 = **£530.4m**, shared by businesses' part of each scheme: RO 3,669.0, FiT 1,122.3, Capacity Market (whole levy) 2,050.7, of 6,842.0: RO **£284.4m**, FiT £87.0m, Capacity Market £159.0m of which net zero's share is in the line: £23.2m. Moved from businesses to taxpayers.
5. **RO in 2028, by payer:** households 1,967.8 - 1,475.9 = **£492.0m**; businesses 3,669.0 - 284.4 = **£3,384.5m**; taxpayers 1,475.9 + 284.4 = **£1,760.3m**; together £5,636.8m, the whole.
6. **VAT** (point 18): 5% of what households pay: 0.05 x 492.0 = **£24.6m**, on the VAT line.

## Check

Budget 2025 policy costings, p.12: Exchequer cost £2,580m (2026-27), £2,100m (2027-28), £2,195m (2028-29), cash. The Budget takes the domestic share as "approximately 41 per cent" of the RO; the model's households' share is 34.9% (point 18), so the model's Exchequer cost is lower. The gap is checked and explained (`explanations.yaml`).
