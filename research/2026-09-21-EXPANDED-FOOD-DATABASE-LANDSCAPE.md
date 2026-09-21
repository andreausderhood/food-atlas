# Expanded Food Database Landscape & Gap-Filling Strategy

**Date:** 2026-09-21  
**Author:** Food Atlas Research & Antigravity  
**Context:** Evaluation of open datasets, public domain resources, and open-content databases to systematically close the 13 rows of the Food Atlas coverage table under the revised open-attribution contract.

---

## 1. Executive Summary & The New Open Attribution Framework

Under our updated model, Food Atlas aims to maximize scientific completeness and open accessibility:
- **No artificial omission of useful data:** Useful open-access databases can be integrated provided every value carries strict provenance (`src`, `ref`, `license`, `attribution`, `url`).
- **Four Clear License Classes:**
  1. **`public_domain`**: Completely unencumbered (CC0, US Federal Government data like USDA WEP & FDC). Free for all downstream uses without condition.
  2. **`open_license`**: Standard open licenses (CC-BY 4.0, Apache-2.0, Etalab 2.0). Reusable and redistributable with attribution.
  3. **`open_content`**: Freely accessible, non-profit or institutional knowledge bases (FPI, FAO, Mansfeld). Fully usable and citable with origin back-links.
  4. **`restricted`**: Proprietary databases requiring individual citation or separate adapters.
- **Dual Export Capability:** Downstream users can filter `WHERE license_class = 'public_domain'` for a 100% pure Public Domain export, or use the complete open knowledge graph.

---

## 2. Gap-Filling Matrix: The 13 Coverage Table Rows

| # | Coverage Table Row | Current State (W0) | Primary Missing Data Points | Top Candidate Databases to Fill Gaps | License Class |
|:-:|:---|---:|:---|:---|:---|
| 1 | **Species identity** | 100% (26,591) | Parent chains, synonyms, taxonomic authority IDs | **USDA GRIN / WEP**, **Kew POWO / WCVP**, **NCBI Taxonomy**, **GBIF Backbone** | `public_domain` & `open_license` |
| 2 | **Common names** | 55.8% (1,171 unsearched) | Vernacular names in DE, EN, FR, ES, IT, indigenous names | **GBIF Vernacular Names** (CC0), **Wikidata** (CC0), **FPI / EPD**, **USDA GRIN** | `public_domain` & `open_content` |
| 3 | **Food hierarchy** | 0% (95,783 products) | Product $\rightarrow$ species mapping, culinary vs botanical parts | **FoodOn Ontology** (CC-BY), **USDA FDC Food Categorization**, **LanguaL** | `open_license` & `public_domain` |
| 4 | **Nutrients** | 2 species (Malus, Brassica) | Analytical & compilation values for thousands of species | **USDA FDC** (CC0), **German BLS 4.0** (CC-BY), **French Ciqual** (Open Licence), **Swiss FCDB v7.1** (Open Gov), **FAO Africa 1968 / WAFCT 2019**, **FAO BioFoodComp** | `public_domain`, `open_license`, `open_content` |
| 5 | **Molecules (ChEBI/PubChem)** | 2 species | Secondary metabolites, polyphenols, volatiles, carotenoids | **FoodAtlas v4.11** (Apache-2.0), **PubChem** (Public Domain), **USDA Flavonoid/Isoflavone DB** (Public Domain), **Phenol-Explorer 3.0**, **PhytoHub** | `public_domain`, `open_license`, `open_content` |
| 6 | **Bioactivity / health** | 0% (26,591 unsearched) | In-vitro assays, antioxidant capacity (FRAP), pathway targets | **ChEMBL 34** (CC-BY-SA), **Carlsen et al. 2010 FRAP** (Open Access), **FoodAtlas literature triples** (PMC) | `open_license` |
| 7 | **Seasonality** | 2 species | Monthly harvest, storage & fresh availability windows | **seasoncalendar DB / BZfE** (DE), **USDA Agricultural Marketing Service (AMS)** seasonal charts (US), regional consumer calendars | `open_content` & `public_domain` |
| 8 | **Distribution / geography** | 94.0% text (1,590 unsearched) | Native range vs introduced range, ISO-3166 country codes | **Khoury et al. 2016** (CC0), **Kew POWO / WCVP TDWG** (CC-BY), **FPI / EPD** (parsed to ISO-3166), **CROPGRIDS / SPAM 2020** | `public_domain`, `open_license`, `open_content` |
| 9 | **Growing / agronomy** | 0% (26,591 unsearched) | Temperature min/opt/max, precipitation, soil pH, elevation, hardiness | **FAO ECOCROP** (2,500+ species), **FPI / EPD grow data**, **USDA Plant Hardiness Zones** | `open_content` & `public_domain` |
| 10 | **Edible parts** | 87.9% text, 6.1% empty | Controlled botanical parts (fruit, seed, leaf, tuber, flower, stem) | **FPI / EPD** (normalized to `foods.PARTS`), **Mansfeld**, **Kew Useful Plants Checklist** | `open_content` & `open_license` |
| 11 | **Varieties / cultivars** | 0% (26,591 unsearched) | Named cultivars, landraces, accession IDs, historical apple/cabbage varieties | **Mansfeld's World Database** (6,100 species), **USDA GRIN-Global Accessions**, **FAO/INFOODS BioFoodComp**, **VIVC** (grape cultivars) | `open_content` & `public_domain` |
| 12 | **Photos** | 0% (33 tombstones) | Authentic, attributed botanical plates and high-res specimen photos | **USDA Pomological Watercolors** (7,497 cultivar plates, Public Domain), **Biodiversity Heritage Library (BHL)** (CC0 / Public Domain), **Pl@ntNet / GBIF** (CC-BY) | `public_domain` & `open_license` |
| 13 | **Evidence chain** | 0% | SHA256 audit hashes, DOI verification, cross-database entity links | **Crossref API**, **NCBI PubMed / PMC**, **Sciverse cache** | `public_domain` & `open_license` |

---

## 3. Deep-Dive on Key Additional Databases to Onboard

### A. Core Public Domain Datasets (Zero Legal Friction)

#### 1. USDA World Economic Plants (WEP) & GRIN-Global
- **URL:** `https://npgsweb.ars-grin.gov/gringlobal/taxon/taxonomysearch`
- **License:** Public Domain (US Federal Government work)
- **Scope:** 12,000+ vascular plant species with economic uses (food, forage, timber, medicine).
- **Attributes:** Botanical nomenclature, recognized synonyms, family/genus hierarchy, vernacular names in multiple languages, economic impact, geographical distribution, and germplasm accession IDs.
- **Role in Food Atlas:** Acts as the primary public domain taxonomic and variety backbone alongside NCBI Taxonomy.

#### 2. USDA Pomological Watercolors Collection
- **URL:** `https://usdawatercolors.nal.usda.gov/`
- **License:** Public Domain (U.S. National Agricultural Library)
- **Scope:** 7,497 watercolor paintings created by USDA artists between 1886 and 1942.
- **Attributes:** 3,807 apple paintings, 670 peach, 611 grape, 563 pear, 335 plum, plus berries and nuts. Each watercolor depicts a specific cultivar with exact harvest date, grower, and locality.
- **Role in Food Atlas:** Replaces missing cultivar imagery with gorgeous, scientifically accurate historical artwork.

#### 3. French ANSES Ciqual Food Composition Table
- **URL:** `https://ciqual.anses.fr/`
- **License:** Open Licence 2.0 (Etalab) — completely compatible with commercial reuse and open redistribution.
- **Scope:** 3,200+ foods, 60+ nutritional components, including detailed fatty acid profiles and cooking/preparation variations.
- **Role in Food Atlas:** Significantly expands European food items and regional preparations beyond BLS 4.0.

#### 4. Swiss Food Composition Database (v7.1, 2026)
- **URL:** `https://naehrwertdaten.ch/`
- **License:** Swiss Federal Open Government Data (FSVO) / Free commercial and non-commercial reuse with attribution.
- **Scope:** 1,200+ foods with quad-lingual naming (German, French, Italian, English).
- **Role in Food Atlas:** Provides high-precision Swiss food values, brand-neutral basic foods, and multilingual aliases.

---

### B. High-Value Open Content & Research Datasets

#### 5. Food Plants International (FPI) / EPD
- **Publisher:** Food Plants International (Bruce French / Non-Profit)
- **License:** Free to access / Open Content (Non-commercial & educational use, citation required)
- **Scope:** 33,000+ edible plant species worldwide.
- **Attributes:** Edible plant parts, distribution by country, climate & growing requirements (temperature, altitude, rainfall), and nutritional highlights.
- **Role in Food Atlas:** Provides the essential baseline facts for tropical, underutilized, and orphan crops that national tables ignore. Every data point links back to the FPI plant profile.

#### 6. FAO/INFOODS BioFoodComp (Biodiversity Database)
- **Publisher:** Food and Agriculture Organization of the United Nations (FAO)
- **License:** FAO Open Terms / Citation with attribution
- **Scope:** Analytical nutrition composition specifically at cultivar, breed, and wild-harvest level (e.g., specific apple cultivars, traditional grain varieties).
- **Role in Food Atlas:** Directly fills the cultivar-level nutrition gap (Rule 6) where national tables only publish generic species averages.

#### 7. FAO ECOCROP Database
- **Publisher:** FAO Land and Water Division
- **License:** FAO Data Terms (Free scientific reuse with citation)
- **Scope:** 2,568 plant species with systematic agro-ecological parameters:
  - Temperature: Absolute minimum, optimal min, optimal max, absolute maximum.
  - Rainfall: Annual precipitation ranges.
  - Soil: pH ranges, depth, drainage, salinity tolerance.
  - Photoperiod and altitude limits.
- **Role in Food Atlas:** Closes the `growing` row of the coverage table deterministically for thousands of species.

#### 8. Biodiversity Heritage Library (BHL) Plates
- **URL:** `https://www.biodiversitylibrary.org/`
- **License:** Public Domain / CC0 (for historical pre-1928 botanical plates)
- **API Key:** Configured in `.env` (`BHL_API_KEY`)
- **Scope:** Millions of digitized high-resolution botanical plates from classical works (Curtis's Botanical Magazine, Flora Londinensis, Köhler's Medizinal-Pflanzen).
- **Role in Food Atlas:** Provides authentic species-level botanical illustrations with verifiable page-level BHL URLs. Dynamically queried via BHL API `NameSearch` and `GetItemPages` without needing bulk image downloads.

#### 9. USDA Flavonoid & Isoflavone Databases
- **Publisher:** USDA Agricultural Research Service
- **License:** Public Domain
- **Scope:** Flavonoid content (flavonols, flavones, flavanones, flavan-3-ols, anthocyanins) and isoflavone values for ~500 food items based on peer-reviewed HPLC analyses.
- **Role in Food Atlas:** Fills concentration claims for key bioactive phytochemicals (quercetin, kaempferol, catechins) with Tier-1 analytical derivations.

---

## 4. Traditional Chinese Medicine (TCM), Ethnomedicine & Indigenous Knowledge

Food species often blur the boundary between culinary sustenance and traditional medicine (*"Food as Medicine"*). The following resources provide open, structured knowledge for traditional applications:

| Database | Scope | Coverage & Key Features | License & Accessibility |
|:---|:---|:---|:---|
| **Dr. Duke's Phytochemical & Ethnobotanical Databases** (USDA ARS) | Global ethnobotany & traditional uses | 80,000+ records linking plants to folk medicinal uses, phytochemical constituents, and ethnobotanical reports worldwide. | **Public Domain (US Govt)** · Bulk CSV / Parquet (~50 MB) |
| **HERB (High-throughput Experiment- & Reference-guided TCM)** | Traditional Chinese Medicine | 1,293 Chinese medicinal herbs, 4,964 ingredients, 19,418 target genes. Published in *Nucleic Acids Research* (2021). | Open Academic Access (`http://herb.ac.cn/`) |
| **TCMSP (TCM Systems Pharmacology)** | Chinese Pharmacopoeia | 499 herbs, 29,384 chemicals, with oral bioavailability (OB) and drug-likeness (DL) properties. | Open Academic Access |
| **CINE Traditional Food Systems** (McGill University) | Indigenous peoples' nutrition | Extensive nutrient compositions and cultural uses of traditional plant and animal foods from Arctic, First Nations, and global indigenous communities. | Academic Citation / Open Content |
| **PROTA / PROSEA** | Tropical Africa & Southeast Asia | Detailed ethnobotanical monographs, traditional recipes, and medicinal preparation methods for thousands of indigenous species. | Open Access / CC BY-NC-SA (factual citations under `open_content`) |
| **WHO Monographs on Selected Medicinal Plants** | Global pharmacopeial standards | 4 volumes published by WHO evaluating traditional uses alongside experimental pharmacology and clinical safety data. | WHO Open Access (PDFs / Structured text) |

*Rule 14 (Community-Gate) applies:* Traditional knowledge claims must always credit the community of origin and cite the ethnobotanical record without synthetic Western extrapolation.

---

## 5. Storage & Download Footprint (How many GB?)

Integrating these databases does **NOT** require downloading massive terabytes of raw data. The footprint breaks down as follows:

| Component | Nature of Data | Estimated Download / Disk Size | Handling Strategy |
|:---|:---|---:|:---|
| **Tabular & Relational Data**<br>(FDC, BLS, Ciqual, Swiss FCDB, ECOCROP, WEP, GBIF names) | CSV, JSON, DuckDB, Parquet | **~1.2 GB** | Bulk downloaded once into `data/raw/` and indexed into `data/build/unified.duckdb`. |
| **FPI / EPD Snapshot** | Text / ZIM dump | **~250 MB** | Already locally present in `data/research/scope/`. |
| **Dr. Duke's Ethnobotanical DB** | Parquet / CSV | **~50 MB** | Lightweight bulk download. |
| **USDA Pomological Watercolors** | Metadata + 7,497 JPEG plates | **~2.5 GB** *(optional)* | Metadata is 5 MB. Images can be cached locally (~2.5 GB) or served directly via USDA NAL image URLs (0 GB local). |
| **BHL (Biodiversity Heritage Library)** | 60M+ pages | **0 GB local** *(API-driven)* | We do **not** download the BHL repository. The BHL API (`BHL_API_KEY`) queries pages dynamically and links directly to high-res BHL plate URLs. |
| **Total Disk Requirement** | Core Unified Dataset | **~1.5 to 4.0 GB** | Easily fits on any standard workstation with zero storage bottlenecks. |

---

## 6. Immediate Roadmap Recommendations

1. **Wave 1 (Species Context):**
   - Ingest **EPD / FPI** (Country codes to ISO-3166, parts to `foods.PARTS`, growing parameters).
   - Ingest **FAO ECOCROP** (Agronomic limits).
   - Ingest **Kew WCVP / POWO** (Native/introduced ranges).
   - Wire **GBIF Vernacular Names** for the remaining 1,171 unsearched species names.
   - Wire **BHL API** for dynamic plate queries on species pages.

2. **Wave 2 (National Public Domain & Open Nutrition):**
   - **FDC Foundation & SR Legacy** (8,262 products).
   - **French Ciqual** + **Swiss FCDB v7.1** (expands European food items).
   - Seed identity edges connecting products to pool species.

3. **Wave 3 (German Deep Nutrition):**
   - **BLS 4.0** (7,140 foods $\times$ 138 nutrients).

4. **Wave 4 (Phytochemistry, Ethnobotany & Deep Composition):**
   - **FoodAtlas v4.11** (193k compounds) + **USDA Flavonoids** (Public Domain analytical concentrations).
   - **Dr. Duke's Ethnobotanical DB** (Traditional & folk uses).
   - Link via InChIKey / ChEBI / PubChem.

5. **Wave 5 (Cultivars, Biodiversity & Visuals):**
   - **FAO BioFoodComp** + **Mansfeld World Database**.
   - **USDA Pomological Watercolors** (curated fruit cultivar plates) + **BHL botanical plates**.
