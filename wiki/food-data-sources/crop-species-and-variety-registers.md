# Crop Species and Variety Registers

> Sources: Food Atlas source landscape research, 2026-09-17; German research synthesis (undated); Food Atlas review of that synthesis, 2026-09-17; Food Atlas pilot source review, 2026-09-17
> Raw: [Existing food atlases and datasets](../../raw/food-data-sources/2026-09-17-existing-food-atlases-and-datasets.md); [German research synthesis](../../raw/food-data-sources/food-species-atlas-resources-de.md); [Review of the German synthesis](../../raw/food-data-sources/2026-09-17-review-food-species-atlas-resources.md); [Pilot source review](../../raw/food-atlas-project/2026-09-17-pilot-source-review.md)
> Updated: 2026-09-17

## Overview

The species layer of a food atlas has good open sources; the variety layer is scattered across genebank catalogues, seed-marketing registers and crop-specific databases. Species lists answer which organisms are edible; variety registers answer which cultivar is on the plate, and the two need different keys.

## Species and taxonomy

| Source | Content | Notes |
| :--- | :--- | :--- |
| **Kew World Checklist of Useful Plant Species** (2020) | 40,292 species with use categories and crop-wild-relative flags | Open download; license not yet read |
| **Ulian et al. 2020** | About 7,039 edible plant species | The headline figure for edible plant diversity |
| **Pironon et al. 2024** | 35,687 utilised species with occurrences and distribution models | Published on Zenodo |
| **Mansfeld's World Database** (IPK Gatersleben) | 6,100 cultivated species | Also the reference for infraspecific ranks |
| **World Economic Plants** (Wiersema & León) | 12,000+ economically important vascular plants | Linked to USDA GRIN germplasm accessions |
| **WCVP / Plants of the World Online** (Kew) | Accepted names and native ranges | License to verify |
| **NCBI Taxonomy, GBIF, Wikidata** | Join keys and occurrence points | GBIF records carry CC0, CC BY or CC BY-NC per dataset |
| **FishBase, SeaLifeBase** | 36,500+ fish species; about 72,000 other aquatic species | CC BY-NC 4.0, so adapter-only |

**Beyond plants:** Boa's FAO report records 2,166 edible fungi, of which 1,069 are used as food; Jongema's Wageningen list covers 2,111 edible insect species, and a 2024 atlas counts 2,205 species eaten in 128 countries; FAO DAD-IS holds livestock breeds by country with risk status.

## Infraspecific ranks: why cabbage and broccoli are not one food

Mansfeld introduces ranks below species: subspecies, convarietas and varietas. The German synthesis gives the decisive example: instead of filing white cabbage, cauliflower, broccoli, kohlrabi and Brussels sprouts as one undifferentiated plant, Mansfeld assigns them to *Brassica oleracea* convar. *capitata*, convar. *botrytis*, convar. *italica*, convar. *gongylodes* and convar. *gemmifera*. The Food Atlas adopts this as its taxon-food level.

> **Status: Disputed**
> The six convarieties are taken from the German synthesis. The pilot source review could not read any Mansfeld taxon record (the site redirected to a database description), so these rank assignments remain unverified in the registry rather than externally supported. NCBI records were verified only at species level: 3750 for *Malus domestica* and 3712 for *Brassica oleracea*.

## Variety and cultivar registers

| Register | Content |
| :--- | :--- |
| **Genesys** (Crop Trust) | 4,464,904 genebank accessions with passport data (December 2025) |
| **EU Plant Variety Database / Common Catalogues** | 23,000+ agricultural and 21,000+ vegetable varieties marketable in the EU |
| **CPVO Variety Finder, UPOV PLUTO** | Protected and registered varieties worldwide |
| **VIVC** | About 23,000 grape cultivars, breeding lines and species, with genetic profiles |
| **UK National Fruit Collection** | 2,040+ apple varieties; about 3,500 fruit cultivars in total, searchable with photos |
| **Slow Food Ark of Taste** | 5,000+ heritage foods |
| **USDA GRIN-Global** | Links taxa to National Plant Germplasm System accessions |

**Tropical and wild plants:** PROTA and PROSEA monographs (via Pl@ntUse) describe thousands of African and South-East Asian useful plants with agronomic and phytochemical detail. PROSEA's texts are CC BY-NC-SA 3.0 NL, so they are reference-only for an MIT atlas. Plants For A Future adds 8,000+ useful plants with edibility, medicinal and hazard ratings, but its database is sold under a paid license.

## See Also

- [The food data landscape](food-data-landscape.md)
- [Food Atlas data model](../food-atlas-project/food-atlas-data-model.md)
- [Pilot source review](../food-atlas-project/pilot-source-review.md)
- [Food reference books](food-reference-books.md)
