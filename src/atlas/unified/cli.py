"""`atlas coverage` — the table, computed from the data; `--check` is the ratchet."""
from __future__ import annotations

from pathlib import Path

from atlas.unified.collectors import load_universe
from atlas.unified.table import (
    build_table,
    next_actions,
    regressions,
    render_next,
    render_text,
    write_json,
)

BASELINE = "docs/coverage/baseline.json"   # committed; only ever moves forward


def register(sub) -> None:
    c = sub.add_parser("coverage", help="the 13-row coverage table, measured on the real data")
    c.add_argument("--check", action="store_true", help="fail if any row lost resolved cells vs the baseline")
    c.add_argument("--write-baseline", action="store_true", help="move the baseline forward to the current state")
    c.add_argument("--next", action="store_true", help="print top 10 recommended next actions/gap blocks")


def run(args, root: Path) -> int:
    universe = load_universe(root)
    rows = build_table(universe)
    print(render_text(rows))
    write_json(root / "data/build/coverage.json", rows)
    if getattr(args, "next", False):
        actions = next_actions(universe, limit=10)
        print("\nNext actions:")
        print(render_next(actions))

    baseline = root / BASELINE
    if args.write_baseline:
        write_json(baseline, rows)
        print(f"baseline written: {baseline}")
    if args.check:
        problems = regressions(rows, baseline)
        for p in problems:
            print("REGRESSION", p)
        return 1 if problems else 0
    return 0
