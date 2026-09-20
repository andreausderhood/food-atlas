# Food Atlas — Database & Pipeline Plan

**Stand:** 2026-09-21 · **Ziel:** Erst die Datenbasis erschließen, daraus die
dauerhaft erweiterte Atlas-Datenbank bauen — die Stitch-Mockups unter
`stitch_design_system_architecture/` sind das Zielbild der Oberfläche, die
daraus gespeist wird.

---

## 0. Ausgangslage (was heute schon steht)

| Baustein | Status |
|---|---|
| Traceability-Contract (`product.md` §3), Claim-Modell, Registry | phase-1, propose-only, 275 Tests |
| Sciverse-Harvest (Literatur): Client + Gap-Pipeline + Lizenz-Triage | live; 75/322 Rule-6 closed, ~450 Calls, Cache |
| FDC-Import (Foundation + SR Legacy, Derivations-Codebook) | live, propose-only |
| BLS-Import | existiert (`ingest/bls.py`) |
| FoodAtlas-v4.11-Bundle (Extraction, propose-only) | live |
| **FAO Africa 1968 FCT** (neu) | geparst: 1.623 Items, 568 Species, 1.093 mit Werten — noch NICHT als Claims |
| **Wikipedia-Species-Pool** (neu) | 2.322 Binomials als Kandidatenliste |
| **FDC API** (neu) | Key in `.env`, verifiziert; FNDDS/Branded noch ungenutzt |
| Food_Plants_World (FileMaker) | blockiert (JS-App, kein HTTP-Zugriff) |
| Website (`atlas build` → `data/build/site`) | statisch, bestehendes Template |
| Stitch-Design-System + 4 Mockups | Design-Quelle, noch nicht implementiert |

---

## 1. Architektur-Entscheidung: eine Datenbank, drei Schichten

Die Atlas-Datenbank wird **dateibasiert und versioniert** bleiben (YAML/JSON +
Parquet im Repo, `data/`), nicht SQLite-Server. Grund: Traceability-Contract
verlangt auditierbare, diffbare Herkunft; Git ist das Ledger. Die drei
Schichten:

```
 raw/            Unveränderte Downloads (immutable, hashes in downloads.yaml)
   │
   ▼  ingest/ (Parser, deterministisch)
 research/            ← harvester output: Kandidaten mit Quotes, noch keine Claims
   │
   ▼  curate/ (propose-only Agenten + André als Freigabe)
 registry/            ← foods.yaml, organisms.yaml, sources.yaml, molecules.yaml …
 claims (curated/)    ← freigegebene Claims mit src, derivation, basis, quote
   │
   ▼  build (pydantic-Validierung, Gaps-Generierung)
 build/ atlas.json    ← die abgeleitete, servierbare Datenbank (Site + API)
```

Regeln, die bleiben: keine Zahl ohne Quelle/Basis/Quote; unknown statt geraten;
Lizenz-Klasse entscheidet Bulk-Import (nur `ship`) vs. Kuratierung (`cite`);
`adapter`/`separate` laufen nie in die gemeinsame DB.

**Neu als Persistenz-Ergänzung:** ein **SQLite-Spiegel** (`data/build/atlas.db`)
— rein abgeleitet (jederzeit aus den YAMLs neu baubar), als Index für
Abfragen (Species ↔ Foods ↔ Claims ↔ Sources) und als Arbeitstisch für die
Pipeline. Source of truth bleibt Git.

---

## A0 — Food Plants International (verifiziert 2026-09-21)

`fms.cmsvr.com/fmi/webd/Food_Plants_World` = **"Edible Plants of the World"**
(Food Plants International), FileMaker WebDirect, live:

- **35.103 Datensätze** — Pflanzen, die "somewhere recorded as being used as food"
- Felder (aus dem Sort-Dialog bestätigt): **Botanical Names, COUNTRIES,
  Distribution, EDIBLE PARTS, DESCRIPTION, REGIONS**
- Kein API, kein Bulk-Export; Bulk-Scraping über die WebDirect-UI ist
  unzuverlässig (Disclaimer/Sort-Gate) und lizenzrechtlich ungeklärt → **Rule 9:
  Klasse unknown bis Klärung, kein Import.**
- Rolle im System: **Funnel-Quelle** (Species-Discovery), keine Messquelle.
  Integrationsweg: (a) Anfrage an FPI für einen Datenexport/Partnership — die DB
  ist "work in progress", Kooperationen sind ihr Modell; (b) taxonomisches
  Rückgrat bis dahin aus Kew Plants of the World Online / World Flora Online;
  (c) die 35k-Botanical-Names-Liste als Discovery-Layer, sobald Lizenz geklärt.
---

## Phase A — Datenbasis konsolidieren

Ziel: Alle vier Quellen in **einem** einheitlichen Kandidaten-Format, mit
Herkunft und Lizenz je Zeile.

- **A1 — FAO-Africa-Ingest als Claims vorbereiten**: 1.093 Items →
  `data/curated/fao-africa-1968.yaml` (tier 3, derivation `literature_extraction`,
  basis `as_sold`/`fresh_weight` je Spalte klären, Refuse-Spalte mappen).
  Registry-Entry `SRC-FAO-AFRICA-1968` (license_class `ship` — zu verifizieren
  gegen FAO-ToU; FAO-Statistik-ToU erlaubt Nicht-Kommerzielles mit Attribution).
- **A2 — Species-Pool vereinen**: FAO-568 ∪ Wikipedia-2.322 →
  `data/research/scope/species-pool.yaml` mit Feldern
  `{binomial, common_names[], sources[], fao_item_nos[], in_atlas, priority, reason}`.
  Dedupe über canonicalisierte Binomials (×, Hybride, Synonyme via FAO-Index).
- **A3 — FDC-API-Ingest** (`ingest/fdc_api.py`): Survey-Foods (FNDDS) +
  Branded als **Ergänzungslayer**, explizit `dataTypes`-gefiltert; Provenance
  `fdcApi` getrennt vom bestehenden FDC-CSV-Import.
- **A4 — Lizenz-Register**: die 70 `unknown`-Dokumente aus der Sciverse-Triage
  am Venue nachlesen (5-Minuten-Checks, batch), damit jede Quelle eine Klasse
  hat, bevor sie Claims speist.

**Exit-Kriterium A:** `make scope-report` zeigt: N Species, davon n mit
≥1 messbaren Wert aus ≥1 Quelle, lizenziert, dedupliziert.

---

## 3. Phase B — Die Atlas-Datenbank (Woche 2)

Ziel: aus dem Kandidaten-Pool die **normale Datenbank** erschaffen, die das
Produkt speist — im bestehenden Registry-/Claims-Modell, nicht als Parallelbau.

- **B1 — Onboarding-Pipeline** (`atlas onboard <species>`): nimmt ein Binomial
  aus dem Pool, erzeugt Food-Node + Organism-Node + Registry-Einträge
  (names_de separat), matched FAO-Items + FDC-Matches automatisch, legt
  leere Claim-Slots + Gap-Einträge an (`status: not_yet_searched` — genau das
  Mockup-Feld aus dem Design-System).
- **B2 — SQLite-Spiegel** (`atlas db rebuild`): baut `atlas.db` aus
  registry+claims; FTS5-Index über Namen/Synonyme; dient Workbench-Queries.
- **B3 — Claim-Ingest aus FAO** über den bestehenden propose-Only-Flow
  (`research/queue` + approval): jede Zahl wird als Proposal mit Quote
  (Item-Zeile als Verbatim) eingereicht, André kuratiert in Batches.
- **B4 — Sciverse-Vertiefung pro neuem Food**: der bestehende
  Sciverse-Harvest wird pro Food-Node gefahren (rule 5+6) und füllt
  `closed_candidate` → kuratierbare Kandidaten. Budget-Deckel pro Food.

**Exit-Kriterium B:** 50 neue Species vollständig onboarded, je ≥5 Claims
freigegeben oder als Gap registriert; `atlas build` grün mit allen Quellen.

---

## 4. Phase C — Die ständige Pipeline (Woche 3+, dann dauerhaft)

Ziel: Erweiterung wird zum Betrieb, nicht zum Projekt.

- **C1 — Cron-Harvest** (Hermes cron, model_snapshot beachten):
  nächtlich `atlas research sciverse` über die offensten Gap-Klassen +
  wöchentlich ein Batch neuer Species aus dem Pool (Funnel §11).
- **C2 — Diff-Reports**: jede Pipeline-Ausführung erzeugt
  `data/research/reports/<date>.md` — neu geschlossene Gaps, neue DOIs,
  Lizenzänderungen. André liest Reports, nicht Rohdaten.
- **C3 — Re-Grading frei**: Extraktor-Verbesserungen laufen gegen den
  Response-Cache ohne API-Kosten (schon gebaut — beibehalten).
- **C4 — Quellen-Refresh**: FDC-Jahresrelease + FAO-Revisionen als
  Versionssprung in `downloads.yaml`, nie über bestehende Daten drüberbügeln.

---

## 5. Phase D — Website auf dem Design-System (Woche 3–4)

Ziel: Die vier Stitch-Screens als Templates des statischen Builders —
auf dem bestehenden `data/build/atlas.json`, nicht als separates Frontend.

| Mockup | Wird | Datenquelle |
|---|---|---|
| `food_explorer_atlas_landscape` | Landing/Index | foods.yaml + coverage |
| `food_workbench_zingiber_officinale` | Food-Detail (Dossier-Rail + Lanes) | claims + molecules + organisms |
| `multi_food_cross_system_matrix` | Vergleichsmatrix | claims cross-food |
| `claim_ledger_gap_register` | Ledger/Gaps-Register | gaps.csv + sources + claims |

Umsetzung: Jinja-Templates im bestehenden `site/build.py` (Newsreader +
Public Sans + JetBrains Mono, Parchment-Palette aus `DESIGN.md`,
Epistemic-Badges als CSS-Klassen). Kein Framework — die Mockups sind
HTML/CSS-orientiert und der Atlas bleibt statisch + schnell.

**Exit-Kriterium D:** Alle vier Screens mit echten Daten aus `atlas.db`
gerendert; Lighthouse ≥ 90; jede Zahl auf der Seite trägt Quote+Quelle.

---

## 6. Offene Punkte (bewusst nicht entschieden)

1. **Deutsch/Englisch** der Site-Oberfläche (names_de existiert schon).
2. **Claim-Schema für traditionelle Systeme** (TCM/Ayurveda-Lanes im
   Mockup): braucht eigene Claim-`group`s + Epistemic-Badges — Datengrundlage
   dafür existiert noch nicht (keine Quelle, keine Extraktion). Erst wenn
   Phase A–B stehen.
3. **User-Contributions** (Mockup zeigt "Contribute"-CTAs): später;
   erst wenn die Kuratier-Pipeline stabil läuft.
4. Food_Plants_World: manuell exportieren oder aufgeben.
