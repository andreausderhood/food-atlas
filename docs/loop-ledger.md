# Loop ledger

## Backlog
- editorial: food:apple.pomace, food:apple.cider, food:apple.dried, food:apple.sauce (narrative+sensory, SRC-EDITORIAL, descriptive only)
- editorial: food:cabbage.green, food:cabbage.red, food:cabbage.savoy, food:cabbage.leaf, food:cabbage.juice, food:sauerkraut (narrative+sensory, SRC-EDITORIAL, descriptive only)
- editorial: food:broccoli.leaf, food:broccoli.stalk, food:broccoli.sprouts, food:cauliflower.leaf, food:kohlrabi.leaf, food:kale.frozen (narrative+sensory, SRC-EDITORIAL, descriptive only)
- mapping: BLS 4.0 is downloaded and loads, but 0 claims accepted — foods.yaml needs `bls_codes` mapping per pilot food. Candidates from `atlas curate bls apfel`: F110100 Apfel roh→food:apple, F120100 geschält roh→food:apple.flesh, F110400 getrocknet→food:apple.dried, F110600 Saft→food:apple.juice, F923900 Kompott ungesüßt→food:apple.sauce, P353100 Apfelwein→food:apple.cider. Verify each against fdc_match/foodon before committing; expect SRC-BLS-4.0 claims > 0 after build.
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
- `loop` — 2026-09-17 — 2dd3047 — first loop delivery batch verified: 201 tests, build --no-raw, audit ok

## Blockers
(none)
