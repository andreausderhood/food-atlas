# Nutrition Composition Databases

> Sources: Food Atlas source landscape research, 2026-09-17; German research synthesis (undated); Food Atlas review of that synthesis, 2026-09-17
> Raw: [Existing food atlases and datasets](../../raw/food-data-sources/2026-09-17-existing-food-atlases-and-datasets.md); [German research synthesis](../../raw/food-data-sources/food-species-atlas-resources-de.md); [Review of the German synthesis](../../raw/food-data-sources/2026-09-17-review-food-species-atlas-resources.md)
> Updated: 2026-09-17

## Overview

National food composition tables are the analytical backbone of any food atlas. Several are now open data; the ones with the deepest variety coverage are not. The practical split for an MIT-licensed atlas is: USDA, Germany, France and Switzerland ship; the FAO biodiversity database and the classic German book do not.

## Open tables that can ship

| Table | Scope | License |
| :--- | :--- | :--- |
| **USDA FoodData Central** | Foundation Foods (with sampling, genotype and production metadata), SR Legacy (final release 2018), FNDDS, Branded | CC0 |
| **BLS 4.0** (Max Rubner-Institut) | 7,140 foods, 138 nutrients; free since 16 Dec 2025 | CC BY 4.0 |
| **Ciqual 2025** (ANSES) | 3,484 foods, 74 constituents | Open licence |
| **Swiss Food Composition Database** | V7.1, 1,246 foods | Free, commercial use allowed with attribution |
| **CoFID 2021** (McCance and Widdowson's) | The UK reference dataset | Free download; license to verify |

**USDA Foundation Foods matters most for the atlas** because it records the underlying analytical sample results together with agricultural metadata: cultivar, growing location, soil, fertilisation, harvest date and maturity. That is the only open route to nutrition at cultivar level.

## Variety-level composition

- **FAO/INFOODS BioFoodComp** is the leading collection of purely analytical nutrient data below species level. Foods must be described at variety, cultivar or breed level, or at species level for wild and underutilised foods. Version 2.0 held 6,411 foods and 451 components; version 3.0 holds 7,953 entries; version 4.0 (2017) carries ISBN 978-92-5-109790-8.
- Its methodology is close to the atlas's own rules: analytical data only, with no calculated or estimated gap-fillers.

> **Status: Disputed**
> The German synthesis reports BioFoodComp 4.0 as holding 10,156 disaggregated entries, all normalised to edible portion on a fresh-weight basis, and treats it as a shippable tier-1 core source. The Food Atlas review could verify neither figure and found the FAO record shows only "© FAO" with no open license, so the database is adapter-only. Known verified figures: 6,411 (v2.0), 6,492 (v2.1) and 7,953 (v3.0).

- **Books:** Simmonds & Preedy's *Nutritional Composition of Fruit Cultivars* (Academic Press, 2016, 774 pages) remains the only book-length source of cultivar-level nutrition.

## Regional and traditional-food tables

- **WAFCT 2019** (FAO/INFOODS, West Africa): 1,028 profiled foods with 47 nutrients, covering underused African species such as Bambara groundnut (*Vigna subterranea*), fonio (*Digitaria exilis*) and baobab pulp (*Adansonia digitata*).
- **CINE** (McGill): nutrient values for traditional foods of Indigenous Peoples, including an Arctic nutrient file covering mammals, birds and fish. The German synthesis presents it as a counterweight to the Eurocentric focus of Western tables; its license still needs checking.

## Aggregators and commercial tables

- **EuroFIR FoodEXplorer** searches 40 national databases at once, for members.
- **Souci-Fachmann-Kraut** (8th ed. 2016; `sfk.online`) publishes about 800 foods and 260 constituents with means **and ranges**, in German, English and French. Ranges are what entry cards need, but it is a commercial product.

## See Also

- [The food data landscape](food-data-landscape.md)
- [Licensing food data for an MIT atlas](../food-atlas-project/mit-licensing-of-food-data.md)
- [Crop species and variety registers](crop-species-and-variety-registers.md)
