# Food Atlas — entry page design

Status: awaiting review · 2026-09-19

Authority for presentation decisions. Supersedes the visual direction in
[interview-implementation.md](../../interview-implementation.md); its data
boundaries still hold. The product rules in [product.md](../../../product.md) §3
remain authoritative, with the rule 8 amendment recorded in §2 below.

Source of decisions: interview rounds of 2026-09-19 (40 questions across eight categories, plus
the composition model),
recorded inline. Where this document and an earlier interview disagree, this document
wins and says so.

---

## 1. What was wrong

The site generated during the Hermes cron runs invented its own styling: system
sans, Georgia italic for taxa, 6px and 10px corner radii, a crimson `#B10034`
accent, drop shadows. It shares nothing with Aesthetics Explorer, the Spotify
playlist explorer or Website Blocks, all of which run on Micrographics v2.

It also carried visible craft defects — a masthead with buttons on two
baselines, an input truncating its own placeholder, filter selects clipping
their labels, an evidence chip breaking an editorial paragraph.

The data underneath is sound: 33 foods, 5,639 claims, 12 sources, 1,582 recorded
gaps, 235 passing tests. The failure was entirely presentational.

---

## 2. Rule 8, amended

**Old:** the atlas may say *"compound-level assay evidence associated with
anti-inflammatory activity"*, never *"anti-inflammatory food"*. Enforced by a
regex word list in `contract.py`.

**New (owner decision, 2026-09-19):** a food-level bioactivity tag is permitted,
but only while its evidence remains attached to it. The prohibition becomes
**no unsupported claim**, not **no food-level claim**.

This changes enforcement from matching words to checking structure: a
food-level bioactivity claim must resolve to at least one compound-level
evidence claim carrying a reference, or it becomes a rule 8 gap.

Two consequences are accepted knowingly:

- `product.md` decision **D1** reasons that rule 8 stays *"because downstream
  users may publish commercially"*. That reasoning still stands; the rule's
  form changed, not its purpose. D1's note needs updating.
- Food-level bioactivity statements are regulated health claims in the EU
  (Regulation 1924/2006). Attached evidence is what keeps them defensible for
  downstream reusers of an MIT-licensed atlas.

A separate enforcement hole was found and must be closed regardless: the
current regex blocks `antiviral food` and `anti-inflammatory food` but lets
`antifungal food` and `antimicrobial vegetables` through, because `fungal` and
`microbial` are absent from its alternation. Tracked as its own task.

---

## 3. Design language

**Micrographics v2 tokens only, botanical register.** Owner decision: *"full
botanical, Micrographics only for tokens."*

Adopted verbatim from
`SPOTIFY/Playlist spotify/MIcrographics v2 Design System/colors_and_type.css`:

| Layer | Tokens |
|---|---|
| Palette | `--paper` `#F2EFE8`, `--paper-2` `#E8E4DA`, `--ink` `#0B0B0B` with the `.90/.55/.30/.15/.08` alpha scale, `--accent` `#FF4F00`, `--cobalt` `#1530FF` |
| Type | `--f-display` Archivo · `--f-body` Inter Tight · `--f-mono` JetBrains Mono · `--f-serif` Instrument Serif |
| Scale | `--t-micro` 10 → `--t-h2` 64, tracking and line-height tokens |
| Spacing | 4px base, `--s-1` … `--s-24` |
| Lines | `--hairline-w` 0.5px, `--radius-0` |

**Explicitly dropped** — the brutalist ornament: crop marks, the persistent data
header strip, rubber stamps, the dot-grid backdrop, and mono-as-chrome. Mono is
confined to genuine metadata: units, identifiers, source codes, reference IDs.

**Warmth comes from** large photography, Instrument Serif for the binomial and
the editorial lede, generous vertical space, and body copy at a comfortable
reading size. Not from rounded corners or shadows, which stay absent.

**Accent discipline** is retained from the house system: one accent per surface,
under 5% of area. `--cobalt` is reserved for one job only — marking traditional
knowledge as a categorically different register (§6).

**Language:** English throughout. Source titles stay verbatim as published —
`Bundeslebensmittelschlüssel (BLS), Version 4.0 — Deutsche Nährstoffdatenbank`
is a citation, and translating it would misattribute the source. No German in UI
copy, including `name_de`.

**Fonts** must be self-hosted as woff2 rather than loaded from the Google Fonts
CDN. The atlas is a static, offline-capable artifact; Aesthetics Explorer already
self-hosts. The prototypes use the CDN and must be converted before shipping.

**Quality bar.** Owner: *professional* means a natural-history atlas and the owner's
own explorers. Interpretation, to be confirmed at review: the entry page takes the
atlas register (plates, calm, precise labelling), while index, compare and search
take the explorer register (interactive, tool-like), so the two never fight on
one page.

**Home.** A public website with an open data release alongside: a static site plus
the MIT dataset. Public performance, accessibility and search-engine legibility
matter. The site is static files with no runtime dependency on a third-party CDN.

---

## 4. Entry page structure

Composition **C — masthead**, chosen from three rendered variants in
`docs/prototype/kale-abovefold-variants.html`.

```
┌─ identity ──────────────────────────┬─ tags ─────────────┐
│ FAMILY · LEVEL                      │ real tags          │
│ Kale                      (Archivo) │ bioactivity tags   │
│ Brassica oleracea convar. acephala  │ (evidence-backed)  │
│ lede                (Instrument Srf)│                    │
├─────────────────────────────────────┴────────────────────┤
│ photographic plate, full width, provenance beneath       │
├──────────────┬──────────────┬────────────────────────────┤
│ NUTRITION    │ SENSORY      │ RESEARCH                   │  ← at a glance
├──────────────┴──────────────┴────────────────────────────┤
│ registers, full width, each independently disclosed      │  ← depth
└──────────────────────────────────────────────────────────┘
```

Above the fold: identity, Latin name, family, tags, plate, and all three
at-a-glance profiles. Below: the deep registers.

**Iceberg model.** Owner: *"imagine an iceberg, but the top is already quite
extensive."* The surface is a substantial, self-sufficient read — not a teaser.
Depth is genuinely deep and never required.

**Disclosure is per-section, never global.** The existing global science-mode
toggle is retired. Each register carries its own *Open …* control, and opening
one reveals that register's measurements, methods, bases and sources.

---

## 5. Evidence presentation

Four decisions, all reversals of the first prototype:

**No page-level evidence summary.** A single aggregate across 5,639 claims of
different kinds is not honestly summarisable. Each register states its own
evidence character in its own header instead.

**Nothing inline on individual values.** The tier tick marks are removed from
the surface. Provenance appears when a register is opened. Tiers remain in the
data and drive ordering and selection; they are internal vocabulary and are
never shown as `T1`…`T5` to a reader.

**Conflicts read as ranges.** Where sources disagree, show the spread:
`389.6–390 µg`, `2870–2873 µg`, `6260–6261 µg`. Where they agree, a single
figure. The reader is never asked to arbitrate and disagreement is never hidden.

**Gaps are summarised and linked.** One line on the entry page, with the full
register elsewhere. Missing data must never read as a zero (interview
2026-09-17), and an empty evidence register is shown rather than omitted.

### Nutrition

A 0–100 g composition bar is required by the 2026-09-17 interview, but Kale is
89.63 g water, which collapses everything else into invisible slivers. Resolved
in two stages:

1. **Water / everything else** on a true 0–100 g scale — the honest split.
2. **The dry matter opened at its own declared scale**, with the scale stated in
   words: *"Everything else, 10.37 g, at its own scale."*

Macronutrients compose 100 g exactly and earn a bar. Micronutrients span
0.053 mg to 6,260 µg, share no meaningful axis, and are listed rather than
drawn. No %DV, no reference intake, no health score — all three invent a
baseline the atlas does not hold.

### The composition model

Owner framing, 2026-09-19: the library treats the raw material as the base, 100%.
Components are fractions of it. A product is a compilation of raw materials.

**Definitions.**

- An entry is a **whole**: 100% of a declared basis. The basis is **fresh edible
  portion**, the basis of every FDC and BLS value already held. Dry matter is a
  possible later switch, with water as the pivot (rule 6).
- **Components** are fractions of the whole, recursively: kale, then dry matter,
  then carbohydrate, then fibre.
- A **product** is a whole whose components are other wholes, with proportions
  that sum to 100%.

**Two views of one whole.** *What it is made of*, the chemical decomposition
(nutrients, then compounds), and *what it is made from*, the anatomical
decomposition (flesh, peel, core, seeds). The page offers one switch between them.

**Fractions are claims.** No new mechanism: a fraction carries a value, basis,
source, tier and method like any other number, so rules 1–10 apply to it.
Three relations between wholes carry one:

| Relation | In the model today | Fraction it carries |
|---|---|---|
| `part_of` | yes (apple flesh, apple peel) | share of the whole |
| `derives_from` | yes (apple juice, apple pomace) | yield |
| `composed_of` | no, new | proportion in a product |

No food record carries a yield, share or proportion today. Every fraction is new
data to source.

**Products.** Composition is calculated from the ingredients' fractions and
labelled `calculated` (an existing derivation, tier 4). Each total lists its
inputs and is never shown as measured.

**Proportions are claims.** A proportion carries a value, basis, source,
derivation and tier like every other number, so rules 1–10 apply to it and no
source type is privileged. `claims.py` already lists `label` as a derivation at
tier 4, so the contract anticipated this.

This widens an earlier decision to take proportions from declared labels only.
Labels describe industrial products, the least interesting compilation this atlas
holds, and the obvious bulk dataset (Open Food Facts) appears to publish under
ODbL, which is share-alike and would likely fail rule 9. That choice bought the
narrowest kind of compilation at the highest licensing cost.

Four kinds of compilation, and where each gets its proportions:

| Kind | The proportion is | Derivation | Tier |
|---|---|---|---|
| Derived form — apple → juice, pomace | a **yield** | food-science literature | 3 |
| Dish — ribollita, colcannon | a **recipe** | published or reference recipe | 2–3 |
| Traditional formula — a decoction, a churna | a **formulation** | classical formulary | 3 |
| Industrial product | an **ordering with bounds** | `label` | 4 |

**Traditional formulas are the reason to widen.** A TCM formula or an Ayurvedic
preparation is literally a compilation of raw materials in stated proportions.
Admitting them makes the composition model the spine joining raw materials,
cooking, dishes and traditional medicine, instead of a feature for packaged goods.
One caveat: the classical texts are old enough to be out of copyright, but modern
translations, critical editions and compilations are not. Rule 9 and the
provenance gate (§7.7) apply to the edition actually used, not to the underlying
text.

**Labels remain, as one tier-4 kind.** A label lists ingredients in descending
weight and, in the EU, gives a percentage generally only for ingredients named,
pictured or emphasised. That yields an interval — each ingredient no larger than
the one before it, all summing to 100% — which is consistent with conflicts shown
as ranges. Each label is a curated single fact with attribution (rule 9 `cite`),
not a bulk import.

**Proportions declare a basis** (rule 6). A recipe's "200 g kale" is a raw weight
going in; a served dish has lost water. A compilation proportion states whether it
is *as combined* or *as served*, and the two are not interchangeable.

**A calculated total is bounded by its inputs.** `calculated` is tier 4 flat, so no
computed total can outrank a measurement. Coverage is the separate risk: a total
computed from three of five ingredients must say so, not present a partial sum as
a whole.

**Invariants the model gives for free**, proposed as build-time checks and not yet
rules:

1. Siblings may not exceed their parent within tolerance. Otherwise the page shows
   a visible disagreement instead of a silent stack. Kale today: sugars 0.8 g plus
   fibre 4.1 g is 4.9 g, against carbohydrate 4.42 g.
2. A product's proportions sum to 100%, or to a stated interval.
3. Missing is never zero. An unaccounted remainder is its own labelled slice.
   Carbohydrate "by difference" already hides one: it is what remains after water,
   protein, fat and ash, so proximate composition closes to 100 g by construction
   (16 of 33 foods, within 0.05 g).

**Limits, from the data.**

- Below nutrients the tree stops. 2,556 molecule claims carry no amount, so
  molecules sit beside the whole, not inside it.
- The nutrient registry holds only a name and a unit, no hierarchy. A parent
  relation is needed before the sibling check can run. One nutrient also carries
  different names per source (`Protein` and `Protein (Nx6,25)`) and needs
  harmonising.
- A microgram amount is invisible on a percentage scale. Each level states its own
  scale, as the two-stage bar does.

**Presentation.** The nutrition profile generalises from two stages to
**interactive descent**: two levels on the surface, and opening a slice descends
one level at its own declared scale. This is the iceberg and per-section disclosure
applied to composition. A raw material's entry gains a **Used in** register, the
reverse of `composed_of`. Apple splitting into juice and pomace becomes a mass
balance once yields exist.

---

## 6. The bioactivity rabbit hole

Prototyped in `docs/prototype/kale-rabbithole.html`. Owner asked to see it
opened before committing to ingestion. Ingestion is sequenced in §7.6.

A bioactivity tag opens **four registers that are never merged**, enforcing
rule 8's original intent structurally rather than by wording:

| Register | Rule | Marker |
|---|---|---|
| Laboratory | in vitro; molecules present, with references | solid ink rule |
| Animal studies | in vivo, non-human | `--ink-55` rule |
| Human studies | trials in people | `--ink-30` rule |
| Traditional use | cultural knowledge, never evidence | dashed `--cobalt` |

A fifth band, **where else this leads**, carries cross-food navigation on shared
molecules. This is the rabbit hole proper: sulforaphane occurs in 11 other foods
in the collection, and the glucosinolate family carries 133 distinct papers.

The empty Human studies register is load-bearing. *"This register being empty is
the most important thing on this panel. It is shown, not hidden."*

**Sample data protocol.** Functional classifications, study settings and
traditional-system correspondences do not exist in `atlas.json`. Where shown for
design evaluation they must be dashed, orange-keyed, suffixed `SAMPLE`, and the
page must carry a standing warning that separates what is real from what is not.
No sample datum may reach a shipped build.

---

## 7. Entry standard and data roadmap

Owner decisions from the data-depth interview, 2026-09-19.

### 7.1 The entry standard

Layered: a mandatory core, then unbounded depth that accretes over time, with no
per-entry completion target.

**Core.** Every entry answers these, even thinly:

1. **Identity and appearance** — names, Latin name, family, plate, plain-language lede.
2. **Composition** — macronutrients and key micronutrients, sourced, conflicts as ranges.
3. **Season and where it grows** — regional availability and basic growing conditions.

Kitchen use is deliberately **not** core. Culinary lineage is wanted, and is
delivered through dish entries (§7.4), not as a mandatory section of every entry.

**Thin entries publish, honestly thin.** Empty registers stay visible as "not yet
recorded". Nothing is hidden, padded or ranked away.

**Reading adopted here:** the core is a structural requirement of the page, not a
data-completeness gate. An entry "answers" a core question when its register is
present and honest, including when it says "not yet recorded". An entry with an
empty season register still publishes. Flagged for confirmation in §9.

**Current state against this standard.** The atlas holds 10 season claims covering
7 of 33 foods, all for one region (DE). Season is core, so most entries will
publish with an empty season register until calendars are ingested.

### 7.2 Which plants

**Criterion: rabbit-hole richness.** Plants with the deepest bioactivity and
traditional-use record, as the best showcase of the four registers (§6).
Target: 20–30.

The current pilot (apple and six brassica foods) is a starting subset, not the
target list. Herbs, spices and medicinal roots fit the criterion but often lack
composition tables in FDC or BLS, so they will meet the core thinly on
Composition. That is accepted under the thin-entry policy. The shortlist is open
(§9).

### 7.3 Preparation as a control

One entry per plant, with preparation as a control on it. Four state groups:

- raw, and chopped-and-rested
- boiled or steamed
- roasted, fried or baked
- fermented, dried or frozen

No structural change is needed. A state is a child food carrying a `process` and
`derives_from` its parent, as `food:kale.frozen` already does via `proc:freezing`.
The control reads the parent's children. The work is the data behind each state,
not the model.

Chopped-and-rested is the strongest claim in the set. It rests on
glucosinolate–myrosinase chemistry, where heat inactivates the enzyme and changes
which compounds form. It needs primary sources under rule 10 before it is stated.

### 7.4 Compilations as their own entries

A new entity type, the **compilation**. The owner's term is "a product is a
compilation of raw materials". Dishes, traditional formulas and industrial
products are one type, differing only in where their proportions come from (§5).
The boundary:

- a **preparation state** is a physical change to one plant, and is a control on
  its entry;
- a **compilation** combines two or more wholes, and is its own entry.

A compilation carries its ingredients, their proportions and its origin. Its
composition is calculated and labelled as such. An earlier draft of this section
forbade any computed total, citing rule 7. That was too strict: rule 7 concerns
model predictions, and `calculated` is an existing derivation at tier 4.

**Derived forms are the case already in the model.** `food:apple.juice` and
`food:apple.pomace` both `derives_from` `food:apple`. Adding yields turns that
pair into a mass balance and makes the composition model work in both directions:
a whole splitting into parts, and parts combining into a whole. This is the
cheapest compilation to build, because the relations already exist and only the
fractions are missing.

Candidate source for ingredient and origin edges is Wikidata (CC0); coverage and
quality are unverified.

### 7.5 Season coverage

Truly global for the reference plants. Owner accepts that coverage will be uneven,
because source availability differs sharply by region. Missing regional data
shows as missing, never as zero (interview 2026-09-17).

### 7.6 Sequencing

**First: read the unread licences.** Nothing below is a source until its licence
has been read (rule 9):

- Dr. Duke's Phytochemical and Ethnobotanical Databases (Ag Data Commons)
- CINE (McGill)
- USDA nutrient retention factors
- Wikidata dish coverage (the licence is CC0; coverage is the open question)

**Then, proposed and not yet decided:** ChEBI classes, then ChEMBL activity.
779 of 789 molecules carry a ChEBI ID and 586 carry a PubChem ID, so this is a
matching job. After that, retention factors, then regional calendars.

Domains in owner priority, unchanged: bioactivity (compound-level), cooking and
processing, agronomy and environment, safety and anti-nutrients, traditional and
ethnobotanical.

### 7.7 Traditional knowledge: a provenance gate

Mirrors rule 9. Each source is assessed for provenance and consent before
ingestion, in addition to its licence. Classical systems (TCM, Ayurveda) stay
available; community and tribal knowledge passes a checkpoint. India's TKDL exists
specifically to keep such knowledge from being absorbed into commercially
reusable databases, and an MIT atlas redistributes whatever it ingests. Licence is
necessary and not sufficient.

Traditional use always renders in its own register (§6), never merged with
evidence.

### 7.8 Automation

Autonomy follows how verifiable the source is.

- **Structured sources** that pass rules 1–10 (for example ChEBI and ChEMBL) may
  be accepted automatically.
- **Literature-extracted and LLM-extracted claims stay propose-only** for owner
  review.

This changes today's approval gate, which is propose-only for everything.

---

## 8. Scope of the build

**In:** the entry page — templates, tokens, client behaviour, and whatever
`build.py` changes the new page model requires.

**Out of this spec:** index, compare, molecules, gaps and sources pages. They
inherit the token layer and component inventory but need their own composition
decisions. The bioactivity ingestion is a research project, not a build task.
Dish entries (§7.4) and the data behind the preparation states (§7.3) are also
out. The entry page must leave room for them: a preparation control that reads a
food's children, and a related-dishes register that renders empty until dishes
exist. The composition model's
data-model changes (§5: `composed_of`, fraction claims, a nutrient hierarchy) are
out as well. The page must leave room for the descent interaction.

**Preserved:** the data model, claim validation, the contract, and the 235-test
suite. No presentational change may weaken a rule.

---

## 9. Open questions

- **The shortlist.** Which 20–30 plants meet "rabbit-hole richness", and which of
  those have composition data at all.
- **Licence outcomes** (§7.6). Each may come back as ship, cite-only or
  adapter-only, which changes what the roadmap can promise.
- **Core as standard or gate.** §7.1 reads the core as structural, so an entry
  with an empty season register still publishes. If you meant the core as a gate,
  26 of 33 foods would not publish today.
- **Which compilation kind is built first.** Derived-form yields are cheapest
  (the relations exist, only fractions are missing); traditional formulas are the
  most valuable to the vision; dishes are the most legible to a reader.
- **Which edition of a classical formulary.** The text may be out of copyright
  while the translation is not (§5).
- **Interval arithmetic.** Label-derived proportions are intervals, so a product's
  headline figure is a range. How that composes across several interval
  ingredients is unspecified.
- **The nutrient hierarchy.** The registry needs a parent relation and
  cross-source name harmonisation before the sibling check can run.
- **Anatomical fractions have no source yet**, for example flesh as a share of an
  apple.
- **Sequencing after the licence reads.** ChEBI then ChEMBL is proposed, not
  decided.
- **The automation gate.** §7.8 changes the propose-only gate the research loop
  uses today. The change itself is unspecified.
- **Rule 8 implementation** (§2), queued as its own task.
- **Dish scope.** How many dishes, chosen how, given they are their own entries.
- **The quality-bar interpretation** in §3.
- **Plate treatment in dark mode.** Current photographs are white-background
  product shots and read as bright blocks against `--paper` `#0B0B0B`.
- **Cross-food navigation depth.** How far the rabbit hole recurses before it
  becomes a graph view rather than an entry page.

---

## 10. Artifacts

| File | What it shows | Standing |
|---|---|---|
| `docs/prototype/kale-specimen.html` | Full Micrographics specimen sheet | Superseded by §3 |
| `docs/prototype/kale-abovefold-variants.html` | Three above-fold compositions | C chosen |
| `docs/prototype/kale-rabbithole.html` | Bioactivity opened, four registers | Reference for §6 |

All three are generated from `data/build/atlas.json` by throwaway scripts, not
hand-written, so they cannot drift from the corpus. They are prototypes and are
not part of the build.
