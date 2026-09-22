"""HERB TCM (High-throughput Experiment- and Reference-guided TCM Database) — JSONL streaming ingest adapter.

Produces ``traditional_use`` claims (tcm:pinyin, tcm:chinese_name, tcm:english_name,
tcm:nature, tcm:flavor, tcm:meridian) and non-amount ``molecules`` presence claims
from HERB JSONL export (http://herb.ac.cn/).

Species-native: no identity edges, no catalog wiring needed.
Coverage flows via store.species_native_with_claims.

Licensed under open_content (Open Academic Access).
Strictly adheres to Rule 14b (Epistemic Separation): Traditional TCM concepts
are cited in authentic vocabulary and never reduced to Western biochemical assays.
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

SRC_ID = "SRC-HERB-TCM"
REF_DEFAULT = "Fang, S. et al. (2021). HERB: a high-throughput experiment- and reference-guided database of traditional Chinese medicine. Nucleic Acids Research, 49(D1), D1197-D1206. http://herb.ac.cn/"

NATURE_KEYWORDS = ("warm", "cold", "cool", "hot", "neutral")
FLAVOR_KEYWORDS = ("sweet", "bitter", "pungent", "acrid", "sour", "salty", "astringent", "bland")


def _slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def _is_binomial(latin: str) -> bool:
    """Check whether a Latin name is a standard two-part binomial."""
    parts = latin.strip().split()
    return len(parts) == 2 and parts[0][0].isupper() and parts[1][0].islower()


def parse_properties(prop_str: str) -> tuple[list[str], list[str]]:
    """Split TCM property string (e.g. 'Minor Warm; Sweet; Slightly Bitter') into natures and flavors."""
    natures: list[str] = []
    flavors: list[str] = []
    parts = [p.strip() for p in re.split(r"[;,]+", prop_str) if p.strip()]
    for p in parts:
        low = p.lower()
        if any(k in low for k in NATURE_KEYWORDS):
            natures.append(p)
        elif any(k in low for k in FLAVOR_KEYWORDS):
            flavors.append(p)
        else:
            flavors.append(p)
    return natures, flavors


def parse_meridians(meridian_str: str) -> list[str]:
    """Split meridian channel string (e.g. 'Lung; Spleen; Heart') into list."""
    return [m.strip() for m in re.split(r"[;,]+", meridian_str) if m.strip()]


# ---------------------------------------------------------------------------
# Claim Generation
# ---------------------------------------------------------------------------

def iter_herb_claims(record: dict[str, Any]) -> Iterator[Claim]:
    """Convert a single HERB JSONL record dictionary into unified claims.

    Species-native: produces identity (subject = species_id) and claims
    but no identity edges. Coverage flows via store.species_native_with_claims.

    Records with empty or non-binomial latin_name are skipped (yields nothing).
    """
    latin_name = record.get("latin_name") or ""
    if not latin_name or not _is_binomial(latin_name):
        return

    subject = species_id(latin_name)
    ref = record.get("herb_id") or REF_DEFAULT

    # Identifiers & names (traditional_use)
    if record.get("pinyin_name"):
        yield Claim(
            subject=subject,
            group="traditional_use",
            field="tcm:pinyin",
            v=str(record["pinyin_name"]).strip(),
            src=SRC_ID,
            derivation="literature",
            ref=ref,
        )

    if record.get("chinese_name"):
        yield Claim(
            subject=subject,
            group="traditional_use",
            field="tcm:chinese_name",
            v=str(record["chinese_name"]).strip(),
            src=SRC_ID,
            derivation="literature",
            ref=ref,
        )

    if record.get("english_name"):
        yield Claim(
            subject=subject,
            group="traditional_use",
            field="tcm:english_name",
            v=str(record["english_name"]).strip(),
            src=SRC_ID,
            derivation="literature",
            ref=ref,
        )

    # Properties (Nature & Flavor)
    if record.get("properties"):
        natures, flavors = parse_properties(str(record["properties"]))
        for n in natures:
            yield Claim(
                subject=subject,
                group="traditional_use",
                field="tcm:nature",
                v=n,
                src=SRC_ID,
                derivation="literature",
                ref=ref,
            )
        for f in flavors:
            yield Claim(
                subject=subject,
                group="traditional_use",
                field="tcm:flavor",
                v=f,
                src=SRC_ID,
                derivation="literature",
                ref=ref,
            )

    # Meridians
    if record.get("meridians"):
        for m in parse_meridians(str(record["meridians"])):
            yield Claim(
                subject=subject,
                group="traditional_use",
                field="tcm:meridian",
                v=m,
                src=SRC_ID,
                derivation="literature",
                ref=ref,
            )

    # Molecules / Chemical ingredients → molecule:herb:{lowercase-HBIN-ID}
    for ing in record.get("ingredients") or []:
        if isinstance(ing, dict):
            hbin = ing.get("id") or ""
            ing_name = ing.get("name") or ""
        else:
            hbin = ""
            ing_name = str(ing)
        if not ing_name:
            continue
        hbin_lower = hbin.lower() if hbin else ""
        field = f"molecule:herb:{hbin_lower}" if hbin_lower else f"molecule:herb:{_slugify(ing_name)}"
        # Ref includes herb_id and latin_name
        ref_with_latin = f"{ref} | {latin_name}" if latin_name else ref
        yield Claim(
            subject=subject,
            group="molecules",
            field=field,
            v=ing_name,
            src=SRC_ID,
            derivation="literature",
            ref=ref_with_latin,
        )


# --------------------------------------------------------------------------
# Ingest Adapter
# --------------------------------------------------------------------------

class HerbAdapter(BaseIngestAdapter):
    """Streaming JSONL ingest adapter for HERB TCM database.

    Species-native: no identity edges, no catalog wiring needed.
    Coverage flows via store.species_native_with_claims.

    Records with empty or non-binomial latin_name are skipped
    (honest reporting: these are coverage gaps, not errors).
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
                            yield from iter_herb_claims(rec)
            elif f.suffix == ".json":
                data = json.loads(f.read_text(encoding="utf-8"))
                records = data if isinstance(data, list) else [data]
                for rec in records:
                    yield from iter_herb_claims(rec)


register(HerbAdapter())