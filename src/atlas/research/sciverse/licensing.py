"""Rule-9 license triage: classify harvested documents by license text.

Classifies ONLY from the license string the index returns (docs/sciverse-prompts.md
§5/§14: an unread license is a build failure; venue reputation must never be
used as evidence). The `access_license` field is empty for most index records,
so most rows come back ``unknown`` — that is the honest state until the
license text is read at the venue.

CLI: ``atlas research sciverse --triage-licenses --execute``
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml

from atlas.research.sciverse.models import MetaFilter
from atlas.research.sciverse.pipeline import (
    CachedClient, DEFAULT_OUT_DIR, ResponseCache)

FIELDS = ["doc_id", "unique_id", "doi", "title", "publication_published_year",
          "publication_venue_name_unified", "access_is_oa",
          "access_oa_status", "access_license"]

# NOTE: query="*" breaks doc_id filtering — omit the query entirely.


def classify(license_str: str) -> tuple[str, bool]:
    """From the license STRING only. Returns (license_class, license_read)."""
    if not license_str:
        return ("unknown", False)
    lic = license_str.lower()
    if "by-nc" in lic or "noncommercial" in lic or "non-commercial" in lic:
        return ("adapter", True)
    if "by-sa" in lic or "by-nd" in lic or "odbl" in lic:
        return ("separate", True)
    if "cc0" in lic or "public domain" in lic or "cc-by" in lic or "cc by" in lic:
        return ("ship", True)
    if "all rights reserved" in lic or "rightsreserved" in lic.replace(" ", ""):
        return ("cite", True)
    return ("unknown", False)


def harvested_doc_ids(root: Path) -> set[str]:
    doc_ids: set[str] = set()
    for path in (root / DEFAULT_OUT_DIR).glob("*/findings.yaml"):
        rows = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        for row in rows:
            for hit in row.get("hits") or []:
                if hit.get("doc_id"):
                    doc_ids.add(hit["doc_id"])
    return doc_ids


def triage_licenses(root: Path, client: CachedClient | None = None) -> dict:
    client = client or CachedClient(
        ResponseCache(root / DEFAULT_OUT_DIR / "cache"), timeout=90.0)
    records: list[dict] = []
    missing: list[dict] = []
    for doc_id in sorted(harvested_doc_ids(root)):
        try:
            res = client.meta_search(
                filters=[MetaFilter(field="doc_id", operator="FILTER_OP_EQ",
                                    value=doc_id)],
                fields=FIELDS, page_size=1)
            results = res.results or []
        except Exception as exc:  # noqa: BLE001
            missing.append({"doc_id": doc_id, "error": str(exc)[:120]})
            continue
        if not results:
            missing.append({"doc_id": doc_id, "error": "not in meta-search index"})
            continue
        raw = results[0].raw
        license_str = str(raw.get("access_license") or "")
        license_class, license_read = classify(license_str)
        records.append({
            "doc_id": doc_id[:16],
            "doi": raw.get("doi") or "",
            "title": (raw.get("title") or "")[:100],
            "year": raw.get("publication_published_year"),
            "venue": raw.get("publication_venue_name_unified") or "",
            "access_is_oa": raw.get("access_is_oa") or "",
            "access_oa_status": raw.get("access_oa_status") or "",
            "license": license_str,
            "license_class": license_class,
            "license_read": license_read,
        })
    out = root / DEFAULT_OUT_DIR / "license-triage.yaml"
    with out.open("w", encoding="utf-8") as stream:
        yaml.safe_dump({"records": records, "not_resolved": missing}, stream,
                       allow_unicode=True, sort_keys=False, width=110)
    return {"records": len(records), "not_resolved": len(missing),
            "classes": dict(Counter(r["license_class"] for r in records))}


def run_cli(root, args) -> dict:
    return triage_licenses(root)
