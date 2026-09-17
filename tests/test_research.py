"""Offline phase-one research tests; evidence fixtures are not research results."""
from dataclasses import replace

import pytest

from atlas.claims import Claim
from atlas.registry import Source
from atlas.research.approval import Evidence, classify
from atlas.research.queue import Task, generate_tasks, rank_ready
from atlas.research.state import State


def source(**changes):
    return replace(Source(id="S", title="Test", publisher="Test", url="https://example.org",
        license="CC0", license_class="ship", license_read=True, kind="measurement",
        independence="independent", supports=("nutrition", "origin"), attribution="Test"), **changes)


def claim(**changes):
    return replace(Claim(subject="food:apple", group="nutrition", field="vitamin",
        v=4.6, src="S", derivation="analytical", unit="mg", basis="fresh_weight",
        food_part="whole", ref="data/raw/test.csv"), **changes)


def test_gate_returns_exact_contract_gap(tmp_path):
    result = classify(claim(basis=None), {"S": source()}, [], tmp_path)
    assert result.action == "reject"
    assert result.gap.rule == 6
    assert "basis" in result.gap.would_be_settled_by


def test_local_file_alone_is_not_numeric_proof(tmp_path):
    path = tmp_path / "data/raw/test.csv"
    path.parent.mkdir(parents=True)
    path.write_text("vitamin,4.6,mg\n")
    evidence = Evidence(ref="data/raw/test.csv", quote="vitamin,4.6,mg")
    # A model can quote a genuine row while inventing the value. File/substring
    # checks alone must NEVER confer unattended write authority.
    assert classify(claim(v=999), {"S": source()}, [evidence], tmp_path).action == "propose"
    assert classify(claim(), {"S": source()}, [evidence], tmp_path).action == "propose"


def test_missing_or_fabricated_evidence_is_rejected(tmp_path):
    assert classify(claim(), {"S": source()}, [], tmp_path).action == "reject"
    path = tmp_path / "data/raw/test.csv"
    path.parent.mkdir(parents=True)
    path.write_text("other row")
    e = Evidence(ref="data/raw/test.csv", quote="invented")
    assert classify(claim(), {"S": source()}, [e], tmp_path).action == "reject"


def test_evidence_path_cannot_escape_raw(tmp_path):
    outside = tmp_path / "secret.txt"
    outside.write_text("vitamin")
    raw = tmp_path / "data/raw"
    raw.mkdir(parents=True)
    (raw / "escape").symlink_to(outside)
    for ref in ("data/raw/../../secret.txt", "data/raw/escape", str(outside)):
        assert classify(claim(ref=ref), {"S": source()},
                        [Evidence(ref=ref, quote="vitamin")], tmp_path).action == "reject"


def test_web_quote_must_be_in_trusted_cache(tmp_path):
    from atlas.research.evidence import Cache
    cache = Cache(tmp_path / "data/research/cache")
    key = cache.store("https://example.org/paper", "Apple origin evidence")
    ref = "https://example.org/paper"
    e = Evidence(ref=ref, quote="origin evidence", cache_key=key)
    c = claim(group="origin", field="origin", v="evidence", ref=ref, derivation="registry")
    assert classify(c, {"S": source()}, [e], tmp_path).action == "propose"
    assert classify(c, {"S": source()}, [replace(e, quote="made up")], tmp_path).action == "reject"
    assert classify(c, {"S": source()}, [replace(e, ref="https://wrong.org")], tmp_path).action == "reject"


def test_generation_is_idempotent_and_license_dependencies_are_generic():
    sources = {"S": source(license_read=False)}
    gaps = [{"subject": "food:apple", "field": "vitamin", "rule": 6, "src": "S"},
            {"subject": "food:apple", "field": "origin", "rule": 5, "src": "S"}]
    tasks = generate_tasks(sources, gaps, {"food:apple": {"name": "Apple"}}, {}, [])
    assert tasks == generate_tasks(sources, gaps, {"food:apple": {"name": "Apple"}}, {}, [])
    license_task = next(t for t in tasks if t.kind == "license_read")
    for t in tasks:
        if t.source == "S" and t.kind != "license_read":
            assert license_task.id in t.dependencies
    assert rank_ready(tasks, set())[0].id == license_task.id
    assert len({t.id for t in tasks}) == len(tasks)


def test_queue_persists_and_stale_worker_cannot_complete(tmp_path):
    path = tmp_path / "state.db"
    task = Task.create("basis_gap", "coverage", "food:apple", "vitamin", "S")
    with State(path) as state:
        state.enqueue([task, task])
        first = state.lease("worker-a", now=100, ttl=10)
        assert first.task.id == task.id
        assert state.lease("worker-b", now=105, ttl=10) is None
    with State(path) as state:
        second = state.lease("worker-b", now=111, ttl=10)
        assert second.token != first.token
        with pytest.raises(ValueError, match="lease"):
            state.complete(task.id, first.token, now=112)
        state.complete(task.id, second.token, now=112)
        assert state.counts() == {"done": 1}
        assert state.lease("worker-c", now=113) is None


def test_failed_lease_backoff_and_dependencies(tmp_path):
    a = Task.create("license_read", "licenses", "S", "license", "S")
    b = Task.create("basis_gap", "coverage", "food:apple", "vitamin", "S", dependencies=(a.id,))
    with State(tmp_path / "state.db") as state:
        state.enqueue([b, a])
        lease = state.lease("a", now=0)
        assert lease.task == a
        state.fail(a.id, lease.token, "test failure", now=1, delay=10)
        assert state.lease("b", now=5) is None
        lease = state.lease("b", now=12)
        state.complete(a.id, lease.token, now=13)
        assert state.lease("b", now=14).task == b


def test_expired_lease_cannot_complete_even_before_reassignment(tmp_path):
    t = Task.create("image", "images", "food:apple", "image")
    with State(tmp_path / "state.db") as state:
        state.enqueue([t])
        lease = state.lease("a", now=0, ttl=1)
        with pytest.raises(ValueError, match="lease"):
            state.complete(t.id, lease.token, now=2)


def test_unknown_dependency_rejected_atomically(tmp_path):
    t = Task.create("image", "images", "food:apple", "image", dependencies=("missing",))
    with State(tmp_path / "state.db") as state:
        with pytest.raises(ValueError, match="dependency"):
            state.enqueue([t])
        assert state.counts() == {}
