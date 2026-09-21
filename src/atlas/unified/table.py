"""Build, render and ratchet the coverage table."""
from __future__ import annotations

import json
from pathlib import Path

from atlas.unified.cells import Cell, RowStats, aggregate
from atlas.unified.collectors import COLLECTORS, Universe
from atlas.unified.fields import FIELDS


def build_table(u: Universe) -> list[RowStats]:
    rows = []
    for f in FIELDS:
        cells = COLLECTORS[f.collector](u) if f.collector else {}
        subjects = u.products if f.axis == "product" else u.species
        rows.append(aggregate(f.key, f.label, f.axis, cells, subjects, f.collector))
    return rows


def render_text(rows: list[RowStats]) -> str:
    head = f"{'field':30} {'axis':8} {'denom':>7} {'claims':>7} {'context%':>9} {'empty%':>7} {'unsearched':>11}  closed"
    lines = [head, "-" * len(head)]
    for r in rows:
        lines.append(f"{r.label:30} {r.axis:8} {r.denominator:7,} {r.counts[Cell.FILLED.value]:7,} "
                     f"{r.pct(Cell.CONTEXT):8.1f}% {r.pct(Cell.SEARCHED_EMPTY):6.1f}% "
                     f"{r.counts[Cell.UNSEARCHED.value]:11,}  {'yes' if r.closed else 'no'}")
    return "\n".join(lines)


def write_json(path: Path, rows: list[RowStats]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([r.as_dict() for r in rows], indent=1, sort_keys=True), encoding="utf-8")


def regressions(rows: list[RowStats], baseline_path: Path) -> list[str]:
    """Ratchet: a row may not lose resolved cells against the committed baseline."""
    if not baseline_path.is_file():
        return []
    baseline = {r["key"]: r for r in json.loads(baseline_path.read_text(encoding="utf-8"))}
    problems = []
    for r in rows:
        old = baseline.get(r.key)
        if old is None:
            continue
        old_resolved = old["denominator"] - old["counts"][Cell.UNSEARCHED.value]
        if r.resolved < old_resolved:
            problems.append(f"{r.key}: resolved cells fell from {old_resolved:,} to {r.resolved:,}")
    return problems
