"""The 13 unified fields of the coverage table (one row each) and their axes."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Field:
    key: str
    label: str
    axis: str          # "species" (26,591 pool) or "product" (15,402 source records)
    closes_with: str   # the "Gap" column of the coverage table
    collector: str | None = None   # name in collectors.COLLECTORS; None = not measurable yet


FIELDS: tuple[Field, ...] = (
    Field("species_identity", "Species identity", "species", "pull parent chains", "species_identity"),
    Field("common_names", "Common names", "species", "name harvest", "common_names"),
    Field("food_hierarchy", "Food hierarchy", "product", "curation funnel", "food_hierarchy"),
    Field("nutrients", "Nutrients", "species", "map products to species", "nutrients"),
    Field("molecules", "Molecules (ChEBI)", "species", "concentration claims", "molecules"),
    Field("bioactivity", "Bioactivity / health", "species", "human trials", "bioactivity"),
    Field("seasonality", "Seasonality", "species", "expand calendar DB", "seasonality"),
    Field("distribution", "Distribution / geography", "species", "parse to country codes", "distribution"),
    Field("growing", "Growing / agronomy", "species", "ECOCROP ingest"),
    Field("edible_parts", "Edible parts", "species", "normalize part vocabulary", "edible_parts"),
    Field("varieties", "Varieties / cultivars", "species", "fetch Mansfeld + Khoury"),
    Field("photos", "Photos", "species", "ZIM harvest"),
    Field("evidence_chain", "Evidence / provenance chain", "species", "audit-hash layer"),
)
FIELD_KEYS = tuple(f.key for f in FIELDS)
