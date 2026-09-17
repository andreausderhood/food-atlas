# Food Atlas

A traceable atlas of edible life — pilot: apple and the cabbage family
(*Malus domestica*; *Brassica oleracea* convar. capitata, italica, botrytis,
gongylodes, gemmifera, acephala), including cider and sauerkraut.

Every published value is a claim with a source, a derivation and an evidence
tier. Values that fail the traceability contract (`product.md` §3, rules 1–10)
become named gaps instead of being hidden. See `product.md` for the full
product definition.

`Resources/` is git-ignored and holds Gupta et al. 2026,
doi:10.1038/s41538-026-01066-1.

## Commands

```bash
uv sync                     # install dependencies
uv run pytest               # unit and integration tests
uv run pytest -q -m data    # also run tests against downloaded raw files
uv run atlas fetch <id>     # download a raw source (data/registry/downloads.yaml)
uv run atlas fetch bls --from-file ~/Downloads/BLS_4_0_2025_DE.zip
uv run atlas check-links    # rule 4: check every source URL
uv run atlas build          # validate all claims, write data/build
uv run atlas site           # render the static site to data/build/site
uv run atlas curate fdc apple   # search raw sources while editing foods.yaml
```

Licenses: code MIT (`LICENSE`); curated data CC BY 4.0 (`LICENSE-DATA`);
imported data keeps its upstream license, listed in the generated `NOTICE.md`.
