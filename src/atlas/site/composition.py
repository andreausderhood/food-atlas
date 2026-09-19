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


def _span(low: float, high: float) -> str:
    """Render a summed quantity the way reading() renders a measured one.

    A total built from ranges is itself a range. Printing only its high end
    states a precision the sources do not support: summing the highs of water
    and dry matter exceeds the declared 100 g basis on real foods (apple
    'Gala': 84.6-85.76 g water + 15.5 g dry). Conflicts read as ranges here
    too, never as a fabricated single total (spec §5).
    """
    low, high = round(low, 2), round(high, 2)
    return _fmt(low) if low == high else f"{_fmt(low)}–{_fmt(high)}"


def macro_split(claims: list[dict]) -> dict | None:
    """Water and dry matter on a true 0-100 g scale, dry matter reopened.

    A single 0-100 g bar on a 90%-water vegetable collapses everything that
    distinguishes it into invisible slivers, so the dry matter is reopened at
    its own scale, which the page states in words (spec §5).

    Totals carry three fields apiece: `dry_total`/`total` are the display text
    (a number, or "low–high" when the sources disagree), `*_low`/`*_high` are
    the numeric bounds, and `*_is_range` says which it is. Bar geometry uses
    the numeric highs -- a bar is a proportion, not a stated quantity -- while
    every rendered TOTAL uses the text, so no reader is shown a bare number
    over 100 g on a 100 g basis.
    """
    water = reading(claims, WATER)
    parts = [(display, reading(claims, label)) for label, display in DRY_MATTER]
    parts = [(display, r) for display, r in parts if r is not None]
    if water is None or not parts:
        return None
    parts.sort(key=lambda pair: -pair[1]["high"])
    dry_low = round(sum(r["low"] for _, r in parts), 2)
    dry_high = round(sum(r["high"] for _, r in parts), 2)
    total_low = round(water["low"] + dry_low, 2)
    total_high = round(water["high"] + dry_high, 2)
    return {
        "water": water,
        "dry": [dict(r, display=display) for display, r in parts],
        "dry_total": _span(dry_low, dry_high),
        "dry_total_low": dry_low,
        "dry_total_high": dry_high,
        "dry_total_is_range": dry_low != dry_high,
        # Water + dry matter against the declared 100 g basis. Nothing renders
        # this today; it is kept range-aware so that any future caller inherits
        # the bounds rather than a high-end sum that can overshoot 100 g.
        "total": _span(total_low, total_high),
        "total_low": total_low,
        "total_high": total_high,
        "total_is_range": total_low != total_high,
    }


# Headline micronutrients in reading order. Micronutrients span 0.053 mg to
# 6260 ug and share no meaningful axis, so they are listed, never drawn on a
# common scale (spec §5).
MICRONUTRIENTS = (
    "Vitamin K (phylloquinone)",
    "Vitamin C, total ascorbic acid",
    "Lutein + zeaxanthin",
    "Carotene, beta",
    "Calcium, Ca",
    "Potassium, K",
    "Manganese, Mn",
    "Iron, Fe",
)


def micro_readings(claims: list[dict], limit: int = 5) -> list[dict]:
    """Headline micronutrients that are present, in declared order."""
    rows = []
    for label in MICRONUTRIENTS:
        r = reading(claims, label)
        if r is not None:
            rows.append(r)
        if len(rows) == limit:
            break
    return rows
