# Database and Pipeline Plan (2026-09-21)

> Sources: `docs/superpowers/specs/2026-09-21-database-and-pipeline-plan.md`; `2026-09-21-unified-database-and-site-system.md`
> Raw: both spec files in-repo
> Updated: 2026-09-21

## Architecture decision

The atlas database stays **file-based and git-versioned** (YAML/JSON under
`data/`, Git as the ledger) — the [traceability contract](traceability-contract.md)
demands auditable, diffable provenance. A deterministically compiled
`atlas.db` (SQLite + FTS5) serves as the query mirror for the website and
pipeline; source of truth remains Git.

## Nine sources, four doors

| Door | Sources | State |
| :--- | :--- | :--- |
| Direct ingest (built) | USDA FDC, BLS 4.0, FoodAtlas v4.11 | 5,645 accepted claims, 275 tests |
| Ingest done, curation open | [FAO Africa 1968](../food-data-sources/fao-africa-1968.md) | parser green, claims to prepare (A1) |
| Standing harvest | [Sciverse](../food-data-sources/sciverse-literature-retrieval.md) | nightly cron, cache makes re-grading free |
| Discovery/enrichment only | [EPD ZIM + FPI](../food-data-sources/edible-plant-database.md), Wikipedia pools | never measurement claims |

Every source entering needs: a registry entry with the license text read, a
tested parser, gap-honest claim mapping (missing fields become gaps, not
assumptions), propose-only curation.

## Phases

- **A — consolidate**: FAO claims (A1), [species funnel](species-funnel.md) (A2, done), FDC-API ingest, close the 70 unknown Sciverse licenses.
- **B — onboard**: `atlas onboard` machine, first batch = 544 P1 species.
- **C — standing pipeline**: nightly Sciverse harvest, weekly funnel promotion, diff reports instead of raw reading.
- **D — site**: rebuild on the [stitch design system](site-design-system.md); the four mockups become Jinja templates with explicit data bindings.

## Open flags

TCM/Ayurveda lanes in the cross-system matrix have no sources onboarded yet —
the matrix ships with honest zeros until they exist. Food_Plants_World stays
blocked on license (rule 9). FDC-API ingest must filter `dataTypes` — the
default search mixes experimental rows into food data.
