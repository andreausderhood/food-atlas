# Food Chemistry and Flavour Databases

> Sources: Food Atlas source landscape research, 2026-09-17; German research synthesis (undated); Food Atlas review of that synthesis, 2026-09-17
> Raw: [Existing food atlases and datasets](../../raw/food-data-sources/2026-09-17-existing-food-atlases-and-datasets.md); [German research synthesis](../../raw/food-data-sources/food-species-atlas-resources-de.md); [Review of the German synthesis](../../raw/food-data-sources/2026-09-17-review-food-species-atlas-resources.md)
> Updated: 2026-09-17

## Overview

Food chemistry is the best-covered layer of the atlas and the most legally constrained one. FoodAtlas ships; FooDB, Phenol-Explorer and PTFI do not. The flavour bridge, which links molecules to taste words, comes from a small, useful slice of these datasets.

## The main compound databases

| Database | Content | Use in an MIT atlas |
| :--- | :--- | :--- |
| **FoodAtlas v4.11** (UC Davis) | 193,236 chemicals; 108,047 food–chemical links; flavour descriptors | Ships (Apache-2.0), minus CTD-derived rows |
| **FooDB** (The Metabolomics Innovation Centre) | 70,926 compounds across about 1,000 raw foods, with ChEBI, PubChem, InChIKey, SMILES and calculated descriptors | Adapter only: commercial reuse needs permission |
| **Phenol-Explorer** (INRAE and partners) | Polyphenol content of 459 foods, with processing retention factors | Adapter only; its method split is worth copying |
| **PTFI** | Standardized multi-omics; 500 foods on the AHA platform; MarkerLab viewer | Adapter only (CC BY-NC, access agreement) |
| **Dr. Duke's Phytochemical and Ethnobotanical Databases** (USDA) | Plant chemicals, activities and ethnobotany | Free CSV on Ag Data Commons |
| **FlavorDB2** (IIIT-Delhi) | 25,595 flavour molecules; 2,254 linked to 936 natural ingredients | Terms to check |

**Phenol-Explorer's method split is the model to copy.** It separates HPLC without hydrolysis (native glycosides and esters), HPLC after chemical or enzymatic hydrolysis (total aglycones), and spectrophotometric sum parameters such as Folin-Ciocalteu. A polyphenol figure means little without knowing which of the three produced it. Version 3.0 onwards adds retention factors for cooking and storage, which is exactly what the atlas's process register needs.

> **Status: Disputed**
> The German synthesis calls FooDB the world's largest open food-compound database, available without restriction in CSV, SQL and JSON, and files both FooDB and Phenol-Explorer as tier-1 shippable sources. The Food Atlas review found that both require the authors' permission for commercial reuse, and that FoodAtlas lists more chemicals (193,236). Both are therefore adapter-only.

## The flavour bridge

- 1,764 chemicals in the FoodAtlas bundle carry flavour descriptors: sweet 358, bitter 265, fruity 118, green 115 and woody 94 are the most common.
- FlavorDB2 adds a far larger molecule set, though only a fraction is tied to natural ingredients.
- Colour and texture have **no** dataset at all. They must be curated, with colour possibly derived from images.

## Deduplication

Molecules arrive under many names: the FoodAtlas apple page lists vitamin C, L-ascorbic acid and L-ascorbate as separate entities. The atlas merges them by InChIKey, with ChEBI, PubChem and CDNO as identifier registries, so a nutrient equivalent is never confused with a pure compound.

## See Also

- [FoodAtlas v4.11 bundle findings](../food-atlas-project/foodatlas-v4-11-bundle-findings.md)
- [Licensing food data for an MIT atlas](../food-atlas-project/mit-licensing-of-food-data.md)
- [Gupta et al. 2026: food bioactivity framework](../food-bioactivity/gupta-2026-food-bioactivity-framework.md)
- [Nutrition composition databases](nutrition-composition-databases.md)
