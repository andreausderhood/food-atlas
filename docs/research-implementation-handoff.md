# Research implementation handoff

## Verified implementation, not full-plan completion

The research foundation provides deterministic tasks, license dependencies, SQLite leases, cached evidence occurrence checks, and a propose-only contract gate. Public CLI: `atlas research init`, `status`, `next --lease-by NAME`, `submit FILE`, `review ID`.

Submission JSON contains `item_id`, `lease_token`, task-matching `kind`, `subject`, `field`, `source`, and `evidence` records (`ref`, `quote`, optional web `cache_key`). License tasks additionally carry `findings.license`; other supported submissions carry a `claim` accepted by the existing contract. Unsupported proposal types fail closed.

Valid submissions atomically move tasks and proposals to `pending_review`. They do NOT mark tasks done or unlock license dependencies. SQLite is authoritative; `review` regenerates an export if needed. Tokens are excluded from exported proposal records. Rejected evidence requeues the task with a recorded failure and backoff. Review is inspection only, not approval/publication.

## Verification

- Full suite: `uv run pytest -q` → 218 passed, one existing FDC mapping warning.
- `uv run atlas build` → 5,555 accepted claims, 1,582 gaps.
- `uv run python tools/audit_build.py` → status ok, no implementation errors.
- Final targeted run: 16 research tests passed; all six public CLI/lifecycle tests individually confirmed passing.
- Separate-process smoke with COPIES of real registry/build inputs in a fresh temporary root: init 1,300 queued; next selected SRC-ECOCROP license_read; status 1 leased / 1,299 queued. Existing development state reported 1,305 items because enqueue is append-only and retains previously generated tasks; it is not the fresh task count.
- Smoke workspace: `/var/folders/kp/l3pd8db97bj0j7hcyr7302dr0000gn/T/atlas-research-smoke-a05f3mw5`.
- No research findings fabricated; lifecycle evidence is explicitly synthetic test data. No new research claims published by this implementation.

## Remaining original-plan work

Phase 1 is partial: no FakeProvider/conversation harness or deterministic raw-row proof adapters yet. The write gate is intentionally propose-only: substring occurrence cannot prove a model's numeric claim. Do not enable auto-write based merely on a local path.

Then implement and verify in original order: provider + conversation loop/tool registry and first licenses run; Commons/images; coverage/niche/source discovery; supervisor/resume/dashboard; optional API provider/failover; breadth. `run`, `stop`, and `accept` are NOT implemented. No autonomous week-long run has been proven.

Live-provider prerequisite: `claude auth status` returns `loggedIn: false`, `authMethod: none`. An operator must authenticate or explicitly choose another configured provider. Do not change the provider silently or treat offline test traces as live research.

## Concurrent ownership

hotspot: src/atlas/research/cli.py — a scheduled worker adopted/committed the initial research foundation while this interactive implementation was running. Current incremental lifecycle edits remain uncommitted. Coordinate ownership or use isolated worktrees before the next implementation run. Existing workflow/spec/ledger documents were written by another session and were not overwritten here. No commit or push was made by this interactive session.
