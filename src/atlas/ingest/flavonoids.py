"""Streaming adapter for the USDA Expanded Flavonoid Database R1.1 (public domain).

Yields ``molecules``-group claims keyed to ``prod:flav:Plus-<NDB_No>``
subjects, with field ``molecule:flav:<Nutr_No>`` and derivation mapped
from the source's Deriv_Cd column.
"""
from __future__ import annotations

import csv
from collections.abc import Iterator
from pathlib import Path

from atlas.claims import Claim
from atlas.ingest.base import BaseIngestAdapter, register

DERIV_MAP: dict[str, str] = {
    "A": "analytical",
    "PAK": "analytical",
    "BFSN": "borrowed",
    "BFSY": "borrowed",
    "BFYN": "borrowed",
    "BFZN": "borrowed",
    "CAZN": "calculated",
    "FLC": "label",
    "T": "borrowed",
    "Z": "assumed_zero",
    "z": "assumed_zero",
}


class FlavonoidAdapter(BaseIngestAdapter):
    """Streaming adapter: reads FOOD_DES/NUTR_DEF/FLAV_DAT CSVs and yields
    one Claim per FLAV_DAT row without loading the full dataset into RAM."""

    src_id = "SRC-USDA-FLAVONOID-EXP-1.1"
    prefix = "prod:flav:Plus"

    def load(self, root: Path, path: Path) -> Iterator[Claim]:
        folder = path if path.name == "flavonoid-exp-1.1" else path

        # Small lookup tables — load into memory.
        foods: dict[str, str] = {}
        for r in csv.DictReader((folder / "FOOD_DES.csv").open(encoding="utf-8")):
            foods[r["NDB_No"]] = r["Long_Desc"]

        nutrients: dict[str, dict[str, str]] = {}
        for r in csv.DictReader((folder / "NUTR_DEF.csv").open(encoding="utf-8")):
            nutrients[r["Nutr_No"]] = {
                "name": r["Nutrient name"],
                "unit": r["Unit"],
            }

        # Stream FLAV_DAT row by row — never load all into RAM.
        with (folder / "FLAV_DAT.csv").open(newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                ndb_no = r["NDB_No"]
                nutr_no = r["Nutr_No"]
                flav_val = r["Flav_Val"]
                deriv_cd = r.get("Deriv_Cd", "").strip()

                nutrient = nutrients.get(nutr_no)
                if nutrient is None:
                    continue

                # Flav_Val=0 is a real value (assumed zero) — include honestly.
                v = float(flav_val)

                # Map Deriv_Cd to derivation label; unknown/empty → assumed_zero.
                # Empty Deriv_Cd with Src_Cd=7 (assumed zero) is the common case.
                if not deriv_cd:
                    derivation = "assumed_zero"
                else:
                    derivation = DERIV_MAP.get(deriv_cd, "assumed_zero")

                subject = f"{self.prefix}-{ndb_no}"
                field = f"molecule:flav:Plus-{nutr_no}"
                unit = nutrient["unit"]

                ref = None
                ref_ndb = r.get("Ref_NDB_No", "").strip()
                if ref_ndb:
                    ref = f"flav:{ref_ndb}"

                yield Claim(
                    subject=subject,
                    group="molecules",
                    field=field,
                    v=v,
                    src=self.src_id,
                    derivation=derivation,
                    unit=unit,
                    basis="as_described",
                    food_part="product",
                    ref=ref,
                )


register(FlavonoidAdapter())