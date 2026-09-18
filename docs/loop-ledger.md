# Loop ledger

## Backlog
- kuratur: cultivar-specific photos (Fuji, Gala, …) instead of labelled taxon references — optional polish, cron lane
- kuratur: image 6 review on Spotify Explorer + Aesthetics DB repos — belongs to those repos' loops, NOT this one; skip here

## Delivered
- `editorial: food:apple.flesh` — 2026-09-17 — 2dd3047 — narrative+sensory, SRC-EDITORIAL
- `editorial: food:apple.peel` — 2026-09-17 — 2dd3047
- `editorial: food:apple.fuji` — 2026-09-17 — 2dd3047
- `editorial: food:apple.gala` — 2026-09-17 — 2dd3047
- `editorial: food:apple.golden-delicious` — 2026-09-17 — 2dd3047
- `editorial: food:apple.granny-smith` — 2026-09-17 — 2dd3047
- `editorial: food:apple.honeycrisp` — 2026-09-17 — 2dd3047
- `editorial: food:apple.red-delicious` — 2026-09-17 — 2dd3047
- `editorial: food:apple.juice` — 2026-09-17 — 2dd3047
- `editorial: food:apple.sweet-cider` — 2026-09-17 — 2dd3047
- `loop` — 2026-09-18 — 9a665f5, 5ac9532 — BLS mapped onto food:apple (F110100): 110 accepted nutrition claims; ingest fixed for missing Datenherkunft ('-'→unverified, honest T5); license_read via blsdb.de (CC BY 4.0, MRI attribution); 202 tests + audit green
- `loop` — 2026-09-18 — dc79c61 — research phase-one layer delivered & committed (approval gate propose-only, task queue, 1305 queued tasks from gaps); cron now drives the research-week pipeline (docs/research-workflow.md, every 30m)

- `prototype` — 2026-09-19 — 649bc63, 774b2a0, 766b31d — ALL 33 entries fully functional: images on every entry (explicit mapping, visible reference labels), season claims from seasoncalendar foods.db (fresh+storage, DE, cite-class), editorial narrative+sensory on all 16 remaining foods; 232 tests; "DE/October/fresh" filter verified in browser (kale, cabbage, brussels-sprout, kohlrabi, apple)

## Blockers
- Grünkohl-frozen kale season: greencabbage maps to food:kale only; food:kale.frozen has no own calendar (inherits taxon read)
