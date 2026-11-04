# Hand-worked example: the Renewables Obligation line (aios-harness#70)

All money in 2024 CPIH prices. Code: `src/billtocome/ro.py`. Law: `data/raw/legislation/` (RO Order 2015 art. 44 and the Scottish and Northern Irish orders).

## 1. Pen y Cymoedd wind farm (R00210RQWA), 2030

| Step | Working | Value |
|---|---|---|
| Certificates | 2023-25 average from Ofgem's register | 547,974 a year |
| End | accredited 17 Oct 2016 (after 25 Jun 2008): 20 years -> 17 Oct 2036, before 31 Mar 2037 | 17 Oct 2036 |
| Decline | wind 1.6%/yr from 2024: x 0.984^6 = 0.9077 | 497,428 in 2030 |
| Buy-out, cash | 2026-27 £69.34, then CPI: 2029-30 £69.34 x 1.0888 = £75.50; 2030-31 x 1.1117 = £77.09; calendar 2030 = 0.25 x 75.50 + 0.75 x 77.09 | £76.69 |
| Recycle | average share of buy-out SY19-SY23 (4.42/50.05, 7.44/50.80, 6.88/52.88, 5.95/59.01, 8.04/64.73) | 11.80% |
| Value per certificate | 76.69 x 1.1180 / CPIH 1.1804 | £72.64 |
| **Payment** | 497,428 x 72.64 | **£36.1m** |

## 2. A station first accredited on or before 25 June 2008

No certificates after 31 March 2027: in 2027 it is paid for 90 days of 365 (24.7%), nothing after. These stations give 22.5% of today's certificates, which is most of the fall from 2026 to 2027.

## 3. Checks

- Today's certificates: 106.7 million a year from 3,597 stations (Ofgem SY23: 105.9 million presented).
- 2026: £7.49bn in 2024 prices, about £8.0bn cash; OBR (Oct 2026) 2026-27: £8.47bn. 2027: about £6.7bn cash; OBR 2027-28: £6.64bn. Within 15%.
- Brackets: recycle at its lowest (8.83%, SY19) and highest (14.65%, SY20) share.
