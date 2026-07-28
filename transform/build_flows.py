"""Combine the latest JODI (+ optional Comtrade) raw snapshots into
data/processed/flows.json: top exporting/importing countries by volume.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ingestion"))
from common import REPO_ROOT, latest_raw_snapshot  # noqa: E402
from countries import country_name  # noqa: E402

OUT_PATH = REPO_ROOT / "docs" / "data" / "processed" / "flows.json"


def top_by_flow(rows: list[dict], flow_code: str, top_n: int) -> list[dict]:
    """For a given flow (export/import), keep each country's most recent
    period, then rank by value descending."""
    latest_per_country: dict[str, dict] = {}
    for row in rows:
        if row["flow"] != flow_code:
            continue
        country = row["country"]
        existing = latest_per_country.get(country)
        if existing is None or row["period"] > existing["period"]:
            latest_per_country[country] = row

    ranked = sorted(latest_per_country.values(), key=lambda r: r["value"], reverse=True)
    return [
        {
            "country_code": r["country"],
            "country": country_name(r["country"]),
            "period": r["period"],
            "value": r["value"],
        }
        for r in ranked[:top_n]
    ]


def build_jodi_flows() -> dict | None:
    snapshot = latest_raw_snapshot("jodi")
    if not snapshot or not snapshot.get("rows"):
        return None
    rows = snapshot["rows"]
    top_n = 10
    return {
        "product": snapshot["product"],
        "unit": snapshot["unit"],
        "top_exporters": top_by_flow(rows, snapshot["export_flow"], top_n),
        "top_importers": top_by_flow(rows, snapshot["import_flow"], top_n),
    }


def build_comtrade_flows() -> dict | None:
    snapshot = latest_raw_snapshot("comtrade")
    if not snapshot or not snapshot.get("rows"):
        return None
    return {"hs_code": snapshot["hs_code"], "rows": snapshot["rows"]}


def main() -> int:
    result = {}
    jodi_flows = build_jodi_flows()
    if jodi_flows:
        result["jodi"] = jodi_flows
    comtrade_flows = build_comtrade_flows()
    if comtrade_flows:
        result["comtrade"] = comtrade_flows

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"  wrote flows for sources {list(result.keys())} -> {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
