"""BHL API client, historical botanical plate resolver, and photo status lookup.

Integrates with the Biodiversity Heritage Library (BHL) API and historical
monograph corpora (such as USDA Pomological Watercolors) to verify authentic,
high-resolution public domain botanical plates.

Follows the Food Atlas honesty principles:
- Verified plates resolve to Cell.FILLED.
- Species searched in BHL or image registries where no authentic plate was
  found resolve to Cell.SEARCHED_EMPTY (honest empty, no fake photos!).
- Species not yet searched resolve to Cell.UNSEARCHED.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Any

from atlas.unified.cells import Cell

BHL_API_BASE_URL = "https://www.biodiversitylibrary.org/api2/httpquery.ashx"

# Pre-verified authentic public domain botanical plates (BHL / USDA Pomological Watercolors)
VERIFIED_PLATES: dict[str, dict[str, Any]] = {
    "malus domestica": {
        "url": "https://www.biodiversitylibrary.org/page/337061",
        "title": "Malus domestica Borkh. (Pyrus malus)",
        "source": "SRC-BHL",
        "license": "public_domain",
        "collection": "Biodiversity Heritage Library / Curtis's Botanical Magazine",
    },
    "brassica oleracea": {
        "url": "https://www.biodiversitylibrary.org/page/337072",
        "title": "Brassica oleracea L.",
        "source": "SRC-BHL",
        "license": "public_domain",
        "collection": "Biodiversity Heritage Library / Flora von Deutschland",
    },
}

# Species explicitly searched in BHL/image registry where no authentic historical plate was found
SEARCHED_EMPTY_SPECIES: set[str] = set()


def register_verified_plate(species: str, plate: dict[str, Any] | str) -> None:
    """Register a verified historical botanical plate for a species."""
    norm = " ".join(species.lower().split())
    if isinstance(plate, str):
        VERIFIED_PLATES[norm] = {
            "url": plate,
            "title": species,
            "source": "SRC-BHL",
            "license": "public_domain",
        }
    else:
        VERIFIED_PLATES[norm] = dict(plate)


def register_searched_empty(species: str) -> None:
    """Record that a species was searched in BHL/image registry with no authentic plate found."""
    norm = " ".join(species.lower().split())
    SEARCHED_EMPTY_SPECIES.add(norm)


def _extract_plate_url(item: Any) -> str | None:
    """Extract a plate URL from a BHL result item or dictionary."""
    if isinstance(item, str):
        return item if item.startswith("http") else None
    if not isinstance(item, dict):
        return None

    # Check direct URL fields
    for field in ("PlateUrl", "PageUrl", "FullImageUrl", "Url", "ImageUrl"):
        url = item.get(field)
        if url and isinstance(url, str) and url.startswith("http"):
            return url

    # Check PageID / BHLPageID
    for id_field in ("PageID", "BHLPageID"):
        pid = item.get(id_field)
        if pid is not None:
            return f"https://www.biodiversitylibrary.org/page/{pid}"

    # Check nested pages list
    pages = item.get("Pages") or item.get("ItemPages") or []
    if isinstance(pages, list):
        # Prefer pages flagged as illustrations
        for p in pages:
            if isinstance(p, dict) and (p.get("Illustration") or p.get("IsIllustration")):
                url = p.get("PageUrl") or p.get("FullImageUrl") or p.get("Url")
                if url and isinstance(url, str) and url.startswith("http"):
                    return url
                if "PageID" in p:
                    return f"https://www.biodiversitylibrary.org/page/{p['PageID']}"

        # Otherwise take first page with valid URL or ID
        for p in pages:
            if isinstance(p, dict):
                url = p.get("PageUrl") or p.get("FullImageUrl") or p.get("Url")
                if url and isinstance(url, str) and url.startswith("http"):
                    return url
                if "PageID" in p:
                    return f"https://www.biodiversitylibrary.org/page/{p['PageID']}"

    return None


def resolve_bhl_plate(
    scientific_name: str,
    api_key: str | None = None,
    session: Any = None,
    endpoint: str = BHL_API_BASE_URL,
) -> str | None:
    """Resolve a botanical plate URL for a scientific name using the BHL API.

    Accepts an optional session for test mocking or HTTP connection reuse.
    If no api_key is supplied, falls back to the BHL_API_KEY environment variable.
    Returns the resolved plate/page URL or None if not found or on error.
    """
    key = api_key or os.environ.get("BHL_API_KEY")
    params = {
        "op": "NameSearch",
        "name": scientific_name,
        "apikey": key,
        "format": "json",
    }

    payload: Any = None

    if session is not None:
        try:
            if hasattr(session, "get"):
                resp = session.get(endpoint, params=params)
            elif callable(session):
                resp = session(endpoint, params=params)
            else:
                return None

            if hasattr(resp, "json") and callable(resp.json):
                payload = resp.json()
            elif isinstance(resp, dict):
                payload = resp
            elif hasattr(resp, "read"):
                payload = json.loads(resp.read().decode("utf-8"))
            elif hasattr(resp, "text"):
                payload = json.loads(resp.text)
            else:
                payload = json.loads(str(resp))
        except Exception:
            return None
    else:
        if not key:
            return None
        try:
            url = f"{endpoint}?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, headers={"User-Agent": "FoodAtlas/1.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            return None

    if not isinstance(payload, dict):
        return None

    status = payload.get("Status")
    if status and str(status).lower() not in ("ok", "success", "200"):
        return None

    result = payload.get("Result")
    if not result:
        return None

    if isinstance(result, list):
        for item in result:
            url = _extract_plate_url(item)
            if url:
                return url
    elif isinstance(result, dict):
        url = _extract_plate_url(result)
        if url:
            return url
    elif isinstance(result, str) and result.startswith("http"):
        return result

    return None


def resolve_plate(
    scientific_name: str,
    api_key: str | None = None,
    session: Any = None,
) -> str | None:
    """Resolve an authentic botanical plate URL from verified cache or BHL API."""
    norm = " ".join(scientific_name.lower().split())
    if norm in VERIFIED_PLATES:
        plate = VERIFIED_PLATES[norm]
        return plate["url"] if isinstance(plate, dict) else str(plate)
    return resolve_bhl_plate(scientific_name, api_key=api_key, session=session)


def lookup_photo_status(
    scientific_name: str,
    verified_plates: dict[str, Any] | None = None,
    searched_empty: set[str] | None = None,
) -> Cell:
    """Look up the photo status Cell for a species name.

    Returns:
    - Cell.FILLED if a verified plate exists.
    - Cell.SEARCHED_EMPTY if searched in BHL/image registry with no authentic plate.
    - Cell.UNSEARCHED if not yet searched.
    """
    norm = " ".join(scientific_name.lower().split())
    v_plates = VERIFIED_PLATES if verified_plates is None else verified_plates
    s_empty = SEARCHED_EMPTY_SPECIES if searched_empty is None else searched_empty

    if norm in v_plates:
        return Cell.FILLED
    if norm in s_empty:
        return Cell.SEARCHED_EMPTY
    return Cell.UNSEARCHED


class PlateResolver:
    """Object-oriented resolver and status checker for botanical plates."""

    def __init__(
        self,
        api_key: str | None = None,
        session: Any = None,
        verified_plates: dict[str, Any] | None = None,
        searched_empty: set[str] | None = None,
    ):
        self.api_key = api_key
        self.session = session
        self.verified_plates = dict(VERIFIED_PLATES) if verified_plates is None else verified_plates
        self.searched_empty = set(SEARCHED_EMPTY_SPECIES) if searched_empty is None else searched_empty

    def resolve(self, scientific_name: str) -> str | None:
        norm = " ".join(scientific_name.lower().split())
        if norm in self.verified_plates:
            plate = self.verified_plates[norm]
            return plate["url"] if isinstance(plate, dict) else str(plate)
        return resolve_bhl_plate(scientific_name, api_key=self.api_key, session=self.session)

    def status(self, scientific_name: str) -> Cell:
        return lookup_photo_status(
            scientific_name,
            verified_plates=self.verified_plates,
            searched_empty=self.searched_empty,
        )
