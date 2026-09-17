# Review: "Systemarchitektur und Datenquellen für die Kartierung essbarer Biodiversität im Food Atlas"

**Reviewed file:** `research/FOOD_SPECIES_ATLAS_RESOURCES_DE.md` (German; copied from `~/Downloads/Food Species Atlas Resources.md`)
**Date:** 2026-09-17
**What it is:** A German research synthesis that cites `product.md` as its reference 1.
- It adds sources and structure.
- It predates the MIT decision.
- Some of its citations do not meet our source contract.

**How it was reviewed:** Each claim that would change the product was checked on the web (✓), or marked as not verified (?).

---

## 1. Adopted into `product.md`

| # | Item from the document | Check | Where it went |
| :-: | :--- | :-: | :--- |
| A1 | **Infraspecific botanical ranks** (subsp., convar., var.) from Mansfeld. *Brassica oleracea* convar. *capitata* / *botrytis* / *italica* / *gongylodes* / *gemmifera* are cabbage, cauliflower, broccoli, kohlrabi and Brussels sprouts: one species, five foods | ✓ (Mansfeld 6,100 spp.; the rank structure is standard botany) | §4: the food levels now separate **botanical taxon** from **cultivar** |
| A2 | **`food_part` inside the claim object**, not only in rule 6 | — | §3 rule 1 |
| A3 | **FoodOn relations**: *derives from* (RO_0001000) links a product to its organism; *has part* (BFO_0000051) links a whole food to its parts | ✓ (FoodOn is CC BY 4.0; relation IDs are standard OBO) | §4 |
| A4 | **Chemical dedup by InChIKey**, mapped to ChEBI, PubChem and CDNO; CDNO separates a pure compound from a nutrient equivalent (α-tocopherol vs vitamin E equivalents) | — | §4 Molecules |
| A5 | **Six-stage ingestion pipeline** (taxonomy → food levels → nutrition → molecules → bioactivity → gaps) | — | §8, corrected for the MIT license gate (see §2) |
| A6 | **New sources**: WAFCT 2019 (1,028 foods ✓); CINE traditional-food data (McGill ✓); PROTA/PROSEA via Pl@ntUse ✓; the Phenol-Explorer processing retention factors ✓ | ✓ | §5; research doc §3 |
| A7 | **Variety matters for nutrition**: provitamin A in sweet potato varies more than 100-fold between white- and orange-fleshed varieties | ? (plausible; cited to BioFoodComp) | Kept as a motivating example only, until checked |

## 2. Corrected

| # | Claim in the document | Correction | Evidence |
| :-: | :--- | :--- | :--- |
| C1 | **FooDB** "steht uneingeschränkt zur Verfügung" (unrestricted) and ships at tiers 1–3 | **Commercial reuse needs the authors' permission** (a CC BY-NC license is also reported). Under MIT it is **adapter only** | ✓ foodb.ca terms (via search) |
| C2 | **Phenol-Explorer** is an "Open Access" tier-1 source | **Commercial reuse needs permission** (CC BY-NC). **Adapter only.** The method split (HPLC with or without hydrolysis, Folin) is still worth copying into our `method` field | ✓ phenol-explorer.eu |
| C3 | **BioFoodComp 4.0** is the tier-1 core, freely usable | Version, ISBN 978-92-5-109790-8 and "analytical data only" are confirmed. **No open license is shown**: the FAO record says only "© FAO". **Adapter only** until FAO confirms, or permission is obtained. Values can be re-extracted from the open-access primary papers BioFoodComp cites | ✓ FAO Knowledge Repository record |
| C4 | **BioFoodComp 4.0 has 10,156 entries, all on an edible-portion fresh-weight basis** | **Not verified.** Known figures: v2.0 6,411; v2.1 6,492; v3.0 7,953. Check the 4.0 user guide before citing | ? |
| C5 | **PTFI** ships at tier 1 in pipeline phase 5; "1,600 foods" | Adapter only (CC BY-NC, access agreement). PTFI *targets* about 1,650 foods; 500 are on the AHA platform today. The 27,713 features are over 322 **foods**, not "species" | ✓ PTFI data page, AHA |
| C6 | **PROTA/PROSEA** available as a MediaWiki dump | PROSEA texts are **CC BY-NC-SA 3.0 NL**, so **adapter only**. PROTA license not checked | ✓ prosea.prota4u.org |
| C7 | **PFAF** available as CSV/SQL for ingestion | Paid database license (home, commercial or student); the "API" cited is a third-party scraper. **Not usable** | ✓ pfaf.org |
| C8 | Gupta et al. assign features to "11 **therapeutic** evidence categories" | Only antioxidant is model-predicted (FRAP). The other 10 are compound-evidence rankings, **not therapeutic claims** (rule 8) | ✓ paper, Fig. 4 |
| C9 | FoodAtlas LLM rows are "quarantined in tier 5" (phase 6), yet the same document's table puts them at tier 3 | Presence-only rows stay at **tier 3** with the flags `llm_extracted` and "amount unknown". **Amounts** without basis or part become gaps. They are not tier 5 | `product.md` §3, §6 |
| C10 | The 94 g apple carbohydrate value is stated as a dry-weight import | **Worse than that.** PMC9818353 is a **kiwifruit** study. It mentions the apple value in its discussion, quoting another paper. The extraction turned a second-hand remark into an apple fact → new **rule 10** | ✓ PMC9818353 text |
| C11 | "Eight rules" | Now ten (rule 9 license gate, rule 10 primary evidence) | `product.md` §3 |
| C12 | Every food is coupled to an NCBI taxon | True for single-organism foods. Composites, and foods from microbial fermentation such as xanthan gum, need a *derives from* chain or several taxa. NCBI lacks most cultivars, so cultivars need their own register IDs | — |
| C13 | FooDB is "the world's largest open food-compound database" | FoodAtlas lists more chemicals (193,236), and FooDB is not open for commercial use | ✓ |
| C14 | FoodOn has "30,000+ concepts" | Not verified. FoodOn's food-product branch has 9,000+ products | ? |

## 3. Rejected as sources (fail our source contract)

These references back claims in the document but cannot be used as `src`:
- **Ref 2:** a clinician's blog, used for "nutritional dark matter". Use Barabási et al. 2019 instead.
- **Ref 5:** EFSA botanicals guidance, cited for Mansfeld.
- **Ref 41:** a Reddit thread.
- **Ref 42:** a third-party scraper API.
- **Ref 48:** a hobby site.
- **Ref 54:** a recipe app catalogue.
- **Ref 55:** a macro-table app blog.
- **Ref 68:** a data-school blog, cited for FooDB flavour vocabulary.

The underlying facts are either re-sourced (Mansfeld from IPK, dark matter from Barabási) or dropped.

## 4. Net effect on the MIT atlas

Four sources the document treats as core are **not shippable** under MIT: FooDB, Phenol-Explorer, PTFI and BioFoodComp (the last pending FAO confirmation).

The shippable analytical nutrition core is therefore:
- USDA FoodData Central (CC0)
- BLS 4.0 (CC BY 4.0)
- Ciqual (open licence)
- the Swiss database (commercial use allowed with attribution)
- CoFID (to verify)
- FAOSTAT for production (CC BY 4.0 ✓)

**Variety-level nutrition**, the document's main argument, comes from two places:
- USDA Foundation Foods (cultivar metadata ✓);
- values re-extracted from open-access primary papers.

That is slower, but it gives cleaner provenance. It also turns BioFoodComp into a *finding aid* for primary papers rather than a source.

**Outreach options (your decision, nothing sent):**
- Ask FAO/INFOODS for permission to redistribute BioFoodComp.
- Ask the FooDB and Phenol-Explorer authors about use in an MIT project.
