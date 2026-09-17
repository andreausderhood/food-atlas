# Traceability Contract

> Sources: Food Atlas project, product.md, 2026-09-17
> Raw: [Food Atlas product definition](../../raw/food-atlas-project/2026-09-17-food-atlas-product-definition.md)
> Updated: 2026-09-17

## Overview

Every value in the Food Atlas is a sourced claim object that must pass ten rules. A claim that fails is never published; it becomes a named open question (a gap), as in the Victorinox library.
- **Rules 1–5** are inherited from Victorinox.
- **Rules 6–10** are new, because food data fails in ways steel data does not.

A claim's evidence tier comes from how its value was obtained, and it lives on the claim, not on the source.

## The claim object

`{v, unit, basis, food_part, src, tier, method, derivation}`. The `derivation` field records how a value was obtained (analytical, calculated, imputed, borrowed, predicted, extracted). National tables publish such codes per value.

## The ten rules

| # | Rule | Meaning |
| :-: | :--- | :--- |
| 1 | Claim object | Every value carries the fields above |
| 2 | Source resolves | Every `src` exists in the source registry |
| 3 | Scope | A source may only back the claim groups it `supports`; USDA nutrition data cannot back a season claim |
| 4 | No broken links | A tier 1–3 claim may not cite a source whose link is broken |
| 5 | Tier 5 quarantined | `SRC-UNVERIFIED` backs tier-5 claims only |
| 6 | No amount without a basis | Each concentration declares its basis (fresh weight, dry weight, as sold) and food part; otherwise it becomes a gap |
| 7 | Predictions are not measurements | Model outputs carry model name, version and confidence tier |
| 8 | Evidence, never health claims | Say "compound-level assay evidence associated with anti-inflammatory activity", never "anti-inflammatory food" |
| 9 | License gate | Only sources that allow open redistribution, including commercial reuse, can ship; an unread license is a build failure; `cite` sources back single curated facts only |
| 10 | Primary evidence only | A figure quoted second-hand in another paper's discussion must be traced to its primary source, or it becomes a gap |

Rule 10 was prompted by a FoodAtlas apple carbohydrate value; see [FoodAtlas v4.11 bundle findings](foodatlas-v4-11-bundle-findings.md).

## Evidence tiers

| Tier | Meaning | Examples |
| :-: | :--- | :--- |
| 1 | Analytical value with documented method and sample | USDA FDC Foundation Foods; national-table values coded analytical; PTFI (adapter only) |
| 2 | Registry or standard | FoodOn, NCBI Taxonomy, GBIF backbone, national variety registers, Codex |
| 3 | Peer-reviewed literature | Primary papers; FoodAtlas literature extractions flagged `llm_extracted` |
| 4 | Predicted, inferred or declared | Model outputs; values coded imputed, calculated or borrowed; breeder and grower descriptions |
| 5 | Unverified | A work queue, not a resting place |

As in Victorinox, each claim also shows its evidence **kind** and its **independence** (independent, or declared by an interested party). One national table can hold a tier-1 analytical value next to a tier-4 borrowed one.

## License classes

The atlas is MIT-licensed, so anyone may reuse it commercially. Anything it ships must allow that.

| Class | Licenses | Use |
| :--- | :--- | :--- |
| Ship | Public domain, CC0, CC BY, Apache-2.0, MIT, UK OGL, other open licences allowing commercial reuse | Imported and redistributed; attribution goes into `NOTICE.md` |
| Cite | Any readable publication | Single facts entered by hand with a `ref`; no bulk import, no copied text |
| Adapter only | CC BY-NC, access agreements, no-redistribution terms | Never in the repository or the published data; an optional local loader may exist |
| Keep separate | Share-alike (ODbL, CC BY-SA) | Not merged into the database; images may ship file by file with their own license |

Per-source verdicts are collected in [Licensing food data for an MIT atlas](mit-licensing-of-food-data.md).

## See Also

- [Food Atlas product overview](food-atlas-product.md)
- [Food Atlas data model](food-atlas-data-model.md)
