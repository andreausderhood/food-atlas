# Nutritional Dark Matter

> Sources: Gupta, Gunning, Ahmed & Tagkopoulos, npj Science of Food, 2026-08-25; German research synthesis (undated)
> Raw: [From metabolomics dark matter to bioactivity](../../raw/food-bioactivity/2026-08-25-from-metabolomics-dark-matter-to-bioactivity.md); [German research synthesis](../../raw/food-data-sources/food-species-atlas-resources-de.md)
> Updated: 2026-09-17

## Overview

Nutritional dark matter is the part of food chemistry that nutrition science does not track: the thousands of metabolites in every food that sit outside the short list of nutrients with recommended intakes. The term frames why a food atlas cannot stop at a nutrition panel, and why the atlas records presence without an amount as a real state rather than a blank.

## The idea

Classical nutrition works with a reduced catalogue of nutrients. Gupta et al. open with the observation that the health and nutritional value of food extends far beyond macro- and micronutrients to a vast "dark matter" of thousands of metabolites that influence human health through diverse biological pathways. Most of these are never resolved structurally: of 27,713 detected features in the study, only 2038 had confirmed structural identities, which is 7.4% of them.

The framing is credited to Barabási, Menichetti and Loscalzo's *The unmapped chemical complexity of our diet* (Nature Food, 2019), which the German synthesis also cites as the origin of the term.

## Why it changes the design of a food database

- **Coverage is sparse and food-specific.** 44% of detected features occur in a single food, so a view built on averaged nutrients misses most of the chemistry.
- **Presence is not potency.** The study stresses that because biological effects are concentration-dependent, the mere presence of a compound is uninformative without an estimate of how much is present. This is the argument behind the atlas's rule that an amount must declare its basis and food part.
- **Nutrient thresholds do not generalise.** The authors argue that recommended dietary allowances are built around single nutrients with defined deficiency endpoints and largely linear dose-response relationships, while the metabolomic landscape is high-dimensional, sparse and non-linear. They call instead for modelling "molecular patterns" and compositional signatures.

## Consequences for the Food Atlas

1. The molecules register is a first-class layer, not an appendix to nutrition.
2. Presence-only links are stored and shown as such, with their evidence flagged.
3. Any pattern-level or predicted value stays at tier 4 with its model recorded, because pattern models are inference, not measurement.

## See Also

- [Gupta et al. 2026: food bioactivity framework](gupta-2026-food-bioactivity-framework.md)
- [Food chemistry and flavour databases](../food-data-sources/food-chemistry-and-flavour-databases.md)
- [FoodAtlas v4.11 bundle findings](../food-atlas-project/foodatlas-v4-11-bundle-findings.md)
