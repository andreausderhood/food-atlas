# The Food Data Landscape

> Sources: Food Atlas source landscape research, 2026-09-17; German research synthesis (undated); scope expansion 2026-09-21
> Raw: [Existing food atlases and datasets](../../raw/food-data-sources/2026-09-17-existing-food-atlases-and-datasets.md); [German research synthesis](../../raw/food-data-sources/food-species-atlas-resources-de.md)
> Updated: 2026-09-21

## Overview

No complete food atlas exists. Every resource is deep in one or two layers and silent on the rest: taxonomy without nutrition, nutrition without varieties, chemistry without provenance, or a beautiful culinary map with no sources at all. The gap the Food Atlas aims at is the join: species down to variety, with a source on every value.

## Best in each category

| Question | Best answer today |
| :--- | :--- |
| Crop species lexicon | Mansfeld's World Database / Encyclopedia of Agricultural and Horticultural Crops (IPK Gatersleben): 6,100 cultivated species |
| Economic plant list | World Economic Plants, 2nd ed. (Wiersema & León, CRC 2013): 12,000+ taxa |
| Edible and useful plant checklist | Kew World Checklist of Useful Plant Species (2020): 40,292 species; Ulian et al. (2020) count about 7,039 edible plant species |
| Book closest to the atlas idea | T.K. Lim, *Edible Medicinal and Non-Medicinal Plants* (Springer, 12 volumes, 1,000+ plants) |
| Most varieties in a book | Facciola, *Cornucopia II* (1998): 3,000 species, 7,000 varieties |
| Illustrated species guide | van Wyk, *Food Plants of the World*, 2nd ed. 2019 |
| Variety-level nutrition | FAO/INFOODS BioFoodComp; Simmonds & Preedy, *Nutritional Composition of Fruit Cultivars* (2016) |
| Open nutrition tables | USDA FoodData Central (CC0) and German BLS 4.0 |
| Food chemistry | FoodAtlas (193,236 chemicals) and FooDB (70,926 compounds) |
| Standardized deep composition | Periodic Table of Food Initiative (PTFI) |
| Culinary atlas as a product | TasteAtlas: 12,272 dishes, 7,744 local ingredients, no sources shown |

## Benchmarks worth studying

- **FoodAtlas** (UC Davis): a food → chemical → disease graph, 10,270 foods, weekly updates, Apache-2.0 bundle. It has no season, origin, growing or sensory data, and its amounts lack a basis. See [FoodAtlas v4.11 bundle findings](../food-atlas-project/foodatlas-v4-11-bundle-findings.md).
- **TasteAtlas:** the user-experience benchmark. Strong cultural storytelling, no nutrition, chemistry, taxonomy or provenance.
- **Mansfeld:** 6,100 crop species with taxonomy, uses and distribution; no nutrition.
- **Plants For A Future:** 8,000+ useful plants with edibility ratings, behind a paid database license, temperate-biased.
- **Slow Food Ark of Taste:** 5,000+ endangered foods from 120+ countries. Stories rather than data, and a natural seed list for the atlas's funnel of underused foods.

## New since 2026-09-17 (now standing in the atlas)

- **Sciverse** — literature retrieval with the traceability contract baked into
  the query; phase-1 harvest closed 75 of 322 basis gaps. See
  [Sciverse literature retrieval](sciverse-literature-retrieval.md).
- **FAO Africa 1968** — 1,623 food items / 560 species of measured composition
  where USDA and BLS are empty. See
  [FAO Africa 1968](fao-africa-1968.md).
- **Edible Plant Database (Kiwix ZIM)** — 27,918 species with edible parts,
  distribution and growing ecology; the discovery layer. Food Plants
  International's live WebDirect (35,103 records) stays locked (no API, license
  unstated). See [Edible Plant Database](edible-plant-database.md).
- **The species funnel** — the three united: 26,591 candidate species,
  544 claim-ready. See [the species funnel](../food-atlas-project/species-funnel.md).

## Gaps no source fills

Three layers must be curated by hand, because no dataset covers them:
- **consumer seasonality** outside Germany;
- **colour and texture** of foods;
- **variety-level nutrition** beyond BioFoodComp and one book.

This is the strongest argument for eventual partnerships with genebanks, national fruit collections and PTFI.

## See Also

- [Nutrition composition databases](nutrition-composition-databases.md)
- [Crop species and variety registers](crop-species-and-variety-registers.md)
- [Food chemistry and flavour databases](food-chemistry-and-flavour-databases.md)
- [Geography, growing and season datasets](geography-growing-and-season-datasets.md)
- [Food reference books](food-reference-books.md)
- [Food Atlas product overview](../food-atlas-project/food-atlas-product.md)
