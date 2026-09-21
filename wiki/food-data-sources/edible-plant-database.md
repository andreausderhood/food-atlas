# Edible Plant Database (EPD) and Food Plants International

> Sources: `data/datasets/edibleplantdb.zim` (9 GB Kiwix archive, 2026-04-13 edition); live WebDirect check 2026-09-21
> Raw: ZIM on disk; extracted records `data/research/scope/epd-zim/species-epd.yaml`
> Updated: 2026-09-21

## The ZIM (the practical one)

Edible Plant Database — Survival Field Guide, offline Kiwix edition:
**27,918 edible plant species, 569 families, 207 countries, 70,677 photos**.
Stated content provenance: Food Plants International (botany, nutrition,
cultivation), PFAF (edible/medicinal uses, hazards), Wikipedia, iNaturalist +
GBIF photos (per-photo CC licenses, mostly CC BY-NC).

`tools/scope_epd_zim.py` (libzim) extracts per species: binomial, common name,
edible parts, distribution/countries, identification, growing ranges (temperature,
rainfall, pH, hardiness), medicinal tags. 25,001 records extracted — 23,381 with
edible parts, 25,001 with distribution, 10,756 with growing, 8,920 medicinal.

## Food Plants International live (the locked one)

`fms.cmsvr.com/fmi/webd/Food_Plants_World` = "Edible Plants of the World",
FileMaker WebDirect, **35,103 records**. Fields confirmed via the sort dialog:
Botanical Names, Countries, Distribution, Edible Parts, Description, Regions.
No API, no export; browser automation stalls at the disclaimer/sort gate —
and the FPI redistribution terms are unstated. Rule 9: unknown, no import.

## What they are for

Discovery and enrichment layer, never measurement claims: edible parts,
distribution, growing ecology — the raw material for the season/geography
lanes. The EAN→species mapping question and the nutrition-ranking numbers in
the EPD remain unvetted; use for scope, not for values.

## Relationship to the pool

EPD ∪ FAO (560 species) ∪ Wikipedia (2,322) = the unified
[species funnel](../food-atlas-project/species-funnel.md). EPD covers the
long tail none of the composition tables touch.
