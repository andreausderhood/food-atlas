# Sciverse — Literature Retrieval for the Atlas

> Sources: `docs/sciverse-prompts.md` (prompt library, 2026-09-20); harvest runs 2026-09-20/21 (`data/research/sciverse/`)
> Raw: prompt library at repo `docs/sciverse-prompts.md`; runs under `data/research/sciverse/` (git-ignored)
> Updated: 2026-09-21

## What Sciverse is

Sciverse (api.sciverse.space) retrieves scientific literature across six tools:
`agentic-search` (passage-level), `content` (full text paging), `meta-search`
(filterable metadata), `meta-catalog` (field discovery), `meta-paper-relations`
(citation graph), `resource` (figures). A prompt library turns it into a source
hunt that satisfies the [traceability contract](../food-atlas-project/traceability-contract.md):
every answer must carry value, unit, basis, food part, method, n, DOI, license —
and "not reported" is a valid answer.

## What the pipeline does (deterministic, no LLM in the loop)

`atlas research sciverse` maps open gaps from `gaps.csv` to queries, grades hits
locally, and writes candidate findings with verbatim quotes. Grading encodes the
contract as code: quote must be verbatim (rule 5), basis never inferred (rule 6),
LaTeX-mangled numbers (`$100\mathrm{g}$`) and HTML `<td>` tables parsed,
DW/FW ratios and bracketed `[21]` citations flagged (rule 10) instead of counted
as wins. A content-addressed response cache makes re-grading free.

## Phase-1 harvest (rule-6 gaps: amounts without basis)

322 unique gaps processed, ~450 API calls: 75 closed candidates (value + unit +
basis + part + verbatim quote), 171 partial with named reason, 76 unresolved.
Closed by food: kale 16, apple 15, broccoli sprouts 9, apple pomace 8. Lesson:
agentic-search ranks one noisy paper first for many gaps of the same food —
spot-check before counting wins.

## License triage (rule 9)

`atlas research sciverse --triage-licenses` looks up each harvested doc_id via
meta-search (no query — `query="*"` breaks doc_id filters; operators are
`FILTER_OP_*`; years arrive as floats) and classifies **only from the license
string**: 16 ship (CC BY), 13 adapter (CC BY-NC), 1 separate (CC BY-SA), 70
unknown — an unread license is a build failure, so unknown blocks import.

## Facts that stay true

- Token via `SCIVERSE_TOKEN` in `.env` (git-ignored), never in code.
- `doc_id` (content) is not `unique_id` (relations) — never interchange.
- Findings from cite-class sources stay local; no copied text into the MIT repo.
- Budget: 2 API calls per gap (search + optional content confirmation).
