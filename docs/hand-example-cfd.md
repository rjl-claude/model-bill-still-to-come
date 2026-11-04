# Hand-worked example: one CfD, one year

East Anglia One, phase 2 (LCCC contract CAA-EAS-167), offshore wind, Allocation Round 1. Year 2030. All money in 2024 prices. Sources: LCCC actual generation and payments (fetched 2 Nov 2026); DESNZ EEP 2024-2050 Annex M.

1. **Contract:** payments began 31 Mar 2020; the term is 15 years, so it ends 30 Mar 2035. 2030 is inside it.
2. **Strike price:** £163.68/MWh in 2024 (the contract's own CPI-indexed price, weighted by 2024 output). Indexed to inflation, it stays about £163.68 in 2024 prices every year.
3. **Output:** 1,122 GWh a year (average of 2023-25).
4. **Market price:** Annex M baseload power price for 2030, reference case: 6.03p/kWh = £60.30/MWh.
5. **Offshore wind's discount:** in 2023-25 this farm earned 94.6% of the average market price (its output-weighted reference price against the plain average of the half-hourly MID price), so its price is £60.30 × 0.946 = £57.0/MWh. (From aios-harness#66 this discount moves with the wind share: `docs/hand-example-discount.md`.)
6. **Payment:** (163.68 − 57.0) × 1,122,200 MWh = **£119.7m** in 2030.

Brackets, Annex M low and high: £134.3m (low gas price: £44.0/MWh) and £102.4m (high: £72.4/MWh). A cheaper market means a bigger top-up.

Check against the record: in 2025 the contract was actually paid £112.4m for 1,159 GWh at a reference price of £73.89/MWh.
