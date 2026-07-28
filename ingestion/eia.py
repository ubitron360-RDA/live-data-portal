"""Pull US product prices from the EIA API v2 (via its v1-seriesID
compatibility route).

Requires env var EIA_API_KEY (free key: https://www.eia.gov/opendata/register.php).
Writes data/raw/eia/<date>.json.
"""
from __future__ import annotations

import os
import sys

from common import fetch_json, load_config, write_raw_snapshot

API_KEY = os.environ.get("EIA_API_KEY")


def fetch_series(api_base: str, series_id: str) -> list[dict]:
    url = f"{api_base}/{series_id}"
    data = fetch_json(url, params={"api_key": API_KEY})
    if not data:
        return []
    rows = data.get("response", {}).get("data", [])
    observations = []
    for row in rows:
        period = row.get("period")
        value = row.get("value")
        if period is None or value in (None, ""):
            continue
        try:
            observations.append({"date": period, "value": float(value)})
        except (TypeError, ValueError):
            continue
    return observations


def main() -> int:
    if not API_KEY:
        print("  [warn] EIA_API_KEY not set - skipping EIA ingestion")
        return 0

    config = load_config()
    eia_cfg = config["prices"]["eia"]
    result = {}
    for series in eia_cfg["series"]:
        print(f"  fetching EIA {series['id']} ({series['name']})...")
        observations = fetch_series(eia_cfg["api_base"], series["id"])
        if not observations:
            print(f"    [warn] no data returned for {series['id']} - check the series id is still valid")
        result[series["id"]] = {
            "name": series["name"],
            "unit": series["unit"],
            "frequency": series["frequency"],
            "observations": observations,
        }
        print(f"    -> {len(observations)} observations")

    write_raw_snapshot("eia", result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
