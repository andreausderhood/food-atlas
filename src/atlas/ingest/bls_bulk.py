"""Streaming BLS 4.0 adapter: yields nutrition claims from the BLS 4.0 Excel file.

Ported from the legacy procedural ``load_bls()`` to the Task-16 adapter
architecture (``BaseIngestAdapter`` + lazy ``Iterator[Claim]`` + self-registration).

Claim semantics follow the legacy adapter: ``basis`` and ``food_part`` are derived
from each food's level in the foods registry (``taxon_food`` → ``fresh_weight``/``whole``,
``form`` → ``as_described``/``whole``).
"""
from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import yaml
from openpyxl import load_workbook

from atlas.claims import Claim, UnmappedDerivation
from atlas.ingest.bls import HERKUNFT, nutrient_columns, parse_value_header
from atlas.ingest.base import BaseIngestAdapter, register
from atlas.foods import FoodNode, basis, food_part


def _find_workbook(path: Path) -> Path:
    """Find the BLS 4.0 data workbook under ``path`` (recursive)."""
    from openpyxl import load_workbook
    hits = sorted(path.rglob("BLS_4_0_Daten_*.xlsx"))
    if len(hits) != 1:
        raise FileNotFoundError(
            f"expected one BLS_4_0_Daten_*.xlsx under {path}, found {len(hits)}")
    return hits[0]


def _load_bls_code_map(root: Path) -> dict[str, FoodNode]:
    """Load foods.yaml and return {bls_code: FoodNode} for all foods that have bls_codes."""
    foods_yaml = root / "data" / "registry" / "foods.yaml"
    if not foods_yaml.exists():
        return {}
    data = yaml.safe_load(foods_yaml.read_text(encoding="utf-8")) or {}
    mapping: dict[str, FoodNode] = {}
    for food_id, info in data.items():
        if not isinstance(info, dict):
            continue
        bls_codes = info.get("bls_codes") or ()
        if not bls_codes:
            continue
        node = FoodNode(
            id=food_id,
            level=info.get("level", "taxon_food"),
            name=info.get("name", ""),
            name_de=info.get("name_de"),
            derives_from=info.get("derives_from"),
            is_a=info.get("is_a"),
            part_of=info.get("part_of"),
            part=info.get("part"),
            process=info.get("process"),
            default_part=info.get("default_part", "whole"),
            foodon=info.get("foodon"),
            foodatlas_ids=tuple(info.get("foodatlas_ids") or ()),
            fdc_match=tuple(info.get("fdc_match") or ()),
            bls_codes=tuple(bls_codes),
        )
        for code in node.bls_codes:
            mapping[str(code)] = node
    return mapping


class BlsAdapter(BaseIngestAdapter):
    """Streaming BLS 4.0 adapter: yields nutrition claims row by row."""

    src_id = "SRC-BLS-4.0"

    def load(self, root: Path, path: Path) -> Iterator[Claim]:
        bls_to_food = _load_bls_code_map(root)
        wb = load_workbook(_find_workbook(path), read_only=True, data_only=True)
        try:
            rows = wb.worksheets[0].iter_rows(values_only=True)
            headers = ["" if h is None else str(h) for h in next(rows)]
            triples = nutrient_columns(headers)
            if not triples:
                raise ValueError("no 'Datenherkunft' columns found in the BLS workbook")
            for row in rows:
                code = "" if row[0] is None else str(row[0]).strip()
                node = bls_to_food.get(code)
                if node is None:
                    continue
                for vi, oi, ri in triples:
                    value = row[vi] if vi < len(row) else None
                    if value is None or value == "":
                        continue
                    origin = "" if row[oi] is None else str(row[oi]).strip()
                    if origin == "-":
                        origin = ""
                    if origin and origin not in HERKUNFT:
                        raise UnmappedDerivation(
                            f"BLS Datenherkunft {origin!r} in column {headers[oi]!r}"
                        )
                    tag, name, unit = parse_value_header(headers[vi])
                    key = f"nutrient:bls:{tag}"
                    reference = row[ri] if ri < len(row) else None
                    yield Claim(
                        subject=node.id,
                        group="nutrition",
                        field=key,
                        v=float(value) if isinstance(value, (int, float)) else str(value),
                        unit=unit,
                        basis=basis(node),
                        food_part=food_part(node),
                        src=self.src_id,
                        derivation=HERKUNFT.get(origin, "unverified"),
                        ref=f"bls:{code}" + (f"; {reference}" if reference else ""),
                    )
        finally:
            wb.close()


register(BlsAdapter())