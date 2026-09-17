"""SQLite queue with atomic leases, fencing tokens and durable event records."""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from atlas.research.queue import Task, rank_ready


@dataclass(frozen=True)
class Lease:
    task: Task
    token: str
    expires: float


class State:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, timeout=30, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY, data TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'queued',
                owner TEXT, token TEXT, expires REAL, available REAL NOT NULL DEFAULT 0,
                attempts INTEGER NOT NULL DEFAULT 0, error TEXT);
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY, at REAL NOT NULL, task_id TEXT, kind TEXT NOT NULL, data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY, started REAL NOT NULL, deadline REAL NOT NULL,
                status TEXT NOT NULL, config TEXT NOT NULL, stop_requested INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS turns (
                run_id TEXT, track TEXT, turn INTEGER, data TEXT NOT NULL,
                PRIMARY KEY(run_id, track, turn));
            CREATE TABLE IF NOT EXISTS proposals (
                id TEXT PRIMARY KEY, task_id TEXT NOT NULL, run_id TEXT NOT NULL,
                track TEXT NOT NULL, kind TEXT NOT NULL, data TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending');
            CREATE TABLE IF NOT EXISTS usage (
                run_id TEXT, track TEXT, calls INTEGER NOT NULL DEFAULT 0,
                input_tokens INTEGER NOT NULL DEFAULT 0, output_tokens INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(run_id, track));
        """)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.db.close()

    def event(self, task_id, kind, data, now=None):
        self.db.execute("INSERT INTO events(at, task_id, kind, data) VALUES (?, ?, ?, ?)",
                        (time.time() if now is None else now, task_id, kind, json.dumps(data)))

    def enqueue(self, tasks):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            known = {r[0] for r in self.db.execute("SELECT id FROM tasks")} | {t.id for t in tasks}
            for task in tasks:
                if not set(task.dependencies) <= known:
                    raise ValueError("unknown dependency")
                if task.id in task.dependencies:
                    raise ValueError("self dependency")
            combined = {t.id: t for t in self.tasks()}
            combined.update({t.id: t for t in tasks})
            visited, active = set(), set()
            def visit(tid):
                if tid in active:
                    raise ValueError("dependency cycle")
                if tid not in visited:
                    active.add(tid)
                    for dep in combined[tid].dependencies:
                        visit(dep)
                    active.remove(tid)
                    visited.add(tid)
            for tid in combined:
                visit(tid)
            for task in tasks:
                self.db.execute("INSERT OR IGNORE INTO tasks(id, data) VALUES (?, ?)", (task.id, task.to_json()))
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def tasks(self):
        return [Task.from_json(r[0]) for r in self.db.execute("SELECT data FROM tasks ORDER BY id")]

    def lease(self, owner, now=None, ttl=300, tracks=None):
        now = time.time() if now is None else now
        if ttl <= 0:
            raise ValueError("lease TTL must be positive")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute("UPDATE tasks SET status='queued', token=NULL, owner=NULL WHERE status='leased' AND expires<=?", (now,))
            rows = self.db.execute("SELECT * FROM tasks").fetchall()
            done = {r["id"] for r in rows if r["status"] == "done"}
            counts = {}
            for r in rows:
                track = Task.from_json(r["data"]).track
                counts[track] = counts.get(track, 0) + r["attempts"]
            ready = rank_ready([Task.from_json(r["data"]) for r in rows
                                if r["status"] == "queued" and r["available"] <= now], done, counts)
            ready = [t for t in ready if tracks is None or t.track in tracks]
            lease = None
            if ready:
                task = ready[0]
                token = uuid.uuid4().hex
                self.db.execute("UPDATE tasks SET status='leased', owner=?, token=?, expires=?, attempts=attempts+1 WHERE id=?",
                                (owner, token, now + ttl, task.id))
                self.event(task.id, "leased", {"owner": owner}, now)
                lease = Lease(task, token, now + ttl)
            self.db.execute("COMMIT")
            return lease
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _transition(self, tid, token, now, status, delay=0, error=None):
        now = time.time() if now is None else now
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute("UPDATE tasks SET status=?, available=?, error=?, token=NULL, owner=NULL "
                "WHERE id=? AND token=? AND status='leased' AND expires>?",
                (status, now + delay, error, tid, token, now))
            if row.rowcount != 1:
                raise ValueError("invalid or expired lease")
            self.event(tid, status, {"error": error}, now)
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def complete(self, tid, token, now=None):
        self._transition(tid, token, now, "done")

    def fail(self, tid, token, error, now=None, delay=60):
        self._transition(tid, token, now, "queued", delay, error)

    def counts(self):
        return dict(self.db.execute("SELECT status, count(*) FROM tasks GROUP BY status").fetchall())
