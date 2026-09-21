# FAO Food Composition Table for Use in Africa (1968)

> Sources: FAO x6877e (Leung, Busson & Jardin, 1968), 31 pages; local ingest `src/atlas/ingest/fao_africa.py`
> Raw: `data/research/scope/fao-africa-1968/` (fetched pages, git-ignored); parsed JSON `parsed.json`
> Updated: 2026-09-21

## What it is

The FAO/US-HEW "Food Composition Table for Use in Africa" — 100 g edible-portion
values for energy, moisture, protein, fat, carbohydrate, fiber, ash, Ca, P, Fe,
retinol, β-carotene, thiamine, riboflavin, niacin, tryptophan, ascorbic acid,
plus a refuse column. The underused-foods funnel's measurement anchor: African
and indigenous foods that USDA and BLS never cover.

## What the parse yields

- **1,623 food items** across 13 groups (vegetables 366, fish 294, fruits 207,
  cereals 185, meats/insects 133, nuts/seeds 124…)
- **1,093 items with values**, 1,100 variants (whole-grain vs meal, raw vs dried)
- **560 distinct species** via the built-in scientific-name index (E23–E26),
  attached by item number

## Parse pitfalls (encoded, don't re-solve)

The composition table is ONE continuous run over pages E05–E19 (item numbers
1–1594 crossing page breaks). Heading rows carry item no + name (binomial often
in parentheses); variant rows under them carry the values; annotation sub-rows
(`(2)` markers, `9.0–9.2` ranges) must be skipped. Group banners repeat inside
the 21-column layout merged with the units row. LaTeX-mangled numbers appear
here too (`$75.8\mathrm{mg}$ GAE/100 g`).

## License

US-HEW co-publication → public domain (17 USC §105, US government work); FAO
co-sponsorship → attribution per FAO terms. Verify against FAO ToU text before
the first claim imports. Proposed registry entry `SRC-FAO-AFRICA-1968`,
license_class `ship` (verification open), values as tier-3
`literature_extraction` — a 1968 compilation, not primary analytics.

## Role

Feeds [the species funnel](../food-atlas-project/species-funnel.md) and the
unified database build; complements [USDA/BLS](nutrition-composition-databases.md)
exactly where those are empty. These values are compilations with 58 years of
age — good for gap-shaped discovery and triangulation, weak as anchor claims.
