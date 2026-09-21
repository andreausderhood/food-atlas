"""Build, render and ratchet the coverage table."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from atlas.unified.cells import Cell, RowStats, aggregate
from atlas.unified.collectors import COLLECTORS, Universe
from atlas.unified.fields import FIELDS


@dataclass(frozen=True)
class Action:
    field: str
    label: str
    axis: str
    priority: int
    unsearched: int
    gap: str

    @property
    def closes_with(self) -> str:
        return self.gap

    @property
    def count(self) -> int:
        return self.unsearched

    def __getitem__(self, item: str):
        if item in ("gap", "closes_with", "description"):
            return self.gap
        if item in ("count", "unsearched"):
            return self.unsearched
        return getattr(self, item)

    def get(self, item: str, default=None):
        try:
            return self[item]
        except (AttributeError, KeyError):
            return default

    def as_dict(self) -> dict:
        return {
            "field": self.field,
            "label": self.label,
            "axis": self.axis,
            "priority": self.priority,
            "unsearched": self.unsearched,
            "gap": self.gap,
            "closes_with": self.gap,
        }



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


def next_actions(u: Universe, limit: int = 10) -> list[Action]:
    actions: list[Action] = []
    for f in FIELDS:
        cells = COLLECTORS[f.collector](u) if f.collector else {}
        if f.axis == "species":
            counts_by_p: dict[int, int] = {}
            for b, entry in u.species.items():
                cell = cells.get(b, Cell.UNSEARCHED)
                if cell == Cell.UNSEARCHED:
                    p = entry.get("priority", 4) if isinstance(entry, dict) else 4
                    try:
                        p = int(p)
                    except (ValueError, TypeError):
                        p = 4
                    counts_by_p[p] = counts_by_p.get(p, 0) + 1
            for p, count in counts_by_p.items():
                if count > 0:
                    actions.append(Action(
                        field=f.key,
                        label=f.label,
                        axis=f.axis,
                        priority=p,
                        unsearched=count,
                        gap=f.closes_with,
                    ))
        elif f.axis == "product":
            unsearched_count = 0
            for p in u.products:
                cell = cells.get(p, Cell.UNSEARCHED)
                if cell == Cell.UNSEARCHED:
                    unsearched_count += 1
            if unsearched_count > 0:
                actions.append(Action(
                    field=f.key,
                    label=f.label,
                    axis=f.axis,
                    priority=1,
                    unsearched=unsearched_count,
                    gap=f.closes_with,
                ))

    actions.sort(key=lambda a: (a.priority, -a.unsearched, a.field))
    return actions[:limit]


def render_next(actions: list[Action]) -> str:
    if not actions:
        return "No remaining coverage gaps."
    head = f"{'priority':8} {'field':28} {'axis':8} {'unsearched':>11}  action / gap"
    lines = [head, "-" * len(head)]
    for a in actions:
        lines.append(f"P{a.priority:<7} {a.label:28} {a.axis:8} {a.unsearched:11,}  {a.gap}")
    return "\n".join(lines)


render_next_actions = render_next

