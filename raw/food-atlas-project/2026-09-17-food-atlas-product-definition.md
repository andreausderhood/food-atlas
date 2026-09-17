# Food Atlas — Product Definition (snapshot)

> Source: Project file `product.md` in the Food Atlas repository (snapshot of the file as of 2026-09-17)
> Collected: 2026-09-17
> Published: 2026-09-17

## Product Definition

**Status:** Draft 0.1, not yet approved. Nothing is built.
**Date:** 2026-09-17
**Lineage:** Victorinox Material & Technology Library. It uses the same traceability contract with a deeper model.
**Data in hand:** FoodAtlas bundle v4.11 (`data/raw/foodatlas/`) and Gupta et al. 2026 (`Resources/`)
**License:** Open source. Code is MIT (decided 2026-09-17). The license for our curated data is still open; see D7.

---

## 1. Vision

**A traceable atlas of edible life.** It covers every food from species down to variety, part and form, together with the molecules in it, the processes that transform it and the microbes that drive them. Every figure can be followed back to its source, and every unknown is named rather than hidden.

### Why it needs to exist

- **A nutrition label describes a food with about a dozen numbers. The chemistry is far larger.** Across 322 foods, Gupta et al. (2026) find 27,713 detected molecular features, and 44% of them occur in only one food. White rice groups with processed foods by chemistry, and xanthan gum groups with walnuts. Culinary labels are poor proxies for what a food *is*.
- **Each existing resource holds one slice.**
  - USDA FoodData Central: nutrition.
  - FoodAtlas: food–chemical–disease links.
  - GBIF: where species occur.
  - FAOSTAT: where food is produced.
  - None of them connects these slices at variety level, and none carries provenance on every value.
- **Most edible biodiversity is invisible.** 10–50 crops supply about 95% of calories (cited in Gupta et al.). The atlas makes the rest findable, for example anise hyssop and lemon balm, which the study ranks high for antioxidant evidence.

---

## 2. Who it serves and what they can ask

| User | Example question |
| :--- | :--- |
| Curious eater, designer, chef | *What is in season now that is red and crunchy?* *How does Honeycrisp differ from Granny Smith?* |
| Product developer, researcher | *Which foods contain quercetin, how much, and how sure are we?* *Which underused crops carry strong antioxidant evidence?* |
| Educator, storyteller | *Where did the apple come from, and where is it grown today?* |

The primary audience depends on decision **D5** (§9).

---

## 3. The traceability contract

This is inherited from Victorinox. Rules 1–5 carry over. Rules 6–10 are new, because food data fails in ways steel data does not.

1. **Every value is a claim object:** `{v, unit, basis, food_part, src, tier, method, derivation}`.
   - `derivation` records how a value was obtained: `analytical`, `calculated`, `imputed`, `borrowed`, `predicted` or `extracted`.
   - National tables publish such codes per value, and the tier follows from them.
2. **Every `src` resolves** to an entry in the source registry.
3. **Scope is enforced.** A source may only back the claim groups it `supports`. USDA nutrition data cannot back a season claim.
4. **No broken links.** A tier 1–3 claim may not cite a source whose link is broken.
5. **Tier 5 is quarantined.** `SRC-UNVERIFIED` backs tier-5 claims only, and tier 5 cites nothing else.
6. **No amount without a basis.** Every concentration declares:
   - its basis: fresh weight, dry weight or as sold;
   - the food part it refers to.

   An amount without a basis is not published. It becomes a gap.
7. **Predictions are never shown as measurements.** Model outputs carry the model name, its version and its confidence tier.
8. **Bioactivity is evidence, never a health claim.** The atlas says *"compound-level assay evidence associated with anti-inflammatory activity"*. It never says *"anti-inflammatory food"*.
9. **License gate.** Every source declares its license and whether the data may be redistributed. Only sources that allow open redistribution, including commercial reuse, can ship in the atlas. An unread license is a build failure, just like a broken link. Sources of class `cite` may back single curated facts (marked `curated`) but are never bulk-imported, and no text is copied from them.
10. **Primary evidence only.** A value must come from the cited work's own measurement, table or registry entry. A figure quoted in a paper's discussion from another study is second-hand: follow it to the primary source, or it becomes a gap. The case that prompted this rule is in §6, finding 2.

Values that fail these rules are removed and registered as named open questions, exactly as in Victorinox.

### Licensing (decided: open source, MIT)

MIT lets anyone reuse the atlas, including commercially. Everything the atlas **ships** must therefore allow that too, whatever the project's own intent. That splits sources into three groups:

| Class | Licenses | How the atlas uses them |
| :--- | :--- | :--- |
| **Ship** | Public domain, CC0, CC BY, Apache-2.0, MIT, UK OGL, open licences that allow commercial reuse | Imported, merged and redistributed. The attribution and NOTICE text of every source goes into `NOTICE.md` |
| **Cite** | Any readable publication | Single facts, entered by hand with a `ref`; no bulk import |
| **Adapter only** | CC BY-NC, access agreements, no-redistribution terms. Covers PTFI, FishBase, SeaLifeBase, CTD, FooDB, Phenol-Explorer and PROSEA, plus BioFoodComp until FAO confirms a license, and the FoodAtlas API | Not in the repository or the published data. The MIT code may include an optional loader, so users with their own access can plug the data in locally, as the Gupta et al. repo does with PTFI |
| **Keep separate** | Share-alike (ODbL, CC BY-SA) | Not merged into our database, because a merged database would inherit share-alike. Images can ship file by file with their own license and credit line |

The layers:
- **Code:** MIT.
- **Imported data:** keeps its upstream license, recorded per source in the registry.
- **Our curated data** (sensory, season, stories, gap register): license still to be decided (D7).
- **The published site:** shows each value's license next to its source chip.

### Evidence tiers

| Tier | Meaning | Examples |
| :---: | :--- | :--- |
| 1 | Analytical value with documented method and sample | USDA FDC Foundation Foods; national-table values coded *analytical*; PTFI (adapter only) |
| 2 | Registry or standard | FoodOn, NCBI Taxonomy, GBIF backbone, national variety registers, Codex |
| 3 | Peer-reviewed literature | Primary papers; FoodAtlas literature extractions, flagged `llm_extracted` |
| 4 | Predicted, inferred or declared | Study model outputs; values coded *imputed*, *calculated* or *borrowed*; breeder and grower descriptions |
| 5 | Unverified | A work queue, not a resting place |

As in Victorinox, each claim also shows the evidence **kind** and its **independence** (independent vs declared by an interested party). A breeder's description is a different kind of evidence, not a worse paper.

The tier lives on the **claim**, not the source. One national table can carry an analytical value (tier 1) next to a borrowed one (tier 4).

---

## 4. Data model

```
 ORGANISM (taxon)                 FOOD                                   MOLECULE
 Malus domestica ──is source of──► Apple ──contains {amount, basis, part}──► Quercetin
   │                                │                                        │
   │ origin · native range          ├── variety ──► Honeycrisp               ├── flavour: bitter
   │ growing · climate              ├── part ─────► peel · flesh · seed      └── bioactivity evidence
   │ occurrence · production        └── form ─────► raw · dried · juice           (11 categories)
   ▼                                │
 MAP · SEASON · GROWING             ▼ transformed by
                                 PROCESS  (fermenting · drying · milling · pressing)
                                    │            ▲
                                    │            └── driven by ── MICROBE (Saccharomyces cerevisiae)
                                    ▼
                                 FOOD  (cider · dried apple · pomace)
```

### Registers

| # | Register | Holds | Join keys |
| :-: | :--- | :--- | :--- |
| 1 | **Organisms** | Species-level facts: origin, native range, growing needs, climate, occurrence, production | NCBI Taxon, GBIF, Wikidata |
| 2 | **Foods** | Four typed levels (below). Nutrition, molecules, sensory, season, images | FoodOn, FoodAtlas ID, FDC ID |
| 3 | **Molecules** | Nutrients, bioactive compounds, food-contact migrants; flavour descriptors; bioactivity evidence | ChEBI, PubChem CID, InChIKey |
| 4 | **Processes** | Transformations from input food to output food, with conditions | Curated |
| 5 | **Microbes** | Bacteria, yeasts and moulds; the processes they drive and the foods they make | NCBI Taxon |
| 6 | **Sources** | The registry: kind, independence, scope, license, link status | — |
| 7 | **Gaps** | Named open questions: what is missing, why it matters, what would settle it | — |
| 8 | **Funnel** | Underused foods moving through evidence gates | — |

### Food levels

The typed levels follow Mansfeld's infraspecific ranks and FoodOn's relations.

| Level | What it is | Example | Links |
| :--- | :--- | :--- | :--- |
| **Taxon food** | Food from a species **or** an infraspecific botanical taxon (subsp., convar., var.) | *Brassica oleracea* convar. *italica*: broccoli. Cabbage, cauliflower, kohlrabi and Brussels sprouts are sibling convarieties of the same species | *derives from* (RO_0001000) → Organism |
| **Cultivar / breed** | A named cultivated variety (ICNCP) or animal breed | Apple 'Honeycrisp' | *is_a* → taxon food; register ID, because NCBI lacks most cultivars |
| **Part** | An anatomical part | Apple peel (exocarp), flesh (mesocarp), seed | *has part* (BFO_0000051) from the whole food |
| **Form** | A state after a process | Raw, dried, juice, pomace | *derives from* a part or food, via a Process |

Foods from more than one organism (composites), or made by a microbe (xanthan gum from *Xanthomonas campestris*), carry a *derives from* chain instead of a single taxon.

Molecules are deduplicated by **InChIKey** and mapped to ChEBI, PubChem and **CDNO**. CDNO keeps a pure compound (α-tocopherol) apart from a nutrient equivalent (vitamin E equivalents).

### Claim groups

`identity` · `nutrition` · `molecules` · `bioactivity` · `sensory` · `origin` · `geography` · `growing` · `season` · `process` · `regulatory` · `narrative`

### A food entry

Each food entry has two layers, as in Victorinox.

- **Editorial layer:** photo, one-line explanation, story, and where the food sits in the family tree.
- **Technical layer:**
  - **Nutrition panel**, with basis and source on every figure.
  - **Molecule list**, with amount, evidence chip and confidence.
  - **Bioactivity profile**, labelled as evidence, with its method (measured, compound evidence or predicted).
  - **Sensory:** colour swatch, texture, taste words, and flavour descriptors from the food's molecules.
  - **Where:** origin, native range and today's production map.
  - **When:** season by region and hemisphere.
  - **Growing:** climate, soil, harvest.
  - **Varieties, parts and forms.**
  - **Made into:** processes and microbes.
  - **This entry's gaps and sources**, visible on the card.

---

## 5. Data sources

| Source | Contributes | License | Status |
| :--- | :--- | :--- | :--- |
| **FoodAtlas v4.11** | Food–chemical links, food taxonomy (FoodOn), flavour descriptors | Apache-2.0 (bundle). **CTD-derived rows are excluded**: CTD prohibits commercial reproduction without permission | **Downloaded 2026-09-17** |
| **Gupta et al. 2026**, npj Sci. Food, doi 10.1038/s41538-026-01066-1 | Bioactivity profiles for 322 foods in 11 categories, metabolite clusters, confidence tiers, method | CC BY 4.0 | Full text in `Resources/` |
| Study repo `IBPA/food-metabolomics-bioactivity` | Method reference. FRAP values are taken from their original open-access papers instead (Carlsen et al. 2010; Rico et al. 2021) | Code MIT. The data README states no per-file licenses. PTFI-derived files (RI library, tiered annotations) are treated as CC BY-NC, so **adapter only** | Not downloaded |
| PTFI metabolomics (AHA Precision Medicine Platform) | 322 foods × 27,713 standardized features | CC BY-NC 4.0, access request | **Adapter only** (D6) |
| USDA FoodData Central | Nutrition, including some named varieties | Public domain | Not downloaded |
| NCBI Taxonomy, GBIF | Taxon backbone, occurrence records | GBIF: per dataset (CC0 / CC BY / CC BY-NC) | Not downloaded |
| FAOSTAT | Production by country and year | CC BY 4.0 ✓ | Not downloaded |
| Wikidata, Wikimedia Commons | Identifiers, images | CC0; images licensed per file | Not downloaded |
| Seasonality | No global dataset exists | — | Curated per region |
| Sensory (colour, texture, taste words) | No dataset exists | — | Curated; colour can be derived from images |
| Varieties beyond FoodAtlas | National variety registers, GRIN-Global | To verify | Not downloaded |
| FAO/INFOODS BioFoodComp 4.0 | Analytical nutrients at cultivar level | "© FAO"; no open license shown | **Adapter only / finding aid** for primary papers. Ask FAO for permission (D8) |
| FooDB, Phenol-Explorer | Food compounds; polyphenols with method and processing retention factors | Commercial reuse needs permission (CC BY-NC) | **Adapter only.** Copy Phenol-Explorer's method split into our `method` field |
| WAFCT 2019 (FAO/INFOODS, West Africa) | 1,028 foods, including underused African species | FAO; license to verify | Not downloaded |
| CINE traditional foods (McGill) | Nutrients in Indigenous traditional foods (the Arctic nutrient file and others) | To verify | Not downloaded |
| PROSEA / PROTA (via Pl@ntUse) | Monographs on tropical useful plants | PROSEA text is CC BY-NC-SA | Adapter only / reference |
| FoodOn | Food classes and relations | CC BY 4.0 ✓ | Not downloaded |

---

## 6. What the FoodAtlas download actually contains

This profile was run on 2026-09-17. The file record is in `data/raw/foodatlas/SOURCE.md`.

**Scale**
- 216,804 entities: 10,270 foods, 193,236 chemicals, 13,298 diseases.
- 542,953 links: 108,047 *contains*, 304,050 *is_a*, 84,099 positive and 46,757 negative chemical–disease correlations.
- 662,821 evidence rows:

| Evidence source | Rows |
| :--- | ---: |
| ChEBI | 269,443 |
| CTD | 218,361 |
| LLM-extracted literature: Claude Opus 4.8 | 124,348 |
| LLM-extracted literature: Gemma 4 | 24,567 |
| USDA FDC | 13,565 |
| FoodOn | 11,682 |
| CDNO | 855 |

### Findings that shape the design

1. **Amounts are scarce.** Only 15,726 evidence rows (2.4%) carry an amount, all in mg/100 g, and 10,326 of those come from FDC. Most *contains* links say only that a molecule is present. The atlas must show "present, amount unknown" as its own state.
2. **No basis is declared, and some evidence is second-hand.** An LLM extracted "carbohydrate 94.07 g/100 g" for apple from PMC 9818353. That paper is a **kiwifruit** study that only mentions the apple figure in its discussion, quoting another paper (checked 2026-09-17). The value sits next to "9.5–22.0 %" from another paper, and the website shows 94% for an apple. It is almost certainly a dry-weight figure passed on second-hand. → Rules 6 and 10.
3. **Part and processing are empty.** The `food_part` and `food_processing` fields exist, but only 1 of 662,821 rows fills them. → The part and form levels have to be built.
4. **Species links are thin.** Only 515 of 10,270 foods mention an NCBI taxon in their synonyms, and only 56 carry one in their external IDs. → The Organisms register has to be built and linked. The map, origin and growing layers all depend on it.
5. **Levels are mixed.** Apple has 15 *is_a* children:
   - 13 cultivars (Honeycrisp, Fuji, Cosmic Crisp, Envy…);
   - 1 wild species, *Malus sieversii*, the apple's ancestor, filed as if it were a variety;
   - 1 form, "apple (raw)".

   → Food levels must be typed.
6. **Nothing is validated.** No evidence row is flagged as validated. A machine plausibility score exists for 5,403 rows. → FoodAtlas literature rows enter at tier 3 with the flags `llm_extracted` and `unvalidated`.
7. **Chemicals are duplicated.** Vitamin C, L-ascorbic acid and L-ascorbate appear as separate rows on the apple page. → Molecules are merged by ChEBI / InChIKey.
8. **A flavour bridge exists.** 1,764 chemicals carry flavour descriptors (sweet 358, bitter 265, fruity 118, green 115, woody 94…). → This gives a molecular flavour layer next to the curated taste words.
9. **Navigation comes for free.** 13 FoodOn food groups (plant, fruit, seed/nut, fish, dairy, meat, spice/herb, fungus, algae…) → top-level browsing.
10. **Licensing is mixed inside the bundle.** The bundle is labelled Apache-2.0, but 218,361 evidence rows (33%) come from CTD, whose terms prohibit commercial reproduction without permission. Those rows back:
    - **all** 130,856 chemical–disease links;
    - 22,364 *is_a* links;
    - no food–chemical links at all.

    → For an MIT atlas, CTD-only links and the disease layer are left out. The food–chemical core is unaffected, and disease links were health-claim territory anyway (rule 8).
11. **The food–chemical core rests mostly on AI extraction.** 95,129 of 108,047 food–chemical links (88%) are backed only by LLM-extracted literature rows. → These enter at tier 3 with the flag `llm_extracted`. FDC-backed values are preferred wherever both exist.
12. **Variety depth varies.** Among the staples checked, the species with the most children are:

| Species | Children |
| :--- | ---: |
| Apple | 15 |
| Rice | 14 |
| Potato | 9 |
| Tomato | 8 |
| Grape | 7 |

---

## 7. Views

| View | Purpose | Phase |
| :--- | :--- | :-: |
| **Foods** | Card grid. Filter by group, colour, texture, taste, season, origin | 1 |
| **Entry** | The two-layer card from §4 | 1 |
| **Compare** | Up to three foods or varieties side by side; a blank reads *not stated* | 1 |
| **Gaps** | Every open question, grouped | 1 |
| **Sources** | The registry, with kind, independence, license and link status | 1 |
| **Molecules** | Molecule register: which foods, how much, how sure | 2 |
| **Fingerprint map** | Foods placed by chemical similarity (after Gupta et al., Fig. 2) | 2 |
| **Bioactivity wheel** | Foods by evidence category, always labelled as evidence | 2 |
| **World map** | Origin, native range and production today | 3 |
| **Season calendar** | What is in season, where and when | 3 |
| **Processes and Microbes** | Transformation chains, e.g. grape → *Saccharomyces* → wine | 4 |
| **Funnel** | Underused foods moving through evidence gates | 4 |

---

## 8. Scope and phasing

| Phase | Deliverable | Done when |
| :-: | :--- | :--- |
| 0 | This document; raw data in hand | D1 and D2 decided |
| 1 | **Pilot slice** (apple + cabbage family (Malus domestica; Brassica oleracea convar. capitata, italica, botrytis, gongylodes, gemmifera, acephala), including cider and sauerkraut) and the contract validator | Every published value passes the validator; every missing field is a named gap |
| 2 | Molecule register, study bioactivity layer, fingerprint map | Molecules merged by ChEBI/InChIKey; every predicted value carries model and tier |
| 3 | Organisms register, world map, season, growing across all 13 food groups | Every pilot food links to a taxon |
| 4 | Processes, microbes, funnel, further datasets (sustainability, trade) | — |

### Not in scope for v1

- Personal diet advice
- Health claims
- Recipes
- Commerce
- A public API

### Build approach (recommendation)

Victorinox used hand-written YAML files plus a single HTML page. That pattern breaks at the molecule level: 354 chemicals for one apple, times thousands of foods. The recommended approach is a hybrid:
- **Hand-written files** for everything a person curates: varieties, sensory, season, stories, sources, gaps.
- **A local analytical database** (DuckDB over the parquet files) for imported bulk data.
- **One validator** enforcing §3 on both.
- **A static site** generated per entry.

### Ingestion pipeline

Adapted from the German research synthesis and corrected for the license gate. See `research/REVIEW_FOOD_SPECIES_ATLAS_RESOURCES.md`.

| Stage | Shippable inputs | What happens | Rules checked | Result |
| :-: | :--- | :--- | :--- | :--- |
| 1 · Taxonomy | Kew useful-plants checklist and WCVP, GRIN, NCBI Taxonomy, GBIF backbone. Mansfeld as a reference | Resolve names and synonyms; build species and infraspecific trees | 2, 3, 9 | Organisms register |
| 2 · Food levels | FoodOn, FoodAtlas food taxonomy, USDA FDC | Type every food as taxon food, cultivar, part or form; replace ambiguous *is_a* links with *derives from* / *has part* | 1 | Foods register |
| 3 · Nutrition | USDA FDC Foundation + SR Legacy, BLS 4.0, Ciqual, Swiss database; open-access primary papers | Read values with their derivation codes; normalise to per 100 g with basis and part | 1, 6, 10 | Nutrition claims |
| 4 · Molecules | FoodAtlas (CTD-free), ChEBI, CDNO, PubChem | Deduplicate by InChIKey; separate amounts from presence-only links; carry flavour descriptors | 1, 6, 10 | Molecules register |
| 5 · Bioactivity | Gupta et al. 2026 (CC BY text); FRAP values from open primary papers | Store as evidence with method and tier 4 for predictions | 7, 8 | Bioactivity layer |
| 6 · Gaps | Everything that failed a rule | Move each failed value to the gap register with what would settle it | 5 | Gaps register and Funnel |

The adapter-only sources (PTFI, FooDB, Phenol-Explorer, BioFoodComp, FishBase) plug into stages 3–5 **locally**, never into the published build.

---

## 9. Open decisions

| ID | Decision | Why it matters |
| :-- | :--- | :--- |
| **D1** | ~~Will this ever be commercial?~~ **Decided 2026-09-17: open source, MIT.** | Anyone may reuse the atlas commercially, so shipped data must allow it (§3 Licensing). Rule 8 stays, because downstream users may publish commercially. |
| **D2** | **Decided 2026-09-17:** apple + cabbage family — *Malus domestica* (cultivars, peel, flesh, juice, pomace, cider, dried apple) and *Brassica oleracea* convar. capitata, italica, botrytis, gongylodes, gemmifera, acephala, incl. sauerkraut. | The proposal in §8 is based on variety depth in FoodAtlas. It could instead follow a story, e.g. one fermentation chain per species. |
| **D3** | **Decided 2026-09-17:** English first; German names (from BLS) stored as `name_de`. | English only, or German and English |
| **D4** | Physical layer | Victorinox had physical samples with QR codes. Does the atlas get specimens (seeds, dried samples, pigments)? |
| **D5** | Primary audience | Decides whether the editorial or the technical layer leads |
| **D6** | ~~Request PTFI access~~ **Resolved by D1:** PTFI is adapter-only | CC BY-NC data cannot ship in an MIT atlas. A contributor with their own access can run an optional PTFI loader locally. |
| **D7** | **Decided 2026-09-17: CC BY 4.0** (`LICENSE-DATA`). Original question: license for **our curated data** | MIT (one license for everything, but written for software); **CC BY 4.0** (the norm for open data, requires attribution, fits our CC BY sources; *recommended*); CC0 (maximum reuse, like USDA). |
| **D8** | Ask data owners for permission? Plan 1 proceeds without partner contact. | FAO/INFOODS (BioFoodComp), FooDB and Phenol-Explorer hold the best variety-level and polyphenol data, but none is confirmed for MIT redistribution. Without permission, values are re-extracted from open primary papers, which is slower. Nothing has been sent. |

---

## 10. Sources for this document

The full source landscape (books, datasets, publications, licenses and acquisition order) is in `research/EXISTING_FOOD_ATLASES_AND_DATASETS.md`.

- FoodAtlas v4.11 bundle, profiled locally. See `data/raw/foodatlas/SOURCE.md`.
- foodatlas.ai: Downloads, Technical Background, Developers and Apple entry pages, read 2026-09-17.
- Gupta, P., Gunning, M., Ahmed, S. & Tagkopoulos, I. (2026). From metabolomics dark matter to bioactivity. *npj Science of Food*. https://doi.org/10.1038/s41538-026-01066-1
- github.com/IBPA/food-metabolomics-bioactivity, README, read 2026-09-17.
- Victorinox Material & Technology Library README and taxonomy files (the contract in §3).
- German research synthesis `research/FOOD_SPECIES_ATLAS_RESOURCES_DE.md` and its review `research/REVIEW_FOOD_SPECIES_ATLAS_RESOURCES.md`.
- PMC9818353 (kiwifruit study; source of the apple carbohydrate extraction), read 2026-09-17.
