"""Catalog helper: list source records from raw FDC and BLS datasets."""
from __future__ import annotations

import csv
from pathlib import Path

FDC_SOURCES = {
    "data/raw/fdc-foundation": "SRC-FDC-FOUNDATION-2026-04",
    "data/raw/fdc-srlegacy": "SRC-FDC-SRLEGACY-2018-04",
}
BLS_SOURCE = "SRC-BLS-4.0"


def _fdc_rows(root: Path = Path(".")) -> list[dict]:
    rows = []
    for rel, src in FDC_SOURCES.items():
        folder = root / rel
        if not folder.is_dir():
            continue
        hits = sorted(folder.rglob("food.csv"))
        if not hits:
            continue
        with hits[0].open(encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rows.append({"source": src, "id": r["fdc_id"], "name": r.get("description", "")})
    return rows


def _bls_rows(root: Path = Path(".")) -> list[dict]:
    folder = root / "data/raw/bls"
    if not folder.is_dir():
        return []
    # BLS excel or csv if present
    hits = sorted(folder.rglob("*.csv")) + sorted(folder.rglob("*.xlsx"))
    if not hits:
        return []
    # If a csv food list exists:
    csv_hits = sorted(folder.rglob("*food*.csv")) or sorted(folder.rglob("*.csv"))
    rows = []
    if csv_hits:
        with csv_hits[0].open(encoding="utf-8", errors="replace") as f:
            for r in csv.DictReader(f):
                rec_id = r.get("BLS_Code") or r.get("code") or r.get("id")
                if rec_id:
                    rows.append({"source": BLS_SOURCE, "id": rec_id, "name": r.get("Food name", r.get("name", ""))})
    return rows
