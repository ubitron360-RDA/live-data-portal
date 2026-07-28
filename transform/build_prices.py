"""Combine the latest FRED + EIA raw snapshots into data/processed/prices.json,
a frontend-ready shape: latest value, % change, and a capped history per series.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ingestion"))
from common import REPO_ROOT, latest_raw_snapshot  # noqa: E402

OUT_PATH = REPO_ROOT / "docs" / "data" / "processed" / "prices.json"
HISTORY_CAP = 120


def build_series_entry(series_id: str, source: str, series: dict) -> dict | None:
    observations = series.get("observations") or []
    if not observations:
        return None
    ordered = sorted(observations, key=lambda o: o["date"])
    history = ordered[-HISTORY_CAP:]
    latest = ordered[-1]
    change_pct = None
    if len(ordered) >= 2 and ordered[-2]["value"]:
        prev = ordered[-2]["value"]
        change_pct = round((latest["value"] - prev) / prev * 100, 2)

    return {
        "id": series_id,
        "source": source,
        "name": series.get("name"),
        "unit": series.get("unit"),
        "frequency": series.get("frequency"),
        "latest_value": latest["value"],
        "latest_date": latest["date"],
        "change_pct": change_pct,
        "history": history,
    }


def main() -> int:
    entries = []
    for source in ("fred", "eia"):
        snapshot = latest_raw_snapshot(source)
        if not snapshot:
            continue
        for series_id, series in snapshot.items():
            entry = build_series_entry(series_id, source, series)
            if entry:
                entries.append(entry)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"series": entries}, f, indent=2)
    print(f"  wrote {len(entries)} price series -> {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
