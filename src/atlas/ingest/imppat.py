"""IMPPAT 2.0 Indian Medicinal Plants, Phytochemistry And Therapeutics — JSONL streaming ingest adapter.

Produces ``traditional_use`` claims (Ayurvedic properties + therapeutic uses
from IMPPAT 2.0 JSONL) and non-amount ``molecules`` presence claims.

Species-native: no identity edges, no catalog wiring needed.
Coverage flows via store.species_native_with_claims.

Licensed under CC-BY-NC-4.0 (open_content, flagged).
Strictly adheres to Rule 14b (Epistemic Separation): Traditional Ayurvedic
concepts are cited in authentic native Sanskrit vocabulary and never reduced
to Western assays.
"""
from __future__ import annotations

import json
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from atlas.claims import Claim
from atlas.ingest.base import BaseIngestAdapter, register
from atlas.unified.identity import species_id

SRC_ID = "SRC-IMPPAT-2.0"
REF_DEFAULT = "Mohanraj, K. et al. (2018). IMPPAT: A curated database of Indian Medicinal Plants, Phytochemistry And Therapeutics. Scientific Reports, 8, 4329. cb.imsc.res.in/imppat/."


def _slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def _first_mesh_token(mesh_id: str) -> str:
    """Extract the first MESH token (without MESH: prefix) from a mesh_id string."""
    if not mesh_id:
        return ""
    for token in mesh_id.split(","):
        token = token.strip()
        if token.startswith("MESH:"):
            return token[5:]
    return ""


# ---------------------------------------------------------------------------
# Claim Generation
# ---------------------------------------------------------------------------

def iter_imppat_claims(record: dict[str, Any]) -> Iterator[Claim]:
    """Convert an IMPPAT JSONL record dictionary into unified claims.

    Species-native: produces identity (subject = species_id) and claims
    but no identity edges. Coverage flows via store.species_native_with_claims.
    """
    plant_name = record.get("plant_name") or ""
    if not plant_name:
        return

    subject = species_id(plant_name)

    # 1. Ayurvedic Classical Properties (Rasa, Guna, Virya, Vipaka, Dosha)
    ayur = record.get("ayurvedic_properties") or {}

    def _emit_ayurveda_props(field_name: str, values: Any):
        if not values:
            return
        v_list = values if isinstance(values, list) else [values]
        for v in v_list:
            v_str = str(v).strip()
            if v_str:
                yield Claim(
                    subject=subject,
                    group="traditional_use",
                    field=field_name,
                    v=v_str,
                    src=SRC_ID,
                    derivation="literature",
                    ref=record.get("reference") or REF_DEFAULT,
                )

    yield from _emit_ayurveda_props("ayurveda:rasa", ayur.get("rasa"))
    yield from _emit_ayurveda_props("ayurveda:guna", ayur.get("guna"))
    yield from _emit_ayurveda_props("ayurveda:virya", ayur.get("virya"))
    yield from _emit_ayurveda_props("ayurveda:vipaka", ayur.get("vipaka"))
    yield from _emit_ayurveda_props("ayurveda:dosha", ayur.get("dosha"))

    # 2. Therapeutic Uses → traditional_use:imppat:{first-MESH-token}
    for tu_item in record.get("therapeutics") or []:
        tu_name = tu_item.get("therapeutic_use") or ""
        if not tu_name:
            continue
        mesh_id = tu_item.get("mesh_id") or ""
        first_mesh = _first_mesh_token(mesh_id)
        ref = tu_item.get("reference") or record.get("reference") or REF_DEFAULT
        yield Claim(
            subject=subject,
            group="traditional_use",
            field=f"traditional_use:imppat:{first_mesh}" if first_mesh else f"traditional_use:imppat:{_slugify(tu_name)}",
            v=tu_name,
            src=SRC_ID,
            derivation="literature",
            ref=ref,
        )

    # 3. Phytochemicals (Molecules Presence) → molecule:imppat:{IMPHY-ID}
    for phy in record.get("phytochemicals") or []:
        phy_name = phy.get("name") or ""
        if not phy_name:
            continue
        phy_id = phy.get("phytochemical_id") or ""
        ref = phy.get("reference") or record.get("reference") or REF_DEFAULT
        part = phy.get("plant_part") or ""
        ref_with_part = f"{ref} | {part}" if part else ref
        yield Claim(
            subject=subject,
            group="molecules",
            field=f"molecule:imppat:{phy_id}" if phy_id else f"molecule:imppat:{_slugify(phy_name)}",
            v=phy_name,
            src=SRC_ID,
            derivation="literature",
            ref=ref_with_part,
        )


# --------------------------------------------------------------------------
# Ingest Adapter
# --------------------------------------------------------------------------

class ImppatAdapter(BaseIngestAdapter):
    """Streaming JSONL ingest adapter for IMPPAT 2.0.

    Species-native: no identity edges, no catalog wiring needed.
    Coverage flows via store.species_native_with_claims.
    """

    src_id = SRC_ID

    def load(self, root: Path, path: Path) -> Iterator[Claim]:
        """Stream claims from JSON or JSONL file(s) under path."""
        files = [path] if path.is_file() else sorted(path.glob("*.json*"))
        for f in files:
            if f.suffix == ".jsonl":
                with f.open(encoding="utf-8") as fp:
                    for line in fp:
                        line = line.strip()
                        if line:
                            rec = json.loads(line)
                            if isinstance(rec, dict):
                                yield from iter_imppat_claims(rec)
            elif f.suffix == ".json":
                data = json.loads(f.read_text(encoding="utf-8"))
                records = data if isinstance(data, list) else [data]
                for rec in records:
                    if isinstance(rec, dict):
                        yield from iter_imppat_claims(rec)


register(ImppatAdapter())