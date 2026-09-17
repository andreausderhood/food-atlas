# Existing Food Atlases, Lexicons, Books and Datasets
## Deep research for the Food Atlas

**Date:** 2026-09-17
**Question:** What are the best and most complete food species atlases and lexicons with nutrition facts and related data? Which books, publications and datasets should the Food Atlas build on?
**See also:** `REVIEW_FOOD_SPECIES_ATLAS_RESOURCES.md`, a review of the German research synthesis with license corrections.
**Method:**
- Web checks of each source's own pages, publisher pages and papers.
- A local profile of the FoodAtlas v4.11 bundle (see `product.md` §6).
- A full read of Gupta et al. 2026 (`Resources/`).

**Legend**
- ✓ = figures checked on the web on 2026-09-17.
- ◦ = from prior knowledge, not re-checked in this pass. Verify before citing.

---

## 0. Bottom line

**No complete food atlas exists.** Every resource is deep in one or two layers and silent on the others. The closest things to "the whole thing" are:

| Question | Best answer today |
| :--- | :--- |
| Most complete **crop species lexicon** | **Mansfeld's World Database / Encyclopedia of Agricultural and Horticultural Crops** (IPK Gatersleben): 6,100 cultivated species ✓ |
| Most complete **economic plant list** | **World Economic Plants: A Standard Reference**, 2nd ed. (Wiersema & León, CRC 2013): 12,000+ taxa ✓ |
| Most complete **edible and useful plant checklist** | **Kew World Checklist of Useful Plant Species** (2020): 40,292 species ✓. Ulian et al. (2020) count about 7,039 edible plant species ✓ |
| **Book closest to the Food Atlas idea** (per species: taxonomy, origin, agroecology, edible parts, botany, nutrition, phytochemicals) | **T.K. Lim, *Edible Medicinal and Non-Medicinal Plants***, Springer, 12 volumes, 1,000+ plants ✓ |
| Book with the **most varieties** | **Facciola, *Cornucopia II*** (1998): 3,000 species, 7,000 varieties ✓ |
| Best **illustrated** species guide with nutrition | **van Wyk, *Food Plants of the World***, 2nd ed. 2019: about 380 plants in depth, 800+ in a checklist, 1,000+ photos ✓ |
| **Variety-level nutrition** | **FAO/INFOODS BioFoodComp**: analytical data at cultivar/breed level (v3.0: 7,953 entries ✓; v4.0 2017 ✓) and **Simmonds & Preedy, *Nutritional Composition of Fruit Cultivars*** (2016) ✓ |
| Most complete **open nutrition tables** | **USDA FoodData Central** (CC0) ✓ and **German BLS 4.0**: 7,140 foods, 138 nutrients, CC BY 4.0, free since 16 Dec 2025 ✓ |
| Most complete **food chemistry** | **FoodAtlas** (193,236 chemicals; already downloaded) and **FooDB** (70,926 compounds ✓) |
| Most standardized **deep composition** | **Periodic Table of Food Initiative (PTFI)**: standardized multi-omics, 500 foods on the AHA platform ✓, MarkerLab viewer ✓ |
| Most complete **culinary atlas product** | **TasteAtlas**: 12,272 dishes, 7,744 local ingredients ✓. It is cultural, not scientific, and shows no sources |

**What this means for us:** the Food Atlas is not competing with any one of these. It is the first resource to join them at variety level with provenance on every value. §6 lists which sources to take first.

---

## 1. Benchmarks: the closest existing products

| Product | What it does well | What it lacks, and so where we win |
| :--- | :--- | :--- |
| **FoodAtlas** (UC Davis) ✓ | Food → chemical → disease graph; 10,270 foods; weekly updates; Apache-2.0 bundle | Only 2.4% of evidence rows carry amounts; no basis; no season, origin, growing, sensory or images; mixed levels. See `product.md` §6 |
| **FooDB** ✓ | 70,926 compounds across about 1,000 raw foods; compound pages | Chemistry only. License terms need checking |
| **PTFI** ✓ | Standardized metabolomics, lipidomics and more; MarkerLab visualizer; raw data via the AHA Precision Medicine Platform; spectra via GNPS | Raw data is non-commercial (CC BY-NC) and needs an access request. No lexicon layer |
| **TasteAtlas** ✓ | A world map of 12,272 dishes and 7,744 ingredients; strong visual and cultural storytelling | No nutrition, chemistry, taxonomy or sources. **The UX benchmark to beat** |
| **Mansfeld DB** ✓ | 6,100 crop species with taxonomy, uses and distribution | Plants only, no nutrition, dated interface |
| **Plants For A Future** ✓ | 8,000+ useful plants with edibility ratings | The database is under a paid license (home, commercial or student edition). Temperate bias |
| **Slow Food Ark of Taste** ✓ | 5,000+ endangered foods from 120+ countries: heritage varieties and breeds | Stories, not data. The ideal seed for our **Funnel** (underused foods) |
| **Kew POWO / useful plants** ✓◦ | The authoritative plant taxonomy and native ranges ◦; the useful-plant checklist ✓ | Not food-centred. No nutrition |

---

## 2. Books: the reference shelf

### 2.1 Species encyclopedias and lexicons

| Book | Scope | Why it matters |
| :--- | :--- | :--- |
| **Hanelt (ed.), *Mansfeld's Encyclopedia of Agricultural and Horticultural Crops*** (Springer, 2001, 6 vols) ✓◦ | 6,100 cultivated species (online DB ✓) | Most complete cultivated-species lexicon; backbone for the Organisms register |
| **Wiersema & León, *World Economic Plants: A Standard Reference*, 2nd ed.** (CRC, 2013) ✓ | 12,000+ economically important vascular plants | Standard names and uses; basis of the USDA GRIN economic-plant data ◦ |
| **T.K. Lim, *Edible Medicinal and Non-Medicinal Plants*** (Springer, 2012–2016, vols 1–12) ✓ | 1,000+ plants: fruits, vegetables, herbs, pulses, cereals, spices, roots, beverages, mushrooms, oils | **Closest to our entry format.** Per species: taxonomy, names, origin/distribution, agroecology, edible parts, botany, nutritive and medicinal properties |
| **Facciola, *Cornucopia II: A Source Book of Edible Plants*** (Kampong, 1998) ✓ | 3,000 species, 7,000 varieties, usage by edible part | The widest species-to-variety book |
| **van Wyk, *Food Plants of the World*, 2nd ed.** (CABI / CSIRO, 2019) ✓ | About 380 plants in depth plus 800+ in a checklist; origin, cultivation, uses, nutrition; 1,000+ photos | **Best visual model** for our editorial layer |
| **Janick & Paull (eds), *The Encyclopedia of Fruit and Nuts*** (CABI, 2008) ✓ | Temperate and tropical fruit and nut species, ordered by family; 100+ experts | Botany, origins, breeding and cultivars for fruit |
| **Sturtevant's *Edible Plants of the World*** (ed. Hedrick, 1919) ◦ | Historical global list | Public domain, so it can be quoted freely for historical notes |
| **PROSEA / PROTA handbooks** ◦ | Plant resources of South-East Asia and tropical Africa | Tropical and underused species. PROSEA feeds the Kew checklist ✓ |

### 2.2 Composition tables in book form

| Book | Scope | Notes |
| :--- | :--- | :--- |
| **Souci, Fachmann & Kraut, *Food Composition and Nutrition Tables*, 8th ed.** (2016) ✓ | About 800 foods, 260 constituents, with means **and ranges** ✓ | German/English/French; online at sfk.online ✓; commercial product. Ranges are what our entries need |
| **McCance and Widdowson's *The Composition of Foods*** / CoFID 2021 ✓ | The UK reference | The dataset is free from gov.uk ✓. License is the UK Open Government Licence ◦ |
| **Simmonds & Preedy (eds), *Nutritional Composition of Fruit Cultivars*** (Academic Press, 2016, 774 pp) ✓ | Botany plus composition of traditional and modern cultivars, by fruit | **The only book-length source of cultivar-level nutrition** |

### 2.3 Culinary, cultural and science-of-food

| Book | Why |
| :--- | :--- |
| **Davidson & Jaine, *The Oxford Companion to Food*, 3rd ed.** (OUP, 2014): 2,650 A–Z entries ✓ | The editorial-layer reference: history, names, cultural use |
| **Kiple & Ornelas (eds), *The Cambridge World History of Food*** (CUP, 2000) ◦ | Origins and history per food, with a dictionary of plant foods ◦ |
| **Harold McGee, *On Food and Cooking*** (2004) ◦ | Texture, colour and flavour explained per ingredient, a model for the sensory layer |
| **Belitz, Grosch & Schieberle, *Food Chemistry*, 4th ed.** (Springer, 2009) ◦ | Molecules per food group, including aroma compounds (German original *Lehrbuch der Lebensmittelchemie*) |
| **Page & Dornenburg, *The Flavor Bible*** (2008) ◦; **Briscione, *The Flavor Matrix*** (2018) ◦ | Culinary flavour vocabulary and pairings |

### 2.4 Varieties, breeds, fungi, insects, microbes

| Book / report | Scope |
| :--- | :--- |
| **Morgan & Richards, *The New Book of Apples*** (2002) ◦ | About 2,000 apple varieties from the UK National Fruit Collection ◦ |
| **Robinson, Harding & Vouillamoz, *Wine Grapes*** (2012) ◦ | 1,368 grape varieties with parentage ◦ |
| **Boa, *Wild Edible Fungi: A Global Overview*** (FAO Non-Wood Forest Products 17, 2004) ✓ | 2,166 edible species, 1,069 used as food ✓ |
| **van Huis et al., *Edible Insects*** (FAO, 2013) ◦ | Insects as food and feed |
| **IDF Bulletin 514/2022, *Inventory of Microbial Food Cultures with Safety Demonstration*** ✓ | The reference list of food microbes, extended beyond dairy in 2022 ✓; for sale from IDF |
| **Batt & Tortorello (eds), *Encyclopedia of Food Microbiology*, 2nd ed.** (2014) ◦; **Katz, *The Art of Fermentation*** (2012) ◦ | Microbe and process encyclopedias |

### 2.5 Atlas design references

**◦ Johnson & Robinson, *The World Atlas of Wine*** (8th ed. 2019) and **Millstone & Lang, *The Atlas of Food*** (2nd ed. 2008) show how maps and data carry a food story.

---

## 3. Datasets by Food Atlas layer

### L1 · Species and taxonomy → Organisms register

| Dataset | Content | License / access |
| :--- | :--- | :--- |
| **World Checklist of Useful Plant Species** (Kew, 2020) ✓ | 40,292 species with use categories and crop-wild-relative flags | Open download (KNB / Kew) ✓; license not yet read |
| **Pironon et al. 2024 datasets** ✓ | 35,687 utilised species, occurrences and 10-arc-minute distribution models | Zenodo 10345634 ✓ |
| **Mansfeld's World Database** ✓ | 6,100 crop species | Free online (IPK) ✓ |
| **WCVP / Plants of the World Online** (Kew) ◦ | Accepted names and native ranges (TDWG regions) for all vascular plants | Open ◦ (verify license) |
| **GRIN-Global Taxonomy** (USDA) ◦ | Economic plants, common names, uses | Public ◦ |
| **GBIF Backbone + occurrences**, **NCBI Taxonomy**, **Wikidata** ◦ | Join keys and occurrence points | GBIF records carry CC0, CC BY or CC BY-NC per dataset; Wikidata is CC0 |
| **FishBase** ✓ / **SeaLifeBase** ✓ | 36,500+ fish species; about 72,000 other aquatic species | **CC BY-NC 4.0** ✓ |
| **Wild edible fungi** (Boa 2004) ✓ | 2,166 edible fungi | FAO report |
| **Edible insects**: Jongema list (WUR) ✓; *Global atlas of edible insects* (2024) ✓ | 2,111 species; 2,205 species in 128 countries | Open list / open-access paper |
| **FAO DAD-IS** ✓ | Livestock breeds by country with risk status | Free. Total breed count not confirmed |

### L2 · Varieties, cultivars, breeds → Foods register (variety level)

| Dataset | Content | License / access |
| :--- | :--- | :--- |
| **Genesys PGR** (Crop Trust) ✓ | 4,464,904 genebank accessions (Dec 2025) with passport data | Free; data terms to check |
| **EU Plant Variety Database / Common Catalogues** ✓ | 23,000+ agricultural and 21,000+ vegetable varieties marketable in the EU | Free search; information only ✓ |
| **CPVO Variety Finder**, **UPOV PLUTO** ✓ | Protected and registered varieties worldwide | Free search (PLUTO needs registration ◦) |
| **VIVC** (Vitis International Variety Catalogue) ✓ | About 23,000 grape cultivars, breeding lines and species, with genetic profiles | Free online |
| **UK National Fruit Collection** ✓ | 2,040+ apple varieties; about 3,500 fruit cultivars in total; searchable with photos | Free online |
| **FAO/INFOODS BioFoodComp** ✓ | **Analytical nutrients at cultivar level** (v2.0: 6,411 foods, 451 components; v3.0: 7,953 entries) | FAO, free download ✓ |
| **Slow Food Ark of Taste** ✓ | 5,000+ heritage foods | Online catalogue |
| **FoodAtlas** (have) | Few varieties (apple 13 cultivars) | Apache-2.0 |

### L3 · Nutrition → Foods register (nutrition claims)

| Dataset | Content | License / access |
| :--- | :--- | :--- |
| **USDA FoodData Central** ✓ | Foundation Foods (with sampling, genotype and production metadata ✓), SR Legacy (final release 2018 ✓), FNDDS, Branded | **CC0** ✓, API available |
| **BLS 4.0** (Max Rubner-Institut, DE) ✓ | 7,140 foods, 138 nutrients | **CC BY 4.0**, free Excel download since 16 Dec 2025 ✓ |
| **Ciqual 2025** (ANSES, FR) ✓ | 3,484 foods, 74 constituents | Open licence, free ✓ |
| **Swiss Food Composition Database** (FSVO) ✓ | V7.1: 1,246 foods | Free, **commercial use allowed with attribution** ✓ |
| **CoFID 2021** (UK) ✓ | The UK reference dataset | Free download ✓ |
| **Souci-Fachmann-Kraut online** ✓ | About 800 foods, 260 constituents, with ranges | Commercial |
| **EuroFIR FoodEXplorer** ✓ | 40 national databases searchable at once | Membership |
| **FAO/INFOODS regional tables** ✓ | Africa, Asia and Latin America tables, plus special databases (fish, pulses, phytate) | Free |
| **Open Food Facts** ◦ | Packaged products | ODbL ◦. Out of scope for species, useful for forms |

### L4 · Molecules and bioactivity → Molecules register

| Dataset | Content | License / access |
| :--- | :--- | :--- |
| **FoodAtlas v4.11** | 193,236 chemicals; 108,047 food–chemical links; chemical–disease correlations | **Have it**, Apache-2.0 |
| **FooDB** ✓ | 70,926 compounds | Free; license to verify |
| **Phenol-Explorer** ✓ | Polyphenol content of 459 foods, including processing effects (v3.x) | Free online |
| **PTFI** ✓ | Standardized metabolomics and more; 500 foods on the AHA platform | MarkerLab viewer; raw data **CC BY-NC** by request; spectra via GNPS |
| **Gupta et al. 2026 + repo** | Bioactivity evidence for 322 foods in 11 categories; tiered identifications; FRAP values for 500 foods | CC BY 4.0 (paper); repo code MIT |
| **Dr. Duke's Phytochemical and Ethnobotanical Databases** (USDA) ✓ | Plant chemicals, activities, ethnobotany | Free; CSV on Ag Data Commons ✓ |
| **Carlsen et al. 2010** (Nutr J 9:3) | Antioxidant content of 3,100+ foods | Open-access paper |
| **USDA special-interest databases** (flavonoids, proanthocyanidins, isoflavones) ◦; **eBASIS** (EuroFIR) ◦ | Bioactive compound content | USDA public ◦; eBASIS membership ◦ |

### L5 · Flavour and sensory → Sensory claims

| Dataset | Content | Notes |
| :--- | :--- | :--- |
| **FlavorDB2** ✓ | 25,595 flavour molecules; 2,254 linked to 936 natural ingredients | IIIT-Delhi; check terms |
| **FoodAtlas flavour descriptors** | 1,764 chemicals with taste words | Have it |
| **Ahn et al. 2011, *Flavor network and the principles of food pairing*** ◦ | Ingredient–compound network | Open paper |
| **Colour and texture** | **No dataset exists** | Curate, or derive colour from images; texture vocabulary after Szczesniak's texture profile ◦ |

### L6 · Origin and domestication → Organisms register (origin claims)

| Dataset | Content | Access |
| :--- | :--- | :--- |
| **Khoury et al. 2016** ✓ | Primary regions of diversity for 151 crop commodities, linked to every country | Dryad doi:10.5061/dryad.s08t2 ✓; interactive at Alliance Bioversity-CIAT ✓ |
| **Meyer, DuVal & Jensen 2012** ✓ | 203 food crops: domestication centre, wild ancestors, dates, traits | Supplementary matrix ✓ |

### L7 · Growing requirements → Organisms register (growing claims)

| Dataset | Content | Access |
| :--- | :--- | :--- |
| **FAO ECOCROP** ✓ | 2,000+ species: temperature, rainfall, soil pH, light, Köppen zone, photoperiod, altitude | Free, inside GAEZ v4 ✓ |
| **GAEZ v4** (FAO / IIASA 2021) ✓ | Land suitability and attainable yields | Free portal ✓ |

### L8 · Where it is grown → World map

| Dataset | Content | Access |
| :--- | :--- | :--- |
| **FAOSTAT** ◦ | Production by country and year | Free; license to verify |
| **CROPGRIDS** (Tang et al. 2024) ✓ | 173 crops, about 2020, 0.05° grid | figshare 22491997 ✓; license to verify |
| **SPAM 2020** (IFPRI / WRI) ✓ | 46 crops, 5 arc-minute grid, by production system; v2r2 released May 2026 ✓ | Free ✓ |
| **EarthStat / Monfreda et al. 2008** ◦ | 175 crops, about 2000 | Free ◦ |

### L9 · Season → Season calendar

| Dataset | Content | Access |
| :--- | :--- | :--- |
| **Sacks et al. 2010** ✓ | Planting and harvest dates for 19 major crops, gridded | Free |
| **WorldCereal crop calendars** ✓ | Maize and wheat | Free |
| **BZfE Saisonkalender** (DE) ✓ | About 75 fruit and vegetable types, month by month (Germany) | Free app and A3 PDF ✓ |
| **Consumer seasonality elsewhere** | **No global dataset** | Curate per country from national calendars (e.g. Verbraucherzentrale ✓) |

### L10 · Microbes → Microbes register

| Dataset | Content | Access |
| :--- | :--- | :--- |
| **IDF Bulletin 514/2022** ✓ | Inventory of food cultures with safety demonstration | Purchase |
| **EFSA QPS list** ◦ | Microbes with Qualified Presumption of Safety | Free |
| **cFMD** (curatedFoodMetagenomicData) ✓ | 3,444 food metagenomes; 14,904 genomes; 1,153 prokaryotic and 110 eukaryotic species-level bins | Open (GitHub SegataLab/cFMD) ✓ |

### L11 · Vocabularies and ontologies → Join keys

These are all from prior knowledge ◦:
- **FoodOn**: food products, already used by FoodAtlas.
- **LanguaL**: food description facets.
- **EFSA FoodEx2**: food classification.
- **AGROVOC**: FAO multilingual thesaurus, including German.
- **Plant Ontology**: plant parts, which gives the atlas its *part* level.
- **CDNO** and **ChEBI**: nutrients and chemicals.

### L12 · Images → Editorial layer

| Dataset | Content | License |
| :--- | :--- | :--- |
| **USDA Pomological Watercolor Collection** ✓ | 7,584 paintings (1886–1942), 3,807 of them apples, by variety | **Public domain** ✓ |
| **Fruits-360** ✓ | 182,945 images, 260 classes, varieties as separate classes (v2025.05) | Check license |
| **Wikimedia Commons**, **Biodiversity Heritage Library**, **iNaturalist** ◦ | Photos and botanical plates | Licensed per file |

---

## 4. Key publications (reading list)

1. Gupta, Gunning, Ahmed & Tagkopoulos (2026). From metabolomics dark matter to bioactivity. *npj Sci Food*. doi:10.1038/s41538-026-01066-1 — *have*
2. Li et al. (2026). A unified knowledge graph linking foodomics to chemical-disease networks and flavor profiles (FoodAtlas). *npj Sci Food*. doi:10.1038/s41538-025-00680-9
3. Jarvis et al. (2024). Periodic Table of Food Initiative for generating biomolecular knowledge of edible biodiversity. *Nature Food* 5:189–193. doi:10.1038/s43016-024-00941-y ✓
4. Barabási, Menichetti & Loscalzo (2019). The unmapped chemical complexity of our diet. *Nature Food* 1:33–37
5. Ulian et al. (2020). Unlocking plant resources to support food security and promote sustainable agriculture. *Plants, People, Planet*. doi:10.1002/ppp3.10145 ✓
6. Diazgranados et al. (2020). *World Checklist of Useful Plant Species*. Royal Botanic Gardens, Kew ✓
7. Pironon et al. (2024). The global distribution of plants used by humans. *Science* 383:293–297. doi:10.1126/science.adg8028 ✓
8. Khoury et al. (2016). Origins of food crops connect countries worldwide. *Proc. R. Soc. B* 283:20160792 ✓
9. Meyer, DuVal & Jensen (2012). Patterns and processes in crop domestication… 203 global food crops. *New Phytologist* 196:29–48. doi:10.1111/j.1469-8137.2012.04253.x ✓
10. Charrondière et al. (2013). FAO/INFOODS food composition database for biodiversity. *Food Chemistry* ✓
11. Rothwell et al. (2013). Phenol-Explorer 3.0. *Database* ✓
12. Goel et al. (2024). FlavorDB2: an updated database of flavor molecules. *J Food Sci*. doi:10.1111/1750-3841.17298 ✓
13. Carlino et al. (2024). Unexplored microbial diversity from 2,500 food metagenomes and links with the human microbiome. *Cell*. doi:10.1016/j.cell.2024.07.039 ✓
14. Sacks et al. (2010). Crop planting dates: an analysis of global patterns. *Global Ecol. Biogeogr.* doi:10.1111/j.1466-8238.2010.00551.x ✓
15. Tang et al. (2024). CROPGRIDS: a global geo-referenced dataset of 173 crops. *Scientific Data*. doi:10.1038/s41597-024-03247-7 ✓
16. Maul et al. (2015). Vitis International Variety Catalogue (VIVC). *BIO Web of Conferences* ✓
17. *The state of food composition databases: data attributes and FAIR data harmonization* (2025). *Frontiers in Nutrition*. doi:10.3389/fnut.2025.1552367 ✓. This is the current landscape review of nutrition databases.
18. *The global atlas of edible insects* (2024). Open access (PMC10904393) ✓
19. Gori et al. (2026). A comprehensive checklist of Mediterranean wild edible plants. *Plants, People, Planet*. doi:10.1002/ppp3.70137 ✓
20. Carlsen et al. (2010). The total antioxidant content of more than 3100 foods… *Nutrition Journal* 9:3
21. Dooley et al. (2018). FoodOn: a harmonized food ontology. *npj Sci Food* ◦
22. Lachat et al. (2018). Dietary species richness as a measure of food biodiversity and nutritional quality of diets. *PNAS* ◦

---

## 5. License map

**Decided 2026-09-17: the atlas is open source (MIT).** Anyone may reuse it commercially, so only the "Commercial" row below can **ship** with the atlas. Everything in "Off-limits" is adapter-only or link-out (see `product.md` §3 Licensing).
Also: the CTD terms prohibit commercial reproduction without permission (✓, via search result; the CTD site sits behind a CAPTCHA). In FoodAtlas v4.11, CTD rows alone back all 130,856 chemical–disease links. Those links are excluded; food–chemical links are unaffected.

| If the atlas is… | Safe to use | Off-limits or needs a deal |
| :--- | :--- | :--- |
| **Commercial / MIT-compatible (ships)** | USDA FDC (CC0) · BLS 4.0 (CC BY 4.0) · Ciqual (open licence) · Swiss FCDB (commercial use with attribution) · FoodAtlas bundle (Apache-2.0) · Pomological Watercolors (public domain) · Wikidata (CC0) · study text (CC BY 4.0) | FishBase / SeaLifeBase (CC BY-NC) · PTFI raw data (CC BY-NC) · PTFI-derived files in the Gupta repo · CTD-derived FoodAtlas rows · FoodAtlas API (non-commercial) · Open Food Facts (ODbL share-alike, keep separate) · GBIF records marked NC · PFAF (paid) · Souci-Fachmann-Kraut (commercial) · EuroFIR (membership) |
| ~~Non-commercial~~ | *Not applicable: the atlas is MIT.* | — |
| **Checked after the MIT decision** | FAOSTAT: CC BY 4.0 ✓ (ships) · FoodOn: CC BY 4.0 ✓ (ships) · FooDB: commercial use needs permission ✓ (adapter) · Phenol-Explorer: commercial use needs permission ✓ (adapter) · PROSEA: CC BY-NC-SA ✓ (adapter) · BioFoodComp: "© FAO", no open license shown ✓ (adapter until FAO confirms) | — |
| **Unverified; read before use** | FlavorDB2 · CROPGRIDS · Genesys · VIVC · ECOCROP · WCVP · Fruits-360 · Duke · CoFID · Kew useful-plants checklist · WAFCT 2019 · CINE · PROTA | — |

The unverified sources get a `license` field in `sources.yaml`, and the build refuses a source whose license is unread. This is the Victorinox rule, extended.

---

## 6. Recommendation: what to acquire, in order

### Tier A · Download next (free, open, highest value per effort)

| # | Source | Fills | Size / form |
| :-: | :--- | :--- | :--- |
| 1 | **USDA FoodData Central** (Foundation Foods + SR Legacy) | Tier-1 nutrition; some named cultivars | CSV bundle |
| 2 | **BLS 4.0** | German nutrition, 138 nutrients | Excel |
| 3 | ~~FAO/INFOODS BioFoodComp~~ → use as a **finding aid only** (no open license shown). Re-extract variety values from the open-access primary papers it cites, and consider asking FAO (D8) | Variety-level nutrition | Excel (local, not shipped) |
| 4 | **FRAP values from the original papers** (Carlsen et al. 2010, open access; Rico et al. 2021, open access), not the PTFI-derived repo files | Antioxidant layer | Supplementary tables |
| 5 | **Kew World Checklist of Useful Plant Species** + **WCVP** | Organisms register, native ranges | CSV |
| 6 | **Khoury 2016** + **Meyer 2012** supplements | Origin and domestication | CSV / XLS |
| 7 | **ECOCROP** | Growing requirements | Portal export |
| 8 | **CROPGRIDS** or **SPAM 2020** | World production map | GeoTIFF |
| 9 | **USDA Pomological Watercolors** (apple subset) | Variety images, public domain | Images |
| 10 | **cFMD** metadata | Microbes register | TSV |

**Downloads need your OK.** I will list file names and sizes before fetching anything.

### Tier B · Request or register

- **PTFI:** MarkerLab for reference browsing only. Its data cannot ship in an MIT atlas, so it is an optional adapter at most.
- **FoodAtlas API key:** not needed. The API is non-commercial, and we have the Apache-2.0 bundle.
- **UPOV PLUTO:** registration, for variety breadth.

### Tier C · Buy or borrow (the reference shelf)

1. T.K. Lim, *Edible Medicinal and Non-Medicinal Plants* (entry model; library or SpringerLink)
2. Simmonds & Preedy, *Nutritional Composition of Fruit Cultivars* (cultivar nutrition)
3. van Wyk, *Food Plants of the World*, 2nd ed. (editorial and visual model)
4. Facciola, *Cornucopia II* (variety breadth)
5. Souci-Fachmann-Kraut, 8th ed. (ranges; German reference)
6. *The Oxford Companion to Food* (editorial voice)
7. IDF Bulletin 514/2022 (microbe inventory)

### Gaps no source fills, so they become our own work

- **Consumer seasonality outside Germany:** curate from national calendars.
- **Colour and texture:** curate a controlled vocabulary; extract colour from images.
- **Variety-level nutrition beyond BioFoodComp and Simmonds & Preedy:** register as gaps. This is the strongest argument for eventual partnerships (genebanks, national fruit collections, PTFI).
