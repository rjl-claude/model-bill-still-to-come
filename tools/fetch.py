"""Fetch the official records the bill still to come is built from, as published, into data/raw/.

Usage: uv run python tools/fetch.py
Every file is saved unchanged; data/raw/MANIFEST.jsonl records its URL, time and sha256.
Re-run on the day the figures are frozen: the registers change daily.
"""
import datetime as dt
import hashlib
import json
import pathlib
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
}


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


if __name__ == "__main__":
    for ds in LCCC:
        try:
            ckan(LCCC_API + ds, folder="lccc")
        except Exception as e:  # noqa: BLE001
            print("FAIL", ds, e)
    ckan(NESO_API, keep=lambda n: n.startswith(NESO_KEEP), folder="neso")
    for rel, url in FILES.items():
        try:
            save(rel, url, get(url))
        except Exception as e:  # noqa: BLE001
            print("FAIL", rel, e)
