"""Fetch the official records the bill still to come is built from, as published, into data/raw/.

Usage: uv run python tools/fetch.py          (everything)
       uv run python tools/fetch.py files    (the named files and Ofgem's registers only)
Every file is saved unchanged; data/raw/MANIFEST.jsonl records its URL, time and sha256.
Re-run on the day the figures are frozen: the registers change daily.
"""
import datetime as dt
import hashlib
import json
import pathlib
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1] / "data" / "raw"
UA = {"User-Agent": "Mozilla/5.0 (bill-still-to-come data fetch; richardlyon.net)"}

LCCC_API = "https://dp.lowcarboncontracts.uk/api/3/action/package_show?id="
LCCC = [
    "cfd-contract-portfolio-status",
    "auction-outcomes",
    "actual-cfd-generation-and-avoided-ghg-emissions",
    "forecast-cfd-generation",
    "forecast-cfd-payments",
    "forecast-market-reference-prices",
    "advanced-forecast-ilr-tra",
]
NESO_API = "https://api.neso.energy/api/3/action/package_show?id=capacity-market-register"
NESO_KEEP = ("cmu_", "capacity-market-auction-capacity-and-cost", "capacity-market-auction-static-data")
FILES = {
    "desnz/Annex_M_assumptions_growth_price.ods":
        "https://assets.publishing.service.gov.uk/media/6981d725f2ea511998158f75/Annex_M_assumptions_growth_price.ods",
    "obr/march-2026-efo-detailed-forecast-tables-receipts.xlsx":
        "https://obr.uk/download/march-2026-economic-and-fiscal-outlook-detailed-forecast-tables-receipts/",
    "sizewell-c/Nuclear_RAB_Licence_special_conditions_v7.pdf":
        "https://assets.publishing.service.gov.uk/media/687f5ebe8adf4250705c9747/Nuclear_RAB_Licence_Full_Form_Special_Conditions_v7_19072025_redacted.pdf",
    # Added for aios-harness#62. The OBR's latest forecast is October 2026 (Budget, 28 Oct 2026).
    "obr/october-2026-efo-detailed-forecast-tables-economy.xlsx":
        "https://obr.uk/download/october-2026-economic-and-fiscal-outlook-detailed-forecast-tables-economy/",
    "obr/october-2026-efo-detailed-forecast-tables-receipts.xlsx":
        "https://obr.uk/download/october-2026-economic-and-fiscal-outlook-detailed-forecast-tables-receipts/",
    "obr/october-2026-efo-detailed-forecast-tables-expenditure.xlsx":
        "https://obr.uk/download/october-2026-economic-and-fiscal-outlook-detailed-forecast-tables-expenditure/",
    "obr/march-2026-efo-detailed-forecast-tables-economy.xlsx":
        "https://obr.uk/download/march-2026-economic-and-fiscal-outlook-detailed-forecast-tables-economy/",
    "desnz/Annex_J_All_Power_Producer_Generation.ods":
        "https://assets.publishing.service.gov.uk/media/6981d69ef2ea511998158f73/Annex_J_All_Power_Producer_Generation.ods",
    "desnz/Annex_F_final_energy_demand_TWh.ods":
        "https://assets.publishing.service.gov.uk/media/6981d642e8900d4c455f374a/Annex_F_final_energy_demand_TWh.ods",
    "desnz/energy-emissions-projections-report-2024-2050.pdf":
        "https://assets.publishing.service.gov.uk/media/6981e958015e2ba11991bb7a/energy-emissions-projections-report-2024-2050.pdf",
    "desnz/electricity-generation-costs-report-2025.pdf":
        "https://assets.publishing.service.gov.uk/media/69ba657326909a14239612e3/electricity-generation-costs-report-2025.pdf",
    "desnz/electricity-generation-costs-2025-annex-a.xlsx":
        "https://assets.publishing.service.gov.uk/media/69d8efec96c86b7513170229/annex-a-additional-estimates-and-key-assumptions-2025.xlsx",
    "ons/cpih-index-l522.csv":
        "https://www.ons.gov.uk/generator?format=csv&uri=/economy/inflationandpriceindices/timeseries/l522/mm23",
    "ons/cpi-index-d7bt.csv":
        "https://www.ons.gov.uk/generator?format=csv&uri=/economy/inflationandpriceindices/timeseries/d7bt/mm23",
    "hpc/hinkley-point-c-contract-for-difference-november-2022.pdf":
        "https://assets.publishing.service.gov.uk/media/6385d8d6e90e07789ae12720/hinkley-point-c-contract-for-difference-november-2022.pdf",
    "sizewell-c/szc-fid-vfm-assessment.pdf":
        "https://assets.publishing.service.gov.uk/media/687f951dfdc190fb6b84689d/szc-fid-vfm-assessment.pdf",
    "sizewell-c/szc-gsp-supplemental-compensation-agreement-redacted.pdf":
        "https://assets.publishing.service.gov.uk/media/687f7ba937c38e28f384686a/szc-gsp-supplemental-compensation-agreement-redacted.pdf",
    "hmt/budget-2026.pdf":
        "https://assets.publishing.service.gov.uk/media/6ae20b85460c1346f7be784e/E03668986_HMT_Budget_2026_ELAY__2_.pdf",
    "bics/government-response-regulatory-changes-and-scheme-delivery.pdf":
        "https://assets.publishing.service.gov.uk/media/6a4d185b024e48e52f26f47e/government-response-to-bics-consultation-on-regulatory-changes-and-scheme-delivery.pdf",
    "bics/bics-sectoral-consumption-estimates.ods":
        "https://assets.publishing.service.gov.uk/media/6a4d1615b485085e13ca48c2/bics-sectoral-consumption-estimates.ods",
    "ofgem/Feed-in-Tariff-Installation-Report-Part-1-092026.xlsx":
        "https://www.ofgem.gov.uk/sites/default/files/2026-10/Feed-in-Tariff-Installation-Report-Part-1-092026.xlsx",
    "ofgem/Feed-in-Tariff-Installation-Report-Part-2-092026.xlsx":
        "https://www.ofgem.gov.uk/sites/default/files/2026-10/Feed-in-Tariff-Installation-Report-Part-2-092026.xlsx",
    "ofgem/Feed-in-Tariff-Installation-Report-Part-3-092026.xlsx":
        "https://www.ofgem.gov.uk/sites/default/files/2026-10/Feed-in-Tariff-Installation-Report-Part-3-092026.xlsx",
    "ofgem/fit_rates_cpi_update_26_27.xlsx":
        "https://www.ofgem.gov.uk/sites/default/files/2026-03/fit_rates_cpi_update_26_27_20260311102855.xlsx",
    "ofgem/feed_in_tariff_annual_report_sy15.pdf":
        "https://www.ofgem.gov.uk/sites/default/files/2025-12/feed_in_tariff_annual_report_sy15_20251210120852.pdf",
    "ofgem/RO_24-25_SY23_Annual_Report.pdf":
        "https://www.ofgem.gov.uk/sites/default/files/2026-03/RO_24-25_SY23_Annual_Report-20260327121336.pdf",
    "ofgem/ro-buy-out-price-mutualisation-2026-27.html":
        "https://www.ofgem.gov.uk/data/renewables-obligation-buy-out-price-and-mutualisation-threshold-and-ceilings-2026-2027",
    # CfD standard terms by round (negative-price rules; aios-harness#63)
    "cfd-terms/AR1_Generic_CfD_TCs_29_August_2014.pdf":
        "https://assets.publishing.service.gov.uk/media/5a7d5b1ce5274a3356f2bb87/Generic_CfD_TCs__29_August_2014_.pdf",
    "cfd-terms/AR2_CFD_Standard_Terms_V2_13_March_2017.pdf":
        "https://assets.publishing.service.gov.uk/media/5a8198f040f0b62305b8fcff/FINAL_CFD_Standard_Terms_and_Conditions_V2-_13_March_2017_.pdf",
    "cfd-terms/AR3_Standard_Terms_and_Conditions.pdf":
        "https://assets.publishing.service.gov.uk/media/5cc981abe5274a1ac83aff12/AR3-Standard-Terms-and-Conditions.pdf",
    "cfd-terms/AR4_Standard_Terms_and_Conditions.pdf":
        "https://assets.publishing.service.gov.uk/media/61e04175d3bf7f054db937f6/AR4_Standard_Terms_and_Conditions.pdf",
    "cfd-terms/AR5_Standard_Terms_and_Conditions.pdf":
        "https://assets.publishing.service.gov.uk/media/6412f9b8e90e0776a0d957de/ar5-standard-terms-and-conditions.pdf",
    "cfd-terms/AR6_Standard_Terms_and_Conditions.pdf":
        "https://assets.publishing.service.gov.uk/media/65f1ab91133c221271cd3861/cfd-ar6-standard-terms-and-conditions.pdf",
    "cfd-terms/AR7_Standard_Terms_and_Conditions_July_2025.pdf":
        "https://assets.publishing.service.gov.uk/media/688b9b55fdde2b8f73469577/AR7_-_Standard_Terms_and_Conditions_July_2025_84916781.18_.pdf",
    # NESO Future Energy Scenarios, Electricity Supply data table ES1 (wind and solar split; point 25)
    "neso-fes/fes2025_es1_v006.csv":
        "https://api.neso.energy/dataset/549b0667-b533-4748-95bd-f6e13933a47d/resource/6c78a777-b885-4bb6-bc35-8100f9e137a2/download/fes2025_es1_v006.csv",
    "neso-fes/10yo2026_es1_v001.csv":
        "https://api.neso.energy/dataset/549b0667-b533-4748-95bd-f6e13933a47d/resource/b3bf8ac0-d27a-447c-975c-208ae92c0fa5/download/10yo2026_es1_v001.csv",
    # Stage 0 facts (aios-harness#79)
    "desnz/DUKES_5.1.xlsx":
        "https://assets.publishing.service.gov.uk/media/6a6a35d80ddb7e4831c629ef/DUKES_5.1.xlsx",
    "hmt/AB26_Policy_Costing.pdf":
        "https://assets.publishing.service.gov.uk/media/6ae1883fe4367e5c8b0467df/AB26_Policy_Costing.pdf",
    "bics/sau-report-on-bics-2026-07-24.pdf":
        "https://assets.publishing.service.gov.uk/media/6a61f3c49a419980593b2aba/final_report.pdf",
    "bics/pq-17079-bics-budget-2026-07-13.json":
        "https://questions-statements-api.parliament.uk/api/writtenquestions/questions/1925771",
    "lccc/market-reference-prices.html":
        "https://www.lowcarboncontracts.uk/our-schemes/contracts-for-difference/market-reference-prices",
    "lccc/baseload-market-reference-price-winter-2026.html":
        "https://www.lowcarboncontracts.uk/news/baseload-market-reference-price-winter-2026-published",
    "nrel/jordan-kurtz-2012-pv-degradation-rates-nrel-ja-5200-51664.pdf":
        "https://www.osti.gov/servlets/purl/1045052",
    "legislation/uksi-2014-2043-Electricity-Capacity-Regulations-2014-latest.pdf":
        "https://www.legislation.gov.uk/uksi/2014/2043/data.pdf",
    "legislation/uksi-2014-2043-Electricity-Capacity-Regulations-2014-latest.xml":
        "https://www.legislation.gov.uk/uksi/2014/2043/data.xml",
    # Stage 2 (aios-harness#81): FiT output by technology, and the RPI uplift of April 2025
    "desnz/DUKES_6.3.xlsx":
        "https://assets.publishing.service.gov.uk/media/6a6a276f8319ab05f7caa1cf/DUKES_6.3.xlsx",
    "ons/rpi-12-month-rate-czbh.csv":
        "https://www.ons.gov.uk/generator?format=csv&uri=/economy/inflationandpriceindices/timeseries/czbh/mm23",
    # Stage 3 (aios-harness#82): Sizewell C's Day-1 RAB and first Allowed Revenue, Ofgem's 2026 PCFM values,
    # nuclear running costs (BEIS 2016; the 2020 and 2025 editions publish none)
    "sizewell-c/DESNZ-Day-1-RAB-and-Y1-AR-Letter-to-Ofgem.pdf":
        "https://www.ofgem.gov.uk/sites/default/files/2025-11/DESNZ-Day-1-RAB-and-Y1-AR-Letter-to-Ofgem.pdf",
    "sizewell-c/Annex-Sizewell-C-variable-value-proposal-to-modify.xlsx":
        "https://www.ofgem.gov.uk/sites/default/files/2026-10/Annex-Sizewell-C-variable-value-proposal-to-modify.xlsx",
    "sizewell-c/SZC-PCFM-variables-determination-v2.2.pdf":
        "https://www.ofgem.gov.uk/sites/default/files/2026-10/SZC-PCFM-variables-determination-v2.2.pdf",
    "desnz/Generation_Costs_Report_2016_Annexes.xlsx":
        "https://assets.publishing.service.gov.uk/media/5ce55ca0ed915d247979f938/Generation_Costs_Report_2016_Annexes.xlsx",
    "desnz/GC20_Key_Data_and_Assumptions.xlsx":
        "https://assets.publishing.service.gov.uk/media/5f450d378fa8f55de885e1b8/GC20_Key_Data_and_Assumptions.xlsx",
}
# Ofgem's Renewable Electricity Register publishes its reports as daily-named files behind share links
# on its dashboard; the RO ones are kept (stations and certificates), named as Ofgem names them.
RER_DASHBOARD = "https://rer.ofgem.gov.uk/Reports/Dashboard"
RER_KEEP = ("RO_",)


def get(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r:
        return r.read()


def save(rel: str, url: str, body: bytes) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    rec = {"file": rel, "url": url, "fetched": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
           "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}
    with (ROOT / "MANIFEST.jsonl").open("a") as m:
        m.write(json.dumps(rec) + "\n")
    print("ok", rel, len(body))


def ckan(api: str, keep=lambda name: True, folder: str = "") -> None:
    pkg = json.loads(get(api))["result"]
    for res in pkg["resources"]:
        if (res.get("format") or "").upper() != "CSV":
            continue
        url = res["url"]
        name = url.rsplit("/", 1)[-1]
        if not keep(name):
            continue
        try:
            save(f"{folder}/{name}", url, get(url))
        except Exception as e:  # noqa: BLE001
            print("FAIL", url, e)


def rer() -> None:
    """The share links set a session cookie on the first hop, then redirect to the named file."""
    import http.cookiejar
    import re
    page = get(RER_DASHBOARD).decode("utf-8", "replace")
    links = sorted(set(re.findall(r'https://ofgemcloud\.sharepoint\.com/:x:/s/RERExternalReportsLive/[^"]+?download=1', page)))
    for url in links:
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        try:
            with opener.open(urllib.request.Request(url, headers=UA), timeout=900) as r:
                name = urllib.parse.unquote(urllib.parse.urlparse(r.url).path.rsplit("/", 1)[-1])
                if not name.startswith(RER_KEEP):
                    print("skip", name)
                    continue
                save(f"ofgem-rer/{name}", url, r.read())
        except Exception as e:  # noqa: BLE001
            print("FAIL", url, e)


if __name__ == "__main__":
    import sys
    only_files = sys.argv[1:] == ["files"]  # `fetch.py files`: the named files and Ofgem's registers only
    for ds in ([] if only_files else LCCC):
        try:
            ckan(LCCC_API + ds, folder="lccc")
        except Exception as e:  # noqa: BLE001
            print("FAIL", ds, e)
    if not only_files:
        ckan(NESO_API, keep=lambda n: n.startswith(NESO_KEEP), folder="neso")
    for rel, url in FILES.items():
        try:
            save(rel, url, get(url))
        except Exception as e:  # noqa: BLE001
            print("FAIL", rel, e)
    rer()
