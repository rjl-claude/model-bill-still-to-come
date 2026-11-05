# Hand example: present values of a three-year stream (aios-harness#84, Stage 5)

Rulings: point 4 (valuation date 1 Jan 2026), point 8 (Green Book 3.5% real to year 30, 3.0% after; DESNZ hurdle rates, real pre-tax, fact 11). Richard, 5 Nov: 2026 is year 0 (the Green Book's own convention: not discounted); a technology with no 2025 DESNZ rate takes the nearest one.

## The stream

One fixed offshore wind contract, cash in 2024 prices: 2026 **£10.0m**, 2027 **£20.0m**, 2028 **-£5.0m** (it pays back).

## Green Book, 3.5%

| Year | t | Factor 1/1.035^t | Cash £m | PV £m |
|---|---|---|---|---|
| 2026 | 0 | 1.000000 | 10.0 | 10.000 |
| 2027 | 1 | 0.966184 | 20.0 | 19.324 |
| 2028 | 2 | 0.933511 | -5.0 | -4.668 |
| | | | **25.0** | **24.656** |

## Hurdle rate, fixed offshore 8.9% (DESNZ 2025, Table 6, medium)

| Year | t | Factor 1/1.089^t | Cash £m | PV £m |
|---|---|---|---|---|
| 2026 | 0 | 1.000000 | 10.0 | 10.000 |
| 2027 | 1 | 0.918274 | 20.0 | 18.365 |
| 2028 | 2 | 0.843226 | -5.0 | -4.216 |
| | | | **25.0** | **24.149** |

## The Green Book step

3.5% for years 0-30 (2026-2056), 3.0% from year 31: factor for 2056 = 1/1.035^30 = **0.356278**; for 2057 = 0.356278 / 1.03 = **0.345901**; for 2099 (year 73) = 0.356278 / 1.03^43 = **0.099951**.

## Rates by technology (point 8; Richard, 5 Nov)

- 2025 rates (Table 6 and Annex A, medium, 2035 on): solar and onshore wind **7.6%**; fixed offshore wind and gas **8.9%**; floating offshore wind, tidal stream and geothermal **10.1%**.
- No 2025 rate, nearest: nuclear (Hinkley Point C, Sizewell C, nuclear in the Capacity Market) at Sizewell C's licence WACC, **6.73%** real (fact 7, 30); hydro and small wind and solar (FiT, RO) **7.6%**; every other fuelled or firm technology (biomass, waste, ACT, AD, landfill and sewage gas, CHP, diesel, storage, DSR, interconnectors) **8.9%**.
- Rows with no technology take their line's rate: VAT is 5% of households' part of a line, so its present value is 5% of that part's present value, year by year; the Exchequer and exemption rows take the cash-weighted factor of their line's own rows that year.

The same stream at nuclear's 6.73%: 10.000 + 20 x 0.936944 - 5 x 0.877863 = **£24.350m**.
