"""Scripted-provider research conversation loop: budget-capped, checkpointed."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from atlas.research.budget import IterationBudget
from atlas.research.history import invalid_reason


class FakeProvider:
    """Scripted assistant messages for offline tests. No network, no model."""

    def __init__(self, scripted):
        self.scripted = [dict(m) for m in scripted]
        self.calls = 0

    def complete(self, messages, tools=None):
        self.calls += 1
        if not self.scripted:
            raise AssertionError("scripted provider exhausted")
        return self.scripted.pop(0)


class ResearchLoop:
    """Run an OpenAI-style conversation until a final answer or budget cutoff.

    The history is validated after every appended message, executed tool
    results are appended before the next provider call, and the full history
    is persisted to checkpoint_dir/checkpoint.json after every turn so a run
    can be resumed with a fresh budget.
    """

    def __init__(self, provider, tools, budget, checkpoint_dir, clock=time.time):
        self.provider = provider
        self.tools = tools
        self.budget = budget
        self.checkpoint_dir = Path(checkpoint_dir)
        self.clock = clock

    def _validate(self, history):
        reason = invalid_reason(history)
        if reason:
            raise ValueError(f"invalid conversation history: {reason}")

    def _checkpoint(self, history, status, turns):
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        target = self.checkpoint_dir / "checkpoint.json"
        tmp = target.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(
            {"status": status, "history": history, "turns": turns},
            ensure_ascii=False, indent=1))
        os.replace(tmp, target)

    def _execute(self, message):
        results = []
        for call in message.get("tool_calls", []):
            name = call["function"]["name"]
            tool = self.tools.get(name)
            if tool is None:
                output = json.dumps({"error": f"unknown tool {name}"}, ensure_ascii=False)
            else:
                try:
                    output = tool["run"](call["function"]["arguments"])
                except Exception as error:  # noqa: BLE001 - report, do not crash run
                    output = json.dumps({"error": str(error)}, ensure_ascii=False)
            results.append({"role": "tool", "tool_call_id": call["id"],
                            "content": output})
        return results

    def run(self, messages):
        history = [dict(m) for m in messages]
        self._validate(history)
        turns = []
        while True:
            try:
                self.budget.require(now=self.clock())
            except Exception:
                self._checkpoint(history, "budget_exhausted", turns)
                return {"status": "budget_exhausted", "history": history,
                        "turns": turns}
            turn = {"n": len(turns) + 1, "phases": ["prep"], "status": "continued"}
            self.budget.spend(now=self.clock())
            turn["phases"].append("call")
            try:
                message = self.provider.complete(
                    history, tools=[{k: t[k] for k in ("name", "description")}
                                    for t in self.tools.values()])
            except Exception as error:  # noqa: BLE001 - turn error phase, not crash
                turn["phases"].append("error")
                turn["status"] = "provider_error"
                turns.append(turn)
                self._checkpoint(history, "provider_error", turns)
                return {"status": "provider_error", "history": history,
                        "error": str(error), "turns": turns}
            turns.append(turn)
            history.append(message)
            if not message.get("tool_calls"):
                turn["status"] = "done"
            else:
                for result in self._execute(message):
                    history.append(result)
            self._validate(history)
            turn["phases"].append("validate")
            turn["phases"].append("persist")
            self._checkpoint(history, turn["status"] if turn["status"] == "done"
                             else "running", turns)
            if turn["status"] != "continued":
                return {"status": turn["status"], "history": history, "turns": turns}
