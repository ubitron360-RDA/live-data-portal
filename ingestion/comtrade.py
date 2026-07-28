"""Pull bilateral crude oil trade values from the UN Comtrade API.

Optional data source: requires a free subscription key from
https://comtradedeveloper.un.org/ (env var COMTRADE_API_KEY). If the key
isn't set, this script exits cleanly without failing the pipeline - JODI
already covers the core country-level flow story.

Writes data/raw/comtrade/<date>.json.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone

from common import fetch_json, load_config, write_raw_snapshot

API_KEY = os.environ.get("COMTRADE_API_KEY")

# Curated set of major crude oil trading countries (UN M49 numeric codes).
# reporterCode is required per-call on the free tier; there's no "all" wildcard.
REPORTERS = {
    "USA": 842, "China": 156, "India": 699, "Japan": 392, "South Korea": 410,
    "Germany": 276, "Netherlands": 528, "Saudi Arabia": 682, "Russia": 643,
    "Canada": 124, "Iraq": 368, "UAE": 784, "Kuwait": 414, "Nigeria": 566,
    "Norway": 579, "Mexico": 484, "Brazil": 76, "Kazakhstan": 398, "Angola": 24,
}


def recent_periods(months_back: int) -> list[str]:
    now = datetime.now(timezone.utc)
    periods = []
    for i in range(months_back):
        m = now.month - i
        y = now.year
        while m <= 0:
            m += 12
            y -= 1
        periods.append(f"{y}{m:02d}")
    return periods


def main() -> int:
    if not API_KEY:
        print("  [warn] COMTRADE_API_KEY not set - skipping UN Comtrade ingestion (optional source)")
        return 0

    config = load_config()
    comtrade_cfg = config["flows"]["comtrade"]
    periods = ",".join(recent_periods(comtrade_cfg["period_lookback_months"]))
    headers = {"Ocp-Apim-Subscription-Key": API_KEY}

    all_rows = []
    for name, code in REPORTERS.items():
        print(f"  fetching Comtrade HS{comtrade_cfg['hs_code']} for {name}...")
        data = fetch_json(comtrade_cfg["api_base"], headers=headers, params={
            "reporterCode": code,
            "partnerCode": 0,  # World
            "period": periods,
            "flowCode": "X,M",
            "cmdCode": comtrade_cfg["hs_code"],
            "customsCode": "C00",
            "motCode": 0,
        })
        if not data:
            continue
        for row in data.get("data", []):
            all_rows.append({
                "reporter": name,
                "period": row.get("period"),
                "flow": row.get("flowDesc") or row.get("flowCode"),
                "trade_value_usd": row.get("primaryValue"),
            })

    write_raw_snapshot("comtrade", {"hs_code": comtrade_cfg["hs_code"], "rows": all_rows})
    return 0


if __name__ == "__main__":
    sys.exit(main())
