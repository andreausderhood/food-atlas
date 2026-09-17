# Food Atlas — Interview synthesis, 2026-09-17

This file records decisions made with André in the product interview on
2026-09-17. It is the authority for UX priorities until product.md is updated.

## Core use case
Understand a known or unknown edible plant. "Omniscient lexicon" ambition:
TCM, nature healing (Naturheilkunde), science, gastronomy, agriculture and
technology united — but perspectives stay distinguishable, never merged into
apparent omniscience.

## Entry paths (priority order)
1. Text search + combinable filters (include AND exclude terms).
2. Browse by images (natural-atlas feel).
3. Photo recognition — LAST, explicitly deferred.

## Entry page = several small profiles side by side
1. General description first (plain language), then visuals.
2. Nutrition profile (bars, explicit 0–100 g scale, no invented %DV).
3. Sensory profile (sweet/sour, crisp/soft, aromas, colours, chemistry links).
4. Research profile: what is studied, evidence strength (lab ≠ human ≠ tradition).
5. First-click depth: varieties & relatives · growing here · culinary/technical
   uses (André's three chosen questions).
6. Science mode toggle: quantities, units, methods, sources inline everywhere.

## Discovery & search
- "Which antifungal foods are in season right now?" — natural language with
  include/exclude; results must visually separate traditional use vs lab
  activity vs human evidence.
- Season as global filter, location-based (manual entry or geolocation),
  global; fresh harvest vs stored produce kept separate. Missing regional
  data shown as missing, never as zero.

## Interview-based design decisions
- Visualization-first: fast comprehension of complex data is THE priority.
- Loved: the Nature bioactivity wheel for simple assignment (one property →
  foods), and radar charts for compact profile comparison. NOT primarily the
  t-SNE scatter.
- 30-second answers: "What's in this food, meaningfully?" and "What's in
  season right now here?"
- No forced health score; missing data must not look like low values.
- Imagery: nature-atlas look (large plant images, botanical calm, precise
  diagrams), research-instrument interaction, sensual culinary closeness.
- Two audiences, one surface: layperson layer + expandable science layer;
  Latin names always visible beside common names.
- Breadth: 20–30 carefully worked reference plants inside a broader, clearly
  marked collection (recommendation accepted).
- Language: English only for now (decision D3 unchanged — earlier German-first
  suggestion rejected in interview round 13).
- Photo recognition: deferred to a later step (interview round 14).
- TCM/nature-healing claims: labelled as tradition/evidence tiers, never
  merged with lab findings (rule 8 remains).
