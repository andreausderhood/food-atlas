"""Offline initialization and inspection of the research queue."""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import yaml

from atlas.registry import load_sources
from atlas.research.queue import Task, generate_tasks, rank_ready
from atlas.research.state import State


def register(sub):
    parser = sub.add_parser("research", help="evidence-first research queue")
    commands = parser.add_subparsers(dest="research_cmd", required=True)
    commands.add_parser("init", help="derive tasks from registries and existing build outputs")
    commands.add_parser("status", help="inspect queue; does not start workers")


def initialize(root: Path):
    build = root / "data/build"
    for name in ("gaps.csv", "claims.csv"):
        if not (build / name).is_file():
            raise ValueError("Missing build artifacts; run atlas build before research init.")
    registry = root / "data/registry"
    sources = load_sources(registry / "sources.yaml", registry / "link_status.yaml")
    foods = yaml.safe_load((registry / "foods.yaml").read_text(encoding="utf-8")) or {}
    # foods.yaml has a wrapper; small mapping-only exports are also accepted.
    foods = foods.get("foods", foods)
    foods = {k: v for k, v in foods.items() if not k.startswith("excluded_")}
    images = yaml.safe_load((registry / "images.yaml").read_text(encoding="utf-8")) or {}
    targets_path = root / "data/research/targets.yaml"
    targets = yaml.safe_load(targets_path.read_text(encoding="utf-8")) if targets_path.exists() else []
    with (build / "gaps.csv").open(encoding="utf-8", newline="") as stream:
        gaps = list(csv.DictReader(stream))
    with (build / "claims.csv").open(encoding="utf-8", newline="") as stream:
        claims = list(csv.DictReader(stream))
    tasks = generate_tasks(sources, gaps, foods, images, targets or [], claims)
    with State(root / "data/research/state.db") as state:
        state.enqueue(tasks)


def status(root: Path):
    path = root / "data/research/state.db"
    if not path.exists():
        return {"initialized": False, "counts": {}, "ready": []}
    with State(path) as state:
        rows = state.db.execute("SELECT * FROM tasks").fetchall()
        done = {r["id"] for r in rows if r["status"] == "done"}
        import time
        now = time.time()
        candidates = [Task.from_json(r["data"]) for r in rows
                      if (r["status"] == "queued" and r["available"] <= now)
                      or (r["status"] == "leased" and r["expires"] <= now)]
        track_counts = Counter()
        for row in rows:
            track_counts[Task.from_json(row["data"]).track] += row["attempts"]
        ready = rank_ready(candidates, done, track_counts)
        return {"initialized": True, "counts": state.counts(),
                "by_kind": dict(sorted(Counter(t.kind for t in state.tasks()).items())),
                "ready_count": len(ready),
                "ready": [asdict(t) for t in ready[:10]]}


def dispatch(args, root: Path):
    try:
        if args.research_cmd == "init":
            initialize(root)
        print(json.dumps(status(root), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as error:
        print(f"research: {error}", file=sys.stderr)
        return 1
