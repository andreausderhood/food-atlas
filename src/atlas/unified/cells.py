"""Cell states: the vocabulary the coverage table counts in.

A cell is one (subject, field) pair. The table is closed when no cell in a
row's denominator is `unsearched` — not when every cell is filled.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping


class Cell(str, Enum):
    FILLED = "filled"                  # at least one accepted claim
    CONTEXT = "context"                # datapoint exists, but as unverified context (no claim)
    SEARCHED_EMPTY = "searched_empty"  # searched, nothing accepted   (matrix "0")
    NOT_APPLICABLE = "not_applicable"  # the field does not exist for this subject
    UNSEARCHED = "unsearched"          # never searched               (matrix "–")


@dataclass(frozen=True)
class RowStats:
    key: str
    label: str
    axis: str
    denominator: int
    counts: dict[str, int]
    collector: str | None

    @property
    def resolved(self) -> int:
        return self.denominator - self.counts[Cell.UNSEARCHED.value]

    @property
    def closed(self) -> bool:
        return self.denominator > 0 and self.counts[Cell.UNSEARCHED.value] == 0

    def pct(self, cell: Cell) -> float:
        return 100.0 * self.counts[cell.value] / self.denominator if self.denominator else 0.0

    def as_dict(self) -> dict:
        return {"key": self.key, "label": self.label, "axis": self.axis,
                "denominator": self.denominator, "counts": dict(self.counts),
                "collector": self.collector, "closed": self.closed}


def aggregate(key: str, label: str, axis: str, cells: Mapping[str, Cell],
              subjects: Iterable[str], collector: str | None) -> RowStats:
    """Count cell states over the denominator; a subject without a state is unsearched."""
    counts = {c.value: 0 for c in Cell}
    total = 0
    for subject in subjects:
        total += 1
        counts[cells.get(subject, Cell.UNSEARCHED).value] += 1
    return RowStats(key, label, axis, total, counts, collector)
