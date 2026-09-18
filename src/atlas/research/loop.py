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

    def _checkpoint(self, history, status):
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        target = self.checkpoint_dir / "checkpoint.json"
        tmp = target.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(
            {"status": status, "history": history}, ensure_ascii=False, indent=1))
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
        while True:
            try:
                self.budget.require(now=self.clock())
            except Exception:
                self._checkpoint(history, "budget_exhausted")
                return {"status": "budget_exhausted", "history": history}
            self.budget.spend(now=self.clock())
            message = self.provider.complete(
                history, tools=[{k: t[k] for k in ("name", "description")}
                                for t in self.tools.values()])
            history.append(message)
            if not message.get("tool_calls"):
                self._validate(history)
                self._checkpoint(history, "done")
                return {"status": "done", "history": history}
            for result in self._execute(message):
                history.append(result)
            self._validate(history)
            self._checkpoint(history, "running")
