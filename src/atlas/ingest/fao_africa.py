"""Ingest the FAO "Food Composition Table for Use in Africa" (Leung, Busson &
Jardin 1968, FAO/US-HEW) — the underused-foods funnel source.

Source pages: https://www.fao.org/4/x6877e/X6877E01.htm … X6877E31.htm
Layout (verified against the live pages, 2026-09):
  - E05–E19: composition tables, 21 columns, split across pages by nutrient
    groups; same foods repeat per page, keyed by Item No.
  - E23–E26: scientific-name index mapping item numbers to binomials.
  - E02: food groups.
License: work of the U.S. Government (17 USC §105, US-HEW 1968), FAO
co-sponsorship asks attribution. Recorded in data/registry/sources.yaml as
SRC-FAO-AFRICA-1968.
"""
from __future__ import annotations

import re
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path

NUTRIENT_COLS = (
    "energy_cal", "moisture_pct", "protein_g", "fat_g", "carb_g", "fiber_g",
    "ash_g", "calcium_mg", "phosphorus_mg", "iron_mg", "retinol_ug",
    "beta_carotene_ug", "thiamine_mg", "riboflavin_mg", "niacin_mg",
    "tryptophan_mg", "ascorbic_acid_mg", "refuse_pct",
)
COMPOSITION_PAGES = range(5, 20)  # E05..E19
INDEX_PAGES = range(23, 27)  # E23..E26


class _TableDump(HTMLParser):
    """Collect non-empty <tr> rows as stripped cell lists."""

    def __init__(self):
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append(re.sub(r"\s+", " ", "".join(self._cell)).strip())
            self._cell = None
        elif tag == "tr" and self._row is not None and any(self._row):
            self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def _rows(path: Path) -> list[list[str]]:
    if not path.exists():
        return []  # partial bundles (real ingest spans E01..E31)
    parser = _TableDump()
    parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
    return parser.rows


def _number(cell: str) -> float | None:
    cell = cell.replace(",", "").replace("--", "").strip()
    if not cell:
        return None
    try:
        return float(cell)
    except ValueError:
        return None


def parse_composition(bundle: Path) -> dict[str, dict]:
    """Join the continuous table spanning E05–E19 (item numbers run 1–~1594
    across page breaks). Heading rows carry item no + food name (often with
    the binomial); variant rows beneath carry the values; annotation rows
    (parenthesized footnote markers, `min–max` ranges) are skipped, never
    parsed as data. Values are per 100 g edible portion as printed."""
    foods: dict[str, dict] = {}
    group = ""
    heading: tuple[str, str, str] | None = None

    def clean(cell: str) -> float | None:
        cell = cell.strip()
        if (not cell or cell.startswith("(") or "–" in cell or "--" in cell
                or cell.endswith("?") and cell[:-1].replace(",", "").replace(".", "").isdigit() is False):
            return None
        return _number(cell)

    for page_no in COMPOSITION_PAGES:
        for row in _rows(bundle / f"X6877E{page_no:02d}.htm"):
            # group banners: standalone (2 cells) or merged with the units row
            # (20 cells) at the table start
            if len(row) >= 2 and not row[0] and re.match(r"^\d+\..+?:$", row[1].strip()) \
                    and not any(re.search(r"\d", c) for c in row[2:]):
                group = row[1].strip().rstrip(":").split(".", 1)[1].strip()
                continue
            if len(row) == 2:
                continue
            if len(row) != 21:
                continue
            col0, name, french, *cells = row
            values = {key: v for key, cell in zip(NUTRIENT_COLS, cells)
                      if (v := clean(cell)) is not None}
            if col0:
                key = col0.rstrip(".").strip()
                if not key.isdigit():
                    continue
                food = foods.setdefault(key, {"item_no": key, "name": "", "french_name": "",
                                              "group": group, "variants": []})
                food["group"] = food["group"] or group
                if name and "continued" not in name:
                    food["name"] = name.rstrip(": ")
                if french:
                    food["french_name"] = food["french_name"] or french
                heading = (key, name.rstrip(": "), french)
                if values:
                    food["variants"].append({"name": "", "values": values})
            elif values and heading is not None:
                food = foods.setdefault(heading[0], {"item_no": heading[0], "name": "", "french_name": "",
                                                     "group": group, "variants": []})
                if name and "continued" not in name:
                    food["variants"].append({"name": name, "values": values})
    # default variant when only the heading row carried values under a variant
    for food in foods.values():
        food.setdefault("variants", [])
    return foods


def parse_species_index(bundle: Path) -> dict[str, list[dict]]:
    """E23–E26: scientific name ↔ item no. Two-row blocks — a binomial row
    followed by rows of (part/preparation, item no)."""
    index: dict[str, list[dict]] = defaultdict(list)
    current: str | None = None
    label = ""
    for page_no in INDEX_PAGES:
        rows = _rows(bundle / f"X6877E{page_no:02d}.htm")
        for row in rows:
            if len(row) < 4:
                continue
            sci, english, item_no, _french = row[:4]
            item_no = item_no.rstrip(".").strip()
            if sci and re.match(r"^[A-Z][a-z]+(?:\s+[a-z-]+)?", sci):
                current = re.sub(r"\s+", " ", sci).strip()
            if current and item_no.isdigit():
                entry = {"name": english, "item_no": item_no}
                if entry not in index[current]:
                    index[current].append(entry)
    return dict(index)


def ingest(bundle: Path) -> dict:
    foods = parse_composition(bundle)
    species = parse_species_index(bundle)
    item_species: dict[str, list[str]] = defaultdict(list)
    for sci, entries in species.items():
        for entry in entries:
            item_species[entry["item_no"]].append(sci)
    for item_no, scis in item_species.items():
        if item_no in foods:
            foods[item_no]["species"] = sorted(set(scis))
    for food in foods.values():
        food.setdefault("species", [])
    foods = {key: food for key, food in foods.items()
             if key.isdigit()}  # section artifacts are not item numbers
    return {
        "foods": dict(sorted(foods.items(), key=lambda kv: int(kv[0]))),
        "stats": {
            "food_items": len(foods),
            "items_with_species": sum(1 for f in foods.values() if f["species"]),
            "species_total": len(species),
            "items_with_values": sum(1 for f in foods.values()
                                     if any(v["values"] for v in f["variants"])),
            "total_variants": sum(len(f["variants"]) for f in foods.values()),
        },
    }


def main(root: Path) -> dict:
    bundle = root / "data/research/scope/fao-africa-1968"
    result = ingest(bundle)
    import json
    out = root / "data/research/scope/fao-africa-1968/parsed.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    return result["stats"]


if __name__ == "__main__":
    import sys
    print(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()))
