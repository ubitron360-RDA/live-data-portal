"""Pull benchmark commodity price series from the FRED API.

Requires env var FRED_API_KEY (free key: https://fred.stlouisfed.org/docs/api/api_key.html).
Writes data/raw/fred/<date>.json.
"""
from __future__ import annotations

import os
import sys

from common import fetch_json, load_config, write_raw_snapshot

API_KEY = os.environ.get("FRED_API_KEY")


def fetch_series(api_base: str, series_id: str) -> list[dict]:
    data = fetch_json(api_base, params={
        "series_id": series_id,
        "api_key": API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 400,
    })
    if not data or "observations" not in data:
        return []
    # FRED uses "." for missing values.
    return [
        {"date": obs["date"], "value": float(obs["value"])}
        for obs in data["observations"]
        if obs.get("value") not in (None, ".")
    ]


def main() -> int:
    if not API_KEY:
        print("  [warn] FRED_API_KEY not set - skipping FRED ingestion")
        return 0

    config = load_config()
    fred_cfg = config["prices"]["fred"]
    result = {}
    for series in fred_cfg["series"]:
        print(f"  fetching FRED {series['id']} ({series['name']})...")
        observations = fetch_series(fred_cfg["api_base"], series["id"])
        result[series["id"]] = {
            "name": series["name"],
            "unit": series["unit"],
            "frequency": series["frequency"],
            "observations": observations,
        }
        print(f"    -> {len(observations)} observations")

    write_raw_snapshot("fred", result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
