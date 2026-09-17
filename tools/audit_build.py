#!/usr/bin/env python3
"""Read-only, offline audit of data/build/atlas.json. Pure stdlib, no atlas imports.

Exit codes: 0 audited, no findings; 1 audited with findings; 2 build absent;
3 unexpected tool failure.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
import sys
from pathlib import Path

RAW_DATASETS = ("fdc_foundation", "fdc_srlegacy", "bls", "foodatlas")
UNKNOWN = "unknown"


def as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def audit_payload(payload: dict) -> dict:
    foods = as_list(payload.get("foods"))
    organisms = as_list(payload.get("organisms"))
    claims = [c for f in foods for c in as_list(f.get("claims"))]
    claims += [c for o in organisms for c in as_list(o.get("claims"))]
    gaps = as_list(payload.get("gaps"))
    sources = as_list(payload.get("sources"))
    stats = payload.get("stats") or {}

    numeric = {"checked": 0, "without_basis": 0, "without_food_part": 0, "non_finite": 0}
    src_ids = {s.get("id") for s in sources if s.get("id")}
    unresolved_refs = []
    for c in claims:
        if isinstance(c.get("v"), (int, float)) and not isinstance(c.get("v"), bool):
            numeric["checked"] += 1
            if not c.get("basis"):
                numeric["without_basis"] += 1
            if not c.get("food_part"):
                numeric["without_food_part"] += 1
            if isinstance(c.get("v"), float) and not math.isfinite(c["v"]):
                numeric["non_finite"] += 1
        if c.get("src") not in src_ids:
            unresolved_refs.append(c.get("src"))

    by_id = {s.get("id"): s for s in sources if s.get("id")}
    used = sorted({c.get("src") for c in claims} - {None})
    source_licenses = [{"id": sid, "license": (by_id.get(sid) or {}).get("license", UNKNOWN),
                        "license_class": (by_id.get(sid) or {}).get("license_class", UNKNOWN),
                        "license_read": bool((by_id.get(sid) or {}).get("license_read")),
                        "claims": sum(1 for c in claims if c.get("src") == sid)}
                       for sid in used]
    missing_raw = sorted(stats.get("missing_raw") or [])
    expected = [{"dataset": name,
                 "src_id": next((sid for sid in src_ids if sid.endswith(name.upper())
                                 or name in sid.lower()), name),
                 "classification": "expected_missing_download",
                 "evidence": f"payload stats.missing_raw={missing_raw}; partial={stats.get('partial')}"}
                for name in missing_raw]

    excluded = payload.get("excluded_foodatlas") or {}
    mapped = {fa: f["id"] for f in foods for fa in as_list(f.get("foodatlas_ids"))}
    violations = sorted(set(mapped) & set(excluded))

    errors = []

    def error(code, **evidence):
        errors.append({"code": code, **evidence})

    unresolved = {"claims": [], "gaps": []}
    for kind, rows in (("claims", claims), ("gaps", gaps)):
        for i, row in enumerate(rows):
            if row.get("src") not in src_ids and (kind == "claims" or row.get("src")):
                item = {"index": i, "src": row.get("src"), "subject": row.get("subject")}
                unresolved[kind].append(item)
                # An explicitly quarantined rule-2 gap is not an accepted provenance failure.
                if kind == "claims" or row.get("rule") != 2 or row.get("carried_value") is not None:
                    error("unresolved_claim_source" if kind == "claims" else "unresolved_gap_source", **item)

    numeric = {"checked": 0, "invalid_basis": 0, "without_food_part": 0,
               "without_unit": 0, "non_finite": 0}
    pmc_ids, missing_pmc, presence = set(), [], 0
    for i, claim in enumerate(claims):
        amount = claim.get("group") in ("nutrition", "molecules") and type(claim.get("v")) in (int, float)
        if amount:
            numeric["checked"] += 1
            bad = []
            if claim.get("basis") not in ("fresh_weight", "dry_weight", "as_sold"):
                numeric["invalid_basis"] += 1
                bad.append("basis")
            for key, counter in (("food_part", "without_food_part"), ("unit", "without_unit")):
                if not isinstance(claim.get(key), str) or not claim[key].strip():
                    numeric[counter] += 1
                    bad.append(key)
            if bad:
                error("invalid_amount", index=i, fields=bad)
            if claim.get("derivation") == "extracted":
                error("accepted_extracted_amount", index=i)
        for key in ("v", "v_min", "v_max", "n"):
            value = claim.get(key)
            if isinstance(value, float) and not math.isfinite(value):
                numeric["non_finite"] += 1
                error("non_finite", index=i, field=key)
        source = by_id.get(claim.get("src"))
        if source:
            licensed = (source.get("license_read") is True and bool(source.get("license"))
                        and source.get("license_class") in ("ship", "cite"))
            if source.get("license_class") == "cite":
                licensed = licensed and claim.get("curated") is True and bool(claim.get("ref"))
            if not licensed:
                error("source_license", index=i, src=claim.get("src"))
            if claim.get("group") not in source.get("supports", []):
                error("source_scope", index=i, src=claim.get("src"))
        ids = set(re.findall(r"\bPMC[0-9]+\b", claim.get("ref") or ""))
        pmc_ids.update(ids)
        if claim.get("group") == "molecules" and claim.get("v") == "present":
            presence += 1
            if str(claim.get("src", "")).startswith("SRC-FOODATLAS") and not ids:
                missing_pmc.append(i)
                error("missing_pmc", index=i)

    duplicate_report = {}
    for kind, rows in (("foods", foods), ("organisms", organisms), ("sources", sources)):
        duplicate_report[kind] = sorted(str(k) for k, n in Counter(r.get("id") for r in rows).items() if n > 1)
        for key in duplicate_report[kind]:
            error("duplicate_id", collection=kind, id=key)
    # Exact repeats only: independent sources and different references are not duplicates.
    duplicate_report["claims"] = []
    seen = {}
    for i, claim in enumerate(claims):
        key = json.dumps(claim, sort_keys=True, ensure_ascii=False)
        if key in seen:
            duplicate_report["claims"].append({"index": i, "first_index": seen[key]})
            error("duplicate_claim", index=i, first_index=seen[key])
        else:
            seen[key] = i
    duplicate_report["mappings"] = []
    for mapping in ("foodatlas_ids", "bls_codes"):
        owners = {}
        for food in foods:
            for value in as_list(food.get(mapping)):
                if value in owners:
                    item = {"mapping": mapping, "value": value, "foods": [owners[value], food.get("id")]}
                    duplicate_report["mappings"].append(item)
                    error("duplicate_mapping", **item)
                owners[value] = food.get("id")
    for value in violations:
        error("excluded_mapping", foodatlas_id=value, food=mapped[value])
    for key, actual in (("accepted", len(claims)), ("gaps", len(gaps)), ("sources_used", used)):
        if stats.get(key) != actual:
            error("stats_mismatch", field=key, declared=stats.get(key), actual=actual)
    for source in sources:
        actual = sum(c.get("src") == source.get("id") for c in claims)
        if source.get("claims") != actual:
            error("stats_mismatch", field="source.claims", src=source.get("id"), actual=actual,
                  declared=source.get("claims"))
    if bool(missing_raw) != bool(stats.get("partial")):
        error("partial_flag_mismatch")
    expected = []
    for name in missing_raw:
        matches = [g for g in gaps if g.get("subject") == "dataset:" + name and g.get("field") == "raw_source"]
        if not matches or any(g.get("src") not in src_ids for g in matches):
            error("missing_raw_gap", dataset=name)
        else:
            expected.append({"dataset": name, "src_id": matches[0]["src"],
                             "classification": "declared_missing_download",
                             "evidence": "stats.missing_raw and matching dataset raw_source gap"})
    source_licenses = [{"id": s.get("id"), "license": s.get("license"),
                        "license_class": s.get("license_class"), "license_read": s.get("license_read"),
                        "claims": sum(c.get("src") == s.get("id") for c in claims)} for s in sources]

    return {
        "schema_version": 1,
        "unresolved_source_refs": unresolved,
        "duplicates": duplicate_report,
        "pmc": {"ids": sorted(pmc_ids), "presence_claims": presence, "missing_reference_indices": missing_pmc},
        "counts": {"foods": len(foods), "organisms": len(organisms), "claims": len(claims),
                   "gaps": len(gaps), "sources": len(sources)},
        "implementation_errors": errors,
        "expected_missing_sources": expected,
        "source_licenses": source_licenses,
        "numeric_checks": numeric,
        "excluded_mappings": {"excluded_ids": sorted(excluded), "violations": violations},
        "limitations": [],
    }


def audit(root: Path) -> dict:
    root = Path(root).resolve()
    atlas = root / "data/build/atlas.json"
    report = {"schema_version": 1, "root": str(root), "status": "not_built",
              "counts": dict.fromkeys(("foods", "organisms", "claims", "gaps", "sources")),
              "implementation_errors": [], "expected_missing_sources": [],
              "source_licenses": [], "numeric_checks": {}, "excluded_mappings": {},
              "limitations": []}
    if not atlas.is_file():
        report["limitations"].append(
            "data/build/atlas.json absent: build not audited; no source failure inferred.")
        return report
    try:
        payload = json.loads(atlas.read_text(encoding="utf-8"))
        report.update(audit_payload(payload))
        report["status"] = "ok"
    except Exception as exc:  # narrow, reported as limitation
        report["limitations"].append(f"atlas.json unreadable: {exc!r}")
        report["status"] = "unreadable"
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    report = audit(args.root)
    print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
    if report["status"] == "not_built":
        return 2
    return 3 if report["status"] != "ok" else 1 if report["implementation_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
