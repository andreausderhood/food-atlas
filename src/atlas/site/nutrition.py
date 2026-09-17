"""Render accepted payload claims; never load, synthesize, or join food records.

This is a selected FDC profile, not an exhaustive nutrient catalog. Definitions
and units were checked against the local USDA Foundation nutrient.csv. In
particular 2000 and 1063 are distinct dictionary entries, not interchangeable
fallbacks. The importer supplies amounts per 100 g on each claim's stated basis.
"""
from collections import defaultdict
import math
import re

# FDC identity, exact dictionary label, unit, display group.
_SPECS = [
    (1003, "Protein", "g", "macronutrients"),
    (1004, "Total lipid (fat)", "g", "macronutrients"),
    (1005, "Carbohydrate, by difference", "g", "macronutrients"),
    (1079, "Fiber, total dietary", "g", "macronutrients"),
    (2000, "Total Sugars", "g", "macronutrients"),
    (1063, "Sugars, Total", "g", "macronutrients"),
    (1051, "Water", "g", "macronutrients"),
    (1050, "Carbohydrate, by summation", "g", "macronutrients"),
    (1087, "Calcium, Ca", "mg", "minerals"),
    (1089, "Iron, Fe", "mg", "minerals"),
    (1090, "Magnesium, Mg", "mg", "minerals"),
    (1091, "Phosphorus, P", "mg", "minerals"),
    (1092, "Potassium, K", "mg", "minerals"),
    (1093, "Sodium, Na", "mg", "minerals"),
    (1095, "Zinc, Zn", "mg", "minerals"),
    (1098, "Copper, Cu", "mg", "minerals"),
    (1101, "Manganese, Mn", "mg", "minerals"),
    (1103, "Selenium, Se", "ug", "minerals"),
    (1162, "Vitamin C, total ascorbic acid", "mg", "vitamins"),
    (1106, "Vitamin A, RAE", "ug", "vitamins"),
    (1109, "Vitamin E (alpha-tocopherol)", "mg", "vitamins"),
    (1114, "Vitamin D (D2 + D3)", "ug", "vitamins"),
    (1165, "Thiamin", "mg", "vitamins"),
    (1166, "Riboflavin", "mg", "vitamins"),
    (1167, "Niacin", "mg", "vitamins"),
    (1170, "Pantothenic acid", "mg", "vitamins"),
    (1175, "Vitamin B-6", "mg", "vitamins"),
    (1177, "Folate, total", "ug", "vitamins"),
    (1178, "Vitamin B-12", "ug", "vitamins"),
    (1185, "Vitamin K (phylloquinone)", "ug", "vitamins"),
    (1008, "Energy", "kcal", "other"),
    (2047, "Energy (Atwater General Factors)", "kcal", "other"),
    (2048, "Energy (Atwater Specific Factors)", "kcal", "other"),
]
NUTRIENTS = {f"nutrient:fdc:{key}": dict(label=label, unit=unit, group=group)
             for key, label, unit, group in _SPECS}
# A stable compact baseline; alternate definitions appear only when reported.
_BASELINE = {1003, 1004, 1005, 1079, 2000, 1051, 1087, 1089, 1090, 1092, 1162, 1177}
_BASES = {"fresh_weight": "fresh weight", "dry_weight": "dry weight", "as_sold": "as sold"}


def _supported(claim):
    spec = NUTRIENTS.get(claim.get("field"))
    value = claim.get("v")
    flags = set(claim.get("flags") or [])
    return bool(
        spec and claim.get("group") == "nutrition"
        and isinstance(value, (int, float)) and not isinstance(value, bool)
        and math.isfinite(value) and value >= 0
        and str(claim.get("unit", "")).lower().replace("µ", "u").replace("μ", "u") == spec["unit"]
        and claim.get("basis") in _BASES and claim.get("food_part")
        and claim.get("src") and re.fullmatch(r"fdc:[0-9]+", claim.get("ref") or "")
        and claim.get("derivation") != "extracted"
        and not flags.intersection({"llm_extracted", "machine_extracted"})
        and not claim.get("machine_extracted")
    )


def _tile(field, claims):
    spec = NUTRIENTS[field]
    values = {c["v"] for c in claims}
    value = next(iter(values)) if len(values) == 1 else None
    unit = "µg" if spec["unit"] == "ug" else spec["unit"]
    display = "Conflicting values" if len(values) > 1 else "Not reported"
    if value is not None:
        # General formatting preserves very small nonzero values instead of
        # rounding them to an apparent zero. Raw precision remains in details.
        display = f"{value:g} {unit}"
    is_bar = spec["group"] == "macronutrients" and value is not None and value <= 100
    note = ""
    if spec["group"] == "macronutrients" and value is not None and value > 100:
        note = "Reported value is outside the 0–100 g scale; not plotted."
    return dict(field=field, label=spec["label"], unit=unit, value=value,
                display=display, bar_value=value if is_bar else None,
                note=note, claims=claims)


def nutrition_profile(food: dict) -> dict:
    """Consume only food['claims'] from the accepted build payload.

    Keep source, FDC reference, basis and part isolated. Missing amounts stay
    missing; conflicting duplicate amounts stay inspectable, not averaged or
    arbitrarily selected. This view does not replace upstream acceptance rules.
    """
    grouped = defaultdict(lambda: defaultdict(list))
    for claim in food.get("claims", []):
        if _supported(claim):
            key = tuple(claim[k] for k in ("src", "ref", "basis", "food_part"))
            grouped[key][claim["field"]].append(dict(claim))
    records = []
    for (src, ref, basis, part), fields in sorted(grouped.items()):
        record: dict = dict(src=src, ref=ref, basis=basis, food_part=part,
                      label=f"{src} · {ref} · {_BASES[basis]} · {part}",
                      macronutrients=[], minerals=[], vitamins=[], other=[])
        for field, spec in NUTRIENTS.items():
            if field in fields or int(field.rsplit(":", 1)[1]) in _BASELINE:
                record[spec["group"]].append(_tile(field, fields.get(field, [])))
        records.append(record)
    return {"records": records, "food_id": food.get("id"), "food_name": food.get("name")}
