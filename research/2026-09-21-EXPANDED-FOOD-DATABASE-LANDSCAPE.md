# Expanded Food Database Landscape & Gap-Filling Strategy

**Date:** 2026-09-21  
**Author:** Food Atlas Research & Antigravity  
**Context:** Comprehensive evaluation of open datasets, public domain resources, alternative knowledge systems (TCM, Ayurveda, Indigenous, TEM), and extensible ingestion pipelines for books and databases under the revised open-attribution contract.

---

## 1. Executive Summary & The Open Attribution Framework

Under our updated model, Food Atlas maximizes scientific completeness, cultural respect, and open accessibility:
- **No artificial omission of useful data:** Useful open-access databases, authoritative botanical handbooks, and classical monographs can be integrated provided every value carries strict provenance (`src`, `ref`, `license`, `attribution`, `url`).
- **Four Clear License Classes:**
  1. **`public_domain`**: Completely unencumbered (CC0, US Federal Government data like USDA WEP, FDC, Dr. Duke's, Pomological Watercolors, historical pre-1928 monographs). Free for all downstream uses without condition. Forms the pure Public Domain export core.
  2. **`open_license`**: Standard open licenses (CC-BY 4.0, Apache-2.0, Etalab 2.0, UK OGL v3.0, Swiss FSVO Open Use). Reusable and redistributable with author attribution.
  3. **`open_content`**: Freely accessible, non-profit or institutional knowledge bases (FPI, FAO ECOCROP, BioFoodComp, Mansfeld, IMPPAT 2.0, HERB TCM, NAEB). Fully usable and citable with origin back-links. No bulk copying of proprietary creative prose.
  4. **`cite` / `restricted`**: Authoritative modern reference monographs (T.K. Lim, Sturtevant, Kunkel) or proprietary databases requiring individual citation (`curated: true`, `ref: "..."`).
- **Dual Export Capability:** Downstream users can filter `WHERE license_class = 'public_domain'` for a 100% pure Public Domain export, or leverage the complete open knowledge graph.

---

## 2. Gap-Filling Matrix: The 13 Coverage Table Rows

| # | Coverage Table Row | Current State (W0) | Primary Missing Data Points | Top Candidate Databases & Sources | License Class |
|:-:|:---|---:|:---|:---|:---|
| 1 | **Species identity** | 100% (26,591) | Parent chains, synonyms, taxonomic authority IDs | **USDA GRIN / WEP**, **Kew POWO / WCVP**, **NCBI Taxonomy**, **GBIF Backbone** | `public_domain` & `open_license` |
| 2 | **Common names** | 55.8% (1,171 unsearched) | Vernacular names in DE, EN, FR, ES, IT, indigenous & traditional names | **GBIF Vernacular Names** (CC0), **Wikidata** (CC0), **FPI / EPD**, **USDA GRIN**, **Mansfeld** | `public_domain` & `open_content` |
| 3 | **Food hierarchy** | 0% (95,783 products) | Product $\rightarrow$ species mapping, culinary vs botanical parts | **FoodOn Ontology** (CC-BY), **USDA FDC Food Categorization**, **LanguaL** | `open_license` & `public_domain` |
| 4 | **Nutrients** | 2 species (Malus, Brassica) | Analytical & compilation values for thousands of species & cultivars | **USDA FDC** (CC0), **German BLS 4.0** (CC-BY), **French Ciqual** (Etalab 2.0), **Swiss FCDB v7.1** (Open Gov), **UK CoFID** (OGL v3.0), **Australian AFCD** (CC-BY), **FAO BioFoodComp**, **FAO WAFCT** | `public_domain`, `open_license`, `open_content` |
| 5 | **Molecules (ChEBI/PubChem)** | 2 species | Secondary metabolites, polyphenols, volatiles, carotenoids | **FoodAtlas v4.11** (Apache-2.0), **PubChem** (Public Domain), **USDA Flavonoid/Isoflavone DB** (Public Domain), **Phenol-Explorer 3.0**, **PhytoHub**, **FooDB** | `public_domain`, `open_license`, `open_content` |
| 6 | **Bioactivity / health** | 0% (26,591 unsearched) | In-vitro assays, antioxidant capacity (FRAP), pathway targets | **ChEMBL 34** (CC-BY-SA), **Carlsen et al. 2010 FRAP** (PMC Open Access), **FoodAtlas literature triples** (PMC) | `open_license` |
| 7 | **Seasonality** | 2 species | Monthly harvest, storage & fresh availability windows | **seasoncalendar DB / BZfE** (DE), **USDA Agricultural Marketing Service (AMS)** seasonal charts (US), regional consumer calendars | `open_content` & `public_domain` |
| 8 | **Distribution / geography** | 94.0% text (1,590 unsearched) | Native range vs introduced range, ISO-3166 country codes | **Khoury et al. 2016** (CC0), **Kew POWO / WCVP TDWG** (CC-BY), **FPI / EPD** (parsed to ISO-3166), **CROPGRIDS / SPAM 2020** | `public_domain`, `open_license`, `open_content` |
| 9 | **Growing / agronomy** | 0% (26,591 unsearched) | Temperature min/opt/max, precipitation, soil pH, elevation, hardiness | **FAO ECOCROP** (2,568 species), **FPI / EPD grow data**, **USDA Plant Hardiness Zones** | `open_content` & `public_domain` |
| 10 | **Edible parts** | 87.9% text, 6.1% empty | Controlled botanical parts (fruit, seed, leaf, tuber, flower, stem) | **FPI / EPD** (normalized to `foods.PARTS`), **Mansfeld**, **Kew Useful Plants Checklist** | `open_content` & `open_license` |
| 11 | **Varieties / cultivars** | 0% (26,591 unsearched) | Named cultivars, landraces, accession IDs, historical apple/cabbage varieties | **Mansfeld's World Database** (6,100 species), **USDA GRIN-Global Accessions**, **FAO/INFOODS BioFoodComp**, **VIVC** (grape cultivars) | `open_content` & `public_domain` |
| 12 | **Photos & Plates** | 0% (33 tombstones) | Authentic, attributed botanical plates and high-res specimen photos | **USDA Pomological Watercolors** (7,497 cultivar plates, Public Domain), **Biodiversity Heritage Library (BHL)** (CC0 / Public Domain), **Pl@ntNet / GBIF** (CC-BY) | `public_domain` & `open_license` |
| 13 | **Evidence chain** | 0% | SHA256 audit hashes, DOI verification, cross-database entity links | **Crossref API**, **NCBI PubMed / PMC**, **Sciverse cache** | `public_domain` & `open_license` |

---

## 3. Comprehensive Database Landscape

### A. Core Public Domain Datasets (Zero Legal Friction)

#### 1. USDA World Economic Plants (WEP) & GRIN-Global (`SRC-USDA-GRIN-WEP`)
- **URL:** `https://npgsweb.ars-grin.gov/gringlobal/taxon/taxonomysearch`
- **License:** Public Domain (U.S. Federal Government work)
- **Scope:** 12,000+ vascular plant species with economic uses (food, forage, timber, medicine).
- **Attributes:** Botanical nomenclature, recognized synonyms, family/genus hierarchy, vernacular names in multiple languages, economic impact, geographical distribution, and germplasm accession IDs.
- **Role in Food Atlas:** Acts as the primary public domain taxonomic and variety backbone alongside NCBI Taxonomy.

#### 2. USDA Pomological Watercolors Collection (`SRC-USDA-POMOLOGICAL`)
- **URL:** `https://usdawatercolors.nal.usda.gov/`
- **License:** Public Domain (U.S. National Agricultural Library)
- **Scope:** 7,497 watercolor paintings created by USDA artists between 1886 and 1942.
- **Attributes:** 3,807 apple paintings, 670 peach, 611 grape, 563 pear, 335 plum, plus berries and nuts. Each watercolor depicts a specific cultivar with exact harvest date, grower, and locality.
- **Role in Food Atlas:** Replaces missing cultivar imagery with authentic, scientifically accurate historical artwork.

#### 3. Dr. Duke's Phytochemical and Ethnobotanical Databases (`SRC-USDA-DR-DUKE`)
- **URL:** `https://phytochem.nal.usda.gov/`
- **License:** Public Domain (USDA Agricultural Research Service)
- **Scope:** 80,000+ records linking plant species to chemical constituents and folk medicinal uses across worldwide cultures.
- **Attributes:** Plant binomials, common names, plant parts, chemical compounds with quantitative concentrations (ppm), biological activities, and ethnobotanical traditional uses.
- **Role in Food Atlas:** Connects traditional ethnobotanical records with phytochemical presence in a completely unencumbered Public Domain dataset.

#### 4. Biodiversity Heritage Library (BHL) Plates (`SRC-BHL`)
- **URL:** `https://www.biodiversitylibrary.org/`
- **License:** Public Domain / CC0 (for historical pre-1928 botanical plates)
- **Scope:** Millions of digitized high-resolution botanical plates from classical works (Curtis's Botanical Magazine, Flora Londinensis, Köhler's Medizinal-Pflanzen).
- **Role in Food Atlas:** Provides authentic species-level botanical illustrations with verifiable page-level BHL URLs. Dynamically queried via BHL API `NameSearch` and `GetItemPages` without needing bulk image downloads.

---

### B. National & International Nutrition Composition Tables

#### 5. USDA FoodData Central (`SRC-FDC-FOUNDATION-2026-04`, `SRC-FDC-SRLEGACY-2018-04`)
- **License:** Public Domain (CC0 1.0)
- **Scope:** 8,262 foods with comprehensive Tier 1/2 analytical and compilation nutrient profiles.

#### 6. German Bundeslebensmittelschlüssel BLS 4.0 (`SRC-BLS-4.0`)
- **License:** CC-BY 4.0 (Max Rubner-Institut)
- **Scope:** 7,140 foods $\times$ 138 nutrients = 985,000 cells. Rich in German vernacular names and preparation variations.

#### 7. French ANSES Ciqual Table (`SRC-CIQUAL-2024`)
- **URL:** `https://ciqual.anses.fr/`
- **License:** Open Licence 2.0 (Etalab) — completely compatible with commercial reuse and open redistribution.
- **Scope:** 3,200+ foods, 60+ nutritional components, including detailed fatty acid profiles and European cooking/preparation styles.

#### 8. Swiss Food Composition Database v7.1 (`SRC-SWISS-FCDB-V7.1`)
- **URL:** `https://naehrwertdaten.ch/`
- **License:** Swiss Federal Open Government Data (FSVO) / Free commercial and non-commercial reuse with attribution.
- **Scope:** 1,200+ foods with quad-lingual naming (German, French, Italian, English).

#### 9. UK Composition of Foods Integrated Dataset / CoFID (`SRC-UK-COFID-2021`)
- **URL:** `https://www.gov.uk/government/publications/composition-of-foods-integrated-dataset-cofid`
- **License:** Open Government Licence v3.0 (OGL) — free open reuse with attribution.
- **Scope:** 3,000+ foods, McCance & Widdowson's analytical standards, extensive vitamin and trace mineral fractions.

#### 10. Australian Food Composition Database / AFCD (`SRC-AUSTRALIA-AFCD-2022`)
- **URL:** `https://www.foodstandards.gov.au/science-data/afcd`
- **License:** CC-BY 4.0 (Food Standards Australia New Zealand / FSANZ).
- **Scope:** 2,000+ basic foods, indigenous Australian bush foods (e.g. Kakadu plum, quandong, bush tomato), and modern fortified staples.

#### 11. FAO/INFOODS BioFoodComp & Regional Tables (`SRC-FAO-BIOFOODCOMP-4.0`, `SRC-FAO-WAFCT-2019`)
- **License:** FAO Open Terms / Citation with attribution.
- **Scope:**
  - **BioFoodComp 4.0:** Focuses explicitly on cultivars, wild plants, and underutilized biodiversity.
  - **WAFCT 2019:** 472 West African indigenous food items (baobab, teff, fonio, cowpea, shea butter).

---

### C. Agronomy, Cultivars & High-Value Open Content

#### 12. Food Plants International (FPI) / EPD (`SRC-FOOD-PLANTS-INTL`)
- **License:** Free to access / Open Content (Non-profit educational reuse with citation).
- **Scope:** 33,000+ edible plant species worldwide.
- **Role in Food Atlas:** Baseline facts for tropical, orphan, and neglected crops: edible parts, distribution, and climate parameters.

#### 13. FAO ECOCROP Database (`SRC-ECOCROP`)
- **License:** FAO Data Terms (Free scientific reuse with citation).
- **Scope:** 2,568 plant species with agro-ecological limits: absolute & optimal temperature, rainfall, soil pH, depth, salinity, photoperiod, and altitude.

#### 14. Mansfeld's World Database of Agricultural and Horticultural Crops (`SRC-MANSFELD`)
- **License:** Academic citation (IPK Gatersleben).
- **Scope:** 6,100 cultivated species, botanical taxonomy, landraces, and cultivated varieties.

---

## 4. Alternative Knowledge Systems & Ethnomedicine

Food Atlas bridges modern biochemical analysis and traditional foodways (*"Food as Medicine"*). Traditional systems treat foods not merely as packets of calories or isolated vitamins, but as living energetic matrices with specific systemic actions on the body.

### A. Epistemic Integrity & Schema (`traditional_use`)

Under **Rule 14b (Epistemic Separation)**:
- Traditional concepts are **never** synthetically converted into Western biomedical diagnoses or biochemical claims (e.g., we do not claim *"cooling clears IL-6"*).
- Traditional knowledge is expressed in its native epistemological vocabulary, citing the specific cultural tradition, canonical treatise, or ethnobotanical record.
- Every claim belongs to claim group `traditional_use`, uses `basis="traditional_record"`, and carries strict provenance.

---

### B. The Five Major Alternative Knowledge Systems

#### 1. Traditional Chinese Medicine (TCM) & East Asian Medicine
- **Conceptual Pillars:**
  - **Thermal Nature (`tcm:nature`):** `hot` (热), `warm` (温), `neutral` (平), `cool` (凉), `cold` (寒).
  - **Five Flavors / Wu Wei (`tcm:flavor`):** `sweet` (甘 - tonifies/harmonizes), `sour` (酸 - astringes), `bitter` (苦 - clears heat/dries damp), `pungent` (辛 - disperses/moves Qi), `salty` (咸 - softens hardness).
  - **Meridian Tropism / Jingluo (`tcm:meridian`):** Organ channel pathways (`lung`, `spleen`, `stomach`, `heart`, `kidney`, `liver`, `large_intestine`, `small_intestine`, `bladder`, `gallbladder`, `pericardium`, `triple_burner`).
  - **Functional Actions (`tcm:action`):** e.g., `tonify_qi`, `nourish_yin`, `clear_heat`, `transform_phlegm`, `quicken_blood`.
  - **Food-Medicine Homology (`tcm:food_medicine_homology`):** Official classification under the Chinese National Health Commission "药食同源" dual-use catalogue (~110 edible species officially recognized as both food and medicine).
- **Primary Data Sources:**
  - **HERB Database (`SRC-HERB-TCM`):** 1,293 Chinese herbs, 4,964 ingredients, 19,418 target genes (Peking University, *NAR* 2021).
  - **TCMSP (`SRC-TCMSP`):** Chinese Pharmacopoeia herbs with ADME properties (oral bioavailability, drug-likeness).
  - **Classical Corpus:** *Shennong Bencao Jing* (Divine Farmer's Materia Medica), *Bencao Gangmu* (Compendium of Materia Medica by Li Shizhen, 1596).

#### 2. Ayurveda & Traditional Indian Systems (AYUSH)
- **Conceptual Pillars:**
  - **Rasa / 6 Tastes (`ayurveda:rasa`):** `madhura` (sweet), `amla` (sour), `lavana` (salty), `katu` (pungent), `tikta` (bitter), `kashaya` (astringent).
  - **Guna / 20 Qualities (`ayurveda:guna`):** Paired physiological attributes: `guru` (heavy) vs `laghu` (light), `snigdha` (unctuous) vs `ruksha` (dry), `sheeta` (cooling) vs `ushna` (heating), `manda` (dull) vs `tikshna` (sharp), etc.
  - **Virya / Energetic Potency (`ayurveda:virya`):** `sheeta` (cooling) or `ushna` (heating).
  - **Vipaka / Post-Digestive Effect (`ayurveda:vipaka`):** `madhura` (sweet), `amla` (sour), or `katu` (pungent).
  - **Dosha Action (`ayurveda:dosha`):** Tridosha actions: `balances_vata`, `increases_vata`, `balances_pitta`, `increases_pitta`, `balances_kapha`, `increases_kapha`, `tridosha_balancing` (tridoshic).
  - **Prabhava (`ayurveda:prabhava`):** Unique, specific non-linear action transcending taste and potency.
  - **Karma (`ayurveda:karma`):** Therapeutic dietary actions: `deepana` (enkindling digestive fire/Agni), `pachana` (digesting metabolic toxins/Ama), `anulomana` (downward digestive regulation), `rasayana` (rejuvenation/longevity), `medhya` (nootropic/cognition).
- **Primary Data Sources:**
  - **IMPPAT 2.0 (`SRC-IMPPAT-2.0`):** Curated database of 4,011 Indian medicinal & food plants, 17,926 phytochemicals, and classical formulations (IMSc Chennai).
  - **Classical Samhitas:** *Charaka Samhita* (Ahara Varga — dietetic classifications), *Sushruta Samhita*, *Ashtanga Hridaya*.

#### 3. Unani-Tibb (Graeco-Arab Medicine) & Siddha
- **Conceptual Pillars:**
  - **Mizaj / Temperament (`unani:mizaj`):** `damawi` (sanguine), `balghami` (phlegmatic), `safrawi` (choleric), `sawdawi` (melancholic).
  - **Degrees of Potency (`unani:degree`):** 1st degree (mild nutritional effect) through 4th degree (intense physiological effect).
  - **Siddha Medicine (`siddha:mukkuttram`, `siddha:suvai`):** Balancing of Vali, Azhal, and Iyyam through taste and seasonal foods.
- **Primary Data Sources:**
  - Ibn Sina (Avicenna): *The Canon of Medicine* (*Al-Qanun fi al-Tibb*).

#### 4. Indigenous Food Systems & Global Ethnobotany
- **Conceptual Pillars:**
  - **Traditional Food Uses (`ethno:traditional_use`):** `staple_food`, `foraged_greens`, `famine_food`, `ceremonial_food`, `maternal_postpartum_food`, `preservation_ration`.
  - **Traditional Processing & Detoxification (`ethno:preparation_method`):** Vital traditional biochemical processing that transforms inedible or toxic plants into staple foods:
    - *Tannin Leaching:* Cold/hot water leaching of acorns (*Quercus* spp.).
    - *Cyanogenic Glycoside Removal:* Grating, fermenting, pressing, and toasting bitter cassava (*Manihot esculenta*).
    - *Nixtamalization:* Alkaline cooking of maize (*Zea mays*) with slaked lime/wood ash, liberating bioavailable niacin (vitamin B3) and preventing pellagra.
    - *Pit Roasting & Earth Ovens:* Extended thermal hydrolysis of complex inulin polysaccharides in camas bulbs (*Camassia*) and agave.
    - *Ash treatment & Smoking:* Mineral supplementation and microbial preservation.
  - **Cultural Attribution & Governance:**
    - `ethno:community`, `ethno:peoples`, `ethno:region`.
    - **CARE Principles for Indigenous Data Governance:** Collective benefit, Authority to control, Responsibility, Ethics.
    - **Nagoya Protocol on Access and Benefit Sharing:** Full citation and acknowledgment of traditional custodians without commercial biopiracy.
- **Primary Data Sources:**
  - **Native American Ethnobotany Database / NAEB (`SRC-NAEB`):** 44,000+ food and medicinal uses of 4,029 plant species across 291 Native American tribes (Daniel Moerman).
  - **CINE Traditional Food Systems (`SRC-CINE`):** Arctic, First Nations, and global indigenous nutritional tables (McGill University).
  - **SEPASAL (Kew):** Survey of Economic Plants for Arid and Semi-Arid Lands.
  - **PROTA / PROSEA:** Plant Resources of Tropical Africa & South-East Asia.

#### 5. Traditional European Medicine (TEM) & Monastic Medicine (Klosterheilkunde)
- **Conceptual Pillars:**
  - **Humoral Qualities (`humoral:temperament`):** The four primary Galenic qualities: `warm_and_moist` (sanguine), `cold_and_moist` (phlegmatic), `warm_and_dry` (choleric), `cold_and_dry` (melancholic).
  - **Gradation (`tem:degree`):** 1st to 4th degree (*gradus*).
  - **Hildegardian Viriditas & Subtleties (`tem:viriditas`, `tem:subtilitas`):** Hildegard von Bingen's classification of plants' intrinsic greening life-power (*viriditas*) and inner nutritional/therapeutic virtues (*subtilitates*).
  - **Traditional Dietary Preparations (`tem:preparation`):** Electuaries, herbal vinegars, oxymels, wine decoctions, spiced bread/broths.
- **Primary Data Sources:**
  - Dioscorides: *De Materia Medica* (1st century AD).
  - Hildegard von Bingen: *Physica* (*Liber subtilitatum diversarum naturarum creaturarum*, c. 1150 AD).
  - Renaissance Kräuterbücher: Leonhart Fuchs (*New Kreüterbuch*, 1543), Hieronymus Bock (1539), Pietro Andrea Mattioli (1544), Nicholas Culpeper (*The English Physitian*, 1652).

---

## 5. Extensible Ingestion Pipeline for Books, Writings & Databases

To ensure that the pipeline gracefully ingests modern databases, digitized historical manuscripts, and multi-volume reference books without structural friction, we define a three-tier modular ingestion architecture:

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                   Quelldaten-Ebene                      │
                    ├───────────────────┬───────────────────┬─────────────────┤
                    │    Datenbanken    │  Historische PDF  │   Fachbücher    │
                    │ (FDC, BLS, Ciqual,│ & BHL Bildtafeln  │ (Lim, Facciola, │
                    │  ECOCROP, WEP)    │  (MinerU / API)   │   van Wyk)      │
                    └─────────┬─────────┴─────────┬─────────┴────────┬────────┘
                              │                   │                  │
                              ▼                   ▼                  ▼
                    ┌───────────────────┬───────────────────┬─────────────────┐
                    │ ingest/bulk/*.py  │ ingest/bhl.py     │ ingest/books.py │
                    │  (Tabular Stream) │  (Plate Metadata) │ (Monograph OCR) │
                    └─────────┬─────────┴─────────┬─────────┴────────┬────────┘
                              │                   │                  │
                              └───────────────────┼──────────────────┘
                                                  │
                                                  ▼  iter_claims()
                                      ┌───────────────────────┐
                                      │ atlas.contract.check  │ ◄── Validierung nach Regeln 1–14
                                      └───────────┬───────────┘
                                                  │
                                                  ▼
                                      ┌───────────────────────┐
                                      │ unified.duckdb Store  │
                                      │ (datapoints + rejects)│
                                      └───────────────────────┘
```

### A. The Universal Ingest Adapter Interface (`src/atlas/ingest/base.py`)

Every source adapter conforms to a single protocol:

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator
from atlas.claims import Claim

class BaseIngestAdapter(ABC):
    src_id: str

    @abstractmethod
    def iter_claims(self, source_path: Path) -> Iterator[Claim]:
        """Yields validated Claim objects with source attribution and citations."""
        ...
```

### B. Monograph & Book Ingestion (`src/atlas/ingest/monographs.py`)

Authoritative reference handbooks and digitized classical books are processed through structured JSON/YAML monograph extracts (`data/raw/monographs/*.json` or `*.yaml` produced via OCR tools like MinerU, Nougat, or Grobid):

```json
{
  "src_id": "SRC-BOTANICAL-MONOGRAPHS",
  "work": "Edible Medicinal and Non-Medicinal Plants",
  "author": "Lim, T. K.",
  "year": 2012,
  "volume": 1,
  "records": [
    {
      "scientific_name": "Malus domestica",
      "page": 412,
      "edible_parts": ["fruit"],
      "traditional_uses": [
        {
          "system": "ethno:traditional_use",
          "context": "stewed fruit used as gentle digestive aid",
          "preparation": "stewed with cinnamon"
        }
      ],
      "growing": {
        "chilling_hours_min": 800,
        "soil_ph_min": 6.0,
        "soil_ph_max": 7.0
      }
    }
  ]
}
```

The monograph parser translates these records into strict `Claim` instances:
- `subject`: `"org:malus-domestica"`
- `group`: `"traditional_use"` or `"growing"`
- `field`: `"ethno:traditional_use"` or `"growing:chilling_hours"`
- `v`: `"stewed fruit used as gentle digestive aid"`
- `basis`: `"traditional_record"`
- `food_part`: `"fruit"`
- `src`: `"SRC-BOTANICAL-MONOGRAPHS"`
- `derivation`: `"literature"`
- `ref`: `"T.K. Lim (2012): Edible Medicinal and Non-Medicinal Plants, Vol. 1, p. 412"`

### C. Streaming Contract & DuckDB Bulk Store

1. Claims flow directly through `atlas.contract.check(claim, sources)`.
2. Valid claims insert into table `datapoints`; invalid claims enter table `rejects` with rule ID and carried value.
3. Completely idempotent: `store.replace_source(src_id, claims, sources, batch)` clears prior records for `src_id` before inserting.
4. Fast: chunked inserts (`CHUNK = 50_000`) handle millions of rows in seconds.

---

## 6. Storage & Download Footprint (How many GB?)

Integrating these databases does **NOT** require downloading terabytes of raw data:

| Component | Nature of Data | Estimated Download / Disk Size | Handling Strategy |
|:---|:---|---:|:---|
| **Tabular & Relational Data**<br>(FDC, BLS, Ciqual, Swiss FCDB, CoFID, AFCD, ECOCROP, WEP, GBIF names) | CSV, JSON, DuckDB, Parquet | **~1.5 GB** | Downloaded once into `data/raw/` and indexed into `data/build/unified.duckdb`. |
| **FPI / EPD Snapshot** | Text / ZIM dump | **~250 MB** | Already locally present in `data/research/scope/`. |
| **Dr. Duke's, IMPPAT 2.0, HERB, NAEB** | Parquet, CSV, JSON | **~180 MB** | Lightweight structured bulk downloads. |
| **Monograph Extracts & Books** | Structured JSON / OCR text | **~150 MB** | Stored in `data/raw/monographs/`. Raw scans remain external or in cloud storage. |
| **USDA Pomological Watercolors** | Metadata + 7,497 JPEG plates | **~2.5 GB** *(optional)* | Metadata is 5 MB. Plates can be cached locally or served dynamically via USDA NAL image URLs. |
| **BHL (Biodiversity Heritage Library)** | 60M+ pages | **0 GB local** *(API-driven)* | Dynamically queried via BHL API (`BHL_API_KEY`). Links directly to Smithsonian/BHL high-res plate URLs. |
| **PubMed / Europe PMC / Crossref** | Scientific literature | **0 GB local** *(API-driven)* | Evidence DOIs and citation links are verified dynamically via REST APIs. |
| **Total Disk Requirement** | Core Unified Dataset | **~2.0 to 4.5 GB** | Easily fits on any workstation or laptop with zero disk storage pressure. |

---

## 7. Wave-by-Wave Ingestion Plan

1. **Wave 1 (Species Context):**
   - EPD / FPI (Country codes to ISO-3166, parts to `foods.PARTS`, growing parameters).
   - FAO ECOCROP (Agronomic limits: temperature, pH, rainfall).
   - Kew WCVP / POWO (Native vs introduced ranges).
   - GBIF Vernacular Names (1,171 unsearched names in multiple languages).
   - BHL API (Dynamic botanical plate linker).

2. **Wave 2 (National Public Domain & Open Nutrition):**
   - USDA FDC Foundation & SR Legacy (8,262 products, CC0).
   - French Ciqual 2024 (Etalab 2.0) & Swiss FCDB v7.1.
   - UK CoFID 2021 (OGL v3.0) & Australian AFCD 2022.
   - Cluster review and edge approval connecting products to species.

3. **Wave 3 (German Deep Nutrition & Cultivars):**
   - BLS 4.0 (7,140 foods $\times$ 138 nutrients = 985k cells).
   - FAO BioFoodComp 4.0 (Cultivar and wild species analytical biodiversity).

4. **Wave 4 (Phytochemistry, Ethnomedicine & Traditional Knowledge):**
   - FoodAtlas v4.11 (193k compound occurrences, Apache-2.0).
   - USDA Flavonoids, Isoflavones, Proanthocyanidins (Public Domain analytical values).
   - Dr. Duke's Phytochemical & Ethnobotanical Databases (Public Domain).
   - TCM Integration: HERB Database & TCMSP (`tcm:nature`, `tcm:flavor`, `tcm:meridian`, `tcm:action`).
   - Ayurveda Integration: IMPPAT 2.0 (`ayurveda:rasa`, `ayurveda:guna`, `ayurveda:virya`, `ayurveda:dosha`).
   - Indigenous Knowledge: NAEB & CINE (`ethno:traditional_use`, `ethno:preparation_method`).

5. **Wave 5 (Visuals, Seasonality, Cultivars & Monograph Corpus):**
   - USDA Pomological Watercolors (7,497 cultivar plates linked).
   - Seasonality calendars (BZfE / USDA AMS).
   - Mansfeld World Database (cultivar taxonomy).
   - Monograph Ingestion Engine (`ingest/monographs.py`): Authoritative texts (Lim, Sturtevant, Hildegard von Bingen, Dioscorides).

6. **Wave 6 (Deep Literature & Evidence Verification):**
   - Sciverse harvest loop (PubMed/PMC literature triples).
   - Evidence chain verification: Crossref DOI resolution, PMC links, `verified_in_source` audit.

7. **Wave 7 (Ratchet Closure & Release Export):**
   - All 13 rows audited: zero cells `unsearched`.
   - Idempotent export: Parquet export via DuckDB `COPY`.
   - Dual Release: 100% Pure Public Domain Export (`WHERE license_class = 'public_domain'`) and Full Open Knowledge Graph.
