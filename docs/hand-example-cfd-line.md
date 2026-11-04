# Hand-worked example: the CfD line (aios-harness#68)

All money in 2024 CPIH prices. Code: `src/billtocome/cfd_line.py`.

## 1. East Anglia One phase 2 (AR1, offshore wind), 2030

| Step | Working | Value |
|---|---|---|
| Output | 1,122,200 MWh (own 2023-25 record, 2024's age) x 0.984^(2030-2024) | 1,018,691 MWh |
| Strike | £163.68 (2024 cash, CPI-indexed) x CPI/CPIH factor 0.99306 | £162.54/MWh |
| Market | Annex M baseload, reference, 2030, in 2024 CPIH prices | £57.91/MWh |
| Discount | own 0.946 moved with the wind share to 2030 (`hand-example-discount.md`) | 0.8837 |
| Negative hours | AR1: none | 0 |
| **Top-up** | (162.54 - 57.91 x 0.8837) x 1,018,691 | **£113.4m** |

(The 3 Nov example gave £119.7m: it had no decline with age, no inflation-measure gap and a fixed 94.5% discount.)

## 2. Drax bridging contract, 2028

Output at the 27% cap: 4 x 645 MW x 8,760 h x 0.27 = 6,102,216 MWh. Strike £109.90 (2012) x 91.20/65.45 = £153.14 (2024), x CPI/CPIH 0.9949 = £152.36. Market £59.06.
**(152.36 - 59.06) x 6,102,216 = £569.3m.** Top-up only: if the market rose above the strike, nothing is paid back. (DESNZ estimated about £470m a year; the OBR £527m in 2027-28: both on higher market prices.)

## 3. Joins and checks

- **Join with the Clock.** Clock 2025, CfD renewables: £2.54bn (2024 prices). Model 2026: £2.51bn. No step.
- **Hinkley's cap.** Central output over both terms: 877 TWh, under the 910 TWh cap, so the cap does not bind at central.
- **LCCC's two-year forecast (base case, Apr 2027 - Sep 2028): fails the 15% test, explained.** Over Apr 2027 - Mar 2028 LCCC forecasts £1.82bn cash (about £1.64bn in 2024 prices) on 44.3 TWh; the model gives about £2.75bn on about 59 TWh. Two causes: (a) price: LCCC uses the market's forward prices, £108-152/MWh for winter 2026-27 (`forecast_market_reference_prices.csv`), against Annex M's £75/MWh for 2026, so its top-up per MWh is about £41 cash against the model's £56; (b) volume: the model starts new contracts on LCCC's expected dates and holds output at each farm's 2023-25 record, about a third more than LCCC's quarters. Recorded in `explanations.yaml` for #77.
