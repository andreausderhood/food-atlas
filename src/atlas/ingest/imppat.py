"""IMPPAT 2.0 Indian Medicinal Plants, Phytochemistry And Therapeutics Ingest Adapter.

Produces authentic ``traditional_use`` claims (Ayurvedic properties: Rasa, Guna, Virya,
Vipaka, Dosha, and therapeutic uses) and non-amount ``molecules`` presence claims
from IMPPAT 2.0 (https://cb.imsc.res.in/imppat/).

Licensed under CC-BY-NC-SA-4.0 (open_content with source citation & non-commercial attribution).
Strictly adheres to Rule 14b (Epistemic Separation): Traditional Ayurvedic concepts are
cited in authentic native Sanskrit vocabulary and never reduced to Western assays.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from collections.abc import Iterator
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from atlas.claims import Claim
from atlas.ingest.base import BaseIngestAdapter, register
from atlas.unified.identity import species_id

SRC_ID = "SRC-IMPPAT-2.0"
REF_DEFAULT = "Mohanraj, K. et al. (2018). IMPPAT: A curated database of Indian Medicinal Plants, Phytochemistry And Therapeutics. Scientific Reports, 8, 4329. cb.imsc.res.in/imppat/."
IMPPAT_AJAX_URL = "https://cb.imsc.res.in/imppat/ajax"


def _slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def _strip_tags(html_text: str) -> str:
    """Strip HTML tags and unescape text."""
    clean = re.sub(r"<[^>]+>", " ", html_text)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


# ---------------------------------------------------------------------------
# HTML Table Parsers (Standard Library, zero external dependencies)
# ---------------------------------------------------------------------------

class _SimpleTableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows: list[list[str]] = []
        self._current_row: list[str] = []
        self._current_cell: list[str] = []
        self._in_cell = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        if tag in ("td", "th"):
            self._in_cell = True
            self._current_cell = []
        elif tag == "tr":
            self._current_row = []

    def handle_endtag(self, tag: str):
        if tag in ("td", "th"):
            self._in_cell = False
            self._current_row.append("".join(self._current_cell).strip())
        elif tag == "tr":
            if self._current_row:
                self.rows.append(self._current_row)

    def handle_data(self, data: str):
        if self._in_cell:
            self._current_cell.append(data)


def parse_imppat_phytochemical_table(html: str) -> list[dict[str, str]]:
    """Parse phytochemical table HTML from IMPPAT AJAX response."""
    parser = _SimpleTableParser()
    parser.feed(html)
    out: list[dict[str, str]] = []
    for row in parser.rows:
        # Expected row: [Plant, Plant part, IMPPAT Phytochemical ID, Phytochemical name, References]
        if len(row) >= 4 and not any(h in row[0].lower() for h in ("indian medicinal plant", "plant part")):
            plant = row[0]
            part = row[1] if len(row) > 1 else ""
            phy_id = row[2] if len(row) > 2 else ""
            name = row[3] if len(row) > 3 else ""
            ref = row[4] if len(row) > 4 else ""
            if name:
                out.append({
                    "plant_name": plant,
                    "plant_part": part,
                    "phytochemical_id": phy_id,
                    "name": name,
                    "reference": ref or REF_DEFAULT,
                })
    return out


def parse_imppat_therapeutics_table(html: str) -> list[dict[str, str]]:
    """Parse therapeutics table HTML from IMPPAT AJAX response."""
    parser = _SimpleTableParser()
    parser.feed(html)
    out: list[dict[str, str]] = []
    for row in parser.rows:
        # Expected row: [Plant, Plant part, Therapeutic use, Identifiers (MESH, etc.), References]
        if len(row) >= 3 and not any(h in row[0].lower() for h in ("indian medicinal plant", "plant part")):
            plant = row[0]
            part = row[1] if len(row) > 1 else ""
            tu = row[2] if len(row) > 2 else ""
            mesh = row[3] if len(row) > 3 else ""
            ref = row[4] if len(row) > 4 else ""
            if tu:
                out.append({
                    "plant_name": plant,
                    "plant_part": part,
                    "therapeutic_use": tu,
                    "mesh_id": mesh,
                    "reference": ref or REF_DEFAULT,
                })
    return out


# ---------------------------------------------------------------------------
# Claim Generation
# ---------------------------------------------------------------------------

def iter_imppat_claims(record: dict[str, Any]) -> Iterator[Claim]:
    """Convert an IMPPAT record dictionary into unified claims."""
    plant_name = record.get("plant_name") or ""
    if not plant_name:
        return

    subject = species_id(plant_name)

    # 1. Ayurvedic Classical Properties (Rasa, Guna, Virya, Vipaka, Dosha)
    ayur = record.get("ayurvedic_properties") or {}

    def _emit_props(field_name: str, values: Any):
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

    yield from _emit_props("ayurveda:rasa", ayur.get("rasa"))
    yield from _emit_props("ayurveda:guna", ayur.get("guna"))
    yield from _emit_props("ayurveda:virya", ayur.get("virya"))
    yield from _emit_props("ayurveda:vipaka", ayur.get("vipaka"))
    yield from _emit_props("ayurveda:dosha", ayur.get("dosha"))

    # 2. Therapeutic Uses
    for tu_item in record.get("therapeutics") or []:
        tu_name = tu_item.get("therapeutic_use") or ""
        if not tu_name:
            continue
        slug = _slugify(tu_name)
        ref = tu_item.get("reference") or record.get("reference") or REF_DEFAULT
        part = tu_item.get("plant_part")
        yield Claim(
            subject=subject,
            group="traditional_use",
            field=f"ayurveda:therapeutic-{slug}",
            v=tu_name,
            src=SRC_ID,
            derivation="literature",
            food_part=part if part else None,
            ref=ref,
        )

    # 3. Phytochemicals (Molecules Presence)
    for phy in record.get("phytochemicals") or []:
        phy_name = phy.get("name") or ""
        if not phy_name:
            continue
        slug = _slugify(phy_name)
        ref = phy.get("reference") or record.get("reference") or REF_DEFAULT
        part = phy.get("plant_part")
        yield Claim(
            subject=subject,
            group="molecules",
            field=f"molecule-imppat-{slug}",
            v=phy_name,
            src=SRC_ID,
            derivation="literature",
            food_part=part if part else None,
            ref=ref,
        )


# ---------------------------------------------------------------------------
# Live API Queries
# ---------------------------------------------------------------------------

def fetch_imppat_phytochemicals(plant_name: str, timeout: int = 15) -> list[dict[str, str]]:
    """Fetch phytochemicals table for an Indian medicinal plant from IMPPAT AJAX."""
    post_data = urllib.parse.urlencode({
        "combine": plant_name,
        "pid": "",
        "pname": "",
        "action": "phytochemical",
    }).encode("utf-8")
    req = urllib.request.Request(
        IMPPAT_AJAX_URL,
        data=post_data,
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "FoodAtlas/1.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        res = json.loads(resp.read().decode("utf-8", errors="ignore"))
    html = res.get("output", "")
    return parse_imppat_phytochemical_table(html)


def fetch_imppat_therapeutics(plant_name: str, timeout: int = 15) -> list[dict[str, str]]:
    """Fetch therapeutic uses table for an Indian medicinal plant from IMPPAT AJAX."""
    post_data = urllib.parse.urlencode({
        "combine": plant_name,
        "tu": "",
        "action": "therapeutics",
    }).encode("utf-8")
    req = urllib.request.Request(
        IMPPAT_AJAX_URL,
        data=post_data,
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "FoodAtlas/1.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        res = json.loads(resp.read().decode("utf-8", errors="ignore"))
    html = res.get("output", "")
    return parse_imppat_therapeutics_table(html)


def fetch_imppat_record(plant_name: str, timeout: int = 15) -> dict[str, Any]:
    """Fetch combined phytochemicals and therapeutics for a plant."""
    phys = fetch_imppat_phytochemicals(plant_name, timeout=timeout)
    tus = fetch_imppat_therapeutics(plant_name, timeout=timeout)
    return {
        "plant_name": plant_name,
        "ayurvedic_properties": {},
        "phytochemicals": phys,
        "therapeutics": tus,
    }


# ---------------------------------------------------------------------------
# Ingest Adapter
# ---------------------------------------------------------------------------

class ImppatAdapter(BaseIngestAdapter):
    """Streaming ingest adapter for IMPPAT 2.0 Ayurvedic database."""

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
                            yield from iter_imppat_claims(rec)
            elif f.suffix == ".json":
                data = json.loads(f.read_text(encoding="utf-8"))
                records = data if isinstance(data, list) else [data]
                for rec in records:
                    yield from iter_imppat_claims(rec)


register(ImppatAdapter())
