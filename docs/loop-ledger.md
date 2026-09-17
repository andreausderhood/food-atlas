# Loop ledger

## Backlog
- editorial: food:apple.flesh, food:apple.peel, food:apple.fuji, food:apple.gala, food:apple.golden-delicious, food:apple.granny-smith, food:apple.honeycrisp, food:apple.red-delicious, food:apple.juice, food:apple.sweet-cider (narrative+sensory, SRC-EDITORIAL, descriptive only)
- editorial: remaining 16 foods without narrative/sensory — derive from `uv run python -c "import json;p=json.load(open('data/build/atlas.json'));print([f['id'] for f in p['foods'] if 'narrative' not in {c['group'] for c in f.get('claims',[])}])"`
- download: BLS 4.0 into data/raw per registry URL (SRC-BLS-4.0, declared_missing_download in audit)
- kuratur: sepia-like CSS filter check on all site images (2 `filter` hits in _style.css.j2 — inspect, remove if it tints photos)
- kuratur: image 6 review on Spotify Explorer + Aesthetics DB repos — belongs to those repos' loops, NOT this one; skip here

## Delivered
(none yet)

## Blockers
(none)
