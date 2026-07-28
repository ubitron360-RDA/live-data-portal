"""Write data/processed/meta.json: per-source last-updated dates and a
pipeline-run timestamp, so the frontend can show real recency instead of
implying everything is equally fresh (prices update daily, flows monthly).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ingestion"))
from common import RAW_DIR, REPO_ROOT  # noqa: E402

OUT_PATH = REPO_ROOT / "docs" / "data" / "processed" / "meta.json"
SOURCES = ["fred", "eia", "jodi", "comtrade"]


def latest_snapshot_date(source: str) -> str | None:
    out_dir = RAW_DIR / source
    if not out_dir.exists():
        return None
    snapshots = sorted(out_dir.glob("*.json"))
    if not snapshots:
        return None
    return snapshots[-1].stem  # filename is YYYY-MM-DD.json


def main() -> int:
    sources = {}
    for source in SOURCES:
        date = latest_snapshot_date(source)
        sources[source] = {"last_updated": date, "available": date is not None}

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": sources,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"  wrote meta -> {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
