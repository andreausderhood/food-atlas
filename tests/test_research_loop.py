"""Offline loop tests: scripted providers, no network, no model."""
import pytest

from atlas.research.budget import BudgetExhausted, IterationBudget


def test_budget_blocks_after_last_call():
    budget = IterationBudget(calls=2, deadline=100.0)
    assert not budget.expired(now=99.0)
    budget.spend(now=99.0)
    assert not budget.expired(now=99.0)
    budget.spend(now=99.5)
    assert budget.expired(now=99.5)
    with pytest.raises(BudgetExhausted):
        budget.require(now=99.6)


def test_budget_expires_at_wall_clock_deadline_even_with_calls_left():
    budget = IterationBudget(calls=5, deadline=100.0)
    budget.spend(now=50.0)
    assert budget.expired(now=100.0)
    with pytest.raises(BudgetExhausted):
        budget.require(now=100.0)


@pytest.mark.parametrize("calls,deadline,now", [(1, 100.0, 100.0), (1, 100.0, 99.0)])
def test_spend_cannot_exceed_budget(calls, deadline, now):
    budget = IterationBudget(calls=calls, deadline=deadline)
    if now < deadline:
        budget.spend(now=now)
    remaining = budget.calls_left
    with pytest.raises(BudgetExhausted):
        budget.spend(now=now)
    assert budget.calls_left == remaining


@pytest.mark.parametrize("calls", [0, -1])
def test_budget_rejects_nonpositive_calls(calls):
    with pytest.raises(ValueError, match="positive"):
        IterationBudget(calls=calls, deadline=100.0)
