"""HERB Traditional Chinese Medicine (TCM) Ingestion Adapter (open_content).

Produces authentic ``traditional_use`` claims (tcm:nature, tcm:flavor, tcm:meridian,
tcm:pinyin, tcm:chinese_name, tcm:english_name) and non-amount ``molecules`` presence
claims from HERB (http://herb.ac.cn/).

Strictly adheres to Rule 14b (Epistemic Separation): Traditional TCM concepts are cited
in authentic vocabulary and never reduced to Western biochemical assays.
"""
from __future__ import annotations

import json
import re
import urllib.request
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


def _extract_binomial(raw: str) -> str:
    """Extract standard genus + species binomial from botanical text."""
    clean = re.sub(r"^(Radix|Herba|Folium|Fructus|Cortex|Rhizoma|Semen|Flos)\s+", "", raw.strip(), flags=re.I)
    m = re.match(r"^([A-Z][a-z]+)\s+([a-z]+)", clean)
    if m:
        return f"{m.group(1)} {m.group(2)}"
    return clean


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


def iter_herb_claims(record: dict[str, Any], ref: str = REF_DEFAULT) -> Iterator[Claim]:
    """Convert a single HERB TCM record dictionary into unified claims."""
    raw_species = record.get("species_name") or record.get("latin_name") or ""
    taxon = _extract_binomial(raw_species)
    if not taxon:
        return

    subject = species_id(taxon)

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

    # Molecules / Chemical ingredients
    for ing in record.get("ingredients") or []:
        ing_name = ing.get("name") if isinstance(ing, dict) else str(ing)
        if not ing_name:
            continue
        slug = _slugify(ing_name)
        yield Claim(
            subject=subject,
            group="molecules",
            field=f"molecule-herb-{slug}",
            v=ing_name,
            src=SRC_ID,
            derivation="literature",
            ref=ref,
        )


# ---------------------------------------------------------------------------
# HERB API Client & Harvester
# ---------------------------------------------------------------------------

HERB_API_URL = "http://herb.ac.cn/chedi/api/"


def search_herb(keyword: str, timeout: int = 15) -> list[dict[str, Any]]:
    """Search HERB database by plant name, pinyin, or English name."""
    payload = json.dumps({"func_name": "search_api", "keyword": keyword, "label": "Herb"}).encode("utf-8")
    req = urllib.request.Request(
        HERB_API_URL,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "FoodAtlas/1.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="ignore"))

    res_data = data.get("res_data") or []
    if len(res_data) <= 1:
        return []

    headers = [str(h).lower() for h in res_data[0]]
    results = []
    for row in res_data[1:]:
        item = {}
        for h, val in zip(headers, row):
            if isinstance(val, dict):
                item[h] = val.get("title", "")
            else:
                item[h] = str(val) if val is not None else ""
        results.append(item)
    return results


def fetch_herb_detail(herb_id: str, timeout: int = 15) -> dict[str, Any] | None:
    """Fetch full TCM record details and ingredients for a given HERB ID."""
    payload = json.dumps({"func_name": "detail_api", "key_id": herb_id, "label": "Herb"}).encode("utf-8")
    req = urllib.request.Request(
        HERB_API_URL,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "FoodAtlas/1.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="ignore"))

    summary_rows = data.get("summary") or []
    if len(summary_rows) <= 1:
        return None

    # Summary headers: ['Herb id', 'Herb pinyin name', 'Herb Chinese name', 'Herb English name', 'Herb Latin name', 'Properties', 'Meridians', 'Use part', ...]
    s_row = summary_rows[1]

    def _val(idx: int) -> str:
        if idx >= len(s_row):
            return ""
        v = s_row[idx]
        return v.get("title", "") if isinstance(v, dict) else str(v or "")

    herb_id_val = _val(0)
    pinyin = _val(1)
    chinese = _val(2)
    english = _val(3)
    latin = _val(4)
    properties = _val(5)
    meridians = _val(6)
    use_part = _val(7)

    # Ingredients
    ingredients = []
    ing_rows = data.get("herb_ingredient") or []
    for r in ing_rows[1:]:
        if len(r) >= 2:
            iid = r[0].get("title", "") if isinstance(r[0], dict) else str(r[0] or "")
            name = str(r[1] or "").strip()
            alias = str(r[2] or "").strip() if len(r) >= 3 else ""
            if name:
                ingredients.append({"id": iid, "name": name, "alias": alias})

    species_candidate = _extract_binomial(use_part) or _extract_binomial(latin)

    return {
        "herb_id": herb_id_val,
        "pinyin_name": pinyin,
        "chinese_name": chinese,
        "english_name": english,
        "latin_name": latin,
        "properties": properties,
        "meridians": meridians,
        "species_name": species_candidate,
        "ingredients": ingredients,
    }


# ---------------------------------------------------------------------------
# Ingest Adapter
# ---------------------------------------------------------------------------

class TcmAdapter(BaseIngestAdapter):
    """Streaming ingest adapter for HERB Traditional Chinese Medicine database."""

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


register(TcmAdapter())
