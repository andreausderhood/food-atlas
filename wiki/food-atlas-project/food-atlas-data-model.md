# Food Atlas Data Model

> Sources: Food Atlas project, product.md, 2026-09-17; German research synthesis (undated); Food Atlas review of that synthesis, 2026-09-17
> Raw: [Food Atlas product definition](../../raw/food-atlas-project/2026-09-17-food-atlas-product-definition.md); [German research synthesis](../../raw/food-data-sources/food-species-atlas-resources-de.md); [Review of the German synthesis](../../raw/food-data-sources/2026-09-17-review-food-species-atlas-resources.md)
> Updated: 2026-09-17

## Overview

The atlas links **organisms** to **foods**, foods to the **molecules** they contain, and foods to one another through **processes** driven by **microbes**. Foods are typed on four levels:
- **taxon food:** food from a species or an infraspecific taxon;
- **cultivar / breed;**
- **part;**
- **form.**

The levels follow Mansfeld's infraspecific ranks and FoodOn's relations. That keeps cabbage and broccoli apart even though they are one species, and keeps a wild ancestor from being filed as a variety.

## Registers

| # | Register | Holds | Join keys |
| :-: | :--- | :--- | :--- |
| 1 | Organisms | Species-level origin, native range, growing needs, climate, occurrence, production | NCBI Taxon, GBIF, Wikidata |
| 2 | Foods | The four typed levels; nutrition, molecules, sensory, season, images | FoodOn, FoodAtlas ID, FDC ID |
| 3 | Molecules | Nutrients, bioactive compounds, food-contact migrants; flavour descriptors; bioactivity evidence | ChEBI, PubChem CID, InChIKey |
| 4 | Processes | Transformations from input food to output food | Curated |
| 5 | Microbes | Bacteria, yeasts and moulds; the processes they drive | NCBI Taxon |
| 6 | Sources | Kind, independence, scope, license, link status | — |
| 7 | Gaps | Named open questions and what would settle them | — |
| 8 | Funnel | Underused foods moving through evidence gates | — |

## Food levels

| Level | What it is | Example | Link |
| :--- | :--- | :--- | :--- |
| Taxon food | Food from a species or an infraspecific taxon (subsp., convar., var.) | *Brassica oleracea* convar. *italica* (broccoli) | *derives from* (RO_0001000) → organism |
| Cultivar / breed | Named cultivated variety or animal breed | Apple 'Honeycrisp' | *is_a* → taxon food; own register ID, because NCBI lacks most cultivars |
| Part | Anatomical part | Apple peel (exocarp), flesh (mesocarp), seed | *has part* (BFO_0000051) from the whole food |
| Form | State after a process | Raw, dried, juice, pomace | *derives from* a part or food, via a process |

**Why the infraspecific level matters:** the German synthesis explains Mansfeld's ranks with *Brassica oleracea*. White cabbage, cauliflower, broccoli, kohlrabi and Brussels sprouts map to convar. *capitata*, *botrytis*, *italica*, *gongylodes* and *gemmifera*: one species, five foods.

**Foods with no single taxon:**
- Composite foods.
- Foods made by microbes, such as xanthan gum from *Xanthomonas campestris*.

These carry a *derives from* chain instead of one taxon.

## Molecules

Molecules are deduplicated by InChIKey and mapped to ChEBI, PubChem and CDNO. CDNO separates a pure compound (α-tocopherol) from a nutrient equivalent (vitamin E equivalents).

## Claim groups and the entry card

**Claim groups:** identity · nutrition · molecules · bioactivity · sensory · origin · geography · growing · season · process · regulatory · narrative.

**The entry card** has two layers, as in Victorinox:
- **Editorial:** photo, explanation, story, and the food's place in the family tree.
- **Technical:**
  - nutrition panel, with basis and source on every figure;
  - molecule list, with evidence chips;
  - bioactivity labelled as evidence;
  - sensory data;
  - origin and production map;
  - season by region;
  - growing;
  - varieties, parts and forms;
  - processes and microbes;
  - the entry's own gaps and sources.

## Ingestion pipeline (as built, 2026-09-21)

| Stage | Shippable inputs | Result |
| :-: | :--- | :--- |
| 1 Taxonomy | Kew useful-plants checklist and WCVP, GRIN, NCBI Taxonomy, GBIF backbone (Mansfeld as reference) | Organisms register |
| 2 Food levels | FoodOn, FoodAtlas food taxonomy, USDA FDC | Foods register |
| 3 Nutrition | USDA FDC Foundation + SR Legacy, BLS 4.0, [FAO Africa 1968](../food-data-sources/fao-africa-1968.md), open primary papers via [Sciverse](../food-data-sources/sciverse-literature-retrieval.md) | Nutrition claims |
| 4 Molecules | FoodAtlas (CTD-free), ChEBI, CDNO, PubChem | Molecules register |
| 5 Bioactivity | Gupta et al. 2026 text; FRAP values from open primary papers | Bioactivity layer |
| 6 Gaps | Everything that failed a rule | Gap register and [funnel](species-funnel.md) |

Enrichment (distribution, edible parts, growing ecology) flows from
[EPD/EPD-ZIM and Wikipedia pools](../food-data-sources/edible-plant-database.md)
as non-claim data with own provenance — never into numeric claims. The
compiled `atlas.db` (SQLite mirror) is built from the same registers and
claims; Git stays the source of truth. See
[Database and pipeline plan](database-and-pipeline-plan.md).

The German synthesis proposed a six-phase pipeline with PTFI, FooDB, Phenol-Explorer and BioFoodComp as core inputs.

> **Status: Disputed**
> The German synthesis places PTFI, FooDB, Phenol-Explorer and BioFoodComp 4.0 inside its main pipeline. The Food Atlas review found that none of these can ship in an MIT atlas. product.md therefore limits them to local adapters that "plug into stages 3–5 **locally**, never into the published build". See [Licensing food data for an MIT atlas](mit-licensing-of-food-data.md).

## See Also

- [Traceability contract](traceability-contract.md)
- [FoodAtlas v4.11 bundle findings](foodatlas-v4-11-bundle-findings.md)
- [Crop species and variety registers](../food-data-sources/crop-species-and-variety-registers.md)
