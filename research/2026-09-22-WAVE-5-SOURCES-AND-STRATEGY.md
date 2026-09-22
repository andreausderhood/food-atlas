# Welle 5 Datenquellen & Ingest-Strategie: Varieties, Seasonality & Visuals

**Datum:** 2026-09-22  
**Autor:** Food Atlas Research & Antigravity  
**Kontext:** Vertiefende Evaluierung offener Primärquellen, APIs und Datenbestände zur Schließung der drei verbleibenden Kern-Achsen in Welle 5 (**Varieties/Cultivars**, **Seasonality** und **Photos/Visuals**) sowie flankierender Vorbereitung für **Bioactivity/Health** unter dem offenen Attributions- und Contract-Framework.

---

## 1. Ausgangslage & Coverage-Zustand nach Welle 4

Nach dem erfolgreichen Abschluss von Welle 4 (FoodAtlas v4.11, USDA Flavonoids, Dr. Duke's Ethnobotany, HERB TCM und IMPPAT 2.0; Commit `760049707`) stellt sich die 13-Zeilen-Coverage-Tabelle wie folgt dar:

| Feld / Zeile | Achse | Denominator | Claims (Filled) | Context % | Empty % | Unsearched | Status |
|:---|:---|---:|---:|---:|---:|---:|:---:|
| **Species identity** | species | 26.591 | 1 | 100.0% | 0.0% | 0 | **closed** |
| **Common names** | species | 26.591 | 2 | 55.8% | 44.2% | 0 | **closed** |
| **Food hierarchy** | product | 133.864 | 38.710 | 0.0% | 0.0% | 95.154 | open |
| **Nutrients** | species | 26.591 | 217 | 0.0% | 0.0% | 26.374 | open |
| **Molecules (ChEBI)** | species | 26.591 | **2.550** | 0.0% | 0.0% | 24.041 | open |
| **Bioactivity / health** | species | 26.591 | 0 | 0.0% | 0.0% | 26.591 | open |
| **Seasonality** | species | 26.591 | **2** | 0.0% | 0.0% | **26.589** | **W5 Fokus** |
| **Distribution / geography** | species | 26.591 | 0 | 90.2% | 3.8% | 1.590 | open |
| **Growing / agronomy** | species | 26.591 | 0 | 40.4% | 53.6% | 1.590 | open |
| **Edible parts** | species | 26.591 | 0 | 84.7% | 9.4% | 1.590 | open |
| **Varieties / cultivars** | species | 26.591 | **0** | 0.0% | 0.0% | **26.591** | **W5 Fokus** |
| **Photos** | species | 26.591 | **2** | 0.0% | 0.0% | **26.589** | **W5 Fokus** |
| **Evidence chain** | species | 26.591 | 0 | 0.0% | 0.0% | 26.591 | open |

**Zentrale Erkenntnis:** Während Identität und Trivialnamen verriegelt sind und Nährstoffe/Moleküle eine solide Basis besitzen, sind die Achsen **Varieties (0%)**, **Seasonality (0.01%)** und **Photos (0.01%)** fast völlig unerschlossen. Die Priorisierungs-Engine `atlas coverage --next` identifiziert diese drei Zeilen als unmittelbare Engpässe für die P1-Arten (die 544 weltweit wichtigsten Nutzpflanzenarten).

---

## 2. Detaillierte Quellenanalyse nach Welle-5-Achsen

### Achse 1: Varieties / Cultivars (`varieties`)

Ziel dieser Zeile ist es, historische und moderne Kultursorten, Landsorten, Zuchtlinien, Synonyme, Elternschaften (Pedigrees) und Genbank-Akzessionen ehrlich mit den 26.591 Pool-Arten zu verknüpfen.

#### 1.1 USDA GRIN-Global National Plant Germplasm System (NPGS)
* **Kategorie:** Public Domain (`public_domain`, US Federal Government)
* **URL:** `https://npgsweb.ars-grin.gov/gringlobal/taxon/taxonomysearch` / Flat-File Downloads
* **Umfang:** ~600.000 Akzessionen, 15.000+ Nutzpflanzenarten, über 100.000 namentlich erfasste Kultursorten und Landsorten.
* **Inhalt:**
  - `taxonomy_species`: Akzeptierter botanischer Name, Autorschaft, Primär- und Sekundär-Genpools.
  - `accession`: Akzessionsnummer (z. B. `PI 512345`), Sortenname (`cultivar_name`), Typ (Kultursorte, Wildform, Landsorte, Zuchtlinie).
  - `pedigree`: Abstammungsbäume bekannter Sorten (z. B. Kreuzungspartner von Äpfeln, Weizen, Mais).
* **Vorteil für Food Atlas:** 100% frei nutzbar (Public Domain), unproblematischer Export, deterministische Identifikatoren (`cult:usda:<accession_id>`).
* **Technische Anbindung:** Direkter Download der tabellarischen Dumps (Text/CSV) oder REST-API.

#### 1.2 EU Common Catalogue of Plant Varieties (DG SANTE / data.europa.eu)
* **Kategorie:** Open Data (`open_license` / Etalab 2.0 / EU Open Data)
* **URL:** `https://data.europa.eu/data/datasets/agricultural-vegetable-catalogue-new`
* **Umfang:** ~55.000 registrierte Sorten für landwirtschaftliche Arten und Gemüse in der Europäischen Union.
* **Inhalt:**
  - Offizielle Sortenbezeichnung (`variety_name`), Synonyme.
  - Artbezeichnung nach EU-Richtlinien (vollständig taxonomisch referenziert).
  - Erhaltungszüchter (`maintainer`), Zulassungsjahr, Zulassungsstatus.
* **Vorteil für Food Atlas:** Liefert die autoritative europäische Nomenklatur für alle marktfähigen Gemüsesorten (Tomaten, Kohl, Möhren, Salat etc.).
* **Technische Anbindung:** ZIP-Archiv mit strukturierter CSV/XML-Datei via EU Open Data Portal.

#### 1.3 Mansfeld’s World Database of Agricultural and Horticultural Crops (IPK Gatersleben)
* **Kategorie:** Open Content (`open_content`, Zitation & Namensnennung)
* **URL:** `http://mansfeld.ipk-gatersleben.de/mansfeld/`
* **Umfang:** 6.100 Kulturpflanzenarten; feingliedrige infraspezifische Taxonomie (Subspezies, Varietäten, Konvarietäten, Sortengruppen).
* **Inhalt:**
  - Historische Evolution und Domestikationsgeschichte.
  - Vollständige Liste von Sortengruppen (z. B. *Brassica oleracea* convar. *capitata* var. *alba* usw.).
  - Vernakuläre Namen in Dutzenden Sprachen.
* **Vorteil für Food Atlas:** Schließt die Lücke zwischen wissenschaftlichem Binomial und landwirtschaftlicher Sortengruppe.
* **Technische Anbindung:** Web-Scraper/Query-Skript analog zu IMPPAT 2.0 (über die PHP-Suchmaske des IPK Gatersleben).

#### 1.4 Harlan & de Wet / Khoury et al. Crop Wild Relatives (CWR) Inventory
* **Kategorie:** Public Domain / CC0 (`public_domain`, Dryad / Figshare / GBIF)
* **DOI / URL:** `10.5061/dryad.s08t2` / `http://www.cwrdiversity.org/checklist/`
* **Umfang:** 1.667 Crop Wild Relatives für 173 zentrale Kulturpflanzenarten weltweit.
* **Inhalt:**
  - Genpool-Klassifizierung: Gene Pool 1 (direkt kreuzbar), Gene Pool 2 (sekundär), Gene Pool 3 (tertiär).
  - Dokumentierte Wildahnen (z. B. *Malus sieversii* für *Malus domestica*, *Oryza rufipogon* für *Oryza sativa*).
* **Vorteil für Food Atlas:** Wissenschaftlich fundierte Stammbaum-Kanten zwischen Kulturpflanzen und ihren wilden Stammformen.

#### 1.5 VIVC – Vitis International Variety Catalogue (Julius Kühn-Institut, JKI)
* **Kategorie:** Open Academic (`open_content`, Zitation)
* **URL:** `https://www.vivc.de/`
* **Umfang:** 23.000+ Rebsorten (*Vitis vinifera* & Hybriden).
* **Inhalt:** Stammbäume (Mikrosatelliten-validierte Parentage), Beerenfarbe, Synonyme, Anbauflächen, Ursprungsländer.
* **Vorteil:** Löst die Rebsorten-Taxonomie auf Goldstandard-Niveau.

---

### Achse 2: Seasonality / Phänologie (`seasonality`)

Ziel dieser Zeile ist es, Ernte-, Lager- und Frischverfügbarkeitsmonate (1–12) für Nahrungspflanzen zu erfassen, differenziert nach Produktionsform (Freiland, Lagerware, Import).

#### 2.1 BLE / BZfE Saisonkalender (Deutschland / Mitteleuropa)
* **Kategorie:** Open Content (`open_content`, Bundesanstalt für Landwirtschaft und Ernährung)
* **URL:** `https://www.bzfe.de/nachhaltiger-konsum/orientierung-beim-einkauf/der-saisonkalender/`
* **Umfang:** ~120 Obst- und Gemüsearten für den mitteleuropäischen Markt.
* **Inhaltliche Struktur pro Monat (1–12):**
  - `status: fresh_field` (Freiland / Frische Ernte)
  - `status: storage` (Lagerware aus heimischem Anbau)
  - `status: protected` (Geschützter Anbau / Gewächshaus unbeheizt/beheizt)
  - `status: import` (Vorwiegend Importware)
* **Vorteil für Food Atlas:** Perfekte Übereinstimmung mit dem mitteleuropäischen Konsumentenbedarf und BLS/Ciqual-Katalogprodukten.

#### 2.2 FAO Global Crop Calendar (FAO GIEWS & SAGE Wisconsin / Sacks et al. 2010)
* **Kategorie:** Open Content / FAO Open Access (`open_content`)
* **URL / API:** `https://www.fao.org/giews/data-tools/` / REST-API Swagger: `https://www.fao.org/crop-calendar/api`
* **Umfang:** Aussaat-, Wachstums- und Erntemonate für hunderte Kulturpflanzen über 2.000+ agroökologische Zonen in 130+ Ländern.
* **Inhalt:**
  - `planting_start` / `planting_end`
  - `harvest_start` / `harvest_end`
  - Agroökologische Zonen (Klimazonen) und Ländercodes (ISO-3166).
* **Vorteil für Food Atlas:** Ermöglicht globale Seasonality-Abdeckung weit über die europäischen Supermarktfrüchte hinaus (z. B. Hirse, Maniok, Yam, Teff, tropische Früchte).

#### 2.3 EUFIC & ESU-services Saisonale Tabellen (Europa)
* **Kategorie:** Open Data / CC-BY (`open_license`)
* **Umfang:** 200+ Früchte und Gemüse über 24 europäische Länder.
* **Inhalt:** Monatliche Frischetabellen mit Zuordnung zu regionalen Produktionszonen und Treibhausgasprofilen.

---

### Achse 3: Photos / Historical Plates / Visuals (`photos`)

Ziel dieser Zeile ist es, verifizierte, qualitativ hochwertige, nicht-erfundene Bildnachweise (authentische historische Farbtafeln, wissenschaftliche Aquarelle, Herbarmuster) bereitzustellen.

#### 3.1 USDA Pomological Watercolor Collection
* **Kategorie:** Public Domain (`public_domain`, National Agricultural Library, NAL)
* **URL:** `https://usdawatercolors.nal.usda.gov/` / Open Data Repo: `https://github.com/jwilber/USDA_Pomological_Watercolors`
* **Umfang:** 7.497 botanisch-pomologische Aquarelle (1886–1942).
* **Bestand:**
  - 3.807 Apfelsorten (*Malus domestica*)
  - 670 Pfirsichsorten (*Prunus persica*)
  - 611 Traubensorten (*Vitis vinifera*)
  - 563 Birnensorten (*Pyrus communis*)
  - 335 Pflaumensorten (*Prunus domestica*)
  - Hunderte Beeren, Zitrusfrüchte, Feigen und Nüsse.
* **Inhaltliche Metadaten:**
  - Sortenname (`cultivar_name`), botanischer Name (`scientific_name`).
  - Künstler (`artist`, z. B. Deborah Griscom Passmore, Amanda Almira Newton).
  - Erntedatum, Züchter, Fundort (`locality`, US-Bundesstaat/Grafschaft).
  - Direkte URLs zu Thumbnails (256px) und High-Resolution Scans (4000px+).
* **Doppelter Hebel für Welle 5:** Dieses Archiv schließt gleichzeitig **Varieties-Kanten** UND liefert **Visuals (Photos)** in Museumsqualität unter 100% Public Domain!

#### 3.2 Biodiversity Heritage Library (BHL) Plates API
* **Kategorie:** Public Domain (`public_domain` / CC0 für historische Vor-1928-Tafeln)
* **URL:** `https://www.biodiversitylibrary.org/api3`
* **Bestand:** Millionen Farbtafeln aus klassischen Monografien (*Curtis’s Botanical Magazine*, *Flora Batava*, *Köhler’s Medizinal-Pflanzen*, *Batsch Elenchus Fungorum*).
* **Status im Code:** Der API-Client-Stub existiert bereits in `src/atlas/unified/photos.py`.
* **Vorgehen:** Abfrage via Binomial `scientific_name` $\rightarrow$ Resolving auf Bildtafel mit BHL-PageID und stabiler Bild-URL.

#### 3.3 Pl@ntNet / GBIF Media API (Feldaufnahmen)
* **Kategorie:** CC-BY 4.0 (`open_license`)
* **URL:** `https://api.gbif.org/v1/occurrence/search?mediaType=StillImage`
* **Umfang:** Über 50 Millionen verifizierte Natur- und Feldbeobachtungen.
* **Inhalt:** Organ-spezifische Bildmarkierungen (`flower`, `fruit`, `leaf`, `habit`).

---

### Achse 4: Flankierende Quellen für Bioactivity (`bioactivity`)

Da Bioactivity derzeit bei 0% steht, sollte Welle 5 mindestens eine fundamentale, offene Primärquelle ingestieren, um die Zeile aktiv zu schalten.

#### 4.1 Carlsen et al. (2010) Antioxidant Food Database
* **Kategorie:** Open Access (`open_license`, CC-BY 2.0, PMC2841576, *Nutrition Journal*)
* **Umfang:** 3.139 Lebensmittel, Gewürze, Kräuter, Getränke und Nahrungsergänzungsmittel.
* **Inhalt:** Experimentell gemessene totale antioxidative Kapazität (FRAP-Assay in mmol/100 g), Minimal-, Maximal- und Mittelwerte.
* **Vorteil:** Kompakte, zitierbare Primärmessung ohne komplexe Modellannahmen.

#### 4.2 Phenol-Explorer 3.0
* **Kategorie:** Open Academic (`open_content`, INRAE / University of Barcelona)
* **URL:** `http://phenol-explorer.eu/`
* **Umfang:** 500+ pflanzliche Lebensmittel $\times$ 400+ Polyphenole; Bioverfügbarkeits- und Metabolismus-Daten aus 1.300+ Publikationen.

---

## 3. Claim- und Vokabular-Design für Welle 5

Nach Regel 14b und dem Contract-System müssen alle neuen Claims strukturierte, typisierte Felder nutzen:

### 3.1 Varieties (`group="varieties"`)
* **Subject:** `prod:usda_grin:<id>`, `prod:eu_var:<id>`, oder direkt Art `org:<ncbi_tax_id>`
* **Field-Muster:**
  - `cultivar:name`: Offizieller Sortenname (z. B. `"Cox's Orange Pippin"`, `"San Marzano"`)
  - `cultivar:group`: Sortengruppe (z. B. `"Capitata Group"`, `"Incomparabilis Group"`)
  - `cultivar:synonym`: Historische oder regionale Synonyme
  - `cultivar:pedigree`: Abstammungsformel (z. B. `"Golden Delicious x Ingrid Marie"`)
  - `cultivar:origin_country`: 2-stelliger ISO-3166-Code des Ursprungs
* **Derivation:** `curated` (bei Genbanken) oder `compilation` (EU-Katalog).

### 3.2 Seasonality (`group="season"`)
* **Subject:** `prod:season:<source>:<food_key>` bzw. `org:<ncbi_tax_id>`
* **Field-Muster:**
  - `season:harvest:month`: Array oder Einzelmonate `[5, 6, 7, 8]`
  - `season:storage:month`: Monate aus Kühllagerung `[9, 10, 11, 12, 1, 2]`
  - `season:peak:month`: Hauptsaison
  - `season:region`: ISO-3166-Code (`"DE"`, `"CH"`, `"FR"`)
* **Value:** String, Integer-Liste oder strukturierter Status.

### 3.3 Visuals / Photos (`group="photos"`)
* **Subject:** `org:<ncbi_tax_id>` bzw. `prod:pom:<painting_id>`
* **Field-Muster:**
  - `photo:url`: Direkte URL zum hochauflösenden Scan
  - `photo:thumb_url`: URL zum Vorschaubild (256px)
  - `photo:artist`: Name des Illustrators / Fotografen
  - `photo:year`: Entstehungsjahr (z. B. `1898`)
  - `photo:license`: `"public_domain"` oder `"CC-BY-4.0"`
  - `photo:source_ref`: Signatur / PageID / NAL-Inventarnummer

---

## 4. Empfohlene Task-Struktur für Welle 5

Basierend auf den analysierten Datenbeständen schlagen wir folgende sieben Tasks für Welle 5 vor:

| Task # | Titel | Primäre Datenquelle | Ziel-Zeile in Coverage | Lizenzklasse |
|:---:|:---|:---|:---|:---:|
| **Task 32** | **USDA Pomological Watercolors Adapter & Visuals** | USDA NAL Pomological Collection (7.497 Werke) | `photos`, `varieties` | `public_domain` |
| **Task 33** | **BHL Plate API Live-Resolver & Caching** | Biodiversity Heritage Library API | `photos` | `public_domain` |
| **Task 34** | **BLE / BZfE Saisonkalender Adapter** | BLE / BZfE Saison-Matrix (~120 Arten, DE/Mitteleuropa) | `seasonality` | `open_content` |
| **Task 35** | **FAO Global Crop Calendar Adapter** | FAO GIEWS / SAGE Wisconsin (19 Kulturen, 130 Länder) | `seasonality` | `open_content` |
| **Task 36** | **EU Common Catalogue & Mansfeld Varieties** | EU Plant Variety Portal & Mansfeld IPK Gatersleben | `varieties` | `open_license` / `open_content` |
| **Task 37** | **Antioxidant Capacity Primär-Ingest (FRAP)** | Carlsen et al. (2010) (3.139 Lebensmittel, PMC Open Access) | `bioactivity` | `open_license` |
| **Task 38** | **Welle 5 Baseline & Ratchet-Schluss** | Messung, `baseline.json` Update, Ratchet-Verriegelung | Alle 13 Zeilen | – |

---

## 5. Fazit & Nächste Schritte

Mit dieser Strategie werden die bisherigen Null- bzw. Niedrigst-Coverage-Zeilen (**Varieties**, **Seasonality**, **Photos** und **Bioactivity**) systematisch und unter vollständiger Wahrung der Ehrlichkeits- und Attributionsregeln (keine erfundenen Bilder, keine Scheingenauigkeit, strikte Provenienz) erschlossen.

**Empfohlener nächster Arbeitsschritt:**
1. Abnahme dieses Research-Dokuments durch den Nutzer.
2. Erstellung der Task-Briefs `32` bis `38` in `data/build/plan-briefs/`.
3. Beginn mit **Task 32 (USDA Pomological Watercolors)**, da dieser als CC0/Public-Domain-Datensatz ohne Vorbedingungen direkt umsetzbar ist und mit einem Schlag Tausende authentische Pflanzenaquarelle und Sortennamen liefert.
