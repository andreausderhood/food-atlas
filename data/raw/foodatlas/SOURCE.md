# Source record — FoodAtlas bundle v4.11

| Field | Value |
| :--- | :--- |
| Source ID | `SRC-FOODATLAS-V4.11` |
| Publisher | AI Institute for Next Generation Food Systems (AIFS), UC Davis |
| Landing page | https://www.foodatlas.ai/food-composition-downloads |
| File | `foodatlas-v4.11.zip` (53.6 MB) |
| Download URL | https://foodatlasdownloadsstack-downloadsbucketb54b8c20-hfoegjgwag4w.s3.us-west-1.amazonaws.com/bundles/foodatlas-v4.11/foodatlas-v4.11.zip |
| SHA-256 | `591176b9d2bf669c34b2127e4e25c434978f582cd93f8e214c3675d0cb25d320` |
| Release date | 2026-09-11 (KGC run `20260915T081827Z`) |
| Downloaded | 2026-09-17 |
| License | Apache-2.0 (bulk bundle). The API is a separate channel, non-commercial only. |
| Citation | Li, F. et al. (2026). A unified knowledge graph linking foodomics to chemical-disease networks and flavor profiles. *npj Science of Food*. https://doi.org/10.1038/s41538-025-00680-9 |

## Contents (unpacked in `foodatlas-v4.11/`)

| File | Rows | What it is |
| :--- | ---: | :--- |
| `entities.parquet` | 216,804 | Foods (10,270), chemicals (193,236), diseases (13,298) |
| `triplets.parquet` | 542,953 | Links: contains 108,047 · is_a 304,050 · positively correlates 84,099 · negatively correlates 46,757 |
| `attestations.parquet` | 662,821 | One evidence row per claim, with amount where given |
| `attestations_ambiguous.parquet` | 180,771 | Rows whose entities could not be resolved uniquely |
| `evidence.parquet` | 161,966 | References (PubMed, CTD, FDC, ontologies) |
| `trust_signals.parquet` | 5,403 | Machine plausibility scores (gemini-3.1-flash-lite) |
| `relationships.parquet` | 4 | Relationship names r1–r4 |

The raw files are never edited. Everything derived from them is regenerated from this record.
