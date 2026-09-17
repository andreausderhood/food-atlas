"""USDA FoodData Central CSV (Foundation Foods, SR Legacy) → nutrition claims."""
from __future__ import annotations

import csv
import re
from collections.abc import Iterator
from pathlib import Path

from atlas.claims import Claim, UnmappedDerivation
from atlas.foods import FoodNode, basis, food_part

REQUIRED_FILES = ("food.csv", "food_nutrient.csv", "nutrient.csv", "food_nutrient_derivation.csv")
# Ordered: the first matching rule wins, so "calculated from analytical" is calculated.
DERIVATION_RULES = (
    (("assumed zero",), "assumed_zero"),
    (("manufacturer", "label"), "label"),
    (("based on", "another form", "similar food", "borrowed"), "borrowed"),
    (("calculated", "summed", "recipe", "formula", "ratio", "computed"), "calculated"),
    (("imputed", "estimated", "assumed"), "imputed"),
    (("analytical", "analysis"), "analytical"),
)
NOT_RAW = re.compile(
    r"\b(cooked|boiled|baked|fried|roasted|dried|dehydrated|frozen|canned|juice|sauce|pickled)\b", re.IGNORECASE
)


class FdcMappingError(ValueError):
    pass


def classify_derivation(description: str) -> str:
    text = description.lower()
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


def match_foods(descriptions: dict[str, str], nodes: dict[str, FoodNode]) -> dict[str, str]:
    patterns = [(n.id, re.compile(p, re.IGNORECASE)) for n in nodes.values() for p in n.fdc_match]
    matched: dict[str, str] = {}
    for fdc_id, desc in descriptions.items():
        hits = sorted({node_id for node_id, p in patterns if p.fullmatch(desc)})
        if len(hits) > 1:
            raise FdcMappingError(f"FDC {fdc_id} {desc!r} matches several foods: {hits}")
        if hits:
            node_id = hits[0]
            if nodes[node_id].level != "form" and NOT_RAW.search(desc):
                raise FdcMappingError(f"FDC {fdc_id} {desc!r} is processed but {node_id} is not a form")
            matched[fdc_id] = node_id
    return matched


def _num(value: str | None) -> float | None:
    return float(value) if value not in (None, "") else None


def load_fdc(root: Path, src_id: str, nodes: dict[str, FoodNode]) -> tuple[list[Claim], dict[str, dict]]:
    folder = find_csv_dir(root)
    derivation_text = {r["id"]: r["description"] for r in read_csv_rows(folder / "food_nutrient_derivation.csv")}
    nutrients = {r["id"]: {"name": r["name"], "unit": r["unit_name"].lower()} for r in read_csv_rows(folder / "nutrient.csv")}
    matched = match_foods({r["fdc_id"]: r["description"] for r in read_csv_rows(folder / "food.csv")}, nodes)
    claims: list[Claim] = []
    used: dict[str, dict] = {}
    for r in read_csv_rows(folder / "food_nutrient.csv"):
        node_id = matched.get(r["fdc_id"])
        if node_id is None or r.get("amount", "") == "":
            continue
        node = nodes[node_id]
        derivation_id = r.get("derivation_id") or ""
        if derivation_id and derivation_id not in derivation_text:
            raise UnmappedDerivation(f"FDC derivation ID {derivation_id!r} is absent from the source table")
        derivation = classify_derivation(derivation_text[derivation_id]) if derivation_id else "unverified"
        key = f"nutrient:fdc:{r['nutrient_id']}"
        used[key] = nutrients[r["nutrient_id"]]
        claims.append(Claim(
            subject=node_id, group="nutrition", field=key, v=float(r["amount"]),
            unit=used[key]["unit"], basis=basis(node), food_part=food_part(node),
            src=src_id, derivation=derivation, ref=f"fdc:{r['fdc_id']}",
            v_min=_num(r.get("min")), v_max=_num(r.get("max")),
            n=int(r["data_points"]) if r.get("data_points") else None,
        ))
    return claims, used
