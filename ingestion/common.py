"""Shared helpers for ingestion scripts: HTTP fetch with retry, config
loading, and writing raw snapshots under data/raw/<source>/<date>.json.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "series.yaml"
RAW_DIR = REPO_ROOT / "data" / "raw"


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def fetch_json(url: str, params: dict | None = None, headers: dict | None = None,
                retries: int = 3, backoff: float = 2.0, timeout: int = 30):
    """GET a URL and parse JSON, retrying on transient failures.

    Returns the parsed JSON, or None if every attempt failed (callers should
    treat that as "skip this series" rather than crashing the whole run).
    """
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                return resp.json()
            last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
        except requests.RequestException as exc:
            last_error = str(exc)
        if attempt < retries:
            time.sleep(backoff ** attempt)
    print(f"  [warn] giving up on {url} after {retries} attempts: {last_error}")
    return None


def fetch_text(url: str, retries: int = 3, backoff: float = 2.0, timeout: int = 60):
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=timeout)
            if resp.status_code == 200:
                return resp.text
            last_error = f"HTTP {resp.status_code}"
        except requests.RequestException as exc:
            last_error = str(exc)
        if attempt < retries:
            time.sleep(backoff ** attempt)
    print(f"  [warn] giving up on {url} after {retries} attempts: {last_error}")
    return None


def write_raw_snapshot(source: str, payload) -> Path:
    """Write today's raw snapshot for a source. Overwrites if run twice in
    one day, so repeated pipeline runs don't pile up duplicate files."""
    out_dir = RAW_DIR / source
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{today_str()}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)
    return out_path


def latest_raw_snapshot(source: str) -> dict | None:
    """Load the most recent raw snapshot for a source, if any exists."""
    out_dir = RAW_DIR / source
    if not out_dir.exists():
        return None
    snapshots = sorted(out_dir.glob("*.json"))
    if not snapshots:
        return None
    with open(snapshots[-1], "r", encoding="utf-8") as f:
        return json.load(f)
