# Site Design System (Stitch)

> Sources: `stitch_design_system_architecture/food_atlas/DESIGN.md`; four screen mockups (screen.png + code.html each)
> Raw: mockups in-repo under `stitch_design_system_architecture/`
> Updated: 2026-09-21

## The four screens and their data bindings

| Screen | Mockup | Reads from |
| :--- | :--- | :--- |
| **Explorer** — atlas landscape | `food_explorer_atlas_landscape/` | species pool + coverage badges (`not_yet_searched` straight from gap rows) |
| **Workbench** — single food dossier | `food_workbench_zingiber_officinale/` | 3-column rail: identity · organoleptic chemistry; 9 system lanes |
| **Cross-System Matrix** | `multi_food_cross_system_matrix/` | tally counts per epistemic system |
| **Claim Ledger / Gap Register** | `claim_ledger_gap_register/` | gaps + evidence links |

Matrix honesty convention: `0` in `#A39E93` (searched, nothing found), `-` in
`#D4CEBF` (never searched). TCM/Ayurveda lanes stay honest-zero until sources
exist — [the plan](database-and-pipeline-plan.md) keeps this as an open flag.

## Token system (from DESIGN.md)

- **Surfaces**: parchment/linen family (`#fcf9f2` background, `#FBF9F5`
  parchment, `#EAE5DC` subtle, borders `#DDD7CD`/`#ECE7DF`)
- **Epistemic colors** — the system identity: biomedical slate `#2D5A7B`,
  TCM cinnabar `#9E4734`, Ayurveda turmeric `#B87333`, indigenous sage
  `#4A6B53`, alternative woad `#3D7068`, unclassified `#736C65`
- **Type trio with fixed roles**: Newsreader (display/headlines, italic =
  botanical names and quotes — the "attribute, don't assert" voice), Public
  Sans (body, tabular figures for quantitative), JetBrains Mono (badges,
  DOIs, label-mono captions)
- **Status colors**: searched-empty `#A39E93`, unsearched `#D4CEBF`

## Implementation path

DESIGN.md tokens become a single token file consumed by the site builder's
`_style.css.j2`; the four `code.html` mockups convert to Jinja templates with
the bindings above; mockup `screen.png`s are the pixel reference. The existing
site (index/food/compare/gaps templates) gets replaced screen by screen —
Explorer last, since its coverage badges depend on phase-B onboarding data.
