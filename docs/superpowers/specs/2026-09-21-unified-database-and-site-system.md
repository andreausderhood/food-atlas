# Unified Database & Website — System-Spezifikation

**Stand:** 2026-09-21 · Ergänzt `2026-09-21-database-and-pipeline-plan.md`.
Zwei Fragen, eine Antwort: **Wie fließen alle genannten Datenbanken in eine
unified database?** und **Welches System braucht die Website auf dem
Stitch-Design-System?** Beides ist ein System: die DB ist das Inhaltsmodell der
Screens, die Screens sind die Leseebene der DB.

---

## 1. Quellen-Matrix — was wir haben und wie es einfließt

| Quelle | Inhalt | Volumen | Lizenz | Integrationsweg | Claim-Tier |
|---|---|---|---|---|---|
| **FDC Foundation/SR Legacy** (CSV) | Nährwerte pro 100 g, Derivation-Codes | ~7k foods relevant | Public domain (US-Gov) → `ship` | fertiger Ingest `ingest/fdc.py` | 1–2 (analytical/calculated) |
| **BLS 4.0** | DE-Nährwerte | ship | fertiger Ingest `ingest/bls.py` | 1 |
| **FoodAtlas v4.11** (Parquet-Bundle) | Moleküle/Claims, attestiert | 543k Triplets | `ship` (CC BY 4.0, CU) | fertiger Ingest, propose-only | 3 (extracted) |
| **FAO Africa 1968** (x6877e, geparst) | Messwerte 17 Nährstoffe, 1.093 Items, 560 Species | parsed.json | US-HEW Co-Publikation → PD + FAO-Attribution → `ship` (A1-Verifikation offen) | Ingest steht (`ingest/fao_africa.py`) | 3 → kuratiert 2 |
| **EPD-ZIM** (Edible Plant Database, 9 GB Kiwix) | 25.001 Species: Edible Parts, Distribution/Länder, Growing, Medicinal, 70.677 Fotos | species-epd.yaml | FPI+PFAF-Anteil `unknown` (nur Discovery-Nutzung), iNaturalist-Fotos CC BY-NC → `adapter` | Extractor `tools/scope_epd_zim.py` → Enrichment-Layer, kein Mess-Claim | — (Discovery + Season/Geography-Rohlage) |
| **Wikipedia-Species-Pool** | 2.322 Binomials, kulinarische Zuordnung | species-candidates.yaml | CC BY-SA → `separate` (Listenstruktur, keine Textübernahme; Binomials sind Daten) | Pool-Member | — |
| **Sciverse** (API, Token in .env) | Primärliteratur: Messungen mit Zitat, Basis, Methode, Lizenz | 75+ closed candidates, wachsend | je Paper klassifiziert (16 ship / 13 adapter / 70 unknown) | Harvest-Pipeline `research/sciverse/`, propose-only | 1 (wenn analytical + ship) |
| **Food Plants International** (WebDirect) | 35.103 Pflanzen, Usage/Distribution | WebDirect, kein API | `unknown` → kein Import; EPD-ZIM ist der funktionale Ersatz | A0 abgeschlossen via EPD | — |
| **Seasonal Food Guide / BZFE-Saisonkalender** | DE-Saisonfenster |Registry-Cite| fertige Registry-Entries | 2 |

**Regel (rule 9, unverändert):** Jede Quelle vor dem ersten Claim-Import als
`SRC-*`-Registry-Entry mit gelesenem Lizenztext. `unknown` importiert nie.
EPD-Enrichment (Distribution, Edible Parts) läuft als **Gap-Setting** und
**Kontext**, nicht als Messwert-Claim.

---

## 2. Das Datenmodell der unified database

Die DB bleibt **dateibasiert + Git-Ledger** (diffbar, auditierbar) und wird
**deterministisch zu SQLite kompiliert** (`atlas db build` → `atlas.db`,
FTS5) — das ist die Abfrage-Ebene der Website und Pipeline.

### Schichten

```
raw/            Original-Downloads (ZIM, Parquet, CSV) — nie editiert
registry/       foods.yaml · organisms.yaml · sources.yaml · aliases
curated/        kuratierte Claims je Lebensmittel (YAML, propose-only-Flow)
research/       Sciverse-Findings, Scopes, Harvest-Cache (git-ignored)
build/          atlas.json (kompiliert) + gaps.csv + site/
  └─ atlas.db   SQLite-Spiegel: foods × claims × gaps × sources (FTS5)
```

### Kern-Entities (SQLite-Schema, abgeleitet aus dem Claim-Modell)

- `species` (binomial PK, family, common_names JSON, pool_priority, sources JSON)
- `foods` (node_id PK, species→FK, part, level, name_de/en, foodon, fdc_match)
- `claims` (subject→food FK, group, field, value, unit, basis, food_part,
  derivation, tier, src→sources FK, ref, quote, verified_at)
- `gaps` (subject, field, rule, question, would_be_settled_by, status:
  `unsearched` | `searched_empty` | `partial`)
- `sources` (registry 1:1: license_class, license_read, attribution)
- `evidence_links` (claim → sciverse doc_id/doi, EPD path, FAO item_no)

### Der Ingest-Vertrag je Quelle

Jede neue Quelle braucht **vier Dinge**, bevor sie in die DB darf:
1. Registry-Entry mit `license_class` + `license_read: true`
2. Parser unter `src/atlas/ingest/<source>.py` mit Offline-Tests
3. Mapping ins Claim-Schema (unit/basis/food_part/derivation) ohne Inferenz —
   Fehlende Felder werden Gaps, keine Annahmen
4. Propose-only-Kuration: numerische Claims erreichen die gebaute DB nur über
   den Approval-Flow (Research-Loop, fenced leases)

---

## 3. Das Website-System — Design-System ↔ Datenbindungen

Die Website ist der statische Renderer (`atlas site`), der aus `atlas.json`
baut — jetzt auf dem Stitch-Design-System. Die vier Mockups werden Templates:

| Stitch-Mockup | Template | Datenbindung (aus atlas.db/atlas.json) |
|---|---|---|
| `food_explorer_atlas_landscape` | `index.html.j2` (umbau) | species-pool + foods + Coverage-Badges (`not_yet_searched` aus gaps) |
| `food_workbench_zingiber_officinale` | `food.html.j2` (umbau) | 3-Spalten-Dossier-Rail: Identität (species/organism) · Claims je Epistemik · organeleptische Chemie; 9 Spalten: System-Lanes (biomedical / TCM / Ayurveda / indigenous / modern) |
| `multi_food_cross_system_matrix` | `compare.html.j2` (umbau) | Cross-System-Tally-Matrix: Rows = Effekt-Begriffe, Cols = Wissenssysteme, Cells = Claim-Counts aus der DB |
| `claim_ledger_gap_register` | `gaps.html.j2` (umbau) | gaps.csv + evidence_links: Status-Badges `searched_empty` (#A39E93) vs `not_yet_searched` (#D4CEBF) |

### Design-Token-Implementierung

`_style.css.j2` bekommt die CSS-Variablen direkt aus dem DESIGN.md-Frontmatter
(Parchment `#FBF9F5`/Linen `#F4F1EA`, Obsidian `#1A211E`, die 5 Epistemik-
Farben, Status-Grau) — Tokens, keine Deko. Typo-Trio mit festen Rollen:
Newsreader (Titel, Taxa, Zitate, kursiv = Botanisch), Public Sans (UI, Filter,
Matrizen, tabular figures), JetBrains Mono (Badges, DOIs, `tnum`-Zahlen).
Komponenten-CSS für: Evidence-Badge (Mono-Chip 1px-Border in Epistemik-Farbe),
Claim-Ribbon (1px `#DDD7CD`, Parchment, Attribution-Footer), Tally-Matrix
(strukturelle Quadrate, `0` in `#A39E93`, `-` in `#D4CEBF`), Lens-Switcher,
Explainer-Banner (3px-Sage-Akzent). Elevation: tonal stepping + 1px-Borders,
keine Schatten (außer Drawer-Lift).

### Rendering-Vertrag

- „Attribute, don't assert": Jede Zahl auf der Website trägt `src`-Badge mit
  Registry-Link; Zitate als Newsreader-Italic mit Mono-Citation. Keine
  synthesized conclusions zwischen Epistemiken.
- Mehrsprachigkeit: EN-First (Korpus-Sprache), DE-Namen aus `names_de`.
- Statisch, aus `atlas.db` kompiliert — gleiche Pipeline wie heute, nur mit
  Design-System-Templates + Species-Auswahl aus dem Pool.

---

## 4. Wie wir an die Daten kommen (Sammel-System)

**Stufe 1 — vorhanden:** FDC + BLS + FoodAtlas + FAO-1968 (alle 4 geparst,
Ingests getestet) → ~5.6k kuratierte + ~1.093 FAO-Claims vorbereiten.

**Stufe 2 — Kuration (laufen bereits):** Sciverse-Harvest nächtlich per Cron
(`research sciverse --execute`, Cache gratis), Rule-9-Triage schließt
Lizenzen, Approval-Flow promoviert Kandidaten zu Claims. Budget: 2 Calls/Gap.

**Stufe 3 — Onboarding-Maschine (zu bauen):**
`atlas onboard '<binomial>'` → schlägt species-pool nach, erzeugt Food-Node +
Registry-Links + Gap-Slots (`not_yet_searched`) aus dem EPD/FAO-Enrichment,
merkt Species für den Sciverse-Queue. Damit werden 544 P1- → dann P3-Species
rollierend onboarded. Jede Species kommt **nur** über diesen Weg in die DB —
kein Bulk-Import von cite/unknown-Quellen.

**Stufe 4 — Season/Geography:** EPD-Distribution + Growing als Gap-Rohlage,
Sciverse-§8-Prompts füllen die verifizierten Fenster; EPD-Felder werden nur
als `not_yet_verified`-Kontext angezeigt, nie als Claim.

---

## 5. Baureihenfolge

1. **DB-Kern:** `atlas db build` (SQLite-Spiegel) + `atlas onboard` (Phase B)
2. **FAO-Claims:** 1.093 Items über propose-only kuratieren (Phase A1)
3. **Harvest-Cron:** nächtlich, Diff-Report statt Rohdaten (Phase C)
4. **Site-Neubau auf Stitch-Tokens:** 4 Templates umbauen (Phase D), Mockups
   als Referenz-Screenshots neben den gerenderten Seiten zum Pixel-Vergleich
5. **Matrize/Workbench ab DB:** Cross-System-Tally + Bridge-Lanes erst, wenn
   TCM/Ayurveda-Quellen onboards sind (offen im Plan — Datenbasis fehlt noch)
