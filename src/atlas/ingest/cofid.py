"""Streaming CoFID 2021 adapter: yields product claims from McCance & Widdowson's
Composition of Foods Integrated Dataset (UK, OGL v3.0).

Ingests sheets 1.3–1.6, 1.8, 1.10, 1.12–1.14.
Skips sheets 1.7, 1.9, 1.11 (per-100FA fatty-acid sheets) — their values are
fatty-acids-per-g-fatty-acid, not per-100g-food, so they lack a direct food
reference and would misrepresent the nutrient density.

Header layout (all sheets):
  Row 1 — nutrient display names  (e.g. "Water (g)")
  Row 2 — abbreviations            (e.g. "WATER")
  Row 3 — descriptions             (e.g. "Water")
  Row 4+ — data rows

Column 0 = Food Code, Column 1 = Food Name, Column 5 = Main data references.
"""
from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

from atlas.claims import Claim
from atlas.ingest.base import BaseIngestAdapter, register

COFID_SOURCE = "SRC-COFID-2021"

# Sheets that contain per-100g-food nutrient values and are ingested.
INGEST_SHEETS = (
    "1.3 Proximates",
    "1.4 Inorganics",
    "1.5 Vitamins",
    "1.6 Vitamin Fractions",
    "1.8 (SFA per 100gFood)",
    "1.10 (MUFA per 100gFood)",
    "1.12 (PUFA per 100gFood)",
    "1.13 Phytosterols",
    "1.14 Organic Acids",
)

# Sheets skipped: 1.7 (SFA per 100gFA), 1.9 (MUFA per 100FA), 1.11 (PUFA per 100gFA).
# These express fatty acids per 100 g of fatty acids, not per 100 g of food.
# Their values are normalised to the fat fraction and have no direct food-portion
# meaning — ingesting them would misrepresent nutrient density.


class CoFidAdapter(BaseIngestAdapter):
    """Streaming CoFID 2021 adapter: yields product claims from the Excel workbook."""

    src_id = COFID_SOURCE

    def load(self, root: Path, path: Path) -> Iterator[Claim]:
        import openpyxl

        # Accept either a directory containing the xlsx or the xlsx itself.
        xlsx_path = path
        if path.is_dir():
            hits = sorted(path.rglob("*.xlsx"))
            # Filter out old superseded file
            hits = [h for h in hits if "oldFoods" not in h.name]
            if not hits:
                return
            xlsx_path = hits[0]

        wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
        try:
            for sheet_name in INGEST_SHEETS:
                if sheet_name not in wb.sheetnames:
                    continue
                ws = wb[sheet_name]
                yield from _iter_sheet(ws)
        finally:
            wb.close()


def _iter_sheet(ws) -> Iterator[Claim]:
    """Yield claims from a single CoFID worksheet."""
    rows = ws.iter_rows(values_only=True)

    # Read header rows 1-3
    header_row1 = next(rows, None)  # nutrient display names
    if header_row1 is None:
        return
    header_row2 = next(rows, None)  # abbreviations
    header_row3 = next(rows, None)  # descriptions (unused but consumed)

    # Determine nutrient column indices (skip first 7 meta columns:
    # Food Code, Food Name, Description, Group, Previous, Main data references, Footnote)
    meta_cols = 7
    nutrient_indices = []
    abbreviations = []
    units: dict[int, str | None] = {}
    if header_row2 is not None:
        for i, abbr in enumerate(header_row2[meta_cols:], start=meta_cols):
            if abbr is not None:
                nutrient_indices.append(i)
                abbreviations.append(str(abbr))
                # Extract unit from last parenthetical in header row 1
                if header_row1[i] is not None:
                    matches = re.findall(r'\(([^)]+)\)', str(header_row1[i]))
                    units[i] = matches[-1] if matches else None
                else:
                    units[i] = None

    # Stream data rows
    for row in rows:
        if row is None:
            continue
        food_code = row[0]
        food_name = row[1]
        main_ref = row[5]  # 'Main data references' column

        if not food_code:
            continue

        ref = str(main_ref).strip() if main_ref else ""

        for idx, abbr in zip(nutrient_indices, abbreviations):
            value = row[idx] if idx < len(row) else None

            # Skip empty cells and 'N' (no measurable value)
            if value is None or value == "" or value == "N":
                continue

            # Handle trace values: CoFID uses 'Tr' (title case) for traces
            if str(value).strip() in ("Tr", "tr", "TR"):
                yield Claim(
                    subject=f"prod:cofid:{food_code}",
                    group="nutrition",
                    field=f"nutrient:cofid:{abbr}",
                    v="tr",
                    src=COFID_SOURCE,
                    derivation="trace",
                    unit=units[idx],
                    basis="as_described",
                    food_part="product",
                    ref=ref,
                )
                continue

            # Try to parse as float for numeric values
            try:
                v = float(value)
            except (ValueError, TypeError):
                # Non-numeric, non-trace value — skip silently
                continue

            yield Claim(
                subject=f"prod:cofid:{food_code}",
                group="nutrition",
                field=f"nutrient:cofid:{abbr}",
                v=v,
                src=COFID_SOURCE,
                derivation="analytical",
                unit=units[idx],
                basis="as_described",
                food_part="product",
                ref=ref,
            )


register(CoFidAdapter())
