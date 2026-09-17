"""USDA FoodData Central CSV (Foundation Foods, SR Legacy) → nutrition claims."""
from __future__ import annotations

import csv
import re
import warnings
from collections.abc import Iterator
from pathlib import Path

from atlas.claims import Claim, UnmappedDerivation
from atlas.foods import FoodNode, basis, food_part

REQUIRED_FILES = ("food.csv", "food_nutrient.csv", "nutrient.csv")
PUBLISHED_TYPES = {"foundation_food", "sr_legacy_food"}
# Foundation 2026-04 omits the lookup, but uses these same FDC derivation IDs.
# Transcribed from the downloaded SR Legacy 2018-04 food_nutrient_derivation.csv
# (archive SHA256 b80817294b8850530aaedf2e515c02593b1824f763a0ff356e5c2081643e6fd0).
# Its source_id=1 says "Analytical OR derived from analytical": AS is not analytical.
# Never use this fallback to fill holes in a supplied (authoritative) lookup.
FALLBACK_DERIVATIONS = {
    "1": ("A", "Analytical"),
    "4": ("AS", "Summed"),
    "49": ("NC", "Calculated"),
}
# Ordered: provenance and transformations take precedence over analytical inputs.
DERIVATION_RULES = (
    (("assumed zero",), "assumed_zero"),
    (("manufacturer", "label"), "label"),
    (("aggregated data",), "aggregated"),
    (("calculated", "summed", "recipe", "formulation", "formula", "linear regression",
      "concentration adjustment using factor", "computed"), "calculated"),
    (("imputed", "imputing", "estimated", "assumed"), "imputed"),
    (("based on", "another form", "similar food", "borrowed", "taken from another source"), "borrowed"),
    (("from the literature",), "literature"),
)
NOT_RAW = re.compile(
    r"\b(cooked|boiled|baked|fried|roasted|dried|dehydrated|frozen|canned|juice|sauce|pickled)\b", re.IGNORECASE
)


class FdcMappingError(ValueError):
    pass


def classify_derivation(description: str) -> str:
    text = " ".join(description.lower().split())
    if text in {"analytical", "analysis"}:
        return "analytical"
    for keys, derivation in DERIVATION_RULES:
        if any(k in text for k in keys):
            return derivation
    raise UnmappedDerivation(f"FDC derivation {description!r}")


def find_csv_dir(root: Path) -> Path:
    hits = sorted(root.rglob("food_nutrient.csv"))
    if len(hits) != 1:
        raise FileNotFoundError(f"expected one food_nutrient.csv under {root}, found {len(hits)}")
    folder = hits[0].parent
    missing = [f for f in REQUIRED_FILES if not (folder / f).exists()]
    if missing:
        raise FileNotFoundError(f"{folder}: missing {missing}")
    return folder


def read_csv_rows(path: Path) -> Iterator[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        yield from csv.DictReader(f)


def match_foods(
    descriptions: dict[str, str], nodes: dict[str, FoodNode],
) -> tuple[dict[str, str], set[tuple[str, str, str]]]:
    """Map FDC descriptions to atlas foods; also return registry conflicts that were skipped."""
    patterns = [(n.id, re.compile(p, re.IGNORECASE)) for n in nodes.values() for p in n.fdc_match]
    matched: dict[str, str] = {}
    skipped: set[tuple[str, str, str]] = set()
    for fdc_id, desc in descriptions.items():
        hits = sorted({node_id for node_id, p in patterns if p.fullmatch(desc)})
        if len(hits) > 1:
            raise FdcMappingError(f"FDC {fdc_id} {desc!r} matches several foods: {hits}")
        if hits:
            node_id = hits[0]
            if nodes[node_id].level != "form" and NOT_RAW.search(desc):
                # A processed FDC row must never feed a raw-part node; skip loudly instead of
                # inventing a mapping or aborting the whole bundle.
                skipped.add((fdc_id, desc, node_id))
                continue
            matched[fdc_id] = node_id
    return matched, skipped


def _num(value: str | None) -> float | None:
    return float(value) if value not in (None, "") else None


def load_fdc(root: Path, src_id: str, nodes: dict[str, FoodNode]) -> tuple[list[Claim], dict[str, dict]]:
    folder = find_csv_dir(root)
    lookup = folder / "food_nutrient_derivation.csv"
    has_lookup = lookup.exists()
    derivations = ({r["id"]: (r.get("code", ""), r["description"])
                    for r in read_csv_rows(lookup)} if has_lookup else FALLBACK_DERIVATIONS)
    if not has_lookup:
        # Reuse the downloaded shared FDC codebook when available; never download here.
        shared = sorted((root.parent / "fdc-srlegacy").rglob("food_nutrient_derivation.csv"))
        if len(shared) > 1:
            raise FdcMappingError("ambiguous shared SR Legacy derivation tables")
        if shared:
            derivations = {r["id"]: (r.get("code", ""), r["description"])
                           for r in read_csv_rows(shared[0])}
            for derivation_id, expected in FALLBACK_DERIVATIONS.items():
                if derivations.get(derivation_id) != expected:
                    raise UnmappedDerivation(f"shared FDC codebook disagrees for ID {derivation_id}")
    nutrients = {r["id"]: {"name": r["name"], "unit": r["unit_name"].lower()} for r in read_csv_rows(folder / "nutrient.csv")}
    # Sample/acquisition rows underpin published foods; importing both double counts evidence.
    matched, skipped = match_foods({r["fdc_id"]: r["description"]
                                    for r in read_csv_rows(folder / "food.csv")
                                    if r.get("data_type") in PUBLISHED_TYPES}, nodes)
    if skipped:
        warnings.warn(
            "FDC rows matching registry patterns but processed (skipped, registry pattern too broad): "
            + "; ".join(f"{fid} {desc!r} -> {node}" for fid, desc, node in sorted(skipped)),
            stacklevel=2,
        )
    claims: list[Claim] = []
    used: dict[str, dict] = {}
    for r in read_csv_rows(folder / "food_nutrient.csv"):
        node_id = matched.get(r["fdc_id"])
        if node_id is None or r.get("amount", "") == "":
            continue
        node = nodes[node_id]
        derivation_id = r.get("derivation_id") or ""
        flags: tuple[str, ...] = ()
        if derivation_id in derivations:
            code, description = derivations[derivation_id]
            derivation = classify_derivation(description)
            origin = "source table" if has_lookup else "SR Legacy 2018-04 lookup (bundled table absent)"
            method = f"FDC derivation {derivation_id} ({code}): {description}; {origin}"
        elif derivation_id and has_lookup:
            raise UnmappedDerivation(f"FDC derivation ID {derivation_id!r} is absent from the source table")
        else:
            derivation = "unverified"
            method = f"FDC derivation ID {derivation_id!r}: no documented derivation"
            flags = ("missing_derivation",) if not derivation_id else ("unmapped_derivation",)
        if not has_lookup:
            flags += ("missing_derivation_table",)
        key = f"nutrient:fdc:{r['nutrient_id']}"
        used[key] = nutrients[r["nutrient_id"]]
        claims.append(Claim(
            subject=node_id, group="nutrition", field=key, v=float(r["amount"]),
            unit=used[key]["unit"], basis=basis(node), food_part=food_part(node),
            src=src_id, derivation=derivation, ref=f"fdc:{r['fdc_id']}",
            method=method, flags=flags,
            v_min=_num(r.get("min")), v_max=_num(r.get("max")),
            n=int(r["data_points"]) if r.get("data_points") else None,
        ))
    return claims, used
