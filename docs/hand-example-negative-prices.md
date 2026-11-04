# Hand-worked example: hours of negative price (aios-harness#67)

Rules (standard terms, `docs/facts.md` 8-10): AR1 and the Investment Contracts are paid through negative hours (the Hornsea Investment Contract has no negative-price clause: checked 4 Nov); AR2-AR3 are not paid in runs of six or more consecutive negative hours; AR4-AR7 are not paid in any negative hour.

## 1. Britain's record, wind (share of wind output in negative MID half-hours)

| | 2017 | 2021 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| any negative | 0.42% | 0.83% | 4.11% | 4.62% | 4.21% |
| in runs of 6 hours or more | 0.13% | 0.00% | 1.41% | 1.45% | 1.85% |

Fit against the wind share (2017-25 without 2022): any = -0.0508 + 0.2936 x share (r² 0.92); six-hour runs = -0.0204 + 0.1150 x share (r² 0.82). Solar against the solar share: any = -0.0878 + 2.326 x share (r² 0.85); six-hour runs = -0.0331 + 0.910 x share (r² 0.72). Clipped to 0-100%. Output-weighted price in those hours, 2023-25: wind -£11.87/MWh, solar -£15.87/MWh.

## 2. Wind in 2030 (share 0.435)

Turned about today's share (0.3154; the fitted line itself at the central slope): any = 7.69%; six-hour runs = 2.96%.

## 3. One year's payment, illustrative offshore farm, 2030

Strike £100/MWh; market £57.91 x discount 0.854 = £49.46/MWh; 1,000,000 MWh.
Without a rule (AR1): (100 - 49.46) x 1,000,000 = **£50.54m**.
AR2-3 rule: less 2.96% x 1,000,000 x (100 - (-11.87)) = £3.31m -> **£47.23m**.
AR4-7 rule: less 7.69% x 1,000,000 x 111.87 = £8.60m -> **£41.94m**.
