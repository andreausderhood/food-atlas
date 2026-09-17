#!/usr/bin/env python3
"""Independent, read-only QA audit of Food Atlas build artifacts. Pure stdlib.

Deliberately imports nothing from `atlas` so it can never inherit the build's
own bugs; it re-derives every finding from the artifact dict on disk.

Audited artifact: data/build/atlas.json (payload written by atlas.build),
cross-checked against claims.csv / gaps.csv / NOTICE.md when present.

Usage: python3 tools/audit_build.py [--root ROOT]
Exit codes: 0 audited, no findings; 1 audited with findings; 2 build absent;
3 unexpected tool failure.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json
import math
import re
import sys
from pathlib import Path

EXPECTED_MISSING = {"SRC-FDC-FOUNDATION-2026-04": "fdc_foundation",
                    "SRC-FDC-SRLEGACY-2018-04": "fdc_srlegacy",
                    "SRC-BLS-4.0": "bls"}
PMC_RE = re.compile(r"\bPMC[0-9]+\b")


def _err(errors: list, code: str, **detail) -> None:
    errors.append({"code": code, **detail})


def audit_payload(payload: dict) -> dict:
    """Audit an in-memory atlas.json payload; the CLI adds file cross-checks."""
    stats = payload.get("stats") or {}
    sources = {s["id"]: s for s in payload.get("sources", [])}
    foods = payload.get("foods", [])
    organisms = payload.get("organisms", [])
    claims = [c for f in foods for c in f.get("claims", [])]
    claims += [c for o in organisms for c in o.get("claims", [])]
    gaps = payload.get("gaps", [])
    errors: list[dict] = []

    # -- counts: re-derived, and cross-checked against stats ----------------
    counts = {"foods": len(foods), "organisms": len(organisms),
              "claims": len(claims), "gaps": len(gaps), "sources": len(sources)}
    if stats.get("accepted") != len(claims):
        _err(errors, "stats_mismatch", field="accepted", stats=stats.get("accepted"), actual=len(claims))
    if stats.get("gaps") != len(gaps):
        _err(errors, "stats_mismatch", field="gaps", stats=stats.get("gaps"), actual=len(gaps))
    if sorted(stats.get("sources_used") or []) != sorted(used := {c["src"] for c in claims}):
        _err(errors, "stats_mismatch", field="sources_used", stats=stats.get("sources_used"), actual=sorted(used))

    # -- rule 2: every claim src resolves -----------------------------------
    for c in claims:
        if c["src"] not in sources:
            _err(errors, "unresolved_claim_source", subject=c.get("subject"), field=c.get("field"), src=c["src"])
    unresolved_gaps = sorted({g["src"] for g in gaps if g.get("src") and g["src"] not in sources})
    for gap in gaps:
        if gap.get("src") in unresolved_gaps and (gap.get("rule") != 2 or gap.get("carried_value") is not None):
            _err(errors, "unresolved_gap_source", src=gap["src"])

    # -- rule 6/1: numeric amounts need unit, basis, part, finite value -----
    checked = 0
    for c in claims:
        for field in ("v", "v_min", "v_max", "n"):
            value = c.get(field)
            if isinstance(value, float) and not math.isfinite(value):
                _err(errors, "non_finite", subject=c.get("subject"), field=field)
        if c.get("group") not in ("nutrition", "molecules"):
            continue
        v = c.get("v")
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            continue
        checked += 1
        if not math.isfinite(v):
            _err(errors, "non_finite", subject=c.get("subject"), field=c.get("field"))
        if c.get("basis") not in ("fresh_weight", "dry_weight", "as_sold"):
            _err(errors, "invalid_amount", subject=c.get("subject"), field=c.get("field"), missing="valid_basis")
        if c.get("derivation") == "extracted":
            _err(errors, "accepted_extracted_amount", subject=c.get("subject"), field=c.get("field"))
        for field in ("unit", "basis", "food_part"):
            if not c.get(field):
                _err(errors, "invalid_amount", subject=c.get("subject"), field=c.get("field"), missing=field)

    # -- rule 9: license gate -----------------------------------------------
    for c in claims:
        s = sources.get(c.get("src"))
        if not s:
            continue
        if c.get("group") not in s.get("supports", []):
            _err(errors, "source_scope", src=s["id"], group=c.get("group"))
        if s.get("license_class") == "cite" and (not c.get("curated") or not c.get("ref")):
            _err(errors, "source_license", src=s["id"], problem="cite requires curated fact and reference")
        if not s.get("license") or s.get("license_read") is not True:
            _err(errors, "source_license", src=s["id"], problem="missing or unread license")
        if s.get("license_class") not in ("ship", "cite"):
            _err(errors, "source_license", src=s["id"], license_class=s.get("license_class"))
        elif s.get("license_class") == "ship" and not s.get("license_read"):
            _err(errors, "source_license", src=s["id"], problem="license_read false for ship class")

    # -- excluded FoodAtlas ids must never appear ---------------------------
    excluded = payload.get("excluded_foodatlas", {})
    violations = [c["subject"] for c in claims
                  if any(str(e) in (c.get("ref") or "") for e in excluded)]
    for f in foods:
        for fa in f.get("foodatlas_ids", []):
            if fa in excluded:
                _err(errors, "excluded_mapping", food=f["id"], foodatlas_id=fa)
    for c in claims:
        for fa in (re.findall(r"\be\d+\b", str(c.get("ref") or ""))):
            if fa in excluded:
                _err(errors, "excluded_mapping", subject=c.get("subject"), foodatlas_id=fa)

    # -- duplicates ----------------------------------------------------------
    seen: dict = {}
    for c in claims:
        key = json.dumps(c, sort_keys=True, ensure_ascii=False)
        seen[key] = seen.get(key, 0) + 1
    for key, n in seen.items():
        if n > 1:
            _err(errors, "duplicate_claim", claim=key, n=n)

    # -- molecules: presence needs PMC refs, amounts are separate rows -------
    pmc_ids = sorted({m for c in claims if c.get("v") == "present" for m in PMC_RE.findall(c.get("ref") or "")})
    for c in claims:
        if c.get("v") == "present" and c.get("group") == "molecules" and c.get("src", "").startswith("SRC-FOODATLAS") and not PMC_RE.findall(c.get("ref") or ""):
            _err(errors, "missing_pmc", subject=c.get("subject"), field=c.get("field"))

    # -- expected missing downloads are NOT implementation errors -----------
    expected_missing = []
    datasets = {v: k for k, v in EXPECTED_MISSING.items()} | {"foodatlas": "SRC-FOODATLAS-V4.11"}
    missing = stats.get("missing_raw") or []
    if bool(missing) != bool(stats.get("partial")):
        _err(errors, "partial_flag_mismatch")
    for dataset in sorted(set(missing)):
        sid = datasets.get(dataset)
        matching = [g for g in gaps if g.get("subject") == "dataset:" + dataset
                    and g.get("field") == "raw_source" and g.get("rule") == 5
                    and g.get("src") == sid and g.get("carried_value") is None]
        if sid not in sources or len(matching) != 1:
            _err(errors, "missing_raw_gap", dataset=dataset)
        else:
            expected_missing.append({"dataset": dataset, "src_id": sid,
                                     "classification": "declared_missing_download",
                                     "evidence": "stats.missing_raw + matching registered rule-5 dataset gap"})
    for kind, rows in (("foods", foods), ("organisms", organisms), ("sources", payload.get("sources", []))):
        for key, count in Counter(r.get("id") for r in rows).items():
            if count > 1:
                _err(errors, "duplicate_id", collection=kind, id=key, count=count)
    for sid, source in sources.items():
        actual = sum(c.get("src") == sid for c in claims)
        if source.get("claims") != actual:
            _err(errors, "stats_mismatch", field="source.claims", src=sid, actual=actual)
    for field in ("foodatlas_ids", "bls_codes"):
        owners = {}
        for food in foods:
            for value in food.get(field, []):
                if value in owners:
                    _err(errors, "duplicate_mapping", field=field, value=value, owners=[owners[value], food["id"]])
                owners[value] = food["id"]
    for owner in foods + organisms:
        for claim in owner.get("claims", []):
            if claim.get("subject") != owner["id"]:
                _err(errors, "claim_owner_mismatch", owner=owner["id"], subject=claim.get("subject"))

    return {
        "schema_version": 1,
        "status": "ok" if not errors else "findings",
        "counts": counts,
        "implementation_errors": errors,
        "expected_missing_sources": expected_missing,
        "source_licenses": [
            {"id": sid, "license": s.get("license"), "license_class": s.get("license_class"),
             "license_read": s.get("license_read"), "claims": sum(1 for c in claims if c["src"] == sid)}
            for sid, s in sorted(sources.items())
        ],
        "numeric_checks": {"checked": checked},
        "excluded_mappings": {"ids": sorted(excluded), "violations": [e for e in errors if e["code"] == "excluded_mapping"]},
        "unresolved_source_refs": {"gaps": [{"src": g["src"]} for g in gaps if g.get("src") not in sources]},
        "duplicates": [{"claim": k, "n": n} for k, n in seen.items() if n > 1],
        "pmc": {"presence_claims": sum(1 for c in claims if c.get("v") == "present"),
                "ids": sorted({m for c in claims if c.get("v") == "present" for m in PMC_RE.findall(c.get("ref") or "")})},
        "limitations": [
            "Static audit of atlas.json only; the DuckDB file and parquet sources are not re-parsed.",
            "License conclusions are taken from the registry, not re-verified against publisher pages.",
            "Presence claims from literature extraction are tier 3 and unvalidated by upstream.",
        ],
    }


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.links = []
        self.duplicate_ids = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        anchor = attrs.get("id") or (attrs.get("name") if tag == "a" else None)
        if anchor:
            if anchor in self.ids:
                self.duplicate_ids.append(anchor)
            self.ids.add(anchor)
        for name in ("href", "src"):
            if attrs.get(name):
                self.links.append(attrs[name])


def audit_site(site: Path, root: Path, report: dict) -> None:
    site = site.resolve()
    links = {"checked": 0, "external_skipped": 0, "broken": [], "html_pages": 0}
    report["internal_links"] = links
    if not site.is_dir():
        report.setdefault("limitations", []).append("Site absent; HTML and internal links not audited.")
        return
    pages = {}
    for path in sorted(site.rglob("*.html")):
        if not path.resolve().is_relative_to(site):
            _err(report["implementation_errors"], "site_symlink_escape", file=str(path))
            continue
        pages[path.resolve()] = Page(path.read_text(encoding="utf-8"))
    links["html_pages"] = len(pages)
    for path, page in pages.items():
        for anchor in page.duplicate_ids:
            _err(report["implementation_errors"], "duplicate_html_id", file=str(path.relative_to(site)), anchor=anchor)
        for href in page.links:
            url = urlsplit(href)
            if url.scheme or url.netloc:
                links["external_skipped"] += 1
                continue
            links["checked"] += 1
            decoded = unquote(url.path)
            target = ((site / decoded.lstrip("/")) if decoded.startswith("/") else (path.parent / decoded)) if decoded else path
            target = target.resolve()
            reason = None
            if not target.is_relative_to(site):
                reason = "outside_site"
            else:
                if target.is_dir():
                    target /= "index.html"
                if not target.is_file():
                    reason = "missing_file"
                elif url.fragment and target in pages and unquote(url.fragment) not in pages[target].ids:
                    reason = "missing_fragment"
            if reason:
                item = {"file": str(path.relative_to(site)), "href": href, "reason": reason}
                links["broken"].append(item)
                _err(report["implementation_errors"], "broken_internal_link", **item)


def _not_built(root: Path) -> dict:
    return {
        "schema_version": 1, "status": "not_built", "root": str(root),
        "counts": {"foods": None, "organisms": None, "claims": None, "gaps": None, "sources": None},
        "implementation_errors": [], "expected_missing_sources": [],
        "limitations": ["data/build/atlas.json not found; run `uv run atlas build` first."],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only, offline audit of data/build/atlas.json. "
                                     "Pure stdlib, no atlas imports. Exit codes: 0 audited, no findings; "
                                     "1 audited with findings; 2 build absent; 3 unexpected tool failure.")
    parser.add_argument("--root", default=".", help="project root containing data/build/atlas.json")
    args = parser.parse_args()
    artifact = Path(args.root) / "data/build/atlas.json"
    try:
        if not artifact.exists():
            report = _not_built(artifact.parent.parent)
        else:
            payload = json.loads(artifact.read_text(encoding="utf-8"))
            report = audit_payload(payload)
            # Cross-check CSV siblings when present.
            for name, key in (("claims.csv", "claims"), ("gaps.csv", "gaps")):
                path = artifact.parent / name
                if path.exists():
                    with path.open(newline="", encoding="utf-8") as f:
                        n = sum(1 for _ in csv.DictReader(f))
                    if n != report["counts"][key]:
                        _err(report["implementation_errors"], "csv_mismatch", file=name, rows=n, payload=report["counts"][key])
            if not (Path(args.root) / "NOTICE.md").exists():
                _err(report["implementation_errors"], "notice_missing")
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"status": "tool_failure", "error": repr(e)}))
        return 3
    print(json.dumps(report, indent=1, allow_nan=False))
    if report["status"] == "not_built":
        return 2
    return 1 if report["implementation_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
