# Hand example: present values of a three-year stream (aios-harness#84, Stage 5)

Rulings: point 4 (valuation date 1 Jan 2026), point 8 (the Green Book's discount rate; since 1.1.0 its 2026 edition as revised 28 Oct 2026, para 6.54: 3.00% real for years 1 to 30, 2.50% for 31 to 75, aios-harness#255; DESNZ hurdle rates, real pre-tax, fact 11). Richard, 5 Nov: 2026 is year 0 (the Green Book's own convention: not discounted); a technology with no 2025 DESNZ rate takes the nearest one.

## The stream

One fixed offshore wind contract, cash in 2024 prices: 2026 **£10.0m**, 2027 **£20.0m**, 2028 **-£5.0m** (it pays back).

## Green Book, 3.00%

| Year | t | Factor 1/1.03^t | Cash £m | PV £m |
|---|---|---|---|---|
| 2026 | 0 | 1.000000 | 10.0 | 10.000 |
| 2027 | 1 | 0.970874 | 20.0 | 19.417 |
| 2028 | 2 | 0.942596 | -5.0 | -4.713 |
| | | | **25.0** | **24.704** |

The factors match the Green Book's own Table 8 (para 6.57) to four places: 1.000, 0.9709, 0.9426, 0.9151, 0.8885, 0.8626 for years 0 to 5.

## Hurdle rate, fixed offshore 8.9% (DESNZ 2025, Table 6, medium)

| Year | t | Factor 1/1.089^t | Cash £m | PV £m |
|---|---|---|---|---|
| 2026 | 0 | 1.000000 | 10.0 | 10.000 |
| 2027 | 1 | 0.918274 | 20.0 | 18.365 |
| 2028 | 2 | 0.843226 | -5.0 | -4.216 |
| | | | **25.0** | **24.149** |

## The Green Book step

3.00% for years 1 to 30 (2027-2056), 2.50% for years 31 to 75 (2057 on): factor for 2056 = 1/1.03^30 = **0.411987**; for 2057 = 0.411987 / 1.025 = **0.401938**; for 2099 (year 73) = 0.411987 / 1.025^43 = **0.142481**. The Green Book's 2.25% from year 76 is past the model's end. (1.0.0 to 1.0.2 used the earlier 3.5% and 3.0%: 0.356278, 0.345901, 0.099951.)

## Rates by technology (point 8; Richard, 5 Nov)

- 2025 rates (Table 6 and Annex A, medium, 2035 on): solar and onshore wind **7.6%**; fixed offshore wind and gas **8.9%**; floating offshore wind, tidal stream and geothermal **10.1%**.
- No 2025 rate, nearest: nuclear (Hinkley Point C, Sizewell C, nuclear in the Capacity Market) at Sizewell C's licence WACC, **6.73%** real (fact 7, 30); hydro and small wind and solar (FiT, RO) **7.6%**; every other fuelled or firm technology (biomass, waste, ACT, AD, landfill and sewage gas, CHP, diesel, storage, DSR, interconnectors) **8.9%**.
- Rows with no technology take their line's rate: VAT is its year's rate of households' part of a line, so its present value is that rate of that part's present value, year by year (5% to 1.2.4; from 1.2.5, `who_pays.vat_rate`: 0% from 1 Oct 2026 to 30 Jun 2027 by days, so 5% x 273/365 in 2026, 5% x 184/365 in 2027, 5% after); the Exchequer and exemption rows take the cash-weighted factor of their line's own rows that year.

The same stream at nuclear's 6.73%: 10.000 + 20 x 0.936944 - 5 x 0.877863 = **£24.350m**.
