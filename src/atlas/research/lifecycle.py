"""Fenced proposal submission. Review is inspection, never publication approval."""
from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import asdict
from pathlib import Path

from atlas.claims import Claim
from atlas.registry import load_sources
from atlas.research.approval import Evidence, classify, verify_evidence
from atlas.research.queue import Task
from atlas.research.state import State


def require_state(root: Path) -> Path:
    path = root / "data/research/state.db"
    if not path.is_file():
        raise ValueError("Run atlas research init first.")
    return path


def next_item(root: Path, owner: str):
    if not owner.strip():
        raise ValueError("lease owner must not be empty")
    with State(require_state(root)) as state:
        lease = state.lease(owner)
    if lease is None:
        return {"item": None, "lease": None}
    return {"item": asdict(lease.task), "lease": {
        "claimed_by": owner, "token": lease.token, "expires": lease.expires}}


def _leased_task(state, tid, token):
    row = state.db.execute(
        "SELECT data FROM tasks WHERE id=? AND token=? AND status='leased' AND expires>?",
        (tid, token, time.time())).fetchone()
    if row is None:
        raise ValueError("invalid or expired lease")
    return Task.from_json(row["data"])


def _validate(root, task, proposal):
    for field, expected in (("kind", task.kind), ("subject", task.subject),
                            ("field", task.field), ("source", task.source)):
        if proposal.get(field) != expected:
            raise ValueError(f"proposal {field} does not match leased task")
    records = proposal.get("evidence")
    if not isinstance(records, list) or not records:
        raise ValueError("evidence records required")
    evidence = [Evidence(**entry) for entry in records]
    for entry in evidence:
        verify_evidence(entry, root)
    if task.kind == "license_read":
        findings = proposal.get("findings")
        if not isinstance(findings, dict) or not findings.get("license"):
            raise ValueError("license findings required")
        return {"action": "propose", "reason": "License evidence occurrence verified; human license review required."}
    if "claim" not in proposal:
        raise ValueError("Only license findings or contract-checked claims are supported yet")
    claim = Claim(**proposal["claim"])
    if (claim.subject, claim.field) != (task.subject, task.field):
        raise ValueError("claim does not match leased subject and field")
    if task.source and claim.src != task.source:
        raise ValueError("claim source does not match leased task")
    registry = root / "data/registry"
    decision = classify(claim, load_sources(registry / "sources.yaml", registry / "link_status.yaml"), evidence, root)
    if decision.action == "reject":
        raise ValueError(json.dumps(asdict(decision), ensure_ascii=False))
    return asdict(decision)


def export_proposal(root: Path, record):
    # SQLite is authoritative: exports can be recreated after a process crash.
    directory = root / "data/proposals" / record["run_id"] / record["track"]
    if not directory.resolve().is_relative_to((root / "data/proposals").resolve()):
        raise ValueError("proposal path escape")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (record["id"] + ".json")
    blob = json.dumps(json.loads(record["data"]), ensure_ascii=False, indent=2)
    temporary = path.with_suffix("." + uuid.uuid4().hex + ".tmp")
    temporary.write_text(blob, encoding="utf-8")
    temporary.replace(path)
    return str(path.relative_to(root))


def submit(root: Path, proposal):
    tid, token = proposal["item_id"], proposal["lease_token"]
    with State(require_state(root)) as state:
        task = _leased_task(state, tid, token)
        try:
            decision = _validate(root, task, proposal)
        except (OSError, ValueError, KeyError, TypeError, UnicodeError) as error:
            state.fail(tid, token, str(error))
            raise
        pid, run_id = uuid.uuid4().hex, uuid.uuid4().hex
        if not re.fullmatch(r"[a-z_]+", task.track):
            raise ValueError("invalid proposal track")
        # Allowlist exported fields; lease fencing tokens never enter durable proposals.
        clean = {key: proposal[key] for key in
                 ("item_id", "kind", "subject", "field", "source", "findings", "claim", "evidence")
                 if key in proposal}
        clean.update(proposal_id=pid, status="pending_review", decision=decision)
        state.db.execute("BEGIN IMMEDIATE")
        try:
            _leased_task(state, tid, token)
            state.db.execute("INSERT INTO proposals(id,task_id,run_id,track,kind,data,status) VALUES (?,?,?,?,?,?,?)",
                             (pid, tid, run_id, task.track, task.kind, json.dumps(clean), "pending_review"))
            state.db.execute("UPDATE tasks SET status='pending_review', token=NULL, owner=NULL, expires=NULL WHERE id=?", (tid,))
            state.event(tid, "pending_review", {"proposal_id": pid})
            state.db.execute("COMMIT")
        except BaseException:
            state.db.execute("ROLLBACK")
            raise
        record = state.db.execute("SELECT * FROM proposals WHERE id=?", (pid,)).fetchone()
        path = export_proposal(root, record)
    return {"proposal_id": pid, "status": "pending_review", "path": path}


def review(root: Path, pid: str):
    with State(require_state(root)) as state:
        record = state.db.execute("SELECT * FROM proposals WHERE id=?", (pid,)).fetchone()
        if record is None:
            raise ValueError("unknown proposal id")
        path = export_proposal(root, record)
        return {"proposal_id": pid, "status": record["status"], "path": path,
                "proposal": json.loads(record["data"])}
