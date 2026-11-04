# Hand-worked example: prices in 2024 consumer money (aios-harness#64)

Rule (build plan point 5): every figure in 2024 CPIH prices. ONS CPIH and CPI to 2025; the OBR's October 2026 forecast for 2026-2031 (its last full calendar year); after 2031 every measure rises at the same rate, so the gap stops growing. Annex M is in 2024 prices by the GDP deflator (Annex M note 15); it is turned back into cash by Annex M's own deflator path (its row "GDP deflator, annual growth", the one DESNZ used) and then into 2024 CPIH prices. Prices after 2050 are 2050's.

## Indices, 2024 = 1

| | 2025 | 2026 | 2027 | 2031 |
|---|---|---|---|---|
| GDP deflator (Annex M growth: 3.1785%, 1.6721%, 1.9754%, ... 2.1255%) | 1.031785 | 1.049038 | 1.069760 | 1.157676 |
| CPIH (ONS 138.0 / 132.9; then OBR 142.464, 147.172, ..., 160.282 on OBR's 2025 = 138.0) | 1.038375 | 1.071967 | 1.107391 | 1.206038 |
| CPI (ONS 138.4 / 133.9; then OBR 147.557 (2027), 160.054 (2031) on OBR's 2025 = 138.368) | | | 1.102208 | 1.195604 |

## 1. Annex M baseload power price, reference case, 2027

6.4859 p/kWh = £64.859/MWh (2024 prices, GDP deflator).
Factor = GDP deflator / CPIH = 1.069760 / 1.107391 = 0.966019.
**£64.859 x 0.966019 = £62.66/MWh in 2024 CPIH prices.**

## 2. The same in 2035 (after the OBR's horizon)

6.4681 p/kWh = £64.681/MWh. The factor is held at 2031's: 1.157676 / 1.206038 = 0.959900.
**£64.681 x 0.959900 = £62.09/MWh.**

## 3. A CPI-indexed strike price, 2027

East Anglia One phase 2: £163.68/MWh in 2024 cash, then indexed by CPI.
Factor = CPI / CPIH = 1.102208 / 1.107391 = 0.995353.
**£163.68 x 0.995353 = £162.92/MWh in 2024 CPIH prices.** After 2031 the factor stays at 0.991347.

## 4. After 2050

2051's price is 2050's: Annex M baseload, reference, 2050 = 10.9723 p/kWh -> £109.72 x 0.959900 = £105.32/MWh, for every year after 2050.
