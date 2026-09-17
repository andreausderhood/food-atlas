# Interview implementation

Authority: [interview synthesis](interview-2026-09-17.md). English UI; no photo recognition.

## Implemented

- Entry description above side-by-side nutrition, sensory and research profiles.
- Nutrition: explicit 0–100 g bars, selected FDC record, never a health score or %DV; conflicting amounts and missing values remain explicit. Source, record, basis and part are not merged.
- Sensory: sourced descriptive observations, without fabricated intensity/radar coordinates. Molecular occurrence is linked but not presented as proof of flavour or health effects.
- Research: distinct study-setting sections for explicit metadata; no inference from evidence tier or molecular occurrence. No bioactivity claims were added.
- First-click sections: varieties/relatives, growing here, culinary/technical uses; claims and empty states remain distinguishable.
- Global science mode opens evidence details and scientific records; selection persists locally.
- Combinable include/exclude keyword and quoted-phrase search, research category and existing library filters. This is not natural-language question answering.
- Manual global region/month/mode selector, fresh harvest separate from stored produce. Unknown availability is counted separately, not treated as out of season. State travels through local storage and internal navigation.

## Explicit data boundaries

The current payload has no validated regional harvest calendars or classified bioactivity studies. These controls cannot manufacture answers for “antifungal foods in season”. A season claim becomes filterable only with an explicit `season:<ISO region>:fresh|stored` field and a non-empty month-number list, on an accepted sourced claim. Free-form season prose is still readable but is not guessed into months.

Research settings use explicit `method` prefixes (`human`, `in_vitro`, `in_vivo`, `tradition`, `model`); other bioactivity remains unclassified. This view does not change upstream acceptance rules or imply clinical efficacy.

## Still open from the interview

- Natural-language interpretation of compound research/season questions.
- Evidence-backed bioactivity wheel and comparable quantitative radar profiles. The existing data does not support invented axes or scores.
- Global calendar coverage, geolocation lookup, and fuller growing/culinary records.
- 20–30 carefully worked reference plants within a broader collection: current pilot breadth is smaller and must not be relabelled as finished coverage.
- Imagery: seven taxon reference photographs (Wikimedia Commons, per-image license and credit) on exactly mapped food IDs; cultivars and processed forms stay image-less rather than inheriting a parent photo. Verified in-browser: no broken images, uniform card heights, captions legible.

## Verification

Run `uv run pytest -q`, then `uv run atlas site`. Browser checks: `node tools/qa_interview.cjs` (requires an available Playwright installation). Screenshots are written under ignored `data/build/`.
