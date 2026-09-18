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

## 2026-09-18 (fire, post-00:56) — P2 FakeProvider conversation loop increment
- Ownership: HEAD 18c8f6a at entry; no foreign dirty research/CLI/test paths (prior ownership-pending state resolved by 3d587b9/18c8f6a). This fire owns only src/atlas/research/loop.py, tests/test_research_agent.py and this ledger entry. Untracked raw BLS/wiki and setup documents remain untouched/uncommitted.
- Delivered: offline `ResearchLoop` (OpenAI-style history, tool registry, iteration-budget cutoff, atomic checkpoint.json after every turn, resume-from-checkpoint) + `FakeProvider` (scripted, no network/model). The loop tool test wires `submit_proposal` to the REAL fenced lifecycle (lifecycle.next_item + submit against a tmp state.db), asserting a `pending_review` proposal actually lands under data/proposals/<run>/<track>/<pid>.json.
- RED: 4 tests failed for the expected reason (ModuleNotFoundError atlas.research.loop). GREEN fixed three real defects found by the tests: (1) validation must run after tool results are appended, the history validator enforces complete pairs; (2) loop must invoke tool["run"], not the registry dict; (3) proposal export path is data/proposals/*/*/*.json.
- GREEN: 4 focused tests passed. Full `.venv/bin/python -m pytest tests/ -q`: 239 passed, 1 existing FDC processed-row warning, 15.24s. Full `.venv/bin/atlas build`: 5555 accepted / 1582 gaps. `.venv/bin/atlas site`: rendered. `tools/audit_build.py`: status ok. (No `atlas audit` subcommand exists; audit_build.py is the audit gate per prior ledger entry.)
- No new claims accepted, no human approvals performed, proposals remain propose-only pending_review; no network/paid calls/auth changes/push/deploy. STOP absent; deadline 2026-09-25T09:00+02:00 not reached (checked between bounded steps).
- Next acceptance: turn phases (analysis/validation/report) around the loop; history compressor (50% preflight, last 20 messages protected, tool pairs atomic, note flush); controlled claude_cli adapter behind a provider registry — each with RED tests first. Live license-track run still blocked on claude CLI auth (loggedIn:false) and human review gates; not retried here.

## 2026-09-19 00:35 CEST — P2 turn-phases increment
- Ownership: HEAD 8ba9248 at entry. The interactive session's season/images/editorial work was dirty (00:02–00:22) and ownership-pending at fire entry, then landed itself as 649bc63..8ba9248 mid-fire; this fire did not touch, adopt or commit it. After their commits the tree was clean except the known-untracked raw BLS/wiki/setup documents, which remain untouched/uncommitted.
- Delivered: turn-phase records in `ResearchLoop.run` — every turn records phases ["prep","call","validate","persist"] with status "continued"/"done"; provider exceptions no longer crash the run: the turn records ["prep","call","error"], run returns/checkpoints status "provider_error" with "error" and "turns"; budget-exhausted result carries "turns". This is the loop-side foundation for turn/{prep,call,error,overflow,recovery}; the compressor and provider adapter remain unimplemented.
- RED: test_provider_error_is_checkpointed_not_raised failed with RuntimeError propagating (feature missing); test_turns_record_phase_progression and test_provider_error_turn_records_error_phase failed with KeyError 'turns'. GREEN: minimal run()/_checkpoint change; 24 focused research tests passed.
- Full `.venv/bin/python -m pytest tests/ -q`: 235 passed, 1 existing FDC processed-row warning (observed baseline at fire entry was 232 + 3 new tests). Full `.venv/bin/atlas build`: 5645 accepted / 1582 gaps (now includes the interactive session's committed season/editorial data). `tools/audit_build.py`: status ok, exit 0.
- No new claims accepted, no human approvals performed, proposals remain propose-only pending_review; no network/paid calls/auth changes/push/deploy. STOP absent; deadline 2026-09-25T09:00+02:00 not reached (checked between bounded steps).
- Next acceptance: history compressor (50% preflight, last 20 messages protected, tool pairs atomic, note flush); controlled claude_cli adapter behind a provider registry — each with RED tests first. Live license-track run still blocked on claude CLI auth + human review gates; not retried in this offline increment.
