"""Curated claims: one YAML file per subject, every claim marked `curated`."""
from __future__ import annotations

from pathlib import Path

import yaml

from atlas.claims import Claim

OPTIONAL = ("unit", "basis", "food_part", "method", "ref", "v_min", "v_max", "n")


def load_curated(folder: Path) -> list[Claim]:
    claims: list[Claim] = []
    for path in sorted(folder.glob("*.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for c in doc.get("claims", []):
            claims.append(Claim(
                subject=doc["subject"], group=c["group"], field=c["field"], v=c["v"],
                src=c["src"], derivation=c["derivation"], flags=tuple(c.get("flags", ())),
                curated=True, **{k: c[k] for k in OPTIONAL if k in c},
            ))
    return claims
