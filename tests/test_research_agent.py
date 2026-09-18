"""Offline research-loop tests: scripted provider, real proposal path, no network."""
import json

import pytest

from atlas.research.budget import IterationBudget
from atlas.research.history import invalid_reason
from atlas.research.lifecycle import next_item, submit
from atlas.research.loop import FakeProvider, ResearchLoop
from atlas.research.queue import Task
from atlas.research.state import State


def setup_root(tmp_path):
    task = Task.create("license_read", "licenses", "S", "license", "S")
    with State(tmp_path / "data/research/state.db") as state:
        state.enqueue([task])
    return task


def proposal_payload(task, lease, tmp_path):
    from atlas.research.evidence import Cache
    key = Cache(tmp_path / "data/research/cache").store(
        "https://example.org/license", "Synthetic test license evidence: CC0")
    return {"item_id": task.id, "lease_token": lease["token"],
            "kind": "license_read", "subject": "S", "field": "license",
            "source": "S", "findings": {"license": "CC0"},
            "evidence": [{"ref": "https://example.org/license",
                          "quote": "CC0", "cache_key": key}]}


def submit_tool(tmp_path):
    """Tool wired to the REAL fenced proposal path (lifecycle.next_item/submit)."""
    def run(arguments):
        payload = json.loads(arguments)
        proposal = dict(payload)
        result = submit(tmp_path, proposal)
        return json.dumps({"proposal_id": result["proposal_id"],
                           "status": result["status"]})
    return {"name": "submit_proposal",
            "description": "submit a validated proposal via the real lifecycle",
            "run": run}


def test_final_answer_without_tool_calls_completes_and_checkpoints(tmp_path):
    setup_root(tmp_path)
    final = {"role": "assistant", "content": "No license evidence found."}
    provider = FakeProvider([final])
    loop = ResearchLoop(provider, tools={}, budget=IterationBudget(calls=3, deadline=1e12),
                        checkpoint_dir=tmp_path / "run")
    result = loop.run([{"role": "user", "content": "read the license of S"}])
    assert result["status"] == "done"
    assert provider.calls == 1
    assert invalid_reason(result["history"]) is None
    saved = json.loads((tmp_path / "run" / "checkpoint.json").read_text())
    assert saved["status"] == "done"
    assert saved["history"] == result["history"]


def test_tool_call_hits_real_proposal_path_and_persists(tmp_path):
    task = setup_root(tmp_path)
    lease = next_item(tmp_path, "agent-loop")["lease"]
    payload = proposal_payload(task, lease, tmp_path)
    provider = FakeProvider([
        {"role": "assistant", "content": None,
         "tool_calls": [{"id": "c1", "type": "function",
                         "function": {"name": "submit_proposal",
                                      "arguments": json.dumps(payload)}}]},
        {"role": "assistant", "content": "Proposal submitted for review."},
    ])
    loop = ResearchLoop(provider, tools={"submit_proposal": submit_tool(tmp_path)},
                        budget=IterationBudget(calls=5, deadline=1e12),
                        checkpoint_dir=tmp_path / "run")
    result = loop.run([{"role": "user", "content": "submit the license proposal"}])
    assert result["status"] == "done"
    assert provider.calls == 2
    tool_msg = [m for m in result["history"] if m.get("role") == "tool"][0]
    assert json.loads(tool_msg["content"])["status"] == "pending_review"
    assert invalid_reason(result["history"]) is None
    saved = json.loads((tmp_path / "run" / "checkpoint.json").read_text())
    assert saved["status"] == "done"
    # The proposal is really on disk through the real lifecycle path.
    import glob
    proposals = glob.glob(str(tmp_path / "data/proposals/*/*/*.json"))
    assert len(proposals) == 1


def test_budget_exhaustion_checkpoints_and_stops_without_extra_call(tmp_path):
    task = setup_root(tmp_path)
    lease = next_item(tmp_path, "agent-loop")["lease"]
    payload = proposal_payload(task, lease, tmp_path)
    final = {"role": "assistant", "content": "done"}
    provider = FakeProvider([
        {"role": "assistant", "content": None,
         "tool_calls": [{"id": "c1", "type": "function",
                         "function": {"name": "submit_proposal",
                                      "arguments": json.dumps(payload)}}]},
        final,
    ])
    loop = ResearchLoop(provider, tools={"submit_proposal": submit_tool(tmp_path)},
                        budget=IterationBudget(calls=1, deadline=1e12),
                        checkpoint_dir=tmp_path / "run")
    result = loop.run([{"role": "user", "content": "work"}])
    assert result["status"] == "budget_exhausted"
    assert provider.calls == 1
    # History stays valid: the executed tool result is part of the checkpoint.
    assert invalid_reason(result["history"]) is None
    assert [m["role"] for m in result["history"]] == ["user", "assistant", "tool"]
    saved = json.loads((tmp_path / "run" / "checkpoint.json").read_text())
    assert saved["status"] == "budget_exhausted"
    # Resume from the persisted checkpoint with fresh budget finishes the task.
    resumed = ResearchLoop(FakeProvider([final]),
                           tools={"submit_proposal": submit_tool(tmp_path)},
                           budget=IterationBudget(calls=3, deadline=1e12),
                           checkpoint_dir=tmp_path / "run")
    result2 = resumed.run(saved["history"])
    assert result2["status"] == "done"


def test_invalid_scripted_history_fails_loudly(tmp_path):
    provider = FakeProvider([
        {"role": "tool", "tool_call_id": "x", "content": "y"},
    ])
    loop = ResearchLoop(provider, tools={}, budget=IterationBudget(calls=5, deadline=1e12),
                        checkpoint_dir=tmp_path / "run")
    with pytest.raises(ValueError, match="tool result without preceding tool call"):
        loop.run([{"role": "user", "content": "hi"}])


def test_provider_error_is_checkpointed_not_raised(tmp_path):
    class BoomProvider:
        def __init__(self):
            self.calls = 0

        def complete(self, messages, tools=None):
            self.calls += 1
            raise RuntimeError("transient provider failure")

    provider = BoomProvider()
    loop = ResearchLoop(provider, tools={}, budget=IterationBudget(calls=3, deadline=1e12),
                        checkpoint_dir=tmp_path / "run")
    result = loop.run([{"role": "user", "content": "work"}])
    assert result["status"] == "provider_error"
    assert result["error"] == "transient provider failure"
    assert provider.calls == 1
    assert invalid_reason(result["history"]) is None
    saved = json.loads((tmp_path / "run" / "checkpoint.json").read_text())
    assert saved["status"] == "provider_error"
    assert saved["history"] == result["history"]


def test_turns_record_phase_progression(tmp_path):
    task = setup_root(tmp_path)
    lease = next_item(tmp_path, "agent-loop")["lease"]
    payload = proposal_payload(task, lease, tmp_path)
    provider = FakeProvider([
        {"role": "assistant", "content": None,
         "tool_calls": [{"id": "c1", "type": "function",
                         "function": {"name": "submit_proposal",
                                      "arguments": json.dumps(payload)}}]},
        {"role": "assistant", "content": "recorded."},
    ])
    loop = ResearchLoop(provider, tools={"submit_proposal": submit_tool(tmp_path)},
                        budget=IterationBudget(calls=5, deadline=1e12),
                        checkpoint_dir=tmp_path / "run")
    result = loop.run([{"role": "user", "content": "work"}])
    assert result["turns"] == [
        {"n": 1, "phases": ["prep", "call", "validate", "persist"], "status": "continued"},
        {"n": 2, "phases": ["prep", "call", "validate", "persist"], "status": "done"},
    ]
    saved = json.loads((tmp_path / "run" / "checkpoint.json").read_text())
    assert saved["turns"] == result["turns"]


def test_provider_error_turn_records_error_phase(tmp_path):
    class BoomProvider:
        def complete(self, messages, tools=None):
            raise RuntimeError("boom")

    loop = ResearchLoop(BoomProvider(), tools={}, budget=IterationBudget(calls=3, deadline=1e12),
                        checkpoint_dir=tmp_path / "run")
    result = loop.run([{"role": "user", "content": "work"}])
    assert result["turns"] == [
        {"n": 1, "phases": ["prep", "call", "error"], "status": "provider_error"}]
