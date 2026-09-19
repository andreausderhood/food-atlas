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
