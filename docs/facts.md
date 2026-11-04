# Facts the bill still to come rests on (aios-harness#63)

4 Nov 2026. Each fact with its saved source (under `data/raw/`, in MANIFEST.jsonl) and page or clause. "Open" means not yet confirmed from a saved source; the ticket that needs it carries it.

## Hinkley Point C (CfD, November 2022 consolidated; `hpc/hinkley-point-c-contract-for-difference-november-2022.pdf`)

1. **Strike price.** "The Initial Strike Price is £89.50/MWh (expressed in Money of the Year for the Base Year)" (cl. 11.1). Clause 14.1: if the *Sizewell C Condition* is not met on or before the Reactor One Start Date, the strike rises by £3/MWh (indexed) from that date, and falls back by £3 from the day the condition is met.
2. **The Sizewell C Condition** (cl. 1.1) is the earlier of (A) Sizewell C entering "a FiT Contract for Difference (or equivalent support)" and meeting any State aid condition, and (B) the first nuclear-island concrete pour at Sizewell C. Sizewell C took its final investment decision on 22 July 2025 under a regulated asset base licence, not a CfD (`sizewell-c/szc-fid-vfm-assessment.pdf`; licence special conditions v7, 19 Jul 2025). Whether the licence counts as "equivalent support" is not stated in any saved source. **For Richard to rule** (central £89.50 or £92.50 until first nuclear concrete).
3. **Term.** Each reactor runs to the 35th anniversary of the *earlier* of its Start Date and the last day of its Target Commissioning Window (cl. 5). Target commissioning dates: Reactor One 1 May 2025, Reactor Two 1 Nov 2025; each window is four years (cl. 2.1, 2.2), so they end 30 Apr 2029 and 31 Oct 2029, extended day for day only for the delays listed in cl. 2.3. So a reactor that starts after its window is paid for fewer than 35 years. **For Richard to rule** (whether any extension is assumed).
4. **Generation cap.** The contract expires when 910,000,000 MWh have been paid for (cl. 1.1 "Contracted Generation Cap", cl. 6.1).
5. **Market reference price** is the baseload (season-ahead) reference price (cl. 12), not the hourly day-ahead price.
6. **Start.** EDF's 2025 results (Feb 2026) put Unit 1's first power in 2030 (New Civil Engineer, 20 Feb 2026; World Nuclear News). Unit 2: not given in those reports. Open: EDF's own release, to save.

## Sizewell C

7. **Cost at final investment decision:** "around £38 billion (2024 prices)" (Sizewell C, FID announcement, 22 Jul 2025; web). Licence thresholds: Original Lower Regulatory Threshold £40,509,000,000 and Higher Regulatory Threshold £47,720,000,000, real 2024/25, construction-index prices; initial WACC 6.73% real CPIH (licence special conditions v7, definitions). The value-for-money assessment calls the LRT the "central" and the HRT the "remote" planning assumption (`sizewell-c/szc-fid-vfm-assessment.pdf`, para 24).

## CfD negative-price rules (standard terms, `cfd-terms/`)

8. **AR1 (Aug 2014 terms):** no negative-price rule; when the hourly reference price is negative the generator is paid strike minus a negative price. The Investment Contracts (FIDeR, 2014) are taken to be the same: open, to confirm from `fider-IC_*.zip` in #67.
9. **AR2 (Mar 2017) and AR3 (2019):** for intermittent plant, no payment in any run of **six or more consecutive hours** of negative day-ahead price ("Intermittent Rolling Negative Price Period"); baseload plant, twelve or more.
10. **AR4, AR5, AR6, AR7:** no payment in **any hour** of negative price ("Intermittent Negative Price Period": one or more settlement units).

## Hurdle rates

11. DESNZ hurdle rates are real pre-tax: "Unless stated otherwise, all hurdle rates in this report are expressed in real pre-tax terms" (BEIS/CEPA *Cost of capital update*, 2020, p.7; the basis the 2025 rates update). The 2025 rates: *Electricity Generation Costs 2025*, Table 6 and Annex A "Technical and Cost Assumptions" (`desnz/`). The 2025 CEPA report itself: not found on gov.uk.

## Renewables Obligation

12. **End dates.** Stations first accredited on or before 25 June 2008 get no certificates for their original capacity after **31 March 2027**; later stations none on or after the 20th anniversary of accreditation or 31 March 2037, whichever is earlier (RO Order 2015 art. 44; ROS Order 2009 art. 17A; NIRO 2009 art. 18A; in `model-subsidy-book/data/raw/legislation/`, to copy in #70). The build plan's "20 years or March 2037" misses the 2027 cut-off.
13. **Taxpayers' share.** 75% of the domestic share of the RO funded by the Exchequer in 2026-27, 2027-28 and 2028-29, from 1 April 2026; domestic share "approximately 41 per cent" (DESNZ); Exchequer cost £2,580m, £2,100m, £2,195m (`hmt/Budget_2025-Policy_Costings.pdf`, p.12). Budget 2026 restates it (`hmt/budget-2026.pdf`).
14. **Indexation.** The buy-out price is indexed by CPI from 1 April 2026 (was RPI): 2026-27 buy-out £69.34 (`ofgem/ro-buy-out-price-mutualisation-2026-27.html`; DESNZ decision 28 Jan 2026).

## Who pays

15. **Households' share.** DESNZ's own estimate for the RO: about 41% levied on households (fact 13). Used as the households' share central; DESNZ's projection by sector (EEP Annex F) as the bracket, in #74.
16. **Manufacturers' exemption.** From 1 April 2027, eligible firms in Great Britain are exempt from the indirect costs of the RO, FiT and Capacity Market, with a back payment for 2026-27; about 10,000 firms (`hmt/budget-2026.pdf`). CfD costs are not exempted.

## OBR

17. The OBR's October 2026 forecast (with Budget 2026, 28 Oct 2026) is the latest: `obr/october-2026-*`. Table 4.20 (receipts): RO £8.0bn 2025-26, £8.47bn 2026-27, then £6.6-6.0bn to 2031-32.

## Open (carried to the ticket that needs it)

- Solar decline 0.5%/yr (Jordan & Kurtz, *Prog. Photovolt.* 21, 2013): nrel.gov unreachable from this machine; to save in #70.
- Capacity Market agreement indexation (CPI, Capacity Market Rules): to cite in #72.
- EDF's own release on the Hinkley schedule: #65.
- Investment Contracts' negative-price terms: #67.
