# The Species Funnel

> Sources: `tools/build_species_pool.py` output 2026-09-21; EPD/FAO/Wikipedia extractions
> Raw: `data/research/scope/species-pool.yaml`
> Updated: 2026-09-21

## What it is

The unified candidate pool: every species the atlas could onboard, one record
each with provenance. Built by a deterministic join (canonical binomials,
`×` hybrid normalization) over three sources:

| Source | Species | Contribution |
| :--- | ---: | :--- |
| EPD ZIM | 25,001 | edible parts, distribution, growing, medicinal |
| Wikipedia food lists | 2,322 | culinary framing, common names |
| FAO Africa 1968 | 560 | measured composition items |
| **Union** | **26,591** | |

## Priorities

- **P1 — 544 species**: FAO values + EPD enrichment. Claim-ready the moment
  onboarding runs; this is the first onboarding batch.
- **P2 — 16**: FAO-listed, no values.
- **P3 — 24,783**: EPD discovery layer (edible parts + distribution, no
  measurements yet).
- **P4 — 1,248**: Wikipedia names only.

## The onboarding machine (phase B)

`atlas onboard '<binomial>'` (to build): species in → food node, registry
entries, claim slots and gap rows out, with `not_yet_searched` status so the
[claim ledger](../food-atlas-project/pilot-source-review.md) shows what has
never been looked at. The nightly [Sciverse harvest](sciverse-literature-retrieval.md)
then fills measurement candidates per species; the website Explorer's
coverage badges read straight from those statuses.

## Design position

The funnel is deliberately demand-driven: P1 first, then species promoted by
editorial need (culinary relevance, region coverage), not bulk import of
26,591 nodes. Discovery data (distribution, edible parts) enters the database
as enrichment with `SRC-EPD-ZIM` provenance and license-class `unknown` until
FPI/PFAF terms are read — enrichment never becomes a numeric claim.
