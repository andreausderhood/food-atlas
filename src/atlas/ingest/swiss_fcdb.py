"""Swiss FCDB v7.1 openpyxl streaming adapter: yields nutrition claims."""
from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

import openpyxl

from atlas.claims import Claim
from atlas.ingest.base import BaseIngestAdapter, register
from atlas.unified.identity import product_id


DERIVATION_MAP = {
    "Automated calculation": "calculated",
    "Calculation on the basis of ingredients": "calculated",
    "Estimation": "imputed",
}


def _parse_unit_from_name(name: str) -> str:
    """Extract unit from Swiss nutrient name, e.g. 'Energy, kilojoules (kJ)' → 'kJ'."""
    m = re.search(r"\(([^)]+)\)", name)
    if m:
        return m.group(1).replace(" ", "")
    return ""


def _skip_value(val: str | None) -> bool:
    """Return True if the value should be skipped (n.d., dash, empty)."""
    if val is None:
        return True
    s = str(val).strip()
    return s in ("", "-", "n.d.")


class SwissFcdbAdapter(BaseIngestAdapter):
    """Streaming Swiss FCDB v7.1 adapter: reads Generic Foods sheet
    with openpyxl read_only mode, parses header row 3 dynamically,
    streams data rows without loading the full workbook into RAM."""

    src_id = "SRC-SWISS-FCDB-V7.1"

    def __init__(self, src_id: str = "SRC-SWISS-FCDB-V7.1", prefix: str = "prod:swiss") -> None:
        self.src_id = src_id
        self.prefix = prefix

    def load(self, root: Path, path: Path) -> Iterator[Claim]:
        xlsx_path = self._find_xlsx(root, path)
        wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
        try:
            ws = wb["Generic Foods"]
            claims = self._stream_ws(ws)
            yield from claims
        finally:
            wb.close()

    def _stream_ws(self, ws) -> Iterator[Claim]:
        # Row 3 is the header
        header: list[str] = []
        for cell in next(ws.iter_rows(min_row=3, max_row=3)):
            header.append(str(cell.value) if cell.value is not None else "")

        # Identify nutrient columns: starting from col 8 (0-indexed: 8),
        # every 3 columns are [nutrient_name, "Derivation of value", "Source"]
        nutrients: list[dict] = []
        i = 8  # column index for first nutrient value (0-based)
        while i < len(header):
            name = header[i]
            if not name:
                break
            unit = _parse_unit_from_name(name)
            # Derivation column is i+1, Source column is i+2
            nutrients.append({"name": name, "unit": unit, "val_col": i, "deriv_col": i + 1, "src_col": i + 2})
            i += 3

        # Stream data rows starting from row 4
        for row in ws.iter_rows(min_row=4, values_only=True):
            if not any(v is not None for v in row):
                continue

            food_id = row[0]
            if food_id is None:
                continue

            food_name = str(row[3]) if row[3] is not None else str(food_id)
            subject = f"{self.prefix}:{food_id}"

            for nut in nutrients:
                val = row[nut["val_col"]] if nut["val_col"] < len(row) else None
                deriv = row[nut["deriv_col"]] if nut["deriv_col"] < len(row) else None
                src = row[nut["src_col"]] if nut["src_col"] < len(row) else None

                if _skip_value(val):
                    continue

                # Map Swiss derivation to atlas taxonomy
                deriv_str = str(deriv).strip() if deriv is not None else ""
                atlas_deriv = DERIVATION_MAP.get(deriv_str, "registry")

                # Build ref from source number
                ref = f"swiss:{food_id}:{nut['name']}"
                if src is not None:
                    ref = f"swiss:{food_id}:{nut['name']}:src{src}"

                # Build method from derivation description
                method = deriv_str if deriv_str else None

                # Parse value (Swiss uses period as decimal separator)
                try:
                    v = float(val)
                except (ValueError, TypeError):
                    continue

                # Skip zero values for nutrients that are typically not zero
                # (we keep them as honest data)

                claim = Claim(
                    subject=subject,
                    group="nutrition",
                    field=f"nutrient:swiss:{nut['name']}",
                    v=v,
                    src=self.src_id,
                    derivation=atlas_deriv,
                    unit=nut["unit"] or None,
                    basis="as_described",
                    food_part="product",
                    ref=ref,
                    method=method,
                )
                yield claim

    def _find_xlsx(self, root: Path, path: Path) -> Path:
        """Find the Swiss FCDB Excel file."""
        candidates = [path]
        if path == root:
            candidates.append(root / "data" / "raw" / "swiss-fcdb")
        for cand in candidates:
            for f in cand.rglob("*.xlsx"):
                if "Swiss_food" in f.name:
                    return f
        raise FileNotFoundError(f"Could not find Swiss FCDB Excel file under {path}")


register(SwissFcdbAdapter())