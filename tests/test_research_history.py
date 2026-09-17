"""History alternation invariants are pure functions of the message list."""
import pytest

from atlas.research.history import invalid_reason


def test_rejects_two_assistant_in_a_row():
    history = [{"role": "assistant"}, {"role": "assistant", "content": "x"}]
    assert invalid_reason(history) == "two assistant messages in a row"


def test_rejects_tool_result_without_preceding_calls():
    history = [{"role": "user"}, {"role": "tool", "content": "r"}]
    assert invalid_reason(history) == "tool result without preceding tool call"


def test_rejects_unpaired_trailing_tool_result():
    history = [{"role": "user"},
               {"role": "assistant", "tool_calls": [{"id": "c1"}]},
               {"role": "tool", "tool_call_id": "c1", "content": "r"},
               {"role": "tool", "tool_call_id": "c2", "content": "r2"}]
    assert invalid_reason(history) == "tool result without preceding tool call"


def test_rejects_assistant_tool_calls_without_result():
    history = [{"role": "user"},
               {"role": "assistant", "tool_calls": [{"id": "c1"}]}]
    assert invalid_reason(history) == "tool call without following tool result"


def test_rejects_tool_result_for_unknown_call_id():
    history = [{"role": "user"},
               {"role": "assistant", "tool_calls": [{"id": "c1"}]},
               {"role": "tool", "tool_call_id": "zz", "content": "r"}]
    assert invalid_reason(history) == "tool result for unknown tool call id"


def test_valid_conversation_has_no_reason():
    history = [{"role": "system", "content": "s"},
               {"role": "user", "content": "u"},
               {"role": "assistant", "tool_calls": [{"id": "c1"}, {"id": "c2"}]},
               {"role": "tool", "tool_call_id": "c1", "content": "r1"},
               {"role": "tool", "tool_call_id": "c2", "content": "r2"},
               {"role": "assistant", "content": "done"}]
    assert invalid_reason(history) is None


@pytest.mark.parametrize("calls", [[{"id": "c1"}, {"id": "c1"}], [{}], [{"id": ""}], [{"id": None}], [{"id": []}]])
def test_rejects_invalid_tool_call_ids(calls):
    history = [{"role": "assistant", "tool_calls": calls},
               {"role": "tool", "tool_call_id": "c1", "content": "r"}]
    assert invalid_reason(history) == "tool call ids must be unique nonempty strings"
