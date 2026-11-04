# Hand-worked example: the farm's discount (aios-harness#66)

Rulings: build plan points 6, 7, 25. Code: `src/billtocome/discount.py`.

## 1. Britain's record (Elexon MID price; Elexon FUELHH and NESO demand data)

| Year | Wind share | Wind earns | Solar share | Solar earns |
|---|---|---|---|---|
| 2017 | 15.9% | 98.9% | 3.56% | 94.2% |
| 2021 | 22.9% | 96.7% | 4.28% | 87.0% |
| 2023 | 30.7% | 94.2% | 5.23% | 89.7% |
| 2024 | 31.55% | 89.9% | 5.33% | 89.6% |
| 2025 | 32.4% | 91.0% | 7.04% | 88.6% |

Fit over 2017-25 without 2022 (eight years): **wind earns 1.081 - 0.522 x share (r² 0.88); solar 1.013 - 2.069 x share (r² 0.30).** The 3 Nov figures (wind 1.087 - 0.551; solar 1.091 - 3.90, r² 0.64) were not saved with their method and are replaced; the wind line agrees, the solar line is weak (a narrow range of shares) and its bracket matters more. 2016 is left out because the MID price begins mid-September 2016 (not a date-format fault, as noted on 3 Nov).

## 2. Future share, wind, 2030 (central)

EEP Annex J renewables, split by FES 2025 "Falling Behind", over EEP total supply: 0.390 in 2024, 0.515 in 2030. Indexed to the measured 2024 share: 0.3155 x 0.515 / 0.390 = **0.435**.

## 3. East Anglia One phase 2 in 2030

Own 2023-25 discount: 0.946 (output-weighted reference price £77.15 / average MID £81.54). Mean measured wind share 2023-25: 0.3154.
0.946 + (-0.522) x (0.435 - 0.3154) = **0.884**. In 2026 (share 0.347): 0.930.

## 4. An offshore farm not yet built, 2030

1.081 - 0.522 x 0.435 = **0.854**.

## 5. Brackets

Steeper and gentler slopes turn the line about today's share (0.3154), so today's discount is unchanged and only the future moves.
