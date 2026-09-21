# Pilot Source Review (2026-09-17)

> Sources: Food Atlas project, docs/source-review.md, 2026-09-17
> Raw: [Pilot source review](../../raw/food-atlas-project/2026-09-17-pilot-source-review.md)
> Updated: 2026-09-17

## Overview

Before the pilot could curate facts, each pilot source's license had to be read at its publisher. The review read publisher pages only, with no bulk downloads, and recommended registry actions rather than making them. Four sources cleared for use; three stayed unread or restricted, which left four curated fields deliberately empty.

## License evidence, source by source

| Source | What was read | Verdict |
| :--- | :--- | :--- |
| FoodAtlas v4.11 | The download page ("free resource under the Apache-2.0"), the bundled README ("Released under the Apache-2.0 license."), and the full Apache-2.0 text including redistribution §4 | `license_read: true`, keep `ship`. The clearance does not cover CTD-derived rows |
| NCBI Taxonomy | NCBI policies, "Copyright Status of Webpages": government-created information is public domain, with NLM acknowledgment requested, and a warning that contributed material may carry separate rights | `license_read: true` for the minimal identity fields; do not describe all NCBI-hosted content as unrestricted |
| Editorial (our own text) | `LICENSE-DATA` and the full CC BY 4.0 legal code, attribution §3 | `license_read: true`; replace the placeholder `https://github.com/` URL with the real project URL once known, not an invented one |
| Khoury 2016 (Dryad) | The dataset page's JSON-LD license, "Creative Commons Zero v1.0 Universal", plus the full CC0 legal code | `license_read: true`, keep CC0 and `ship`. License verification is not download approval |
| BZfE Saisonkalender | The current imprint: website **text** is CC licensed, but **not pictures or graphics**, and the actual link is CC BY-NC-ND 4.0 | Keep `cite`, do not promote to `ship`; keep `license_read: false` for the calendar graphic |
| ECOCROP (FAO) | FAO terms, "REUSE OF WEB CONTENT": general reuse is non-commercial, and statistical databases have separate terms. The ECOCROP landing page yielded only its title | Keep `license_read: false` and `cite` pending ECOCROP-specific review |
| Mansfeld (IPK) | The publisher home redirected to a page describing the database, which supplied neither the Brassica rank records nor a reuse grant | Keep `license_read: false` and `cite` |

## Verified taxonomy facts

Two NCBI records were read directly:
- Taxonomy ID 3750, *Malus domestica*, rank species.
- Taxonomy ID 3712, *Brassica oleracea*, rank species.

These are NCBI's record identities, not an adjudication of botanical nomenclature, and species-level verification does not verify the registry's six `convar` assignments.

## What stayed empty, and why

Nine curated YAML files held 41 claims: 35 editorial claims (colour, texture, taste, ELI5 and a short story for each of apple, cabbage, broccoli, cauliflower, kohlrabi, Brussels sprout and kale) plus six NCBI identity claims. Four groups of fields were left absent rather than filled with placeholders:

- **Seven season claims (Germany):** the BZfE page was readable but no month-by-month crop rows were read, and the applicable terms for the calendar graphic are unsettled. The review warns against copying the plan's fixture months, which were invented for tests.
- **Two origin claims:** the Dryad license is verified, but the apple and Brassica commodity rows were not read. It also notes that "A centre of diversity is not automatically a native range or domestication origin."
- **Growing facts for two species:** ECOCROP's dynamic page exposed no records, so no temperature, rainfall or pH values were guessed.
- **Six Brassica infraspecific ranks:** no Mansfeld taxon record was read, so the registry's `convar` values remain unverified rather than externally supported.

## Execution check

With the unchanged registry, validation of the 41 curated claims returned 0 accepted and 41 rule-9 license gaps: exactly what the license gate should do before licenses are read. An in-memory copy that set only the editorial and NCBI sources to `license_read: true` returned 41 accepted and 0 gaps, with no registry file changed.

## See Also

- [Traceability contract](traceability-contract.md)
- [Licensing food data for an MIT atlas](mit-licensing-of-food-data.md)
- [Crop species and variety registers](../food-data-sources/crop-species-and-variety-registers.md)
