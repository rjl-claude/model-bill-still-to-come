"""Fetch half-hourly prices and wind and solar output, 2016-2025, for wind's and solar's share of the
market price (cannibalisation). Saved as published-derived CSV per year in data/raw/halfhourly/.

- Price: Elexon Market Index Data (MID), provider APXMIDP, £/MWh.
- Transmission wind: Elexon FUELHH, fuel type WIND, MW.
- Embedded wind and solar, and national demand: NESO Historic Demand Data, one CSV a year (saved as published).

Usage: uv run python tools/fetch_hourly.py
"""
import csv
import datetime as dt
import hashlib
import json
import pathlib
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1] / "data" / "raw"
OUT = ROOT / "halfhourly"
UA = {"User-Agent": "Mozilla/5.0 (bill-still-to-come data fetch; richardlyon.net)"}
ELEXON = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
YEARS = range(2016, 2026)


def get(url: str) -> bytes:
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return r.read()
        except Exception:  # noqa: BLE001
            time.sleep(2 ** attempt)
    raise RuntimeError(url)


def manifest(rel: str, url: str, body: bytes) -> None:
    rec = {"file": rel, "url": url, "fetched": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
           "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}
    with (ROOT / "MANIFEST.jsonl").open("a") as m:
        m.write(json.dumps(rec) + "\n")


def weeks(year: int):
    d = dt.date(year, 1, 1)
    while d.year == year:
        e = min(d + dt.timedelta(days=7), dt.date(year + 1, 1, 1))
        yield d, e
        d = e


def elexon_year(year: int) -> None:
    path = OUT / f"elexon_{year}.csv"
    if path.exists():
        return
    rows = {}
    for d, e in weeks(year):
        mid = json.loads(get(f"{ELEXON}/MID?from={d}T00:00Z&to={e}T00:00Z&dataProviders=APXMIDP&format=json"))["data"]
        for r in mid:
            k = (r["settlementDate"], r["settlementPeriod"])
            if r["settlementDate"].startswith(str(year)):
                rows.setdefault(k, {})["price"] = r["price"]
                rows[k]["mid_volume"] = r["volume"]
        last = e - dt.timedelta(days=1)
        fuel = json.loads(get(f"{ELEXON}/FUELHH?settlementDateFrom={d}&settlementDateTo={last}&fuelType=WIND&format=json"))["data"]
        for r in fuel:
            rows.setdefault((r["settlementDate"], r["settlementPeriod"]), {})["wind_tx_mw"] = r["generation"]
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["settlement_date", "settlement_period", "price", "mid_volume", "wind_tx_mw"])
        for (sd, sp), v in sorted(rows.items()):
            w.writerow([sd, sp, v.get("price"), v.get("mid_volume"), v.get("wind_tx_mw")])
    manifest(f"halfhourly/elexon_{year}.csv", f"{ELEXON}/MID + FUELHH (derived: one row per settlement period)", path.read_bytes())
    print("ok elexon", year, len(rows))


def neso_years() -> None:
    pkg = json.loads(get("https://api.neso.energy/api/3/action/package_show?id=historic-demand-data"))["result"]
    for r in pkg["resources"]:
        name = r["url"].rsplit("/", 1)[-1]
        if not name.startswith("demanddata_") or int(name[11:15]) not in YEARS:
            continue
        path = OUT / name
        if path.exists():
            continue
        body = get(r["url"])
        path.write_bytes(body)
        manifest(f"halfhourly/{name}", r["url"], body)
        print("ok neso", name)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    neso_years()
    for y in YEARS:
        elexon_year(y)
