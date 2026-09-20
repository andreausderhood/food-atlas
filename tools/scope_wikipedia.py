#!/usr/bin/env python3
"""Scope-expansion scraper: candidate edible-species pool from Wikipedia lists.

Writes data/research/scope/species-candidates.yaml — one record per binomial
with provenance. Read-only on the web; all parsing local.

Usage: .venv/bin/python tools/scope_wikipedia.py
"""
from __future__ import annotations

import re
import sys
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

BINOMIAL = re.compile(r"^[A-Z][a-z-]+(?:\s+[×x]\s*)?(?:\s+[a-z-]+){1,3}$")
TR = re.compile(r"<tr\b.*?</tr>", re.S)
ITALIC = re.compile(r"<i\b[^>]*>(.*?)</i>", re.S)
TAG = re.compile(r"<[^>]+>")
LINK = re.compile(r"<a\b[^>]*>(.*?)</a>", re.S)

# curated from Category:Lists of foods — the lists that name plants/species
PAGES = {
    "culinary-fruits": (
        "https://en.wikipedia.org/wiki/List_of_culinary_fruits", "table"),
    "vegetables": (
        "https://en.wikipedia.org/wiki/List_of_vegetables", "table"),
    "leaf-vegetables": (
        "https://en.wikipedia.org/wiki/List_of_leaf_vegetables", "table"),
    "culinary-nuts": (
        "https://en.wikipedia.org/wiki/List_of_culinary_nuts", "table"),
    "edible-seeds": (
        "https://en.wikipedia.org/wiki/List_of_edible_seeds", "table"),
    "citrus": (
        "https://en.wikipedia.org/wiki/List_of_citrus_fruits", "table"),
    "gourds-squashes": (
        "https://en.wikipedia.org/wiki/List_of_gourds_and_squashes", "table"),
    "herbs-spices": (
        "https://en.wikipedia.org/wiki/List_of_culinary_herbs_and_spices", "table"),
}


def fetch_wikitext(title: str) -> str:
    url = f"https://en.wikipedia.org/w/index.php?title={title}&action=raw"
    req = urllib.request.Request(url, headers={"User-Agent": "food-atlas-scope/0.1"})
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
        return resp.read().decode("utf-8", "replace")


BINOMIAL_LINE = re.compile(
    r"^[A-Z][a-z-]+(?:\s+[×x]\s*)?(?:\s+[a-z-]+){1,3}(?:\s*\([^)]*\))?$")
APOS = re.compile(r"''+")


def _clean_cell(cell: str) -> str:
    cell = APOS.sub("", cell)
    cell = re.sub(r"\[\[(?:[^]|]*\|)?([^]]+)\]\]", r"\1", cell)
    cell = re.sub(r"\[(?:https?://[^ \]]+|[^ \]]+)\s+([^]]+)\]", r"\1", cell)
    cell = re.sub(r"\{\{[^}]*\}\}", "", cell)
    cell = re.sub(r"<ref[^>]*>.*?</ref>", "", cell, flags=re.S)
    cell = re.sub(r"<ref[^/>]*/>", "", cell)
    cell = cell.replace("[[", "").replace("]]", "").replace("'''", "")
    return cell.strip()


def parse_wikitext(text: str) -> list[dict]:
    out: list[dict] = []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith(("|}", "{|", "!", "|-")) or not line:
            continue
        cells = [_clean_cell(c) for c in line.strip("|").split("|")] \
            if line.startswith("|") else [_clean_cell(line.lstrip("* ").strip())]
        if not line.startswith("|"):
            cells = [c.lstrip("* ").strip() for c in [line]]
        bins = []
        common = ""
        for cell in cells:
            probe = re.sub(r"\s*\([^)]*\)$", "", cell).strip()
            if BINOMIAL_LINE.match(probe):
                bins.append(cell)
            elif cell and not common:
                common = cell
        for binomial in bins:
            out.append({"binomial": binomial, "common": common})
    return out


def parse_binomials(html: str) -> list[dict]:
    out: list[dict] = []
    for row in TR.findall(html):
        binomials = [re.sub(r"\s+", " ", TAG.sub("", it)).strip()
                     for it in ITALIC.findall(row)]
        binomials = [b for b in binomials if BINOMIAL.match(b)]
        if not binomials:
            continue
        names = [re.sub(r"\s+", " ", TAG.sub("", a)).strip()
                 for a in LINK.findall(row)]
        common = next((n for n in names if n and n.lower() != binomials[0].lower()), "")
        for binomial in binomials:
            out.append({"binomial": binomial, "common": common})
    return out


def main() -> int:
    out_dir = ROOT / "data/research/scope"
    out_dir.mkdir(parents=True, exist_ok=True)
    candidates: dict[str, dict] = {}
    per_page: dict[str, int] = {}
    for slug, (url, _kind) in PAGES.items():
        title = url.split("/wiki/")[1]
        rows = parse_wikitext(fetch_wikitext(title))
        per_page[slug] = len(rows)
        for row in rows:
            key = row["binomial"].lower().replace("×", "x")
            rec = candidates.setdefault(key, {"binomial": row["binomial"], "sources": [],
                                              "common": set()})
            if slug not in rec["sources"]:
                rec["sources"].append(slug)
            if row["common"] and row["common"] not in rec["common"]:
                rec["common"].add(row["common"])
    for rec in candidates.values():
        rec["common"] = sorted(rec["common"])
    payload = {
        "stats": {"unique_binomials": len(candidates),
                  "per_page": per_page},
        "candidates": dict(sorted(candidates.items())),
    }
    out = out_dir / "species-candidates.yaml"
    with out.open("w", encoding="utf-8") as stream:
        yaml.safe_dump(payload, stream, allow_unicode=True, sort_keys=False, width=100)
    print(f"wrote {out} — {len(candidates)} unique binomials")
    print(per_page)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
