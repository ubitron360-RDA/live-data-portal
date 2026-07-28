"""Pull crude oil export/import volumes by country from the JODI-Oil World
Database bulk CSV (free, no API key required).

Writes data/raw/jodi/<date>.json.
"""
from __future__ import annotations

import csv
import io
import sys
from datetime import datetime, timezone

from common import fetch_text, load_config, write_raw_snapshot


def parse_csv_rows(csv_text: str, product: str, flows: set[str], unit: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = []
    for row in reader:
        if row.get("ENERGY_PRODUCT") != product:
            continue
        if row.get("FLOW_BREAKDOWN") not in flows:
            continue
        if row.get("UNIT_MEASURE") != unit:
            continue
        raw_value = (row.get("OBS_VALUE") or "").strip()
        try:
            value = float(raw_value)
        except ValueError:
            continue  # "-", "x", or other non-numeric placeholders
        rows.append({
            "country": row.get("REF_AREA"),
            "period": row.get("TIME_PERIOD"),
            "flow": row.get("FLOW_BREAKDOWN"),
            "value": value,
        })
    return rows


def main() -> int:
    config = load_config()
    jodi_cfg = config["flows"]["jodi"]
    flows = {jodi_cfg["export_flow"], jodi_cfg["import_flow"]}

    current_year = datetime.now(timezone.utc).year
    all_rows = []
    for year in (current_year, current_year - 1):
        url = jodi_cfg["csv_url_template"].format(year=year)
        print(f"  fetching JODI CSV for {year}...")
        text = fetch_text(url)
        if not text:
            continue
        rows = parse_csv_rows(text, jodi_cfg["product"], flows, jodi_cfg["unit"])
        print(f"    -> {len(rows)} matching rows")
        all_rows.extend(rows)

    write_raw_snapshot("jodi", {
        "product": jodi_cfg["product"],
        "unit": jodi_cfg["unit"],
        "export_flow": jodi_cfg["export_flow"],
        "import_flow": jodi_cfg["import_flow"],
        "rows": all_rows,
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())
