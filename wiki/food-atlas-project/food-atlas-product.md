# Food Atlas — Product Overview

> Sources: Food Atlas project, product.md, 2026-09-17
> Raw: [Food Atlas product definition](../../raw/food-atlas-project/2026-09-17-food-atlas-product-definition.md)
> Updated: 2026-09-17

## Overview

The Food Atlas is planned as "A traceable atlas of edible life". It would cover foods from species down to variety, part and form, together with their molecules, the processes that transform them and the microbes that drive those processes. It inherits its traceability contract from the user's Victorinox Material & Technology Library and extends it for food data. The project is open source: code is MIT, and curated data is CC BY 4.0. Phase 1 is a pilot covering apple plus the cabbage family.

## Why it should exist

- **Labels are too small.** Nutrition labels describe a food with about a dozen numbers, while the chemistry is far larger. Gupta et al. (2026) report 27,713 detected molecular features across 322 foods, 44% of them found in only one food. See [Gupta et al. 2026](../food-bioactivity/gupta-2026-food-bioactivity-framework.md).
- **Existing resources each hold one slice:**
  - USDA FoodData Central: nutrition.
  - FoodAtlas: food–chemical–disease links.
  - GBIF: occurrence.
  - FAOSTAT: production.
  
  None connects these slices at variety level with provenance on every value.
- **Most edible biodiversity is invisible.** 10–50 crops supply about 95% of calories (a figure cited in Gupta et al.), so the atlas aims to make underused foods findable.

## Users and example questions

| User | Example question |
| :--- | :--- |
| Curious eater, designer, chef | What is in season now that is red and crunchy? How does Honeycrisp differ from Granny Smith? |
| Product developer, researcher | Which foods contain quercetin, how much, and how sure are we? |
| Educator, storyteller | Where did the apple come from, and where is it grown today? |

## Phases and views

| Phase | Deliverable | Views |
| :-: | :--- | :--- |
| 1 | Pilot slice plus the contract validator | Foods, Entry, Compare, Gaps, Sources |
| 2 | Molecule register, bioactivity layer, fingerprint map | Molecules, Fingerprint map, Bioactivity wheel |
| 3 | Organisms register, world map, season, growing across all 13 food groups | World map, Season calendar |
| 4 | Processes, microbes, funnel, further datasets | Processes and Microbes, Funnel |

**Not in scope for v1:** personal diet advice, health claims, recipes, commerce and a public API.

**Build approach:**
- Victorinox's pattern (hand-written YAML plus one HTML page) breaks at the molecule level: 354 chemicals for one apple, times thousands of foods.
- The recommended hybrid therefore uses:
  - hand-written files for curated content;
  - DuckDB over parquet files for bulk imports;
  - one validator for both;
  - a static site generated per entry.

## Decisions

| ID | Decision | State (2026-09-17) |
| :-- | :--- | :--- |
| D1 | Commercial or not | Decided: open source, MIT |
| D2 | Pilot slice | Decided: *Malus domestica* (cultivars, peel, flesh, juice, pomace, cider, dried apple) and *Brassica oleracea* convar. capitata, italica, botrytis, gongylodes, gemmifera and acephala, including sauerkraut |
| D3 | Language | Decided: English first; German names from BLS stored as `name_de` |
| D4 | Physical specimens (as Victorinox had) | Open |
| D5 | Primary audience | Open |
| D6 | Request PTFI access | Resolved by D1: PTFI is adapter-only |
| D7 | License for curated data | Decided: CC BY 4.0 (`LICENSE-DATA`) |
| D8 | Ask data owners (FAO/INFOODS, FooDB, Phenol-Explorer) for permission | Plan 1 proceeds without partner contact; nothing has been sent |

> **Status: Outdated** (2026-09-17)
> The header of the 2026-09-17 product.md snapshot still says "Nothing is built" and that the curated-data license "is still open; see D7". Its own §9 records D7 as decided (CC BY 4.0). The decision table above follows §9.

## See Also

- [Traceability contract](traceability-contract.md)
- [Food Atlas data model](food-atlas-data-model.md)
- [FoodAtlas v4.11 bundle findings](foodatlas-v4-11-bundle-findings.md)
