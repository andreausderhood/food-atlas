# Licensing Food Data for an MIT Atlas

> Sources: Food Atlas project, product.md, 2026-09-17; Food Atlas review of the German synthesis, 2026-09-17; Food Atlas source landscape research, 2026-09-17; Food Atlas pilot source review, 2026-09-17
> Raw: [Food Atlas product definition](../../raw/food-atlas-project/2026-09-17-food-atlas-product-definition.md); [Review of the German synthesis](../../raw/food-data-sources/2026-09-17-review-food-species-atlas-resources.md); [Existing food atlases and datasets](../../raw/food-data-sources/2026-09-17-existing-food-atlases-and-datasets.md); [Pilot source review](../../raw/food-atlas-project/2026-09-17-pilot-source-review.md)
> Updated: 2026-09-17

## Overview

MIT lets anyone reuse the atlas commercially, so every dataset it ships must allow commercial redistribution too. That single decision reclassified several of the richest food datasets as local adapters, and it changed where the atlas gets its variety-level nutrition data: from open primary papers rather than from the best-curated compilations.

## What can ship

| Source | License | Note |
| :--- | :--- | :--- |
| USDA FoodData Central | CC0, public domain | The analytical backbone |
| BLS 4.0 (Max Rubner-Institut) | CC BY 4.0, free since 16 Dec 2025 | 7,140 foods, 138 nutrients |
| Ciqual 2025 (ANSES) | Open licence | 3,484 foods, 74 constituents |
| Swiss Food Composition Database | Free, commercial use allowed with attribution | V7.1, 1,246 foods |
| FoodAtlas bundle v4.11 | Apache-2.0 | CTD-derived rows excluded |
| FAOSTAT | CC BY 4.0 | Production statistics |
| FoodOn | CC BY 4.0 | Food classes and relations |
| USDA Pomological Watercolor Collection | Public domain | 7,584 paintings, 3,807 of apples |
| Wikidata | CC0 | Identifiers |
| Khoury et al. 2016 (Dryad) | CC0 | Crop origins |
| Gupta et al. 2026 (paper text) | CC BY 4.0 | Bioactivity evidence layer |

## What cannot ship

| Source | Restriction | Consequence |
| :--- | :--- | :--- |
| PTFI metabolomics | CC BY-NC 4.0 plus an access agreement | Adapter only; the study's own repository does not redistribute it either |
| FooDB | Commercial reuse needs the authors' permission | Adapter only |
| Phenol-Explorer | Commercial reuse needs permission | Adapter only; its method split is still worth copying into our `method` field |
| FAO/INFOODS BioFoodComp 4.0 | The FAO record shows only "© FAO", with no open license | Adapter only, used as a finding aid to the primary papers it cites |
| CTD rows inside FoodAtlas | Commercial reproduction prohibited without permission | Excluded; they back all chemical–disease links |
| FishBase, SeaLifeBase | CC BY-NC 4.0 | Adapter only |
| PROSEA texts | CC BY-NC-SA 3.0 NL | Adapter only |
| Plants For A Future | Paid database license | Not usable |
| Open Food Facts | ODbL share-alike | Kept separate, never merged |

## Cite-only sources

Some sources may back single curated facts but never a bulk import: BZfE's seasonal calendar (website text is CC BY-NC-ND, and the graphic's terms are unsettled), FAO ECOCROP (general FAO reuse terms are non-commercial), and Mansfeld (no reuse grant found). See [Pilot source review](pilot-source-review.md).

## Consequences for the atlas

- **Variety-level nutrition** now comes from USDA Foundation Foods, which records cultivar metadata, and from values re-extracted from open-access primary papers. That is slower than importing BioFoodComp, but the provenance is cleaner.
- **The disease layer is dropped** with the CTD rows, which suits rule 8 anyway.
- **Adapters** let a contributor plug in their own copy of PTFI, FooDB, Phenol-Explorer or BioFoodComp locally, without those data ever entering the published build.
- **Permission requests** to FAO/INFOODS, FooDB and Phenol-Explorer remain an open decision (D8); nothing has been sent.

> **Status: Disputed**
> The German research synthesis treats FooDB, Phenol-Explorer, BioFoodComp 4.0 and PTFI as core, shippable inputs and calls FooDB's data "uneingeschränkt" available. The Food Atlas review found the opposite for each: commercial reuse needs permission (FooDB, Phenol-Explorer), no open license is shown (BioFoodComp), and PTFI is CC BY-NC with an access agreement.

## See Also

- [Traceability contract](traceability-contract.md)
- [Pilot source review](pilot-source-review.md)
- [Nutrition composition databases](../food-data-sources/nutrition-composition-databases.md)
- [Food chemistry and flavour databases](../food-data-sources/food-chemistry-and-flavour-databases.md)
