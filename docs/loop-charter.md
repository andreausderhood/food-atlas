# Food Atlas growth loop — charter

Continuous, unattended extension of the atlas data corpus. One verified delivery per run.

## Publication authority
- **Local commits only.** No push, no deploy, no external side effects.
- Writable: `data/curated/`, `data/registry/images.yaml` (metadata only), `docs/loop-ledger.md`, `NOTICE.md` (regenerated), `data/images/` (only with verified provenance).
- Read-only: `src/`, `tests/`, `data/raw/` (append-only for registered downloads), `wiki/` (untracked research notes — leave alone).

## Hard rules
1. Never invent data. Nutrition numbers, season months, bioactivity, health claims: only from registered sources passing the contract gates. Editorial narrative/sensory prose is allowed and must stay descriptive (no health claims — Rule 8).
2. Tests + build + audit green before every commit (`uv run pytest -q`, `uv run atlas build`, `uv run python tools/audit_build.py`). Red repo = stop, report, do not commit.
3. One backlog item per run. Mark it in `docs/loop-ledger.md` § delivered with the commit hash. Never redo a delivered item.
4. No `rm`, no `git reset/checkout --`, no new dependencies, no force operations, no secrets.
5. If a gate fails twice for the same reason: stop, write the blocker into the ledger § blockers, report.
6. Report ≤ 8 lines.

## Backlog order
1. Editorial entries for the 26 foods without narrative/sensory (list in ledger).
2. Registered source downloads (BLS 4.0 etc. — registry rules apply).
3. Kuratur tasks from André (image review, sepia audit) — only after 1–2 prove the loop; images require real license + credit, never fabricated.
4. Deepening existing entries with claims from already-registered sources.

Ledger: [loop-ledger.md](loop-ledger.md)
