#!/usr/bin/env python3
"""Build the unified species pool (Phase A2): EPD ∪ FAO ∪ Wikipedia.

Output: data/research/scope/species-pool.yaml — one record per binomial with
provenance, FAO item numbers (when present), EPD enrichment (edible parts,
distribution, growing, medicinal) and an onboarding priority.

Deterministic join, no network.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SCOPE = ROOT / "data/research/scope"

BINOMIAL_LEAD = re.compile(
    r"^([A-Z][a-z-]+(?:\s+[×x]\s*)?(?:\s+[a-z-]+){1,2})")


def canon(b: str) -> str:
    return b.lower().replace("×", "x").strip()


def load_fao_items() -> tuple[dict[str, list], set[str]]:
    parsed = json.loads((SCOPE / "fao-africa-1968/parsed.json").read_text())
    items: dict[str, list] = {}
    species: set[str] = set()
    for food in parsed["foods"].values():
        for sci in food.get("species", []):
            m = BINOMIAL_LEAD.match(sci)
            if not m:
                continue
            binomial = canon(m.group(1))
            species.add(binomial)
            items.setdefault(binomial, []).append({
                "item_no": food["item_no"], "name": food["name"],
                "group": food["group"],
                "has_values": any(v["values"] for v in food["variants"])})
    return items, species


def main() -> dict:
    epd = yaml.safe_load((SCOPE / "epd-zim/species-epd.yaml").read_text())
    wiki = yaml.safe_load((SCOPE / "species-candidates.yaml").read_text())
    fao_items, fao_species = load_fao_items()

    pool: dict[str, dict] = {}

    def slot(binomial: str) -> dict:
        key = canon(binomial)
        return pool.setdefault(key, {
            "binomial": key, "common_names": [], "sources": [],
            "fao_item_nos": [], "epd": None, "in_atlas": False})

    for key, rec in epd.items():
        rec = rec or {}
        entry = slot(key)
        entry["sources"].append("epd-zim")
        if rec.get("common"):
            entry["common_names"].append(rec["common"])
        entry["epd"] = {k: rec.get(k) for k in
                        ("edible_parts", "distribution", "grow", "identify",
                         "medicinal", "path") if rec.get(k)}
    for key, rec in wiki["candidates"].items():
        entry = slot(key)
        entry["sources"].extend(f"wiki:{s}" for s in rec.get("sources", []))
        entry["common_names"].extend(rec.get("common", []) or [])
    for binomial, items in fao_items.items():
        entry = slot(binomial)
        entry["sources"].append("fao-africa-1968")
        entry["fao_item_nos"] = items

    for entry in pool.values():
        entry["sources"] = sorted(set(entry["sources"]))
        entry["common_names"] = sorted(set(entry["common_names"]))[:6]
        # priority: FAO measured + EPD enrichment first, then FAO-only, then EPD-only
        if entry["fao_item_nos"] and any(i["has_values"] for i in entry["fao_item_nos"]):
            entry["priority"] = 1
        elif entry["fao_item_nos"]:
            entry["priority"] = 2
        elif entry["epd"]:
            entry["priority"] = 3
        else:
            entry["priority"] = 4

    out = SCOPE / "species-pool.yaml"
    yaml.safe_dump({"species": len(pool), "pool": pool}, out.open("w"),
                   allow_unicode=True, sort_keys=False, width=110)
    from collections import Counter
    stats = Counter(e["priority"] for e in pool.values())
    print(f"wrote {out} — {len(pool)} species; priority: {dict(sorted(stats.items()))}")
    return {"species": len(pool)}


if __name__ == "__main__":
    main()
