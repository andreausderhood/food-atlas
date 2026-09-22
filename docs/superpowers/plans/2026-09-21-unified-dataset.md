# Unified Dataset — coverage-getriebene Erweiterung Implementation Plan (Orca Multi-Agent Protocol)

> **For agentic workers in Orca:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aus FDC, BLS, Ciqual, Swiss FCDB, CoFID, FoodAtlas, EPD/FPI, USDA WEP, BHL, ECOCROP, Dr. Duke's, IMPPAT, HERB TCM, NAEB, historischen Monografien und den Kalender-/Foto-Beständen einen einzigen, ständig wachsenden Datensatz machen, dessen Fortschritt die 13-Zeilen-Coverage-Tabelle *misst* — bis in jeder Zeile keine Zelle mehr „nie gesucht" ist.

**Orca Multi-Agent Ecosystem & Resource Status (2026-09-21):**
- **Orca Workspace:** Die Ausführung erfolgt über [Stably Orca](https://github.com/stablyai/orca).
- **Antigravity (Gemini 3.8 Flash): ACTIVE & PRIMARY** — Steuert die aktuelle TDD-Implementierung, Core Engine, Contracts, Python Code & Test-Execution.
- **Claude Hermes (OpenRouter / Qwen & Gemma lokal): ACTIVE** — Für autonome Hintergrund-Harvesting-Loops und Long-Running Tasks.
- **Laya (`model@laya-v1`) / Jev (`model@jev-v1`): ACTIVE (lokal/cached)** — Taxonomie-Matching & Triage-Scores.
- **Claude (Anthropic API): PAUSED** (Wöchentliches Nutzungslimit erreicht, Reset: Do 24. Sep 05:00 Uhr).
- **Codex (OpenAI API): PAUSED** (5-Stunden Limit erreicht, Reset: 01:00 Uhr nachts).

**Architecture:** Drei Schichten mit je einer Wahrheit:
1. *Ledger* (Git): kuratierte Claims, Registry (`sources.yaml`), **Identitätsentscheidungen** (`product → species` in `edges.jsonl`).
2. *Bulk-Store* (`data/build/unified.duckdb`): Claims aus den Rohdaten, deterministisch aus Rohdatei-Hash + Parser + Entscheidungen erzeugt, nie von Hand editiert.
3. *Coverage-Engine*: berechnet die Tabelle aus (1)+(2)+Pool. Claims hängen am **Produkt** (dem Quell-Datensatz); die Art hängt nur über eine freigegebene Kante daran, per Join beim Lesen. Eine Freigabe hebt die Species-Abdeckung sofort, ohne Re-Ingest.

**Tech Stack:** Python 3.12/3.13, DuckDB, PyYAML, pytest. Keine neuen Abhängigkeiten (kein pyarrow/pandas; Parquet-Export geht mit DuckDB `COPY`).

---

## Global Constraints & Neues Offenes Attributions-Framework

- **Ehrlichkeitsprinzipien bleiben:** Chips nur für echte Claims; Matrixzelle `0` = gesucht, nichts akzeptiert, `–` = nie gesucht; übernommene Werte immer rejected/unresolved; kein Ranking über verschiedene Quellen; keine erfundenen Bilder; **Kandidat ≠ Claim**.
- **Neues Attributions- und Lizenz-Framework (Regel 9):**
  - **`public_domain`** (CC0, USDA WEP, FDC, BHL, Pomological Watercolors, Khoury, Dr. Duke's, historische Schriften): Völlig uneingeschränkt frei, Basis des Public-Domain-Core-Exports.
  - **`open_license`** (CC-BY 4.0, Apache-2.0, Etalab 2.0, UK OGL v3.0, Swiss FSVO Open Use, BLS 4.0, FoodAtlas, Ciqual, AFCD): Frei nutzbar und redistributierbar mit Namensnennung & Attribution.
  - **`open_content`** (Food Plants International/FPI, FAO ECOCROP, FAO BioFoodComp, Mansfeld, IMPPAT 2.0, HERB TCM, NAEB, CINE): Vollwertig integrierbar und zitierbar mit Ursprungsverweis, DOI/URL und Nennung. Keine Rohtextkopien geschützter kreativer Prosa.
  - **`cite` / `restricted`**: Reine Einzelfakt-Zitate aus autoritativen Fachbüchern (`curated: true`, `ref: "..."`).
- **Jeder Bulk-Claim läuft durch `atlas.contract.check`.** Es gibt keinen zweiten Validierungspfad.
- **Schreibbereiche:** `src/atlas/unified/**`, `src/atlas/ingest/**`, `src/atlas/site/**`, `src/atlas/db.py`, Tests. `src/atlas/cli.py` wird nur **erweitert**. **Nicht anfassen:** `src/atlas/build.py`, `src/atlas/research/**`, Inhalte von `data/**` — außer den in „Freigaben" genannten Pfaden und Pipeline-Outputs unter `data/research/proposals/`.
- **Tests:** `PYTHONPATH=src .venv/bin/python -m pytest -q` — während eines Tasks nur die Task-Tests, die volle Suite am Ende.
- **Modelle (Laya, Jev, Hermes, Antigravity, Codex) schlagen vor;** der deterministische Contract entscheidet; Identitäten und Regeln gibt ein Mensch frei (Regel 13).
- **Ausführung pro Task via Subagent mit Review dazwischen:** Jeder Task wird durch einen isolierten Subagenten nach TDD abgearbeitet und vor dem nächsten Schritt gereviewt.

---

## 1. Alternative Wissenssysteme, Ethnomedizin & Indigenes Wissen

Food Atlas schlägt die Brücke zwischen moderner Nährstoff- und Phytochemie-Analytik und traditionellen Ernährungstraditionen (*"Food as Medicine"*).

### A. Das Claim-Schema für `traditional_use`:
- **Claim-Gruppe:** `traditional_use`
- **Epistemische Trennung (Regel 14b):** Traditionelle Begrifflichkeiten werden niemals künstlich in westliche biochemische Labor-Konzepte umgedeutet (keine synthetische Reduktion wie „kühlend hemmt NF-κB"). Sie werden im authentischen begrifflichen Kontext zitiert und attribuiert.
- **Basis:** `basis="traditional_record"`
- **Standardisierte Subsystem-Präfixe in `field`:**

#### 1. TCM (Traditionelle Chinesische Medizin / Ostasiatische Medizin):
- `tcm:nature`: thermische Natur (`hot` [热], `warm` [温], `neutral` [平], `cool` [凉], `cold` [寒]).
- `tcm:flavor`: Fünf Geschmacksrichtungen / Wu Wei (`sweet` [甘], `sour` [酸], `bitter` [苦], `pungent` [辛], `salty` [咸]).
- `tcm:meridian`: Organbezug / Leitbahnen (`lung`, `spleen`, `stomach`, `heart`, `kidney`, `liver`, `large_intestine`, `small_intestine`, `bladder`, `gallbladder`, `pericardium`, `triple_burner`).
- `tcm:action`: Traditionelle Wirkrichtung (z. B. `tonify_qi`, `nourish_yin`, `clear_heat`, `transform_phlegm`).
- `tcm:food_medicine_homology`: Amtlicher Status der National Health Commission (NHC) "药食同源" (Doppelnutzung als Nahrung und Medizin).
- *Quellen:* HERB Database (`SRC-HERB-TCM`, NAR 2021), TCMSP (`SRC-TCMSP`), Arzneibuch der VR China.

#### 2. Ayurveda & Traditionelle Indische Systeme (AYUSH):
- `ayurveda:rasa`: Die 6 Geschmacksrichtungen (`madhura` [süß], `amla` [sauer], `lavana` [salzig], `katu` [scharf], `tikta` [bitter], `kashaya` [herb/adstringierend]).
- `ayurveda:guna`: Die 20 physiologischen Qualitäten (`guru` [schwer] vs `laghu` [leicht], `snigdha` [ölig/feucht] vs `ruksha` [trocken], `sheeta` [kühlend] vs `ushna` [erhitzend] etc.).
- `ayurveda:virya`: Thermische Wirkpotenz (`sheeta` [kühlend], `ushna` [erhitzend]).
- `ayurveda:vipaka`: Geschmackswirkung nach der Verdauung (`madhura`, `amla`, `katu`).
- `ayurveda:dosha`: Wirkung auf die Bioenergien (`balances_vata`, `increases_vata`, `balances_pitta`, `increases_pitta`, `balances_kapha`, `increases_kapha`, `tridosha_balancing`).
- `ayurveda:prabhava`: Spezifische, nichtlineare Heil-/Nahrungswirkung jenseits von Geschmack und Potenz.
- `ayurveda:karma`: Therapeutische Verdauungswirkung (`deepana` [entzündet Agni], `pachana` [baut Ama ab], `anulomana`, `rasayana` [Verjüngung], `medhya` [Geist/Kognition]).
- *Quellen:* IMPPAT 2.0 (`SRC-IMPPAT-2.0`, IMSc Chennai, 4.011 Pflanzen, 17.926 Phytochemikalien), Charaka Samhita (Ahara Varga), Sushruta Samhita.

#### 3. Unani-Tibb (Griechisch-Arabische Medizin) & Siddha:
- `unani:mizaj`: Temperament (`damawi` [sanguinisch], `balghami` [phlegmatisch], `safrawi` [cholerisch], `sawdawi` [melancholisch]).
- `unani:degree`: Wirkungsgrad von 1. Grad (milde Nahrungswirkung) bis 4. Grad (starke physiologische Wirkung).
- `siddha:mukkuttram`: Harmonisierung der drei Prinzipien (Vali, Azhal, Iyyam).
- *Quellen:* Ibn Sina (Avicenna): *Kanon der Medizin*, Siddha Pharmacopoeia of India.

#### 4. Indigene Nahrungssysteme (Globale Ethnobotanik):
- `ethno:traditional_use`: Dokumentierte traditionelle Verwendung (`staple_food`, `foraged_greens`, `famine_food`, `ceremonial_food`, `maternal_postpartum_food`, `preservation_ration`).
- `ethno:preparation_method`: Traditionelle Entgiftungs- und Aufbereitungsverfahren, die Pflanzen erst essbar machen:
  - *Tannin-Auswaschung:* Wässern von Eicheln (*Quercus*).
  - *Cyanid-Elimination:* Reiben, Fermentieren, Auspressen und Rösten von bitterem Maniok (*Manihot esculenta*).
  - *Nixtamalisation:* Alkalische Kochung von Mais mit Holzasche/Kalk zur Freisetzung von bioverfügbarem Niacin (Vitamin B3).
  - *Erdöfen & Dämpfen:* Hydrolyse von Inulin in Camas-Zwiebeln (*Camassia*) und Agaven.
- `ethno:community`, `ethno:peoples`, `ethno:region`: Genaue Nennung der Urhebergemeinschaft.
- **CARE-Prinzipien & Nagoya-Protokoll:** Volle Einhaltung indigener Datenrechte (Collective benefit, Authority to control, Responsibility, Ethics) ohne biopiratische Ausbeutung.
- *Quellen:* Dr. Duke's Databases (`SRC-USDA-DR-DUKE`, 80k Einträge), Native American Ethnobotany Database (`SRC-NAEB`, 44k Einträge, Moerman), CINE (`SRC-CINE`, McGill University), PROTA/PROSEA.

#### 5. Traditionelle Europäische Medizin (TEM) & Klostermedizin:
- `humoral:temperament`: Galenische Primärqualitäten (`warm_and_moist`, `cold_and_moist`, `warm_and_dry`, `cold_and_dry`).
- `tem:degree`: Graduierung im 1. bis 4. Grad (*gradus*).
- `tem:viriditas`, `tem:subtilitas`: Hildegard von Bingens Klassifikation der inneren Lebens- und Grünkraft (*viriditas*) und der spezifischen subtilen Tugenden (*subtilitates*).
- `tem:preparation`: Traditionelle diätetische Zubereitungen (Lattwergen, Kräuterweine, Oxymel, Dinkelzubereitungen).
- *Quellen:* Dioskurides (*De Materia Medica*), Hildegard von Bingen (*Physica*, ca. 1150), Renaissance-Kräuterbücher (Leonhart Fuchs 1543, Hieronymus Bock 1539, Pietro Andrea Mattioli 1544, Nicholas Culpeper 1652).

---

## 2. Erweiterbare Pipeline-Architektur für Bücher, Schriften & Datenbanken

Die Ingestion-Pipeline ist strikt modular und erweiterbar aufgebaut. Neue Fachbücher, historische Schriften und wissenschaftliche Datenbanken werden ohne Refactoring des Cores integriert:

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

### A. Standard-Adapter-Schnittstelle (`src/atlas/ingest/base.py`)

Jeder Ingest-Adapter implementiert eine einheitliche Schnittstelle:

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

### B. Buch- & Monografien-Ingest (`src/atlas/ingest/monographs.py`)

Fachbücher und historische Schriften werden über standardisierte JSON/YAML-Extraktionen (`data/raw/monographs/*.json` oder `*.yaml`) eingelesen, die aus OCR-Läufen (MinerU, Nougat, Grobid) stammen.
Jeder Claim trägt zwingend eine präzise Fundstelle im Werk:
- `ref`: `"<Autor> (<Jahr>): <Werktitel>, Band <Vol>, S. <Seite>"` (z. B. `ref="T.K. Lim (2012): Edible Medicinal and Non-Medicinal Plants, Vol. 1, p. 412"` oder `ref="Dioskurides: De Materia Medica, Buch II, Kap. 120"`).
- `basis`: `"traditional_record"` oder `"scientific_monograph"`.
- `derivation`: `"literature"`.

### C. Streaming Contract & Idempotenter Bulk-Store

1. Claims durchlaufen `atlas.contract.check(claim, sources)`.
2. Gültige Zeilen landen in `datapoints`; ungültige in `rejects` mit Regel-ID und `carried_value`.
3. Vollkommen idempotent: `store.replace_source(src_id, claims, sources, batch)` löscht alte Einträge dieser Quelle vor dem Einfügen.
4. Chunked Insert (`CHUNK = 50_000`) skaliert auf Millionen Zeilen in wenigen Sekunden.

---

## 3. Umfassende Datenquellen-Matrix & Speicher-Fußabdruck

| Quelle | Scope & Nutzen | Zeilen der Tabelle | Lizenzklasse | Download / Speicher |
|:---|:---|:---|:---|---:|
| **USDA WEP / GRIN** | 12.000+ Nutzarten, Taxonomie & Synonyme | Identity, Origin, Growing | `public_domain` | ~150 MB |
| **USDA FDC** | 8.262 Produkte, Referenz-Nährwerte Tier 1/2 | Nutrients, Hierarchy | `public_domain` | ~250 MB |
| **BLS 4.0** | 7.140 Lebensmittel $\times$ 138 Nährstoffe, DE-Namen | Nutrients, Common names | `open_license` | ~600 MB |
| **French Ciqual 2024** | 3.200+ Lebensmittel, europäische Zubereitungen | Nutrients, Common names | `open_license` | ~80 MB |
| **Swiss FCDB v7.1** | 1.200+ Schweizer Grundnahrungsmittel, 4-sprachig | Nutrients, Common names | `open_license` | ~30 MB |
| **UK CoFID 2021** | 3.000+ McCance & Widdowson's Nährwerte | Nutrients | `open_license` | ~50 MB |
| **Australian AFCD 2022** | 2.000+ Lebensmittel inkl. Indigenous Bush Foods | Nutrients, Common names | `open_license` | ~40 MB |
| **FAO BioFoodComp 4.0** | Nährwerte auf Sorten- und Wildartenebene | Nutrients, Varieties | `open_content` | ~70 MB |
| **FAO ECOCROP** | 2.568 Arten, Anbaugrenzen (Temp, pH, Regen, Höhe) | Growing | `open_content` | ~20 MB |
| **Food Plants Intl (FPI)** | 33.000+ essbare Arten, Teile, Geographie | Edible parts, Distribution | `open_content` | ~250 MB |
| **Mansfeld's Database** | 6.100 Kulturpflanzen, Landsorten, Taxonomie | Varieties, Edible parts | `open_content` | ~90 MB |
| **Dr. Duke's Ethnobotanik** | 80.000+ Pflanzen-Wirkstoff- und Volkstraditions-Einträge | Molecules, Traditional use | `public_domain` | ~50 MB |
| **HERB & TCMSP** | TCM-Arzneidrogen, thermische Natur, Geschmack, Meridiane | Traditional use, Molecules | `open_content` | ~60 MB |
| **IMPPAT 2.0** | 4.011 indische Pflanzen, Rasa, Guna, Virya, Dosha | Traditional use, Molecules | `open_content` | ~45 MB |
| **NAEB (Moerman) & CINE** | 44.000+ indigene nordamerikanische Verwendungen & Zubereitung | Traditional use, Process | `open_content` | ~35 MB |
| **BHL API** | Millionen digitalisierter historischer Farbtafeln | Photos / Plates | `public_domain` | **0 GB** (API-Query) |
| **USDA Pomological** | 7.497 historische Kultursorten-Aquarelle | Photos / Cultivars | `public_domain` | ~5 MB (Meta) / 2.5 GB (Opt.) |
| **PubMed / Crossref API** | DOI-Validierung, Primärliteratur-Nachweise | Evidence chain | `public_domain` | **0 GB** (API-Query) |
| **Gesamter Speicher** | **Vollständiger Kern-Datensatz Food Atlas** | **Alle 13 Zeilen** | – | **~2,0 bis 4,5 GB** |

> [!NOTE]
> BHL, Crossref und PubMed werden **ausschließlich per API** gezielt nach Bedarf abgefragt. Es werden keine Multi-Terabyte-Repositoren heruntergeladen.

---

## 4. Wellen-Roadmap

| Welle | Zeilen der Tabelle | Quellen | Ausführer in Orca | Exit-Kriterium |
|:---|:---|:---|:---|:---|
| **W0** | alle 13 messbar | – | Antigravity | **ERLEDIGT:** Baseline committed, Ratchet grün, Tasks 0–8 abgeschlossen |
| **W1** | Distribution, Growing, Edible parts, Photos, Common names | EPD/FPI, FAO ECOCROP, Kew WCVP, BHL API, GBIF | Subagenten-Kette | Ländercodes normiert (ISO-3166); Growing-Kollektor live; Edible parts $\ge 95\%$; Photos per BHL API |
| **W2** | Nutrients, Food hierarchy | USDA FDC, French Ciqual, Swiss FCDB, UK CoFID | Subagenten-Kette | Paritätstest grün; Nutrients $\ge 108$ Arten; Hierarchy entschieden |
| **W3** | Nutrients (Tiefe), Common names (DE) | BLS 4.0 (7.140 Foods $\times$ 138 Nährstoffe), FAO BioFoodComp | Subagenten-Kette | 985k Zellen im Store; Sorten-Nährwerte live |
| **W4** | Molecules, Bioactivity, Traditionswissen | FoodAtlas v4.11, USDA Flavonoids, Dr. Duke's, HERB, IMPPAT 2.0 | Subagenten-Kette | ChEBI/PubChem Kanten; Bioaktivität mit PMC-Attribution; `traditional_use` Claims |
| **W5** | Seasonality, Varieties, Visuals | Saisonkalender, USDA Pomological Watercolors, Mansfeld, BHL Plates | Subagenten-Kette | Pomological Watercolors verlinkt; Saisonkalender gemappt |
| **W6** | Tiefe & Schriften | Monografien-Ingest (Lim, Sturtevant, Hildegard, Fuchs), Sciverse | Subagenten-Kette | `verified_in_source` verifiziert; Fachbuch-Zitate aktiv |
| **W7** | Abschluss | Audit-Hash-Schicht, Dual-Export (Public Domain + Open Graph) | Subagenten-Kette | Alle 13 Zeilen `closed` |

---

## 5. Welle 0 Status: Abgeschlossen

- [x] **Task 0: Orca Worktree-Setup** (`.claude/worktrees/unified-dataset`)
- [x] **Task 1: Identität — Kanten, Cluster, Review-Blatt** (`identity.py`, 5 Tests)
- [x] **Task 2: Bulk-Store — DuckDB, Contract-Stream, Kanten-Join** (`store.py`, 3 Tests)
- [x] **Task 3: Coverage Engine — 13 Zeilen & Kollektoren** (`cells.py`, `fields.py`, `collectors.py`, `table.py`)
- [x] **Task 4: CLI — `atlas coverage` und Ratchet** (`cli.py`, 6 Tests)
- [x] **Task 5: CLI Verdrahtung & Echte Baseline** (`docs/coverage/baseline.json`)
- [x] **Task 6: Regel 6′ — Produktdatensätze im Contract** (`as_described` / `product`)
- [x] **Task 7: Symbolbilder der 33 Knoten entfernen & images.yaml grabsteinen**
- [x] **Task 8: Orca Multi-Agent Task Harness** (`tools/plan_tasks.py` split & guard)

---

## 6. Welle 1 Detail-Tasks (Species-Kontext)

Die Ausführung erfolgt **strikt pro Task via Subagent**, mit Test-First (TDD), Diff-Guard und Review dazwischen.

### Task 9: Agronomie & Growing-Kollektor (`growing`)
**Ziel:** Anbauparameter (Temperatur, Boden-pH, Regen, Höhe) aus EPD und FAO ECOCROP in den Kollektor `growing` einspeisen.
- **Files:**
  - Modify: `src/atlas/unified/collectors.py` (Kollektor `growing` implementieren)
  - Modify: `src/atlas/unified/fields.py` (Kollektor `growing` verdrahten)
  - Modify: `tools/build_species_pool.py` (Anbaudaten im Pool verankern)
  - Test: `tests/test_unified_growing.py`
- [x] **Step 1:** Failing Test für `growing`-Kollektor schreiben (`tests/test_unified_growing.py`).
- [x] **Step 2:** Test fehlschlagen sehen.
- [x] **Step 3:** Kollektor in `collectors.py` implementieren.
- [x] **Step 4:** Test grün verifizieren.
- [x] **Step 5:** Diff Guard prüfen & committen.

### Task 10: Geographie & ISO-3166 Normalisierung (`distribution`)
**Ziel:** EPD-Länderlisten und Kew WCVP in standardisierte ISO-3166 2-Letter-Codes parsen.
- **Files:**
  - Create: `src/atlas/unified/geo.py` (Länder-Parser & ISO-3166 Lookup)
  - Modify: `src/atlas/unified/collectors.py` (Kollektor `distribution` umstellen)
  - Test: `tests/test_unified_geo.py`
- [x] **Step 1:** Failing Test für ISO-3166 Parser schreiben (`tests/test_unified_geo.py`).
- [x] **Step 2:** Test fehlschlagen sehen.
- [x] **Step 3:** Parser und ISO-3166 Zuordnungstabelle implementieren.
- [x] **Step 4:** Test grün verifizieren.
- [x] **Step 5:** Diff Guard prüfen & committen.

### Task 11: Essbare Teile Vokabular-Normalisierung (`edible_parts`)
**Ziel:** Freitext-Teileangaben aus EPD/FPI gegen das kontrollierte 10-Begriffe-Vokabular (`foods.PARTS`) normalisieren.
- **Files:**
  - Create: `src/atlas/unified/parts.py` (Teile-Normalisierer & Review-Filter)
  - Modify: `src/atlas/unified/collectors.py` (Kollektor `edible_parts` aktualisieren)
  - Test: `tests/test_unified_parts.py`
- [x] **Step 1:** Failing Test für `parts.py` schreiben (`tests/test_unified_parts.py`).
- [x] **Step 2:** Test fehlschlagen sehen.
- [x] **Step 3:** Vokabular-Normalisierung implementieren.
- [x] **Step 4:** Test grün verifizieren.
- [x] **Step 5:** Diff Guard prüfen & committen.

### Task 12: BHL API & Bild-Kollektor (`photos`)
**Ziel:** Kollektor `photos` aktivieren, der verifizierte Bildtafeln (BHL API & USDA Pomological Watercolors) als `filled` und fehlende als `searched_empty` erfasst.
- **Files:**
  - Create: `src/atlas/unified/photos.py` (BHL API Client & Plate Linker)
  - Modify: `src/atlas/unified/collectors.py` (Kollektor `photos` implementieren)
  - Modify: `src/atlas/unified/fields.py` (Kollektor `photos` verdrahten)
  - Test: `tests/test_unified_photos.py`
- [x] **Step 1:** Failing Test für BHL Plate Resolver schreiben (`tests/test_unified_photos.py`).
- [x] **Step 2:** Test fehlschlagen sehen.
- [x] **Step 3:** BHL Plate Abfrage & Kollektor implementieren.
- [x] **Step 4:** Test grün verifizieren.
- [x] **Step 5:** Diff Guard prüfen & committen.

### Task 13: Trivialnamen-Erweiterung (`common_names`)
**Ziel:** Die 1.171 Arten ohne Namen über offene Quellen (GBIF Vernacular / Wikidata) erschließen.
- **Files:**
  - Modify: `src/atlas/unified/collectors.py` (Kollektor `common_names` erweitern)
  - Test: `tests/test_unified_coverage.py`
- [x] **Step 1:** Failing Test für 100% Namensabdeckung schreiben.
- [x] **Step 2:** Test fehlschlagen sehen.
- [x] **Step 3:** Namens-Erweiterung einbinden.
- [x] **Step 4:** Test grün verifizieren.
- [x] **Step 5:** Diff Guard prüfen & committen.

### Task 14: Priorisierungs-Engine (`atlas coverage --next`)
**Ziel:** CLI-Option `--next` implementieren, die die 10 wirksamsten Lückenblöcke nach Pool-Priorität ausgibt.
- **Files:**
  - Modify: `src/atlas/unified/cli.py`
  - Modify: `src/atlas/unified/table.py`
  - Test: `tests/test_unified_coverage.py`
- [x] **Step 1:** Failing Test für `--next` schreiben.
- [x] **Step 2:** Test fehlschlagen sehen.
- [x] **Step 3:** Priorisierungs-Berechnung implementieren.
- [x] **Step 4:** Test grün verifizieren.
- [x] **Step 5:** Diff Guard prüfen & committen.

### Task 15: Welle 1 Baseline & Ratchet-Schluss
**Ziel:** Coverage messen, neue Baseline für Welle 1 schreiben und Ratchet verriegeln.
- **Files:**
  - Modify: `docs/coverage/baseline.json`
- [x] **Step 1:** `atlas coverage` ausführen und Werte prüfen.
- [x] **Step 2:** `atlas coverage --write-baseline` ausführen.
- [x] **Step 3:** `atlas coverage --check` verifizieren.
- [x] **Step 4:** Commit & Welle 1 Review.

---

## 7. Welle 2 Detail-Tasks (National Public Domain & Open Nutrition)

Die Ausführung erfolgt **strikt pro Task via Subagent**, mit Test-First (TDD), Diff-Guard und Review dazwischen.

### Task 16: Base Ingestion Architecture & CLI (`atlas ingest`)
**Ziel:** Einheitliche Ingestion-Architektur mit `BaseIngestAdapter` und CLI-Befehl `atlas ingest` bereitstellen.
- **Files:**
  - Create: `src/atlas/ingest/base.py` (Standard-Adapter-Interface & Registry)
  - Modify: `src/atlas/cli.py` (Befehl `atlas ingest <src_id> <path>` verdrahten)
  - Test: `tests/test_ingest_base.py`
- [x] **Step 1:** Failing Test für Ingest-CLI und Adapter-Interface schreiben (`tests/test_ingest_base.py`).
- [x] **Step 2:** Test fehlschlagen sehen.
- [x] **Step 3:** `BaseIngestAdapter` in `src/atlas/ingest/base.py` und `atlas ingest` in `src/atlas/cli.py` implementieren.
- [x] **Step 4:** Test grün verifizieren.
- [x] **Step 5:** Diff Guard prüfen & committen.
  *(Erledigt 2026-09-22, Commit ad7d07a — via Hermes-Subagenten-Fallback nach Antigravity-Quota-Stopp.)*

### Task 17: FDC Foundation & SR Legacy Streaming Adapter (`bulk_fdc`)
**Ziel:** Schnellen, streaming-fähigen FDC-Parser bauen, der 8.262 Produkte nach Regel 6′ (`prod:fdcf:*`, `prod:fdcs:*`, `basis="as_described"`, `food_part="product"`) in `unified.duckdb` streamt.
- **Files:**
  - Create: `src/atlas/ingest/bulk_fdc.py` (FDC Streaming Adapter)
  - Modify: `src/atlas/ingest/base.py` (Adapter registrieren)
  - Test: `tests/test_ingest_fdc_stream.py`
- [x] **Step 1:** Failing Test für FDC Streaming Adapter schreiben (`tests/test_ingest_fdc_stream.py`).
- [x] **Step 2:** Test fehlschlagen sehen.
- [x] **Step 3:** FDC Streaming Adapter implementieren und Ingest beider FDC-Quellen ausführen.
- [x] **Step 4:** Test grün verifizieren (Store-Zahlen & 0 Contract Rejects).
- [x] **Step 5:** Diff Guard prüfen & committen.
  *(Erledigt 2026-09-22, Commit 82a66e5 — 8.261 Produkte/665.551 Claims, 0 Rejects; eine Foundation-Art (fdc_id 2758999) ist im USDA-Rohfile ohne Nährwertzeilen, ehrlich leer.)*

### Task 18: European Nutrition Adapters (Ciqual & Swiss FCDB)
**Ziel:** Ingest-Adapter für ANSES Ciqual 2024 und Swiss FCDB v7.1 implementieren und ausführen.
- **Files:**
  - Create: `src/atlas/ingest/ciqual.py` (Ciqual Adapter)
  - Create: `src/atlas/ingest/swiss_fcdb.py` (Swiss FCDB Adapter)
  - Modify: `src/atlas/ingest/base.py` (Adapter registrieren)
  - Test: `tests/test_ingest_european.py`
- [x] **Step 1:** Failing Test für europäische Adapter schreiben (`tests/test_ingest_european.py`).
- [x] **Step 2:** Test fehlschlagen sehen.
- [x] **Step 3:** Adapter implementieren und Ingest ausführen.
- [x] **Step 4:** Test grün verifizieren.
- [x] **Step 5:** Diff Guard prüfen & committen.
  *(Erledigt 2026-09-22, Commit 22e6393 — Ciqual 2025 statt 2024 (ANSES hat 2024 zurückgezogen; DOI 10.57745/RDMHWY, Etalab 2.0): 3.484 Foods/151.981 Claims; Swiss FCDB 1.216/52.658; 0 Rejects. Katalog-/Identity-Registrierung nachgezogen in 21e1b48 — Produktdenominator 100.483.)*

### Task 19: Identity Cluster Proposals & Paritätsprüfung
**Ziel:** Vorschläge für Kanten (`product -> species`) generieren, Parität der Pilot-Arten (*Malus domestica*, *Brassica oleracea*) absichern und exakte Matches ($\ge 0.95$) in `edges.jsonl` übernehmen.
- **Files:**
  - Create: `tests/test_unified_parity.py`
  - Modify: `data/registry/identity/edges.jsonl`
- [x] **Step 1:** Failing Paritätstest schreiben (`tests/test_unified_parity.py`).
- [x] **Step 2:** Test fehlschlagen sehen.
- [x] **Step 3:** Cluster-Vorschläge anwenden und Kanten eintragen.
- [x] **Step 4:** Paritätstest grün verifizieren.
- [x] **Step 5:** Diff Guard prüfen & committen.
  *(Erledigt 2026-09-22, Commits fd7365b + 1503f7f — 62.018 Proposals; 136 exakte scientific-name-Kanten approbiert (Ciqual `alim_nom_sci`; 126 species-level + 10 infraspezifische Pool-Key-Exakte), 58 Arten mit Nährwert-Anbindung. Ciqual-`sci`-Namen ergänzt, Test-Isolation-Leak behoben. Decision: nur exakte scientific-name-Identität wird auto-approbiert (André, 2026-09-22).)*

### Task 20: Welle 2 Baseline & Ratchet-Schluss
**Ziel:** Coverage messen, Nutrients $\ge 108$ Arten und Food Hierarchy Produkte verifizieren, Baseline aktualisieren und Ratchet verriegeln.
- **Files:**
  - Modify: `docs/coverage/baseline.json`
- [x] **Step 1:** `atlas coverage` ausführen und Werte prüfen (Nutrients $\ge 108$ Arten).
- [x] **Step 2:** `atlas coverage --write-baseline` ausführen.
- [x] **Step 3:** `atlas coverage --check` verifizieren.
- [x] **Step 4:** Commit & Welle 2 Review.
  *(Erledigt 2026-09-22, Commit e0eec9c — Abweichung vom Exit-Kriterium: 58 statt ≥108 Arten. Grund: der Common-Name-Matcher erzeugt falsche Identitäten (z. B. „Peppers, bell" → *Piper nigrum*); eine Bulk-Freigabe der 546 `common_exact`-Cluster wäre Regel-13-Verstoß. André hat den ehrlichen Lock bei 58 freigegeben; ≥108 wird in Welle 3 (Tasks 21–22) erreicht.)*

### Task 21: Identity-Matcher-Qualität (Multi-Word & Qualifier-Regeln)
**Ziel:** Den Common-Name-Matcher review-fähig machen: Single-Word-Matching (Regel 3) erzeugt demonstrabel falsche Identitäten („Peppers, bell" → *Piper nigrum*; „Mushroom, lion's mane" → *Agaricus spp.*). Nach dem Cleanup sollen die `common_exact`-Cluster zum Human Gate geeignet sein.
- **Files:**
  - Modify: `src/atlas/unified/identity.py` (Matcher-Regeln 3–5)
  - Modify: `tests/test_unified_parity.py`
  - Pipeline-Output: `data/research/proposals/identity-proposals.jsonl` (regeneriert)
- [x] **Step 1:** Failing Regressions-Tests schreiben: „Peppers, bell, green, raw" darf *kein* *Piper nigrum*-Proposal erzeugen; „Mushroom, lion's mane" kein *Agaricus*; True Positives müssen bestehen bleiben („Almonds" → *Prunus dulcis*, „Black currant" → *Ribes nigrum*, „Apple" → *Malus domestica*).
- [x] **Step 2:** Test fehlschlagen sehen.
- [x] **Step 3:** Matcher anpassen: Multi-Word-Common-Names nur als Phrase-Exact; Single-Word-Match nur wenn das Wort im Pool eindeutig ist (genau eine Art trägt diesen Common Name) oder der Phrase-Kontext die Art disambiguiert; generische Kategorienwörter (mushroom, beans, peppers, berries …) als Single-Word-Match ausgeschlossen.
- [x] **Step 4:** Proposals über alle 100.483 Produkte neu generieren; Cluster-Delta gegen Vorher (546 `common_exact`-Cluster / 230 Arten / 47.838 Produkte) berichten.
- [x] **Step 5:** Volle Suite grün, Guard, Commit.

### Task 22: Review-Blatt & Human-Gate-Runde (Common-Exact-Cluster)
**Ziel:** Die gereinigten Cluster als Review-Blatt exportieren, André geben pro Cluster frei (Regel 13), Approvals nach `edges.jsonl`. Ziel: Nutrients $\ge 108$ Arten.
- **Files:**
  - Modify: `src/atlas/unified/identity.py` (Review-Blatt-Export + Approval-Anwendung)
  - Test: `tests/test_unified_review_sheet.py`
  - Modify: `data/registry/identity/edges.jsonl` (nach Freigabe)
- [ ] **Step 1:** Failing Test für Review-Blatt-Export (Cluster sortiert nach Größe, je 5 Namens-Samples, Konflikt-Markierung wenn ein Produkt mehr als eine Art vorschlägt).
- [ ] **Step 2:** Test fehlschlagen sehen.
- [ ] **Step 3:** Export implementieren; Blatt nach `data/research/proposals/review/`.
- [ ] **Step 4:** **HUMAN GATE:** Task pausiert; André approbiert/rejected Cluster (im Chat oder direkt im Blatt).
- [ ] **Step 5:** Approvals anwenden (Cluster-level approve/reject), Kanten schreiben, Suite grün.
- [ ] **Step 6:** Bericht: eindeutige Arten mit Nährwert-Claims vs. 108-Ziel; Guard & Commit.

### Task 23: BLS 4.0 Streaming-Adapter (7.140 Foods × 138 Nährstoffe, DE-Namen)
**Ziel:** BLS 4.0 (CC-BY-4.0, Max Rubner-Institut, DOI 10.25826/Data20251217-134202-0) in den Bulk-Store: Portierung des Legacy-`bls.py` auf die Task-16-Adapter-Architektur; DE-Common-Names fließen in die Identity-Proposals (P1 „Common names (DE)").
- **Files:**
  - Create: `src/atlas/ingest/bls_bulk.py`
  - Modify: `src/atlas/ingest/base.py` (registrieren)
  - Modify: `src/atlas/site/catalog.py` (`_bls_rows` auf die BLS-4.0-Struktur heben)
  - Test: `tests/test_ingest_bls.py`
- [x] **Step 1:** Failing Test (Fixtures aus echten BLS-Zeilen, Regel 6′: `basis="as_described"`, `food_part="product"`, Datenherkunft-Map von `bls.py` übernehmen).
- [x] **Step 2:** Test fehlschlagen sehen.
- [x] **Step 3:** Adapter implementieren, Ingest ausführen, DE-Namen in `generate_proposals` mitschicken.
- [x] **Step 4:** Test grün (Store-Zahlen, 0 Contract Rejects — Logische-Null/Annahme-Derivationen ehrlich mappen).
- [x] **Step 5:** Guard & Commit.

### Task 24: UK CoFID 2021 Intake & Adapter (W2-Nachlass)
**Ziel:** McCance & Widdowson's CoFID 2021 (UK OGL v3.0, ~3.000 Foods) ingestieren — war in der W2-Quellenliste, fehlt im Store.
- **Files:**
  - Create: `src/atlas/ingest/cofid.py`
  - Modify: `src/atlas/ingest/base.py`, `data/registry/sources.yaml` (Eintrag ergänzen — Orchestrator)
  - Test: `tests/test_ingest_cofid.py`
- [x] **Step 1:** Orchestrator: Intake nach `data/raw/cofid-2021/` + SOURCE.md (URL, SHA-256) + Registry-Eintrag `SRC-COFID-2021`.
- [x] **Step 2:** Failing Test, `identity.py` SOURCE_SHORT ergänzen (`prod:cofid`).
- [x] **Step 3:** Adapter implementieren, Ingest ausführen.
- [x] **Step 4:** Test grün, Guard & Commit.

### Task 25: FAO BioFoodComp 4.0 — Sorten-Nährwerte (Varieties-Achse)
**Ziel:** FAO BioFoodComp 4.0 (`open_content`): Nährwerte auf Sorten- und Wildartenebene → die Varieties-Zeile der Tabelle lebt; Meilenstein „985k Zellen im Store; Sorten-Nährwerte live" (W3-Exit).
- **Files:**
  - Create: `src/atlas/ingest/biofoodcomp.py`
  - Modify: `src/atlas/ingest/base.py`, `src/atlas/unified/identity.py` (SOURCE_SHORT), `data/registry/sources.yaml` (Orchestrator)
  - Test: `tests/test_ingest_biofoodcomp.py`
- [x] **Step 1:** Orchestrator: Intake nach `data/raw/biofoodcomp-4.0/` + SOURCE.md + Registry `SRC-BFOODCOMP-4.0`.
- [x] **Step 2:** Failing Test (Fixtures aus echten Zeilen).
- [x] **Step 3:** Adapter implementieren, Ingest ausführen; Claims auf Wild-/Sortenebene mit ehrlicher `derivation`.
- [x] **Step 4:** Test grün, Guard & Commit.

### Task 26: Welle 3 Baseline & Ratchet-Schluss
**Ziel:** Coverage messen (Ziele: Nutrients $\ge 108$ Arten nach Task 22, Store-Zellen Richtung 985k), Baseline aktualisieren, Ratchet verriegeln, Welle-3-Review.
- **Files:**
  - Modify: `docs/coverage/baseline.json`
- [x] **Step 1:** `atlas coverage` + Exit-Kriterien prüfen.
- [x] **Step 2:** `atlas coverage --write-baseline`, `--check` grün.
- [x] **Step 3:** Commit & Welle 3 Review.

---

## 8. Multi-Agent Orchestration & Model Role Matrix (Orca Setup)

| Agent / Model | Orca Role | Primary Responsibility | Input Artifacts | Output Artifacts |
|:---|:---|:---|:---|:---|
| **Antigravity** | Lead Developer & Architect | Engine implementation, contract enforcement, TDD core | Plan briefs, pytest outputs | Python modules, pytest suites, Git commits |
| **Claude Hermes** | Async Cron Engine & Ingest | Background ingest runs, raw file fetching, harvest loops | Raw source files, cron triggers | Ingest logs, raw duckdb tables |
| **Codex** | Code & Test Synthesizer | Fast boilerplate, helper parser functions, unit tests | Brief specs, file interfaces | Helper modules, test fixtures |
| **Laya (`model@laya-v1`)** | Taxonomy Matcher | Proposals for FoodOn <-> NCBI <-> Binomial matching | Unmapped raw names | `data/research/proposals/laya_*.json` |
| **Jev (`model@jev-v1`)** | Triage & Evidence Scorer | Bioactivity triage, gap priority scoring | Raw extract triples | `data/research/proposals/jev_*.json` |

Jedes Orca-Modell arbeitet streng isoliert. Vorschläge von Laya und Jev fließen niemals direkt in Claims oder Matrizen, sondern verbleiben als gecachte Vorschläge (`model@version`, `input_hash`), die deterministisch von `contract.py` geprüft und von menschlichen Reviewern per `edges.jsonl` freigegeben werden.
