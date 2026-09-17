# Research workflow ledger

## Setup — 2026-09-18
- Existing scheduled integrator: 6920430db1c8 (previously growth-loop, every 120m). Reuse, do not duplicate.
- Source implementation is concurrently in progress by another worker: untracked src/atlas/research/ and tests/test_research.py. Ownership pending; do not adopt.
- Observed test run: `.venv/bin/python -m pytest tests/test_research.py -x -q` → 10 passed in 2.50s. Earlier full collection failed while approval.py was still being written; that was a transient snapshot, not a completed suite verdict.
- Current tracked HEAD observed: 5486a98 (BLS mappings). Raw BLS and wiki files already untracked; preserve.

## Scheduler configured
- Updated existing native job 6920430db1c8 to `Food Atlas — research-week pipeline`: enabled, every 30m, continuity on, local output, repeat cap 353 total including existing completion. Tool-confirmed next run at configuration: 2026-09-18T00:47:08+02:00 (manual fire subsequently shifted it to 00:47:17).
- Read-only manual validation fire deleg_0a0c8d02 completed successfully. Saved report: /Users/ausderhood/.hermes/profiles/andreos/cron/output/6920430db1c8/2026-09-18_00-18-05.md. Report confirms workflow files, timezone-aware deadline and research init/status help; no end-to-end research engine operation proven. Next fire reported: 2026-09-18T00:48:05+02:00.
- Follow-up direct CLI test: `.venv/bin/python -m pytest tests/test_research_cli.py -x -q` → 3 passed in 0.25s. Source research/CLI paths no longer dirty in that snapshot, but tests/test_research_cli.py and tests/test_research_lifecycle.py remain untracked and ownership pending. Do not infer a clean full suite or adopt those tests.
- Later full-suite snapshot during concurrent implementation: 212 passed, 3 failed in test_research_cli.py because the CLI subparser was still absent. No code changed or committed by this setup session. Workflow documents remain available on disk; no red implementation committed.

## Next
Inspect owner-committed implementation and select the first missing P1/P2 acceptance test from docs/research-workflow.md. If dirty research files persist, report ownership pending rather than write over them.

## Blockers
- No targets.yaml seed list observed: breadth cannot be invented.
- Human license/source/image/text proposal reviews remain gates; unattended scheduling cannot substitute approval.

## 2026-09-18 00:56 CEST — P2 budget/history increment
- Ownership: HEAD 3d587b9 commits prior research/lifecycle work; no foreign dirty research/CLI/tests at entry or pre-commit. Single integrator 6920430db1c8 owns only budget.py, history.py and their two new test files in this fire. Untracked raw BLS/wiki and other setup documents remain untouched.
- Delivered: iteration/deadline budget refusing exhausted spend; complete-history tool-call/result pairing, assistant alternation and unique nonempty call IDs. These are offline primitives, not an operating supervisor or provider loop.
- RED: missing modules observed; exhausted spend reproduced as two DID NOT RAISE failures; invalid/duplicate call IDs reproduced as five failures. GREEN: 17 focused tests passed. Full `.venv/bin/python -m pytest -q`: 235 passed, 1 existing FDC processed-row warning, 49.13s.
- Full `.venv/bin/atlas build`: 5555 accepted / 1582 gaps. `tools/audit_build.py`: status ok, no implementation errors, 2880 numeric checks, 3668 internal links checked with none broken. No rendered-output change; browser gate not applicable.
- No new claims accepted, no new proposals or license approvals, no paid calls/auth changes/push/deploy. STOP absent and deadline checked between bounded steps.
- Checkpoint: local commit with subject `research: enforce conversation budget and history invariants` (this entry accompanies it; resolve hash via git log).
- Next acceptance: FakeProvider scripted tool-call/result loop against the real proposal path with budget cutoff and persisted checkpoint tests; compressor/turn phases/adapter/live license run remain unimplemented. Prior claude auth blocker not retried in this offline increment.
