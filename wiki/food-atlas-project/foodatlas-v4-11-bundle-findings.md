# FoodAtlas v4.11 Bundle Findings

> Sources: Food Atlas project, product.md, 2026-09-17; Food Atlas review of the German synthesis, 2026-09-17
> Raw: [Food Atlas product definition](../../raw/food-atlas-project/2026-09-17-food-atlas-product-definition.md); [Review of the German synthesis](../../raw/food-data-sources/2026-09-17-review-food-species-atlas-resources.md)
> Updated: 2026-09-17

## Overview

The FoodAtlas v4.11 bulk bundle (UC Davis, Apache-2.0) was profiled locally on 2026-09-17. The findings:
- It is large.
- Amounts are rare and carry no basis.
- Most food–chemical links rest only on LLM extraction.
- Parts and processing are empty.
- Species links are thin.
- A third of its evidence comes from CTD, which prohibits commercial reproduction without permission.

These findings drove several Food Atlas rules and design choices.

## Scale

- **Entities:** 216,804 in total: 10,270 foods, 193,236 chemicals, 13,298 diseases.
- **Links:** 542,953 in total: 108,047 *contains*, 304,050 *is_a*, 84,099 positive and 46,757 negative chemical–disease correlations.
- **Evidence rows:** 662,821 in total.

| Evidence source | Rows |
| :--- | ---: |
| ChEBI | 269,443 |
| CTD | 218,361 |
| LLM extraction, Claude Opus 4.8 | 124,348 |
| LLM extraction, Gemma 4 | 24,567 |
| USDA FDC | 13,565 |
| FoodOn | 11,682 |
| CDNO | 855 |

## Findings and design consequences

1. **Amounts are scarce.** 15,726 evidence rows (2.4%) carry an amount, all in mg/100 g, and 10,326 of those come from FDC. → "present, amount unknown" is its own state.
2. **No basis, and second-hand evidence.** An LLM extracted "carbohydrate 94.07 g/100 g" for apple from PMC 9818353. That paper is a kiwifruit study that mentions the apple figure only in its discussion, quoting another paper. The website shows 94% for an apple. → Rules 6 and 10 in the [traceability contract](traceability-contract.md).
3. **Parts and processing are empty.** Only 1 of 662,821 rows fills `food_part` or `food_processing`. → The part and form levels must be built.
4. **Species links are thin.** 515 of 10,270 foods mention an NCBI taxon in their synonyms, and only 56 carry one in their external IDs. → The Organisms register must be built.
5. **Levels are mixed.** Apple has 15 *is_a* children: 13 cultivars, the wild ancestor *Malus sieversii* filed as if it were a variety, and the form "apple (raw)". → Food levels are typed.
6. **Nothing is validated.** No evidence row is flagged as validated; 5,403 rows have a machine plausibility score.
7. **Chemicals are duplicated.** Vitamin C, L-ascorbic acid and L-ascorbate appear as separate rows on the apple page. → Molecules are merged.
8. **Flavour bridge.** 1,764 chemicals carry flavour descriptors (sweet 358, bitter 265, fruity 118, green 115, woody 94).
9. **Navigation.** 13 FoodOn food groups can drive top-level browsing.
10. **Mixed licensing.** 218,361 evidence rows (33%) come from CTD. They back all 130,856 chemical–disease links and 22,364 *is_a* links, but no food–chemical links. → CTD-only links and the disease layer are left out of the MIT atlas.
11. **AI-extracted core.** 95,129 of 108,047 food–chemical links (88%) rest only on LLM-extracted literature rows. → Tier 3 with the flag `llm_extracted`; FDC-backed values are preferred.
12. **Variety depth varies.** Among the staples checked, apple has 15 children, rice 14, potato 9, tomato 8 and grape 7.

> **Status: Disputed**
> The German synthesis states flatly that dry-weight values were imported without a basis label, so the apple shows 94 g carbohydrate per 100 g fresh weight. The Food Atlas review calls this "Worse than that." PMC9818353 is a kiwifruit study that only quotes the apple value from another paper. The dry-weight reading is an inference, not a checked fact.

## See Also

- [Traceability contract](traceability-contract.md)
- [Food chemistry and flavour databases](../food-data-sources/food-chemistry-and-flavour-databases.md)
- [Licensing food data for an MIT atlas](mit-licensing-of-food-data.md)
