"""Pure, reproducible task generation and dependency-aware priority ordering."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass

from atlas.registry import Source

NICHE_GROUPS = ("origin", "growing", "process", "geography")
COST = {"license_read": 0, "basis_gap": 1, "derivation_gap": 1,
        "coverage_gap": 2, "image": 3, "niche": 4, "source_discovery": 5, "breadth": 6}


@dataclass(frozen=True)
class Task:
    id: str
    kind: str
    track: str
    subject: str
    field: str
    source: str | None = None
    dependencies: tuple[str, ...] = ()
    context: str = ""

    @classmethod
    def create(cls, kind, track, subject, field, source=None, dependencies=(), context=""):
        key = json.dumps([kind, subject, field, source], ensure_ascii=False)
        tid = hashlib.sha256(key.encode()).hexdigest()[:24]
        return cls(tid, kind, track, subject, field, source, tuple(dependencies), context)

    def to_json(self):
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, text):
        data = json.loads(text)
        data["dependencies"] = tuple(data["dependencies"])
        return cls(**data)


def rank_ready(tasks, done, track_counts=None):
    counts = track_counts or {}
    remaining = [t for t in tasks if t.id not in done]
    unblocks = {t.id: sum(t.id in x.dependencies for x in remaining) for t in remaining}
    return sorted((t for t in remaining if set(t.dependencies) <= done),
                  key=lambda t: (-unblocks[t.id], COST[t.kind], counts.get(t.track, 0), t.id))


def generate_tasks(sources: dict[str, Source], gaps, foods, images, targets, claims=()):
    tasks = {}
    def add(kind, track, subject, field, source=None, context=""):
        deps = ()
        if source in sources and not sources[source].license_read and kind != "license_read":
            deps = (Task.create("license_read", "licenses", source, "license", source).id,)
        task = Task.create(kind, track, subject, field, source, deps, context)
        tasks[task.id] = task
    for sid, s in sorted(sources.items()):
        if not s.license_read:
            add("license_read", "licenses", sid, "license", sid,
                json.dumps({"title": s.title, "url": s.url, "license_url": s.license_url}))
    for gap in gaps:
        rule = int(gap["rule"])
        sid = gap.get("src") or None
        if rule == 6:
            kind = "basis_gap"
        elif rule == 5 and sid and "FDC" in sid:
            kind = "derivation_gap"
        elif rule == 5 and sid in sources:
            kind = "coverage_gap"
        else:
            continue
        add(kind, "coverage", gap["subject"], gap["field"], sid, json.dumps(gap, default=str))
    present = {(c["subject"], c["group"]) for c in claims}
    for fid, food in sorted(foods.items()):
        if fid not in images:
            add("image", "images", fid, "image", context=json.dumps(food))
        for group in NICHE_GROUPS:
            if (fid, group) in present:
                continue
            eligible = [sid for sid, s in sorted(sources.items()) if group in s.supports
                        and s.license_class in ("ship", "cite") and s.id != "SRC-UNVERIFIED"]
            if eligible:
                # Prefer a source already usable; source choice remains a research question.
                sid = min(eligible, key=lambda sid: (not sources[sid].license_read, sid))
                add("niche", "niche", fid, group, sid, json.dumps({"sources": eligible, "food": food}))
            else:
                add("source_discovery", "discovery", fid, group)
    for target in targets:
        # Seeds are supplied by the operator, not invented during initialization.
        add("breadth", "breadth", target["id"], "identity", context=json.dumps(target))
    return sorted(tasks.values(), key=lambda t: t.id)
