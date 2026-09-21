"""Streaming FDC bulk adapter: yields product claims from Foundation and SR Legacy CSV data.

Produces ``prod:fdcf:*`` claims for Foundation Foods and ``prod:fdcs:*`` claims
for SR Legacy foods (rule 6': basis=as_described, food_part=product).
Streams food_nutrient.csv row by row so the full dataset is never loaded into RAM.
"""
from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from atlas.claims import Claim
from atlas.ingest.fdc import read_csv_rows
from atlas.ingest.base import BaseIngestAdapter, register


REQUIRED_FILES = ("food.csv", "food_nutrient.csv", "nutrient.csv")


def _find_csv_dir(path: Path) -> Path:
    """Find the FDC CSV directory under ``path`` (recursive)."""
    hits = sorted(path.rglob("food_nutrient.csv"))
    if len(hits) != 1:
        raise FileNotFoundError(
            f"expected one food_nutrient.csv under {path}, found {len(hits)}")
    folder = hits[0].parent
    missing = [f for f in REQUIRED_FILES if not (folder / f).exists()]
    if missing:
        raise FileNotFoundError(f"{folder}: missing {missing}")
    return folder


class BulkFdcAdapter(BaseIngestAdapter):
    """Streaming FDC bulk adapter: yields product claims from Foundation or SR Legacy CSV data."""

    def __init__(self, src_id: str, prefix: str, food_type: str | None = None) -> None:
        self.src_id = src_id
        self.prefix = prefix
        self.food_type = food_type

    def load(self, root: Path, path: Path) -> Iterator[Claim]:
        folder = _find_csv_dir(path)

        # Nutrient metadata is small (~500 rows) — load into memory.
        nutrients: dict[str, dict[str, str]] = {}
        for r in read_csv_rows(folder / "nutrient.csv"):
            nutrients[r["id"]] = {"name": r["name"], "unit": r["unit_name"].lower()}

        # Collect valid fdc_ids for this source by streaming food.csv.
        valid_ids: set[str] = set()
        for r in read_csv_rows(folder / "food.csv"):
            if self.food_type is None or r.get("data_type") == self.food_type:
                valid_ids.add(r["fdc_id"])

        # Stream food_nutrient.csv row by row — never load all into RAM.
        for r in read_csv_rows(folder / "food_nutrient.csv"):
            if r["fdc_id"] not in valid_ids:
                continue
            if not r.get("amount", ""):
                continue
            nutrient = nutrients.get(r["nutrient_id"])
            if nutrient is None:
                continue
            yield Claim(
                subject=f"{self.prefix}:{r['fdc_id']}",
                group="nutrition",
                field=f"nutrient:fdc:{r['nutrient_id']}",
                v=float(r["amount"]),
                src=self.src_id,
                derivation="analytical",
                unit=nutrient["unit"],
                basis="as_described",
                food_part="product",
                ref=f"fdc:{r['fdc_id']}",
            )


# Register both bulk FDC adapters at import time so ``atlas ingest`` can find them.
register(BulkFdcAdapter("SRC-FDC-FOUNDATION-2026-04", "prod:fdcf", "foundation_food"))
register(BulkFdcAdapter("SRC-FDC-SRLEGACY-2018-04", "prod:fdcs", None))
