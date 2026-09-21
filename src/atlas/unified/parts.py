"""Normalization and vocabulary mapping for edible parts.

Maps free-text part descriptions (e.g. from EPD/FPI) to the controlled
10-term vocabulary in atlas.foods.PARTS:
("whole", "head", "leaf", "inflorescence", "stem", "axillary_bud",
 "exocarp", "mesocarp", "seed", "seedling")
"""
from __future__ import annotations

import re
from atlas.foods import PARTS

# Canonical parts mapping
_PART_MAP: dict[str, str] = {
    # 1. Whole ("whole")
    "whole": "whole",
    "whole plant": "whole",
    "plant": "whole",
    "entire plant": "whole",
    "all parts": "whole",
    "aerial parts": "whole",
    "mushroom": "whole",
    "mushrooms": "whole",
    "fungus": "whole",
    "fungi": "whole",
    "truffle": "whole",
    "truffles": "whole",
    "seaweed": "whole",
    "seaweeds": "whole",
    "alga": "whole",
    "algae": "whole",
    "lichen": "whole",
    "lichens": "whole",

    # 2. Head ("head")
    "head": "head",
    "heads": "head",
    "cabbage": "head",
    "cabbages": "head",

    # 3. Leaf ("leaf")
    "leaf": "leaf",
    "leaves": "leaf",
    "frond": "leaf",
    "fronds": "leaf",
    "greens": "leaf",
    "foliage": "leaf",
    "needle": "leaf",
    "needles": "leaf",
    "petiole": "leaf",
    "petioles": "leaf",

    # 4. Inflorescence ("inflorescence")
    "inflorescence": "inflorescence",
    "inflorescences": "inflorescence",
    "flower": "inflorescence",
    "flowers": "inflorescence",
    "blossom": "inflorescence",
    "blossoms": "inflorescence",
    "floret": "inflorescence",
    "florets": "inflorescence",
    "flowering head": "inflorescence",
    "flowering heads": "inflorescence",
    "flower bud": "inflorescence",
    "flower buds": "inflorescence",
    "floral": "inflorescence",

    # 5. Stem ("stem") - includes botanical stems, roots, tubers, rhizomes, corms, bulbs, shoots
    "stem": "stem",
    "stems": "stem",
    "stalk": "stem",
    "stalks": "stem",
    "shoot": "stem",
    "shoots": "stem",
    "young shoot": "stem",
    "young shoots": "stem",
    "root": "stem",
    "roots": "stem",
    "taproot": "stem",
    "taproots": "stem",
    "tuber": "stem",
    "tubers": "stem",
    "tuberous root": "stem",
    "tuberous roots": "stem",
    "rhizome": "stem",
    "rhizomes": "stem",
    "corm": "stem",
    "corms": "stem",
    "bulb": "stem",
    "bulbs": "stem",
    "cane": "stem",
    "canes": "stem",
    "culm": "stem",
    "culms": "stem",
    "pith": "stem",
    "heart": "stem",
    "palm heart": "stem",
    "heart of palm": "stem",

    # 6. Axillary Bud ("axillary_bud")
    "axillary bud": "axillary_bud",
    "axillary buds": "axillary_bud",
    "axillary_bud": "axillary_bud",
    "axillary_buds": "axillary_bud",
    "bud": "axillary_bud",
    "buds": "axillary_bud",
    "terminal bud": "axillary_bud",
    "terminal buds": "axillary_bud",

    # 7. Exocarp ("exocarp") - peel, rind, skin, bark
    "exocarp": "exocarp",
    "exocarps": "exocarp",
    "peel": "exocarp",
    "peels": "exocarp",
    "rind": "exocarp",
    "rinds": "exocarp",
    "skin": "exocarp",
    "skins": "exocarp",
    "bark": "exocarp",
    "barks": "exocarp",
    "inner bark": "exocarp",
    "outer bark": "exocarp",
    "cortex": "exocarp",

    # 8. Mesocarp ("mesocarp") - fruit, pods, berries, flesh, pulp, arils
    "mesocarp": "mesocarp",
    "mesocarps": "mesocarp",
    "fruit": "mesocarp",
    "fruits": "mesocarp",
    "fruit mesocarp": "mesocarp",
    "flesh": "mesocarp",
    "fruit flesh": "mesocarp",
    "pulp": "mesocarp",
    "fruit pulp": "mesocarp",
    "pod": "mesocarp",
    "pods": "mesocarp",
    "berry": "mesocarp",
    "berries": "mesocarp",
    "pericarp": "mesocarp",
    "aril": "mesocarp",
    "arils": "mesocarp",
    "capsule": "mesocarp",
    "capsules": "mesocarp",
    "pepo": "mesocarp",
    "drupe": "mesocarp",
    "drupes": "mesocarp",
    "calyx": "mesocarp",

    # 9. Seed ("seed") - seeds, nuts, kernels, grains, beans
    "seed": "seed",
    "seeds": "seed",
    "nut": "seed",
    "nuts": "seed",
    "kernel": "seed",
    "kernels": "seed",
    "bean": "seed",
    "beans": "seed",
    "grain": "seed",
    "grains": "seed",
    "caryopsis": "seed",
    "pip": "seed",
    "pips": "seed",
    "stone": "seed",
    "stones": "seed",
    "endosperm": "seed",

    # 10. Seedling ("seedling") - sprouts, germinated seeds
    "seedling": "seedling",
    "seedlings": "seedling",
    "sprout": "seedling",
    "sprouts": "seedling",
    "germinated seed": "seedling",
    "germinated seeds": "seedling",
    "microgreen": "seedling",
    "microgreens": "seedling",
}


def normalize_part(raw: str) -> str | None:
    """Map a raw part token or phrase to a canonical part in atlas.foods.PARTS.

    Returns None if the token is empty, unparseable, or not a recognized plant part.
    """
    if not raw or not isinstance(raw, str):
        return None

    # Strip parenthesized qualifiers like "(POISONOUS)" or "(cooked)"
    cleaned = re.sub(r"\([^)]*\)", "", raw).strip()
    # Strip leading/trailing punctuation and whitespace
    cleaned = cleaned.strip(",;:.?!*\"'_-\t\r\n ")
    if not cleaned:
        return None

    # Normalize whitespace and separators
    norm = " ".join(cleaned.lower().replace("-", " ").replace("_", " ").split())
    if not norm:
        return None

    return _PART_MAP.get(norm)


def normalize_edible_parts(raw: list[str] | str | None) -> tuple[str, ...]:
    """Return a sorted, unique tuple of canonical parts from a raw parts field.

    Handles None, empty list, single string, or list of strings with trailing punctuation.
    """
    if raw is None:
        return ()

    raw_items: list[str] = []
    if isinstance(raw, str):
        raw_items = [raw]
    elif isinstance(raw, (list, tuple, set)):
        raw_items = [str(x) for x in raw if x is not None]
    else:
        return ()

    # First flatten items split by delimiters: commas, semicolons, slashes, newlines
    tokens: list[str] = []
    for item in raw_items:
        parts = re.split(r"[,;\n|/]+", item)
        for p in parts:
            p_strip = p.strip()
            if p_strip:
                tokens.append(p_strip)

    found: set[str] = set()

    # Pass 1: check each token directly
    for tok in tokens:
        part = normalize_part(tok)
        if part:
            found.add(part)
            continue
        # If not matched directly, check if it contains " and ", " & ", or " - "
        if re.search(r"\s+(?:and|&|-)\s+", tok, flags=re.IGNORECASE):
            sub_toks = re.split(r"\s+(?:and|&|-)\s+", tok, flags=re.IGNORECASE)
            for st in sub_toks:
                st_part = normalize_part(st)
                if st_part:
                    found.add(st_part)

    # Pass 2: check consecutive pairs from original list (e.g. ['Inner', 'bark,'] or ['Palm', 'heart'])
    for i in range(len(tokens) - 1):
        pair = f"{tokens[i]} {tokens[i + 1]}"
        pair_part = normalize_part(pair)
        if pair_part:
            found.add(pair_part)

    return tuple(sorted(found))
