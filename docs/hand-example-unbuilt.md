# Hand-worked example: unbuilt contracts (aios-harness#69)

Source: LCCC portfolio and auction outcomes (`data/raw/lccc/`). Code: `src/billtocome/unbuilt.py`.

## Abandonment (termination rate, AR1-AR4)

| Technology | Terminated | Awarded | Rate |
|---|---|---|---|
| Offshore wind | 4 | 40 | 10.0% |
| Onshore wind | 4 | 25 | 16.0% |
| Solar PV | 13 | 69 | 18.8% |
| Remote island wind | 6 | 10 | 60.0% |
| Advanced conversion | 9 | 10 | 90.0% |
| All AR1-AR4 (for technologies with fewer than 10) | 41 | 164 | 25.0% |

An unbuilt offshore farm's payments are cut by 10%; a built farm's are not touched.

## Late starts (delay from 1 April of the delivery year to first payment, contracts generating)

AR1: 2.12 years (22 contracts); AR4: 1.97 (34). AR2 (9), AR5 (6) and AR6 (9) have too few to stand alone. Mature rounds AR1, AR2, AR4 together: (22 x 2.12 + 9 x 1.57 + 34 x 1.97) / 65 = **1.97 years**, used for AR2, AR3, AR5, AR6 and AR7.

Example: an AR7 farm bidding for delivery year 2029-30 is expected from 1 Apr 2029 + 1.97 years = about 19 Mar 2031. If LCCC already expects it later, its date stands. Its 20-year term moves with it.
Result at central data: of 457 unbuilt allocation-round contracts, 376 move, by 0.98 years on average (AR3: none, LCCC's dates are already later; AR7: 1.27 years).
