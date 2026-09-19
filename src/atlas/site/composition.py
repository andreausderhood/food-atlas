"""Composition: a whole is 100% of a declared basis; components are fractions.

Spec: docs/superpowers/specs/2026-09-19-entry-page-design.md §5. Where sources
disagree the spread is shown, so the reader is never asked to arbitrate and
disagreement is never hidden. An absent nutrient is absent, never zero.
"""
from __future__ import annotations


def _fmt(value: float) -> str:
    return f"{value:g}"


def _matching(claims: list[dict], label: str) -> list[dict]:
    return [c for c in claims
            if c.get("group") == "nutrition" and c.get("label") == label]


def reading(claims: list[dict], label: str) -> dict | None:
    """Collapse one nutrient's claims into a value or a range.

    Returns None when the nutrient is absent. Callers must render that as
    absent: a missing measurement is not a measurement of zero.
    """
    matching = _matching(claims, label)
    values = sorted({
        c["v"] for c in matching
        if isinstance(c.get("v"), (int, float)) and not isinstance(c.get("v"), bool)
    })
    if not values:
        return None
    best = min(matching, key=lambda c: c.get("tier", 5))
    return {
        "label": label,
        "low": values[0],
        "high": values[-1],
        "text": _fmt(values[0]) if len(values) == 1
                else f"{_fmt(values[0])}–{_fmt(values[-1])}",
        "is_range": len(values) > 1,
        "unit": best.get("unit") or "",
        "tier": best.get("tier", 5),
        "sources": len({c["src"] for c in matching}),
    }


WATER = "Water"
# FDC dictionary label -> display name. These five compose 100 g exactly:
# carbohydrate is "by difference", i.e. the remainder after the other four.
DRY_MATTER = (
    ("Carbohydrate, by difference", "Carbohydrate"),
    ("Protein", "Protein"),
    ("Ash", "Minerals (ash)"),
    ("Total lipid (fat)", "Fat"),
)


def macro_split(claims: list[dict]) -> dict | None:
    """Water and dry matter on a true 0-100 g scale, dry matter reopened.

    A single 0-100 g bar on a 90%-water vegetable collapses everything that
    distinguishes it into invisible slivers, so the dry matter is reopened at
    its own scale, which the page states in words (spec §5).
    """
    water = reading(claims, WATER)
    parts = [(display, reading(claims, label)) for label, display in DRY_MATTER]
    parts = [(display, r) for display, r in parts if r is not None]
    if water is None or not parts:
        return None
    parts.sort(key=lambda pair: -pair[1]["high"])
    dry_total = round(sum(r["high"] for _, r in parts), 2)
    return {
        "water": water,
        "dry": [dict(r, display=display) for display, r in parts],
        "dry_total": dry_total,
        "total": round(water["high"] + dry_total, 2),
    }
