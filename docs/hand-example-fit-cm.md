# Hand examples: one FiT group, one Capacity Market agreement (aios-harness#81, Stage 2)

## FiT: retrofit roof-top solar, 0-4 kW, higher rate, eligible October-December 2015, exporting, ending December 2035

Group `PV-R/0-4/06H-2|export|2035-12`: 13,377 installations, 47,535.993 kW (Ofgem installation report, Sep 2026). Eligibility date (later of application and commissioning) 2 to 31 December 2015; 20 years (eligible after 1 Aug 2012), so the last ends 30 December 2035.

1. **Tariff.** Code `PV-R/0-4/06H-2`: Ofgem's table, April 2015-March 2016 sheet, Photovoltaic, Retrofit, 0-4 kW, Higher, 1 Oct-31 Dec 2015: **19.63 p/kWh** (2026-27, CPI-adjusted).
2. **Output per kW.** DUKES 6.3, solar PV load factor 2023-25: (10.50 + 9.22 + 11.08) / 3 = 10.267%, so 899.36 kWh/kW. All installations at DUKES load factors: PV 5,148.258 MW x 10.267%, wind 771.851 MW x 24.687%, hydro 268.408 MW x 37.700%, AD 302.363 MW x 62.513%, x 8,760 h = 8.841 TWh, against Ofgem's 7.97 TWh in SY15 (para 3.6): scale **0.90143**. So **810.71 kWh/kW** in 2024.
3. **2030 output.** 47,535.993 x 810.71 x 0.995^6 (point 17, from 2024) = **37,396,085 kWh**.
4. **Indexation.** Calendar 2030 = 1/4 of scheme year 2029-30 + 3/4 of 2030-31; each scheme year's tariff is 2026-27's x CPI of the previous calendar year / CPI 2025: 0.25 x 1.12538/1.03361 + 0.75 x 1.14906/1.03361 = **1.10597**.
5. **Generation payments.** 37,396,085 x £0.1963 x 1.10597 = **£8.119m** cash.
6. **Export payments.** Ofgem's 1.47 TWh exported in SY15 is 20.181% of exporting installations' output; export tariff 7.64 p (eligible after 1 Aug 2012): 37,396,085 x 0.20181 x £0.0764 x 1.10597 = **£0.638m** cash.
7. **In 2024 prices:** (8.119 + 0.638) / CPIH 1.18035 = **£7.42m**, plus the group's share of qualifying costs.

Check on the whole line: SY15 output at 2025-26 tariffs gives generation payments of £1,709m; Ofgem's SY15 actual, at 2024-25 tariffs (one RPI uplift lower, 3.5% Dec 2024, ONS CZBH), was £1,732m, so the model is about 5% low at SY15 tariffs (£1,651m). Export payments £97.8m against Ofgem's £94.1m.

## Capacity Market: IFA interconnector, 2026-27 four-year-ahead auction

Agreement `CAN-2026-IFA_19-001` (NESO register, 28 Oct 2026): 1,260 MW, delivery year 2026/27 only; clearing price **£63/kW/yr**; base period Winter 2021/2022.

1. **Base CPI** (Oct 2021-Apr 2022, ONS D7BT): (113.6 + 114.5 + 115.1 + 114.9 + 115.8 + 117.1 + 120.0) / 7 = **115.857**.
2. **CPI of the winter before the delivery year** (Oct 2025-Apr 2026): (139.8 + 139.5 + 140.1 + 139.5 + 140.1 + 141.0 + 142.1) / 7 = **140.300**.
3. **Delivery-year payment:** 1,260 x 1,000 kW x £63 x 140.300/115.857 = **£96.13m** cash.
4. **Calendar years:** October-December carries 27.37% of a delivery year's GB demand (NESO demand record, delivery years 2022/23-2024/25): £26.31m in 2026, £69.82m in 2027.
5. **2026 in 2024 prices:** 26.31 / CPIH 1.07197 = £24.54m (whole levy); net zero's share 14.607% (Clock engine v4-s43, 2025): **£3.59m**.

## Checks

- FiT: the OBR publishes no FiT forecast after 2025-26 (Table 4.20 shows 0); the checks are the Clock join and the SY15 payments above.
- Capacity Market: the whole levy (before net zero's share) against the OBR, calendarised; 2025-26 at £1.6bn, the OBR's own footnote figure (Table 4.20 note 1: outturn not yet in the ONS's numbers).
