# Pilot source review — 2026-09-17

Scope: Task 10 of `playful-spinning-whisper.md`. Read publisher pages and the existing FoodAtlas source record; no bulk downloads. Only `data/curated/*.yaml` and this document were written. Registry updates below are recommendations for the parent, not edits performed here.

## License evidence and registry recommendations

| Source | Primary evidence actually read | Recommended registry action |
| --- | --- | --- |
| `SRC-FOODATLAS-V4.11` | [Download page](https://www.foodatlas.ai/food-composition-downloads): “free resource under the Apache-2.0” license. Existing `data/raw/foodatlas/SOURCE.md:13` identifies Apache-2.0 for the bulk bundle; bundled `foodatlas-v4.11/README.md:3–4` independently says “Released under the Apache-2.0 license.” Full [Apache-2.0 text](https://www.apache.org/licenses/LICENSE-2.0.txt) read, including redistribution §4. | `license_read: true`, retain `ship` and Apache-2.0. Existing `license_url` is useful applicability evidence; optionally point it at `https://www.apache.org/licenses/LICENSE-2.0` while retaining the download URL as `url`. Preserve license copy, attribution, change notices, and any upstream NOTICE material on redistribution. This review does **not** clear CTD-derived rows or separately licensed underlying evidence; keep their exclusion. |
| `SRC-NCBI-TAXONOMY` | [NCBI policies](https://www.ncbi.nlm.nih.gov/home/about/policies/), “Copyright Status of Webpages”: government-created information is public domain, may be copied and distributed, and NLM acknowledgment is requested. The same section warns that contributed/licensed material may have separate rights. | `license_read: true`; retain policy URL and `ship` for the minimal NCBI identity fields below. Do not describe all NCBI-hosted content as unrestricted. Keep attribution and the NCBI disclaimer available to users. |
| `SRC-EDITORIAL` | Repository `LICENSE-DATA:1–9` applies CC BY 4.0 to curated data; user explicitly approved this choice. Full [CC BY 4.0 legal code](https://creativecommons.org/licenses/by/4.0/legalcode.en) read, especially attribution §3. | `license_read: true`; add `license_url: https://creativecommons.org/licenses/by/4.0/`. Replace the generic `https://github.com/` source URL with the actual project URL once known, not an invented repository. |
| `SRC-KHOURY-2016` | [Exact Dryad dataset page](https://datadryad.org/dataset/doi:10.5061/dryad.s08t2), publisher JSON-LD `license`: “Creative Commons Zero v1.0 Universal”, linked to `https://spdx.org/licenses/CC0-1.0.html`. Full [CC0 legal code](https://creativecommons.org/publicdomain/zero/1.0/legalcode.en) read. | `license_read: true`; retain CC0 and `ship`. Replace generic terms `license_url` with the exact dataset page (applicability proof). This is license verification, **not download approval** or verification of crop rows. |
| `SRC-BZFE-SAISONKALENDER` | [Current imprint](https://www.bzfe.de/rechtliches/impressum), “Urheberrecht”: text, **not pictures or graphics**, is CC licensed unless marked otherwise. Its actual link is [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/deed.de); the English deed was read. | Fix `license_url` to the current imprint. Keep `cite`; do not promote to `ship`. Keep `license_read: false` for the **calendar graphic**, whose applicable permission was not verified. Record website text as BY-NC-ND, not freely reusable CC BY. A citation is not blanket permission to reproduce a calendar or its substantial contents. |
| `SRC-ECOCROP` | [FAO terms](https://www.fao.org/contact-us/terms/en/), “REUSE OF WEB CONTENT”: general reuse is non-commercial; specified statistical databases have separate terms. [ECOCROP landing page](https://gaez.fao.org/pages/ecocrop) yielded only its title. | Keep `license_read: false` and `cite` pending ECOCROP-specific applicability review. Reading the general terms does not establish which data policy applies to this dataset. No climate values curated. |
| `SRC-MANSFELD` | [Publisher home](https://mansfeld.ipk-gatersleben.de/) redirected to `https://mansfeld.ipk-gatersleben.de/apex/f?p=257:1`; the readable page describes the database but supplies neither the needed Brassica rank records nor a reuse grant. | Keep `license_read: false`, `cite`, and existing stable homepage. No convariety rank claims curated. |

FoodAtlas API non-commercial restrictions are stated in the local `SOURCE.md`; this review verified the **bulk** channel online, not the API terms. The local SHA-256 is recorded evidence, not a newly recomputed checksum. FDC and BLS licensing were outside this delegated review; do not change their flags on this report's authority.

## Verified external claims

Each claim's `ref` identifies the exact record URL and page label, accessed 2026-09-17. Because clean web extraction omitted key labels, the actual publisher HTML was also fetched and read as text.

| Subject | Exact record | Read values |
| --- | --- | --- |
| `org:malus-domestica` | [NCBI record 3750](https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?mode=Info&id=3750) | `Taxonomy ID: 3750`; current name `Malus domestica` (authority omitted from our canonical binomial); `Rank: species`. |
| `org:brassica-oleracea` | [NCBI record 3712](https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?mode=Info&id=3712) | `Taxonomy ID: 3712`; current name `Brassica oleracea` (authority omitted); `Rank: species`. |

These are NCBI's record identities, not an adjudication of botanical nomenclature. Species-level verification does not verify the registry's six `convar` assignments.

## Editorial and deliberate gaps

Nine YAML files contain 41 claims: 35 original editorial claims (colour, texture, taste, ELI5, and a short observational/imaginative story for each of apple, cabbage, broccoli, cauliflower, kohlrabi, Brussels sprout, kale), plus six NCBI identity claims. Editorial claims use `SRC-EDITORIAL`, `derivation: editorial`; they are qualitative descriptions, not measurements, health claims, or sourced histories.

Unfilled Task 10 fields remain absent, not placeholder values:

- **Seven `season/DE` claims:** the [BZfE page](https://www.bzfe.de/kueche-und-alltag/einkaufen/der-saisonkalender) was readable and distinguishes imported versus German supply, but no month-by-month crop rows were read. Need the actual chart/legend, applicable graphic terms, and a decision about harvest versus market availability. Do not copy the plan's expressly fictional August–October fixture.
- **Two `origin/primary_region_of_diversity` claims:** Dryad license verified, but matching apple and Brassica commodity rows were not read. Needs approved access to the dataset file, exact row references, and explicit commodity-to-species scope checks. A centre of diversity is not automatically a native range or domestication origin.
- **Growing facts for two species:** ECOCROP's dynamic page did not expose records. Need exact crop entries, units, optimal/absolute range distinctions, and applicable reuse terms. No temperature, rainfall, or pH guesses.
- **Six Brassica infraspecific ranks:** Mansfeld's home loaded via lightweight retrieval, but no target taxon record or license was read. Browser escalation was blocked because the local Camofox service was unavailable. Existing `convar` registry values must remain unverified rather than being treated as externally supported claims.

## Execution check

`load_curated` loaded all 41 claims. With the unchanged source registry, validation returned **0 accepted, 41 rule-9 license gaps**, as expected. An in-memory copy setting only `SRC-EDITORIAL` and `SRC-NCBI-TAXONOMY` to `license_read: true` returned **41 accepted, 0 gaps**; no registry file was changed. Assertions verified all claims have refs and none invent season/origin/growing coverage.

`python -m pytest tests/test_curated.py -q` passed: **1 passed in 0.02s**. A combined pytest invocation could not run because `tests/test_pilot_coverage.py` did not exist at review time. Full Task 10 coverage is intentionally incomplete until the missing primary facts are obtained; licensing flags alone do not fill those gaps.
