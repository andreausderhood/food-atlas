"""Validate complete OpenAI-style histories before provider calls/checkpoints."""
from __future__ import annotations


def invalid_reason(history: list[dict]) -> str | None:
    pending = set()
    previous = None
    for message in history:
        role = message.get("role")
        if role == "assistant" and previous == "assistant":
            return "two assistant messages in a row"
        if role == "tool":
            if not pending:
                return "tool result without preceding tool call"
            call_id = message.get("tool_call_id")
            if call_id not in pending:
                return "tool result for unknown tool call id"
            pending.remove(call_id)
        else:
            if pending:
                return "tool call without following tool result"
            if role == "assistant":
                ids = [call.get("id") for call in message.get("tool_calls", [])]
                if any(not isinstance(cid, str) or not cid.strip() for cid in ids):
                    return "tool call ids must be unique nonempty strings"
                if len(set(ids)) != len(ids):
                    return "tool call ids must be unique nonempty strings"
                pending = set(ids)
        previous = role
    if pending:
        return "tool call without following tool result"
    return None
