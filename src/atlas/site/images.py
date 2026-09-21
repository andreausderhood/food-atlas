"""Offline, explicitly mapped photographs for the pilot plant atlas.

No name, species, parent, part or cultivar fallback is permitted. Images are
reference photographs, not botanical identification evidence. The registry may
hold tombstones ({removed: reason}); they resolve to no image. Keep the registry
and data/images together; the site builder copies assets into output/images.
"""
from __future__ import annotations

from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

DATA_DIR = Path(__file__).resolve().parents[3] / "data"


@lru_cache(maxsize=1)
def _registry() -> dict[str, dict[str, Any]]:
    path = DATA_DIR / "registry" / "images.yaml"
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def image_for(food: Any) -> dict[str, Any] | None:
    """Return a fresh image dict for an exact food ID, or None.

    Accept a FoodNode, the site payload's mapping, or an explicit ``food:...``
    string. Unknown cultivars and processed foods stay image-less rather than
    silently inheriting a photograph of their parent species.
    """
    if isinstance(food, str):
        food_id = food
    elif isinstance(food, Mapping):
        food_id = food.get("id")
    else:
        food_id = getattr(food, "id", None)
    if not isinstance(food_id, str):
        return None
    image = _registry().get(food_id)
    return dict(image) if image and image.get("url") else None
