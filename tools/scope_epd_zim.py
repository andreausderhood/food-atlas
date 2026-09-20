"""Scope expansion: Edible Plant Database ZIM → species-pool enrichment.

Reads the 9 GB Kiwix ZIM (libzim), extracts per-species structured fields:
binomial, family, common name, edible parts, distribution/countries, growing
ranges, medicinal tags. Output feeds data/research/scope/species-pool.yaml.

Read-only on the ZIM; write-only to scope dir. 9 GB file, no copying.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ZIM = ROOT / "data/datasets/edibleplantdb.zim"
OUT = ROOT / "data/research/scope/epd-zim/species-epd.yaml"

SECTION_RE = {
    "eat": "What to Eat",
    "distribution": "Where to Find It",
    "identify": "How to Identify",
    "grow": "How to Grow",
    "medicinal": "Medicinal Uses",
    "other_uses": "Other Uses",
}

BINOMIAL = re.compile(r"^[A-Z][a-z-]+(?:\s+[×x]\s*)?(?:\s+[a-z-]+){1,3}$")


def _clean(html: str) -> str:
    txt = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", txt).strip()


def _section(name: str, html: str) -> str | None:
    match = re.search(
        rf"<h2>{name}</h2>(.*?)(?=<h2>|</div>\s*</div>\s*<footer|$)", html, re.S)
    return _clean(match.group(1)) if match else None


def parse_plant(entry_title: str, html: str) -> dict:
    binomial = entry_title.split("—")[0].strip()
    common = entry_title.split("—", 1)[1].strip() if "—" in entry_title else ""
    sections = {key: _section(name, html) for key, name in SECTION_RE.items()}
    edible_parts: list[str] = []
    if sections["eat"]:
        match = re.match(r"Edible parts:\s*(.+?)(?:\.\s|\s[A-Z])", sections["eat"])
        if match:
            edible_parts = match.group(1).split()
    family = None
    match = re.search(r"More from ([A-Za-z-]+)</a>", html) or \
        re.search(r'More from <a[^>]*>([A-Za-z-]+)</a>', html)
    if match:
        family = match.group(1)
    return {
        "binomial": binomial,
        "common": common,
        "family": family,
        "edible_parts": [p for p in edible_parts if p],
        "distribution": sections["distribution"][:300] if sections["distribution"] else None,
        "identify": sections["identify"][:300] if sections["identify"] else None,
        "grow": sections["grow"][:300] if sections["grow"] else None,
        "medicinal": sections["medicinal"][:200] if sections["medicinal"] else None,
    }


def main(zim_path: Path = ZIM, limit: int | None = None) -> dict:
    import libzim  # noqa: F401  (runtime install: uv pip install libzim)
    from libzim.reader import Archive
    archive = Archive(zim_path)
    # enumerate plant articles via country-independent family-less strategy:
    # the /plants/<id>/<slug> namespace; iterate via suggestions is bounded,
    # so walk with get_entry_by_path from slug enumeration instead: use the
    # title index through suggest() per letter is unreliable — read all paths
    # from the dirent list with a low-level iterator.
    # libzim python exposes iteration only through suggest(); practical route:
    # follow family pages. But families are discovered via index page links.
    index_html = archive.get_entry_by_path("index").get_item().content.tobytes().decode("utf-8", "replace")
    families = sorted(set(re.findall(r'href="families/([^"]+)"', index_html)))
    countries = sorted(set(re.findall(r'href="countries/([^"]+)"', index_html)))
    plant_paths: set[str] = set()
    for country in countries:
        html = archive.get_entry_by_path(f"countries/{country}").get_item() \
            .content.tobytes().decode("utf-8", "replace")
        plant_paths.update(re.findall(r'href="\.\./plants/(\d+/[a-z0-9-]+)"', html))
        if limit and len(plant_paths) >= limit:
            break
    records: dict[str, dict] = {}
    for rel in sorted(plant_paths)[:limit] if limit else sorted(plant_paths):
        path = f"plants/{rel}"
        entry = archive.get_entry_by_path(path)
        html = entry.get_item().content.tobytes().decode("utf-8", "replace")
        record = parse_plant(entry.title, html)
        record["path"] = path
        records[record["binomial"].lower()] = record
    stats = {
        "plant_paths": len(plant_paths),
        "families_on_index": len(set(re.findall(r'href="families/', index_html or ""))),
        "countries": len(countries),
        "records": len(records),
    }
    out_dir = ROOT / "data/research/scope/epd-zim"
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "species-epd.yaml").open("w", encoding="utf-8") as stream:
        yaml.safe_dump(records, stream, allow_unicode=True, width=100)
    (out_dir / "stats.json").write_text(json.dumps(stats, indent=2))
    return stats


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    print(json.dumps(main(limit=limit)))
