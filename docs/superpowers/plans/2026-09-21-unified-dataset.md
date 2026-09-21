# Unified Dataset — coverage-getriebene Erweiterung Implementation Plan (Orca Multi-Agent Protocol)

> **For agentic workers in Orca:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aus FDC, BLS, FoodAtlas, EPD, FAO-1968 und den Kalender-/Foto-Beständen einen einzigen, ständig wachsenden Datensatz machen, dessen Fortschritt die 13-Zeilen-Coverage-Tabelle *misst* — bis in jeder Zeile keine Zelle mehr „nie gesucht" ist.

**Orca Multi-Agent Ecosystem & Resource Status (2026-09-21):**
- **Orca Workspace:** Die Ausführung erfolgt über [Stably Orca](https://github.com/stablyai/orca).
- **Antigravity (Gemini 3.6 Flash): ACTIVE & PRIMARY** — Steuert die aktuelle TDD-Implementierung, Core Engine, Contracts, Python Code & Test-Execution.
- **Claude Hermes (OpenRouter / Qwen & Gemma lokal): ACTIVE** — Für autonome Hintergrund-Harvesting-Loops und Long-Running Tasks.
- **Laya (`model@laya-v1`) / Jev (`model@jev-v1`): ACTIVE (lokal/cached)** — Taxonomie-Matching & Triage-Scores.
- **Claude (Anthropic API): PAUSED** (Wöchentliches Nutzungslimit erreicht, Reset: Do 24. Sep 05:00 Uhr).
- **Codex (OpenAI API): PAUSED** (5-Stunden Limit erreicht, Reset: 01:00 Uhr nachts).

**Architecture:** Drei Schichten mit je einer Wahrheit. (1) *Ledger* (Git): kuratierte Claims, Registry, **Identitätsentscheidungen** (`product → species`). (2) *Bulk-Store* (`data/build/unified.duckdb`): Claims aus den Rohdaten, deterministisch aus Rohdatei-Hash + Parser + Entscheidungen erzeugt, nie von Hand editiert. (3) *Coverage-Engine*: berechnet die Tabelle aus (1)+(2)+Pool. Claims hängen am **Produkt** (dem Quell-Datensatz); die Art hängt nur über eine freigegebene Kante daran, per Join beim Lesen. Eine Freigabe hebt die Species-Abdeckung sofort, ohne Re-Ingest.

**Tech Stack:** Python 3.12, DuckDB (vorhanden), PyYAML, pytest. Keine neuen Abhängigkeiten (kein pyarrow/pandas; Parquet-Export geht mit DuckDB `COPY`).

**Spec:** `docs/handoff/2026-09-21-claude-plan-handover.md`, `docs/superpowers/specs/2026-09-21-database-and-pipeline-plan.md`, `docs/superpowers/specs/2026-09-21-unified-database-and-site-system.md` (alle im `main`-Checkout).

---

## Global Constraints & Orca Multi-Agent Protocol

- **Ehrlichkeitsprinzipien bleiben:** Chips nur für echte Claims; Matrixzelle `0` = gesucht, nichts akzeptiert, `–` = nie gesucht; übernommene Werte immer rejected/unresolved; kein Ranking über verschiedene Quellen; keine erfundenen Bilder; **Kandidat ≠ Claim**.
- **Die zehn Regeln (`product.md` §3) dürfen angepasst werden** — jede Änderung steht in §1a, hat einen Test und braucht deine Freigabe (§2).
- **Jeder Bulk-Claim läuft durch `atlas.contract.check`.** Es gibt keinen zweiten Validierungspfad.
- **Schreibbereiche:** `src/atlas/unified/**`, `src/atlas/ingest/bulk/**`, `src/atlas/site/**`, `src/atlas/db.py`, Tests. `src/atlas/cli.py` wird nur **erweitert**. **Nicht anfassen:** `src/atlas/build.py`, `src/atlas/research/**`, Inhalte von `data/**` — außer den in „Freigaben" genannten Pfaden und Pipeline-Outputs unter `data/research/proposals/`.
- **Tests:** `PYTHONPATH=src .venv/bin/python -m pytest -q` — die volle Suite hat auf `main` **346 Tests in 7 Minuten**; während eines Tasks nur die Task-Tests, die volle Suite einmal am Ende (im Hintergrund).
- **Modelle (Laya, Jev, Hermes-Modelle, Antigravity, Codex, jedes LLM) schlagen vor;** der deterministische Contract entscheidet; Identitäten und Regeln gibt ein Mensch frei (Regel 13, §1a). Kein Modell-Score ist ein Claim-Wert oder ein Kantengewicht.
- **Jeder Ausführer in Orca arbeitet in einem eigenen Git-Worktree** (`.claude/worktrees/`), nie im Hauptcheckout (Task 0, §6b).
- **Zahlen im Plan** sind am 2026-09-21 auf den lokalen Beständen gemessen, nicht geschätzt.

---

## 0. Was die Tabelle wirklich misst (vor dem Bauen klären)

Beim Nachmessen fielen fünf Dinge auf, die den Plan bestimmen:

1. **Die Prozentwerte mischen Achsen.** „Nutrients 57,9 %" ist `15.402 Produkt-Datensätze / 26.591 Species`. Der Matcher hat heute 1.385 Produkte auf **108 verschiedene Species** abgebildet (0,4 % des Pools). „Molecules 38,6 %" sind 10.270 FoodAtlas-*Entitäten*, keine Species.
2. **FoodAtlas-Lebensmittel haben keine Artnamen.** Alle 10.270 `food`-Entitäten haben leeres `scientific_name` und keine NCBI-ID; nur FoodOn-IDs (10.246) und 264 FDC-IDs. Über Name/Synonym treffen nur 132 Pool-Binomials exakt. Die Species-Zuordnung ist also *eigene Identitätsarbeit* (Brücken: FDC-ID → FDC-Kante, FoodOn → NCBITaxon). Laya (`model@laya-v1`) generiert dafür strukturierte Matching-Vorschläge.
3. **`data/build/` und `data/research/` sind gitignored.** Der Species-Pool (26.591) und die Matcher-Vorschläge sind nicht versioniert. Freigegebene Entscheidungen müssen an einen getrackten Ort (`data/registry/identity/edges.jsonl`).
4. **Die 33 Ledger-Knoten sind nur zwei Arten.** 15 Knoten gehören zu *Malus domestica*, 18 zu *Brassica oleracea* (Kohl, Brokkoli, Blumenkohl … als Convars). Auf der Species-Achse tragen heute **2 von 26.591 Arten** kuratierte Claims (0,0075 %); der Matcher hat 108 weitere vorgeschlagen. „~0,4 % Abdeckung" in der Tabelle ist ein Produkt-Wert, kein Species-Wert.
5. **1,8 Mio. Claims passen nicht durch `atlas.json`.** `build()` sammelt Claims als Python-Liste ins JSON-Payload (heute 4 MB). Bulk-Claims brauchen einen eigenen, gestreamten Pfad über `unified.duckdb`. Das Ledger bleibt die Wahrheit für *Entscheidungen*, nicht für 1,8 Mio. abgeleitete Zeilen.

Konsequenz: **Welle 0 macht die Tabelle ehrlich** (eine Achse je Zeile, Produkt-Achse separat, Claims als absolute Zahl), bevor irgendetwas ingestet wird. Ehrlicher Ausgangsstand — Dry-Run der Task-3-Module auf den echten Daten vom 2026-09-21:

| Zeile | Achse | Nenner | Claims | Kontext | gesucht/leer | nie gesucht |
|:--|:--|--:|--:|--:|--:|--:|
| Species identity | Species | 26.591 | 1 ¹ | 100,0 % | 0 % | 0 |
| Common names | Species | 26.591 | 0 | 55,8 % | 39,8 % | 1.171 |
| Food hierarchy | **Produkt** | 15.402 | 0 | – | – | 15.402 |
| Nutrients | Species | 26.591 | **2** | – | – | 26.589 |
| Molecules | Species | 26.591 | **2** | – | – | 26.589 |
| Bioactivity | Species | 26.591 | 0 | – | – | 26.591 |
| Seasonality | Species | 26.591 | **2** | – | – | 26.589 |
| Distribution | Species | 26.591 | 0 | 94,0 % | 0 % | 1.590 |
| Growing | Species | 26.591 | 0 | – | – | 26.591 |
| Edible parts | Species | 26.591 | 0 | 87,9 % | 6,1 % | 1.590 |
| Varieties, Photos, Evidence chain | Species | 26.591 | 0 | – | – | 26.591 |

Common names, Distribution und Edible parts stimmen mit der Ausgangstabelle überein (55,8 / 94,0 / 87,9 %). ¹ *Species identity* zählt nur Arten mit eigenem Artebene-`taxon_food` (Apfel); *Brassica oleracea* hat nur Convar-Knoten und zählt daher bei Nutrients/Molecules/Seasonality, aber nicht bei Identity — das ist die bestehende Regel aus `_library_species`.

---

## 1. Entscheidungen (Antworten auf die Plan-Fragen des Handovers)

**„Geschlossen" heißt: keine Zelle `unsearched`, nicht 100 % gefüllt.** Jede (Species × Feld)-Zelle ist `filled` (Claim), `context` (unverifizierter Kontext, kein Claim), `searched_empty` (gesucht, nichts akzeptiert → Matrix `0`), `not_applicable` oder `unsearched` (→ Matrix `–`). Cultivars werden nie 100 % gefüllt; sie sind geschlossen, wenn jede Species gegen Mansfeld/Khoury geprüft wurde. Das ist messbar und zwingt nicht zum Raten.

**Ingest-Reihenfolge:** EPD-Kontext (W1) → **FDC** (W2) → **BLS** (W3) → **FoodAtlas** (W4) → Kleintabellen (W5) → Tiefe (W6) → Abschluss (W7).
- FDC vor BLS: Foundation/SR Legacy tragen Derivation-Codes und min/max/n (Tier 1), die Parser-Zuordnung steht, und der Matcher ist auf englischen Namen am stärksten. Die 8.262 Produkte prüfen Speicher-Performance und Review-Ablauf, bevor die 985k BLS-Zellen kommen. BLS-Datensätze tragen zusätzlich einen englischen Namen (`Food name`), den der Matcher mitnutzen kann.
- FoodAtlas zuletzt der drei großen: Laya liefert Vor-Zuordnungen, die erst über FDC-IDs und FoodOn/NCBITaxon-Kanten freigegeben werden.

**Node-IDs:**
- Art: `org:<slug>` (Slug = `species_slug`, identisch zur Seiten-URL). Ledger-Knoten `food:<slug>` bleiben nur für **kuratierte** Einträge. Die übrigen ~26k Pool-Arten bekommen **keine** YAML-Dateien; ihre Seiten kommen aus dem Bulk-Store.
- Produkt: `prod:<quelle>:<record>` (`fdcf`, `fdcs`, `bls`), z. B. `prod:bls:B100000`.
- Kante: `Edge(product, species, method, confidence, batch, approved_by, approved_at, status)`.

**Identitäts-Freigabe:** Die decision unit ist der **Cluster** (Art × Quelle × Match-Klasse), nicht das Einzelprodukt. 1.385 Vorschläge = 108 Arten ≈ 200 Cluster. `exact_binomial ≥ 0,95` ist im Blatt vorausgefüllt (`approve`), aber überschreibbar. Review-Blatt: CSV mit `decision` ∈ `approve | reject | other:<binomial>`. Leer = unentschieden, `reject` wird gespeichert und nie wieder vorgeschlagen.

**Speicher:** DuckDB-Datei `data/build/unified.duckdb` (Tabellen `datapoints`, `rejects`, `product_species`). Jeder Lauf ersetzt genau eine Quelle (`replace_source`) → idempotent. Release-Export als Parquet per DuckDB `COPY … TO`.

**Orca Multi-Agent Workflow:**
- **Laya (`model@laya-v1`)** schlägt Taxonomie-Zuordnungen und Ontology-Brücken vor.
- **Jev (`model@jev-v1`)** bewertet Evidenzsicherheit und schlägt Lücken-Prioritäten vor.
- **Antigravity / Codex / Hermes** bauen Pipeline, CLI, Store und führen TDD-Tasks aus.
- Alle Modell-Outputs werden in `data/research/proposals/*.json` mit Hash gecacht und über `contract.py` strikt validiert.

---

## 1a. Die zehn Regeln auf dem Prüfstand

| # | Regel | Skaliert? | Vorschlag | Wann |
|:-:|:--|:--|:--|:--|
| 1 | Jeder Wert ist ein Claim-Objekt | ja | unverändert; `subject` darf eine Produkt-ID `prod:…` sein | – |
| 2 | `src` steht in der Registry | ja | unverändert; ein Eintrag je Datensatz-*Version* | – |
| 3 | Scope wird erzwungen | ja | unverändert | – |
| 4 | Keine kaputten Links (Tier 1–3) | ja | unverändert; Prüfung je Quelle, nicht je Claim | – |
| 5 | Tier 5 ist Quarantäne | offen | behalten. BLS-Zellen mit Herkunft `-` werden zu `unverified` | W3 |
| 6 | Keine Menge ohne Basis + Teil | **bricht** | siehe **6′** unten (Produkt-Datensätze deklarieren `as_described` / `product`) | Task 6 |
| 7 | Vorhersagen nie als Messung | ja | unverändert; Modelle erzeugen nur Vorschläge/Tier 4 | – |
| 8 | Bioaktivität ist Evidenz | teilweise | Jev-Triage priorisiert; Contract validiert strukturiert | W4 |
| 9 | Lizenz-Tor | ja, mit Lücke | **9b** Kontext-Schicht braucht eigene Regel | W1 |
| 10 | Nur Primärbelege | ja | **10′** verified_in_source für Sciverse-Extracts | W6 |
| 11 | **neu:** Identitäts-Tor | – | Ein Claim hängt an einer Quell-Produkt-ID. Art-Zuordnung nur über freigegebene Kante | Task 1 |
| 12 | **neu:** Ratchet + Schließung | – | `atlas coverage --check` verbietet Rückschritt | Task 4 |
| 13 | **neu:** Modell-Ausgaben sind Vorschläge | – | Jede modellerzeugte Ausgabe (Laya-Verdikt, Jev-Score, LLM-Übersetzung, Codex-Entwurf) trägt `model@version`, Hash und Konfidenz. Keinerlei automatisches Freigeben | Task 2, W6 |
| 14 | **neu:** Community-Gate für Traditionswissen | – | CARE-Prinzipien / Nagoya-Protokoll beachten | Vor TK-Ingest |

---

## 2. Freigaben, die vor Welle 2 gebraucht werden

1. **Getrackter Ort für Entscheidungen:** `data/registry/identity/edges.jsonl`
2. **Pool versionieren:** `data/registry/species.jsonl`
3. **Baseline:** `docs/coverage/baseline.json`
4. **Regeländerungen aus §1a:** 6′, 9b, 10′, 11, 12, 13, 14.
5. **Symbolbilder der 33 Knoten löschen:** Task 7.

---

## 3. Wellen-Roadmap

| Welle | Zeilen der Tabelle | Quelle | Ausführer in Orca | Exit-Kriterium |
|:--|:--|:--|:--|:--|
| **W0** | alle 13 messbar | – | Antigravity, Codex, Hermes, Laya, Jev | Baseline committed; Ratchet grün; Tasks 0–8 erledigt |
| W1 | Distribution, Growing, Edible parts, Photos, Common names | EPD-ZIM, `manifest.jsonl` | Antigravity + Hermes Cron | Ländercodes normiert; Photos geerntet |
| W2 | Nutrients, Food hierarchy | FDC Foundation + SR Legacy | Codex + Antigravity | Paritätstest grün; Nutrients ≥ 108 Arten |
| W3 | Nutrients (Tiefe), Common names (DE) | BLS 4.0 | Hermes Cron + Antigravity | 985k Zellen im Store; DE-Namen live |
| W4 | Molecules, Bioactivity | FoodAtlas v4.11 | Laya (Matching) + Jev (Triage) + Antigravity | FoodOn/NCBITaxon-Kanten freigegeben |
| W5 | Seasonality, Varieties, Growing | Saisonkalender, Mansfeld, ECOCROP | Hermes Cron + Codex | Jede Art geprüft |
| W6 | Molecules/Bioactivity Tiefe | Sciverse-Loop, Gap-Pipeline | Jev (Gap Prioritization) + Antigravity | verified_in_source verifiziert |
| W7 | Evidence chain | Audit-Hash-Schicht | Antigravity + Hermes | Alle 13 Zeilen `closed` |

---

## 4. Dateistruktur (Welle 0)

| Datei | Verantwortung |
|:--|:--|
| `src/atlas/unified/__init__.py` | Paket |
| `src/atlas/unified/identity.py` | Node-IDs, `Edge`, Review-Blatt, Freigabe, Validierung, `resolver` |
| `src/atlas/unified/store.py` | DuckDB-Store, `replace_source` (Contract-Stream), Kanten-Join |
| `src/atlas/unified/cells.py` | Zellzustände, `RowStats`, `aggregate` |
| `src/atlas/unified/fields.py` | die 13 Zeilen + Achse + „Gap"-Text |
| `src/atlas/unified/collectors.py` | ein Kollektor je Zeile, `Universe`, `load_universe` |
| `src/atlas/unified/table.py` | Tabelle bauen, rendern, Ratchet |
| `src/atlas/unified/cli.py` | `atlas coverage [--check] [--write-baseline]` |
| `src/atlas/cli.py` | **3 Zeilen** Verdrahtung |
| `tests/test_unified_{identity,store,coverage,cli_wiring}.py` | Tests |
| `docs/coverage/baseline.json` | getrackte Baseline (Ratchet) |
| `src/atlas/claims.py`, `src/atlas/contract.py` | Regel 6′ (Task 6) |
| `tests/test_contract_product.py` | Regel 6′ |
| `tools/plan_tasks.py`, `tests/test_plan_tasks.py` | Orca Task Brief Splitter & Diff Guard (Task 8) |
| `data/images/*.jpg`, `data/registry/images.yaml`, `src/atlas/site/images.py` | Symbolbilder entfernen (Task 7) |

---

### Task 0: Orca Worktree-Setup

- [ ] **Step 1: Worktree in Orca anlegen**
```bash
git worktree add .claude/worktrees/unified-dataset -b unified-dataset main
```

- [ ] **Step 2: Daten und venv verknüpfen**
```bash
cd .claude/worktrees/unified-dataset
MAIN="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
mkdir -p data/build data/research
cp -Rc "$MAIN/data/raw/." data/raw/
cp -Rc "$MAIN/data/research/." data/research/
cp -c "$MAIN/data/build/atlas.json" data/build/
ln -s "$MAIN/.venv" .venv
echo '.venv' >> "$(git rev-parse --git-path info/exclude)"
export PYTHONPATH=src
```

- [ ] **Step 3: Import-Pfad verifizieren**
```bash
PYTHONPATH=src .venv/bin/python -c "import atlas; print(atlas.__file__)"
```

- [ ] **Step 4: Test-Basis prüfen**
```bash
PYTHONPATH=src .venv/bin/python -m pytest -q -k "not test_real_data"
```

---

### Task 1: Identität — Kanten, Cluster, Review-Blatt

**Files:**
- Create: `src/atlas/unified/__init__.py`
- Create: `src/atlas/unified/identity.py`
- Test: `tests/test_unified_identity.py`

- [ ] **Step 1: Failing test schreiben** (`tests/test_unified_identity.py`)
- [ ] **Step 2: Test fehlschlagen sehen** (`.venv/bin/python -m pytest tests/test_unified_identity.py`)
- [ ] **Step 3: Implementierung** (`src/atlas/unified/identity.py`)
- [ ] **Step 4: Test grün sehen**
- [ ] **Step 5: Git Commit** (`git commit -m "feat(unified): identity edges and cluster review sheet"`)

---

### Task 2: Bulk-Store — DuckDB, Contract-Stream, Kanten-Join

**Files:**
- Create: `src/atlas/unified/store.py`
- Test: `tests/test_unified_store.py`

- [ ] **Step 1: Failing test schreiben** (`tests/test_unified_store.py`)
- [ ] **Step 2: Test fehlschlagen sehen**
- [ ] **Step 3: Implementierung** (`src/atlas/unified/store.py`)
- [ ] **Step 4: Test grün sehen**
- [ ] **Step 5: Git Commit** (`git commit -m "feat(unified): duckdb bulk store with contract stream"`)

---

### Task 3: Coverage Engine — 13 Zeilen & Kollektoren

**Files:**
- Create: `src/atlas/unified/cells.py`, `fields.py`, `collectors.py`, `table.py`
- Test: `tests/test_unified_coverage.py`

- [ ] **Step 1: Failing test schreiben** (`tests/test_unified_coverage.py`)
- [ ] **Step 2: Test fehlschlagen sehen**
- [ ] **Step 3: Implementierung**
- [ ] **Step 4: Test grün sehen**
- [ ] **Step 5: Git Commit** (`git commit -m "feat(unified): coverage engine and collectors"`)

---

### Task 4: CLI — `atlas coverage` und Ratchet

**Files:**
- Create: `src/atlas/unified/cli.py`
- Test: `tests/test_unified_coverage.py` (CLI tests)

- [ ] **Step 1: Failing CLI test ausführen**
- [ ] **Step 2: Implementierung** (`src/atlas/unified/cli.py`)
- [ ] **Step 3: Test grün sehen**
- [ ] **Step 4: Git Commit** (`git commit -m "feat(unified): atlas coverage command and ratchet"`)

---

### Task 5: CLI Verdrahtung & Echte Baseline

**Files:**
- Modify: `src/atlas/cli.py`
- Create: `docs/coverage/baseline.json`
- Test: `tests/test_unified_cli_wiring.py`

- [ ] **Step 1: Wiring test schreiben & fehlschlagen sehen**
- [ ] **Step 2: `src/atlas/cli.py` erweitern**
- [ ] **Step 3: Echte Baseline schreiben:** `.venv/bin/atlas coverage --write-baseline`
- [ ] **Step 4: Ratchet prüfen:** `.venv/bin/atlas coverage --check`
- [ ] **Step 5: Git Commit** (`git commit -m "feat(unified): wire atlas coverage command and commit baseline"`)

---

### Task 6: Regel 6′ — Produktdatensätze im Contract [HUMAN GATE]

**Files:**
- Modify: `src/atlas/claims.py`
- Modify: `src/atlas/contract.py`
- Modify: `product.md`
- Test: `tests/test_contract_product.py`

- [ ] **Step 1: Test schreiben & fehlschlagen sehen**
- [ ] **Step 2: `claims.py` und `contract.py` erweitern** (Support für `as_described` / `product`)
- [ ] **Step 3: `product.md` Regel 6 aktualisieren**
- [ ] **Step 4: Tests prüfen & committen** (`git commit -m "feat(contract): rule 6' for product records"`)

---

### Task 7: Symbolbilder der 33 Knoten entfernen [HUMAN GATE]

**Files:**
- Delete: `data/images/*.jpg`
- Modify: `data/registry/images.yaml` (Tombstones eintragen)
- Modify: `src/atlas/site/images.py`
- Modify: `tests/test_images.py`, `tests/test_site_workbench.py`

- [ ] **Step 1: Tests aktualisieren & fehlschlagen sehen**
- [ ] **Step 2: `images.yaml` grabsteinen & Fotos per `git rm` löschen**
- [ ] **Step 3: `images.py` anpassen**
- [ ] **Step 4: Site-Build testen:** `.venv/bin/atlas site --fast`
- [ ] **Step 5: Git Commit** (`git commit -m "chore(images): tombstone symbolic node images"`)

---

### Task 8: Orca Multi-Agent Task Harness (`tools/plan_tasks.py`)

**Files:**
- Create: `tools/plan_tasks.py`
- Test: `tests/test_plan_tasks.py`

- [ ] **Step 1: Failing test schreiben** (`tests/test_plan_tasks.py`)
- [ ] **Step 2: `plan_tasks.py` implementieren** (`split` & `guard` Kommandos)
- [ ] **Step 3: Test grün sehen**
- [ ] **Step 4: Task Briefs splitten:** `python3 tools/plan_tasks.py split docs/superpowers/plans/2026-09-21-unified-dataset.md data/build/plan-briefs`
- [ ] **Step 5: Diff Guard verifizieren:** `python3 tools/plan_tasks.py guard data/build/plan-briefs/01-*.md`
- [ ] **Step 6: Git Commit** (`git commit -m "feat(tools): Orca multi-agent plan task harness and diff guard"`)

---

## 6. Multi-Agent Orchestration & Model Role Matrix (Orca Setup)

| Agent / Model | Orca Role | Primary Responsibility | Input Artifacts | Output Artifacts |
|:---|:---|:---|:---|:---|
| **Antigravity** | Lead Developer & Architect | Engine implementation, contract enforcement, TDD core | Plan briefs, pytest outputs | Python modules, pytest suites, Git commits |
| **Claude Hermes** | Async Cron Engine & Ingest | Background ingest runs, raw file fetching, harvest loops | Raw source files, cron triggers | Ingest logs, raw duckdb tables |
| **Codex** | Code & Test Synthesizer | Fast boilerplate, helper parser functions, unit tests | Brief specs, file interfaces | Helper modules, test fixtures |
| **Laya (`model@laya-v1`)** | Taxonomy Matcher | Proposals for FoodOn <-> NCBI <-> Binomial matching | Unmapped raw names | `data/research/proposals/laya_*.json` |
| **Jev (`model@jev-v1`)** | Triage & Evidence Scorer | Bioactivity triage, gap priority scoring | Raw extract triples | `data/research/proposals/jev_*.json` |

Jedes Orca-Modell arbeitet streng isoliert. Vorschläge von Laya und Jev fließen niemals direkt in Claims oder Matrizen, sondern verbleiben als gecachte Vorschläge (`model@version`, `input_hash`), die deterministisch von `contract.py` geprüft und von menschlichen Reviewern per `edges.jsonl` freigegeben werden.
