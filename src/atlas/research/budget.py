"""Iteration and wall-clock budget for a research worker conversation loop."""
from __future__ import annotations

import time


class BudgetExhausted(Exception):
    """Raised when the worker must stop and checkpoint instead of calling again."""


class IterationBudget:
    def __init__(self, calls: int, deadline: float):
        if calls < 1:
            raise ValueError("budget calls must be positive")
        self.calls_left = calls
        self.deadline = deadline

    def expired(self, now: float | None = None) -> bool:
        now = time.time() if now is None else now
        return self.calls_left <= 0 or now >= self.deadline

    def spend(self, now: float | None = None) -> None:
        self.require(now)
        self.calls_left -= 1

    def require(self, now: float | None = None) -> None:
        if self.expired(now):
            raise BudgetExhausted("iteration budget exhausted; checkpoint and stop")
