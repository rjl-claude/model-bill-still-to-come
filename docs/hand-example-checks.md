# Hand example: the checks (aios-harness#80, Stage 1)

Build plan point 14: 15% for each line in each year; a larger gap fails unless `explanations.yaml` holds a written explanation for that check, line and period.

## OBR, calendarised (point 4)

The OBR forecasts by financial year (April to March); the model counts calendar years. Calendar year Y takes the last quarter of financial year Y-1 and three quarters of financial year Y:

    calendar Y = 0.25 x FY(Y-1 to Y) + 0.75 x FY(Y to Y+1)

RO, calendar 2026, from OBR October 2026 Table 4.20 (cash, £bn): 2025-26 outturn 8.000, 2026-27 forecast 8.465.

    0.25 x 8.000 + 0.75 x 8.465 = 2.000 + 6.349 = 8.349 (£bn, cash)

The model is in 2024 CPIH prices, so its year is turned back into cash by CPIH (2024 = 1) before the comparison. Years checked: 2026 to 2031 (2031 needs 2031-32, the OBR's last year). Lines: RO; CfD (the three CfD lines together, as the OBR has one CfD row).

## The Clock join (check 2 of the build plan)

The model's first year against the Clock's last measured year, both in 2024 prices. CfD: the Clock's 2025 (`cfd.csv`, `cost_real`) against the model's 2026, all three CfD lines. RO: the Clock's RO record ends in 2024 (`renewables-obligation.csv`), so the model's 2026 is set against 2024, and the report says so.

## LCCC (check 4)

LCCC's forecast of CfD payments (`lccc/forecast_cfd_payments.csv`) covers two quarters: October-December 2026 and January-March 2027. The model's calendar years are spread evenly over their quarters (stated: wind's winter is windier, so this understates the model's winter), giving model = 0.25 x 2026 + 0.25 x 2027, turned into cash by CPIH, against LCCC's sum. Renewables only (LCCC's forecast has no Hinkley or bridging payments in those quarters).

## Pass or fail

    gap = model / reference - 1

|gap| at most 0.15 passes; above it, the check passes only with a matching entry in `explanations.yaml`. A test doubles the model and checks the report fails.
