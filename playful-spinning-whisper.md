# Food Atlas — Pilot Foundation Implementation Plan (Plan 1 of 4)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a working, fully traceable pilot of the Food Atlas: apple plus the cabbage family (*Brassica oleracea*). It uses only freely accessible, MIT-shippable data and involves no outside partners.

**Architecture:**
- **Hand-written YAML registries** hold everything a person curates: sources, organisms, food levels, processes, molecule aliases and curated claims.
- **Importers** read the raw USDA FDC CSVs, the BLS 4.0 Excel file and the FoodAtlas parquet files into one `Claim` model.
- **A single validator** enforces product.md rules 1–10. A claim that fails becomes a named gap.
- **The build writes** DuckDB, JSON and CSV outputs plus `NOTICE.md`.
- **A Jinja2 generator** renders a static site with five views: Foods, Entry, Compare, Gaps and Sources.

**Tech stack:** Python 3.12 (via `uv`), duckdb, PyYAML, openpyxl, Jinja2, pytest.

**Spec:** `/Users/ausderhood/Food Atlas/product.md`. Background reading:
- `research/EXISTING_FOOD_ATLASES_AND_DATASETS.md`
- `research/REVIEW_FOOD_SPECIES_ATLAS_RESOURCES.md`
- `data/raw/foodatlas/SOURCE.md`

---

## Context

`product.md` defines a traceable food lexicon modelled on the user's Victorinox Material & Technology Library (`~/Documents/Dokumente Macbook Air/Claude/victorinox/`). That project used YAML taxonomy files, a Python pipeline, a source-and-tier contract and a single-file site. Research settled which data can ship under the chosen MIT license, and the user asked for an implementation plan that uses **only what is accessible now, without partners**.

Nothing is built yet. The project folder contains only `product.md`, `research/`, `Resources/` (the Gupta et al. 2026 paper) and the downloaded FoodAtlas v4.11 bundle.

This plan delivers Phase 1 of product.md §8. Phases 2–4 get their own plans (see the Roadmap at the end).

## Decisions this plan relies on (asked and answered 2026-09-17)

| ID | Decision |
| :-- | :--- |
| D1 | Open source. Code is MIT. |
| D2 | **Pilot slice: apple + cabbage family.** It covers *Malus domestica* (its cultivars, peel, flesh, juice, pomace, cider and dried apple) and six convarieties of *Brassica oleracea*: capitata (cabbage), italica (broccoli), botrytis (cauliflower), gongylodes (kohlrabi), gemmifera (Brussels sprouts) and acephala (kale). Sauerkraut is included as a lactic-fermentation form. |
| D3 | **English first.** German names (from BLS) are stored as `name_de`. |
| D7 | **Curated data is CC BY 4.0** (`LICENSE-DATA`). |
| D8 | **No partner contact in this plan.** Adapter-only sources (PTFI, FooDB, Phenol-Explorer, BioFoodComp, FishBase) are not used. |

## Global Constraints

- **Python** ≥ 3.12, managed with `uv`. Runtime deps: `duckdb>=1.1`, `pyyaml>=6.0`, `openpyxl>=3.1`, `jinja2>=3.1`. Dev dep: `pytest>=8`.
- **Licenses:**
  - Code is MIT (`LICENSE`).
  - Our curated data is CC BY 4.0 (`LICENSE-DATA`).
  - Imported data keeps its upstream license. The build lists every such source in a generated `NOTICE.md`.
- **Traceability contract (product.md §3, rules 1–10) is enforced by `atlas/contract.py`.** A claim that fails any rule is never published; it becomes a `Gap`. Tier comes from `derivation` and is never typed by hand.
- **License classes:**
  - `ship`: bulk import allowed.
  - `cite`: single curated facts only; no bulk import, no copied text.
  - `adapter` and `separate`: never used in this plan.
- **Amount claims** (groups `nutrition` and `molecules` with a numeric value) must carry `unit`, a `basis` in {`fresh_weight`, `dry_weight`, `as_sold`} and a `food_part`.
- **FoodAtlas CTD rows are never read.** For food–chemical links, only `lit2kg:*` attestations are read; USDA values come from our own FDC import. Evidence sentences from PubMed Central are **not** shipped, only PMC IDs, because their licenses vary.
- **Excluded FoodAtlas foods must never map to a pilot food:**
  - chinese cabbage, which is *Brassica rapa*: e1671, e7808, e1673, e1672;
  - cauliflower fungus, which is *Sparassis*: e10084;
  - siberian kale, which is *Brassica napus*: e1475, e1548.
- **Downloads:** ask the user in chat before each download, stating file name, source and size.
- **No health-claim wording** anywhere (rule 8).
- **Raw files** under `data/raw/` are never edited. They are git-ignored, except each folder's `SOURCE.md`.

## File structure

```
Food Atlas/
├── pyproject.toml · LICENSE · LICENSE-DATA · README.md · NOTICE.md (generated)
├── product.md · research/ · docs/superpowers/plans/2026-09-17-food-atlas-pilot-foundation.md
├── data/
│   ├── registry/                  hand-authored, reviewed, no code
│   │   ├── sources.yaml           source registry (license, class, kind, scope)
│   │   ├── link_status.yaml       machine-owned (atlas check-links)
│   │   ├── downloads.yaml         what `atlas fetch` retrieves
│   │   ├── organisms.yaml         species + infraspecific taxa
│   │   ├── processes.yaml         pressing, drying, fermentation…
│   │   ├── foods.yaml             typed food levels + source mappings + exclusions
│   │   └── molecule_aliases.yaml  FoodAtlas chemical → canonical molecule key
│   ├── curated/                   one YAML per subject: origin, growing, season, sensory, narrative
│   ├── raw/                       downloads (git-ignored except SOURCE.md)
│   └── build/                     generated: atlas.json, atlas.duckdb, claims.csv, gaps.csv, site/
├── src/atlas/
│   ├── __init__.py
│   ├── claims.py        Claim, Gap, derivation→tier
│   ├── registry.py      Source registry loader
│   ├── contract.py      rules 1–10 → accepted claims + gaps
│   ├── foods.py         organisms, processes, food levels, basis/part helpers
│   ├── fetch.py         downloads + SOURCE.md records
│   ├── links.py         link checker (rule 4)
│   ├── ingest/__init__.py · fdc.py · bls.py · foodatlas.py
│   ├── curated.py       curated YAML → claims
│   ├── curate.py        search helpers for mapping raw rows to foods
│   ├── build.py         pipeline + outputs + NOTICE
│   ├── cli.py           `atlas fetch|check-links|build|site|curate`
│   └── site/__init__.py · build.py · templates/*.html.j2
└── tests/
    ├── conftest.py      fixture builders (mini registry, FDC CSVs, BLS xlsx, FoodAtlas parquet)
    ├── test_claims.py · test_registry.py · test_contract.py · test_foods.py
    ├── test_fetch.py · test_fdc.py · test_bls.py · test_foodatlas.py
    ├── test_curated.py · test_build.py · test_site.py · test_cli.py
    ├── test_pilot_coverage.py   repo registry + curated files pass the contract
    └── test_real_data.py        @pytest.mark.data — runs against downloaded raw files
```

## Downloads this plan needs (confirm each in chat before fetching)

| ID | File | Source | Size | License |
| :-- | :--- | :--- | :--- | :--- |
| `fdc-foundation` | `FoodData_Central_foundation_food_csv_2026-04-30.zip` | fdc.nal.usda.gov | 3.8 MB | CC0 |
| `fdc-srlegacy` | `FoodData_Central_sr_legacy_food_csv_2018-04.zip` | fdc.nal.usda.gov | 6.1 MB | CC0 |
| `bls` | `BLS_4_0_2025_DE.zip` (contains `BLS_4_0_Daten_2025_DE.xlsx`) | blsdb.de/download; the link carries a session token, so fetch it via the browser and pass `--from-file` | shown at download | CC BY 4.0 |
| `khoury2016` | Dryad dataset doi:10.5061/dryad.s08t2 | datadryad.org; browser download, then `--from-file` | shown at download | CC0 (Dryad) |
| `foodatlas` | `foodatlas-v4.11.zip` | already present, sha256 `591176b9…d320` | 53.6 MB | Apache-2.0 |

---

### Task 1: Project scaffold, licenses, recorded decisions

**Files:**
- Create:
  - `pyproject.toml`, `.gitignore`, `LICENSE`, `LICENSE-DATA`, `README.md`
  - `src/atlas/__init__.py`, `src/atlas/ingest/__init__.py`, `src/atlas/site/__init__.py`
  - `tests/test_smoke.py`
  - `docs/superpowers/plans/2026-09-17-food-atlas-pilot-foundation.md` (a copy of this plan)
- Modify: `product.md` §3 (rule 9 wording), §8 (pilot line), §9 (D2, D3, D7, D8)

**Interfaces:**
- Produces: the importable package `atlas` with `atlas.__version__ == "0.1.0"`, and the console script `atlas` pointing at `atlas.cli:main` (Task 12).

- [ ] **Step 1: Initialise git and write `pyproject.toml`**

```bash
cd "/Users/ausderhood/Food Atlas" && git init -b main
```

```toml
[project]
name = "food-atlas"
version = "0.1.0"
description = "A traceable atlas of edible life"
requires-python = ">=3.12"
license = "MIT"
dependencies = ["duckdb>=1.1", "pyyaml>=6.0", "openpyxl>=3.1", "jinja2>=3.1"]

[project.scripts]
atlas = "atlas.cli:main"

[dependency-groups]
dev = ["pytest>=8"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/atlas"]

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = ["data: needs downloaded raw files in data/raw (skipped when missing)"]
```

- [ ] **Step 2: Write `.gitignore`, the licenses and the package files**

`.gitignore`:
```
.venv/
__pycache__/
*.pyc
.pytest_cache/
.DS_Store
data/raw/**
!data/raw/**/
!data/raw/**/SOURCE.md
data/build/
Resources/
```

- `LICENSE`: the standard MIT text, with the line `Copyright (c) 2026 Food Atlas contributors`.
- `LICENSE-DATA`: explains that everything under `data/registry/` and `data/curated/` is licensed CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Imported data under `data/raw/` and its derivatives in `data/build/` keep their upstream licenses, as listed in `NOTICE.md`.
- `README.md`: the project purpose (one paragraph linking `product.md`), plus the commands `uv sync`, `uv run pytest`, `uv run atlas fetch <id>`, `uv run atlas build`, `uv run atlas site`. Note that `Resources/` is git-ignored and holds doi:10.1038/s41538-026-01066-1.

`src/atlas/__init__.py`:
```python
"""Food Atlas — a traceable atlas of edible life."""

__version__ = "0.1.0"
```
`src/atlas/ingest/__init__.py` and `src/atlas/site/__init__.py` each contain a one-line docstring.

- [ ] **Step 3: Write the smoke test**

`tests/test_smoke.py`:
```python
import atlas


def test_package_imports():
    assert atlas.__version__ == "0.1.0"
```

- [ ] **Step 4: Install and run the tests**

Run: `uv sync && uv run pytest -q`
Expected: `1 passed`

- [ ] **Step 5: Record the decisions in `product.md`**

Make these edits:
- **§3, rule 9:** append the sentence *"Sources of class `cite` may back single curated facts (marked `curated`) but are never bulk-imported, and no text is copied from them."*
- **§3 Licensing table:** add the row `| **Cite** | Any readable publication | Single facts, entered by hand with a `ref`; no bulk import |`.
- **§8, Phase 1 row:** replace the pilot proposal with *"apple + cabbage family (Malus domestica; Brassica oleracea convar. capitata, italica, botrytis, gongylodes, gemmifera, acephala), including cider and sauerkraut"*.
- **§9:**
  - Mark D2, D3 and D7 as **Decided 2026-09-17**, with the answers from this plan's decision table.
  - Add to D8: *"Plan 1 proceeds without partner contact."*
- **Copy this plan** to `docs/superpowers/plans/2026-09-17-food-atlas-pilot-foundation.md`.

- [ ] **Step 6: Commit**

```bash
git add .gitignore pyproject.toml uv.lock LICENSE LICENSE-DATA README.md src tests product.md research docs data/raw/foodatlas/SOURCE.md
git commit -m "chore: scaffold food-atlas package, licenses and recorded pilot decisions"
```

---

### Task 2: Claim model and derivation → tier

**Files:**
- Create: `src/atlas/claims.py`, `tests/test_claims.py`

**Interfaces:**
- Produces:
  - `Claim` (frozen dataclass): `subject, group, field, v, src, derivation, unit=None, basis=None, food_part=None, method=None, ref=None, v_min=None, v_max=None, n=None, flags=(), curated=False`
  - `Claim.tier -> int` and `Claim.is_amount -> bool` (both properties)
  - `Gap` (frozen dataclass): `subject, field, rule, question, would_be_settled_by, carried_value=None, src=None`
  - `BASES`, `AMOUNT_GROUPS`, `DERIVATION_TIER`
  - `tier_for(derivation) -> int`
  - exception `UnmappedDerivation`

- [ ] **Step 1: Write the failing tests**

`tests/test_claims.py`:
```python
import pytest

from atlas.claims import Claim, tier_for


def test_tier_follows_derivation():
    assert tier_for("analytical") == 1
    assert tier_for("aggregated") == 2
    assert tier_for("registry") == 2
    assert tier_for("extracted") == 3
    assert tier_for("borrowed") == 4
    assert tier_for("editorial") == 4
    assert tier_for("unverified") == 5


def test_unknown_derivation_raises():
    with pytest.raises(ValueError):
        tier_for("guessed")


def test_amount_detection():
    base = dict(subject="food:apple", field="nutrient:fdc:1162", src="S", derivation="analytical")
    assert Claim(group="nutrition", v=4.6, **base).is_amount
    assert not Claim(group="nutrition", v="present", **base).is_amount
    assert not Claim(group="sensory", v=3.0, **base).is_amount
    assert not Claim(group="nutrition", v=True, **base).is_amount


def test_claim_tier_property():
    c = Claim(subject="food:apple", group="nutrition", field="x", v=1.0, src="S", derivation="literature")
    assert c.tier == 3
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_claims.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'atlas.claims'`

- [ ] **Step 3: Implement `src/atlas/claims.py`**

```python
"""Claims are the atoms of the atlas: one value, one source, one derivation."""
from __future__ import annotations

from dataclasses import dataclass

BASES = ("fresh_weight", "dry_weight", "as_sold")
AMOUNT_GROUPS = ("nutrition", "molecules")
DERIVATION_TIER: dict[str, int] = {
    "analytical": 1,
    "aggregated": 2,
    "registry": 2,
    "literature": 3,
    "extracted": 3,
    "calculated": 4,
    "imputed": 4,
    "borrowed": 4,
    "label": 4,
    "assumed_zero": 4,
    "trace": 4,
    "predicted": 4,
    "declared": 4,
    "editorial": 4,
    "unverified": 5,
}


class UnmappedDerivation(ValueError):
    """A source uses a derivation label the atlas has not classified yet."""


def tier_for(derivation: str) -> int:
    try:
        return DERIVATION_TIER[derivation]
    except KeyError:
        raise ValueError(f"unknown derivation: {derivation!r}") from None


@dataclass(frozen=True)
class Claim:
    subject: str
    group: str
    field: str
    v: object
    src: str
    derivation: str
    unit: str | None = None
    basis: str | None = None
    food_part: str | None = None
    method: str | None = None
    ref: str | None = None
    v_min: float | None = None
    v_max: float | None = None
    n: int | None = None
    flags: tuple[str, ...] = ()
    curated: bool = False

    @property
    def tier(self) -> int:
        return tier_for(self.derivation)

    @property
    def is_amount(self) -> bool:
        return (
            self.group in AMOUNT_GROUPS
            and isinstance(self.v, (int, float))
            and not isinstance(self.v, bool)
        )


@dataclass(frozen=True)
class Gap:
    subject: str
    field: str
    rule: int
    question: str
    would_be_settled_by: str
    carried_value: object = None
    src: str | None = None
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_claims.py -q`
Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add src/atlas/claims.py tests/test_claims.py
git commit -m "feat: claim and gap model with derivation-based tiers"
```

---

### Task 3: Source registry

**Files:**
- Create: `src/atlas/registry.py`, `data/registry/sources.yaml`, `tests/test_registry.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `Source` (frozen dataclass): `id, title, publisher, url, license, license_class, license_read, kind, independence, supports, attribution, identifier=None, license_url=None, link_status="unchecked"`
  - `load_sources(path, link_status_path=None) -> dict[str, Source]`
  - `RegistryError`
  - the constants `CLAIM_GROUPS`, `LICENSE_CLASSES`, `KINDS`, `INDEPENDENCE`, `LINK_STATUSES`

- [ ] **Step 1: Write the failing tests**

`tests/test_registry.py`:
```python
import textwrap

import pytest

from atlas.registry import RegistryError, load_sources

GOOD = """
SRC-A:
  title: A
  publisher: P
  url: https://example.org/a
  license: CC0-1.0
  license_class: ship
  license_read: true
  kind: measurement
  independence: independent
  supports: [nutrition]
  attribution: "P. A."
"""


def write(tmp_path, text, name="sources.yaml"):
    p = tmp_path / name
    p.write_text(textwrap.dedent(text), encoding="utf-8")
    return p


def test_loads_source(tmp_path):
    s = load_sources(write(tmp_path, GOOD))["SRC-A"]
    assert s.license_class == "ship" and s.supports == ("nutrition",) and s.link_status == "unchecked"


def test_missing_field_is_an_error(tmp_path):
    with pytest.raises(RegistryError, match="attribution"):
        load_sources(write(tmp_path, GOOD.replace('  attribution: "P. A."\n', "")))


def test_unknown_license_class(tmp_path):
    with pytest.raises(RegistryError, match="license_class"):
        load_sources(write(tmp_path, GOOD.replace("class: ship", "class: maybe")))


def test_unknown_claim_group(tmp_path):
    with pytest.raises(RegistryError, match="claim groups"):
        load_sources(write(tmp_path, GOOD.replace("[nutrition]", "[vibes]")))


def test_link_status_is_merged(tmp_path):
    status = write(tmp_path, "SRC-A: {status: broken, checked: 2026-09-17}\n", "link_status.yaml")
    assert load_sources(write(tmp_path, GOOD), status)["SRC-A"].link_status == "broken"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_registry.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'atlas.registry'`

- [ ] **Step 3: Implement `src/atlas/registry.py`**

```python
"""Source registry: who backs a claim, under which license, for which claim groups."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

CLAIM_GROUPS = (
    "identity", "nutrition", "molecules", "bioactivity", "sensory", "origin",
    "geography", "growing", "season", "process", "regulatory", "narrative",
)
LICENSE_CLASSES = ("ship", "cite", "adapter", "separate")
KINDS = (
    "measurement", "compilation", "registry", "research",
    "literature_extraction", "brand_claim", "library_editorial", "unverified",
)
INDEPENDENCE = ("independent", "declared_by_maker", "library_editorial")
LINK_STATUSES = ("unchecked", "ok", "redirected", "broken")
REQUIRED = (
    "title", "publisher", "url", "license", "license_class", "license_read",
    "kind", "independence", "supports", "attribution",
)


class RegistryError(ValueError):
    pass


@dataclass(frozen=True)
class Source:
    id: str
    title: str
    publisher: str
    url: str
    license: str
    license_class: str
    license_read: bool
    kind: str
    independence: str
    supports: tuple[str, ...]
    attribution: str
    identifier: str | None = None
    license_url: str | None = None
    link_status: str = "unchecked"


def _read(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_sources(path: Path, link_status_path: Path | None = None) -> dict[str, Source]:
    status = _read(link_status_path) if link_status_path and link_status_path.exists() else {}
    sources: dict[str, Source] = {}
    for sid, d in _read(path).items():
        missing = [k for k in REQUIRED if k not in d]
        if missing:
            raise RegistryError(f"{sid}: missing fields {missing}")
        for key, allowed in (("license_class", LICENSE_CLASSES), ("kind", KINDS), ("independence", INDEPENDENCE)):
            if d[key] not in allowed:
                raise RegistryError(f"{sid}: {key} {d[key]!r} not in {allowed}")
        unknown = sorted(set(d["supports"]) - set(CLAIM_GROUPS))
        if unknown:
            raise RegistryError(f"{sid}: unknown claim groups {unknown}")
        link = (status.get(sid) or {}).get("status", "unchecked")
        if link not in LINK_STATUSES:
            raise RegistryError(f"{sid}: link status {link!r} not in {LINK_STATUSES}")
        sources[sid] = Source(
            id=sid, title=d["title"], publisher=d["publisher"], url=d["url"],
            license=d["license"], license_class=d["license_class"],
            license_read=bool(d["license_read"]), kind=d["kind"],
            independence=d["independence"], supports=tuple(d["supports"]),
            attribution=d["attribution"], identifier=d.get("identifier"),
            license_url=d.get("license_url"), link_status=link,
        )
    return sources
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_registry.py -q`
Expected: `5 passed`

- [ ] **Step 5: Write the pilot registry `data/registry/sources.yaml`**

**Rule for filling it in:**
- `license_read: true` only once the license page has actually been opened and read during this step.
- NCBI, Mansfeld, ECOCROP and BZfE start at `false`. Open each `license_url` and flip the flag after reading it.
- If a page does not allow the declared use, change `license_class` to `adapter`, and tell the user.

```yaml
# Food Atlas — source registry. Every claim's `src` must resolve here (rule 2).
# license_class: ship (bulk import allowed) | cite (single curated facts only) | adapter | separate
SRC-FDC-FOUNDATION-2026-04:
  title: "USDA FoodData Central — Foundation Foods (April 2026)"
  publisher: "U.S. Department of Agriculture, Agricultural Research Service"
  url: "https://fdc.nal.usda.gov/download-datasets"
  identifier: "FoodData_Central_foundation_food_csv_2026-04-30.zip"
  license: "CC0-1.0"
  license_url: "https://fdc.nal.usda.gov/faq"
  license_class: ship
  license_read: true
  kind: measurement
  independence: independent
  supports: [identity, nutrition]
  attribution: "U.S. Department of Agriculture, Agricultural Research Service. FoodData Central: Foundation Foods, April 2026. fdc.nal.usda.gov."
SRC-FDC-SRLEGACY-2018-04:
  title: "USDA FoodData Central — SR Legacy (April 2018, final release)"
  publisher: "U.S. Department of Agriculture, Agricultural Research Service"
  url: "https://fdc.nal.usda.gov/download-datasets"
  identifier: "FoodData_Central_sr_legacy_food_csv_2018-04.zip"
  license: "CC0-1.0"
  license_url: "https://fdc.nal.usda.gov/faq"
  license_class: ship
  license_read: true
  kind: compilation
  independence: independent
  supports: [identity, nutrition]
  attribution: "U.S. Department of Agriculture, Agricultural Research Service. FoodData Central: SR Legacy, April 2018. fdc.nal.usda.gov."
SRC-BLS-4.0:
  title: "Bundeslebensmittelschlüssel (BLS), Version 4.0 — Deutsche Nährstoffdatenbank"
  publisher: "Max Rubner-Institut"
  url: "https://blsdb.de/download"
  identifier: "doi:10.25826/Data20251217-134202-0"
  license: "CC-BY-4.0"
  license_url: "https://blsdb.de/download"
  license_class: ship
  license_read: true
  kind: compilation
  independence: independent
  supports: [identity, nutrition]
  attribution: "Max Rubner-Institut (2025): Bundeslebensmittelschlüssel (BLS), Version 4.0 — Deutsche Nährstoffdatenbank. Karlsruhe. DOI: 10.25826/Data20251217-134202-0"
SRC-FOODATLAS-V4.11:
  title: "FoodAtlas knowledge graph bundle v4.11 (CTD-derived rows excluded)"
  publisher: "AI Institute for Next Generation Food Systems, UC Davis"
  url: "https://www.foodatlas.ai/food-composition-downloads"
  identifier: "foodatlas-v4.11.zip, sha256 591176b9d2bf669c34b2127e4e25c434978f582cd93f8e214c3675d0cb25d320"
  license: "Apache-2.0"
  license_url: "https://www.foodatlas.ai/food-composition-downloads"
  license_class: ship
  license_read: true
  kind: literature_extraction
  independence: independent
  supports: [identity, molecules]
  attribution: "Li, F. et al. (2026). A unified knowledge graph linking foodomics to chemical-disease networks and flavor profiles. npj Science of Food. doi:10.1038/s41538-025-00680-9"
SRC-NCBI-TAXONOMY:
  title: "NCBI Taxonomy"
  publisher: "National Center for Biotechnology Information"
  url: "https://www.ncbi.nlm.nih.gov/taxonomy"
  license: "NCBI data use policy"
  license_url: "https://www.ncbi.nlm.nih.gov/home/about/policies/"
  license_class: ship
  license_read: false
  kind: registry
  independence: independent
  supports: [identity]
  attribution: "Schoch, C. L. et al. (2020). NCBI Taxonomy. Database, baaa062."
SRC-MANSFELD:
  title: "Mansfeld's World Database of Agricultural and Horticultural Crops"
  publisher: "Leibniz Institute of Plant Genetics and Crop Plant Research (IPK) Gatersleben"
  url: "https://mansfeld.ipk-gatersleben.de/"
  license: "Cited fact by fact"
  license_url: "https://mansfeld.ipk-gatersleben.de/"
  license_class: cite
  license_read: false
  kind: registry
  independence: independent
  supports: [identity, origin]
  attribution: "Mansfeld's World Database of Agricultural and Horticultural Crops, IPK Gatersleben."
SRC-KHOURY-2016:
  title: "Data from: Origins of food crops connect countries worldwide"
  publisher: "Dryad (Khoury, C. K. et al.)"
  url: "https://datadryad.org/dataset/doi:10.5061/dryad.s08t2"
  identifier: "doi:10.5061/dryad.s08t2"
  license: "CC0-1.0"
  license_url: "https://datadryad.org/stash/terms"
  license_class: ship
  license_read: false
  kind: research
  independence: independent
  supports: [origin]
  attribution: "Khoury, C. K. et al. (2016). Origins of food crops connect countries worldwide. Proc. R. Soc. B 283: 20160792. Data: doi:10.5061/dryad.s08t2"
SRC-ECOCROP:
  title: "FAO ECOCROP — crop environmental requirements"
  publisher: "Food and Agriculture Organization of the United Nations"
  url: "https://gaez.fao.org/pages/ecocrop"
  license: "Cited fact by fact"
  license_url: "https://www.fao.org/contact-us/terms/en/"
  license_class: cite
  license_read: false
  kind: compilation
  independence: independent
  supports: [growing]
  attribution: "FAO. ECOCROP database. gaez.fao.org."
SRC-BZFE-SAISONKALENDER:
  title: "Der Saisonkalender (Obst und Gemüse)"
  publisher: "Bundeszentrum für Ernährung (BZfE)"
  url: "https://www.bzfe.de/kueche-und-alltag/einkaufen/der-saisonkalender"
  license: "Cited fact by fact"
  license_url: "https://www.bzfe.de/impressum"
  license_class: cite
  license_read: false
  kind: compilation
  independence: independent
  supports: [season]
  attribution: "Bundeszentrum für Ernährung. Der Saisonkalender."
SRC-EDITORIAL:
  title: "Food Atlas editorial"
  publisher: "Food Atlas contributors"
  url: "https://github.com/"
  license: "CC-BY-4.0"
  license_class: ship
  license_read: true
  kind: library_editorial
  independence: library_editorial
  supports: [sensory, narrative]
  attribution: "Food Atlas contributors (CC BY 4.0)."
SRC-UNVERIFIED:
  title: "Unverified — no traceable source"
  publisher: "—"
  url: "https://github.com/"
  license: "n/a"
  license_class: ship
  license_read: true
  kind: unverified
  independence: library_editorial
  supports: [identity, nutrition, molecules, bioactivity, sensory, origin, geography, growing, season, process, regulatory, narrative]
  attribution: "—"
```

Once the repository has a public remote, replace the two `https://github.com/` placeholder URLs with the repository URL. Until then `atlas check-links` reports them as `ok`, which is harmless.

- [ ] **Step 6: Add a test that loads the repo registry, then run it**

Append to `tests/test_registry.py`:
```python
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_repo_registry_loads():
    sources = load_sources(REPO / "data/registry/sources.yaml")
    assert {"SRC-FDC-FOUNDATION-2026-04", "SRC-BLS-4.0", "SRC-FOODATLAS-V4.11", "SRC-UNVERIFIED"} <= set(sources)
    assert all(s.license_class in ("ship", "cite") for s in sources.values())
```

Run: `uv run pytest tests/test_registry.py -q`
Expected: `6 passed`

- [ ] **Step 7: Commit**

```bash
git add src/atlas/registry.py data/registry/sources.yaml tests/test_registry.py
git commit -m "feat: source registry with license classes and pilot sources"
```

---

### Task 4: Traceability contract (rules 1–10)

**Files:**
- Create: `src/atlas/contract.py`, `tests/test_contract.py`

**Interfaces:**
- Consumes: `Claim`, `Gap`, `BASES` and `DERIVATION_TIER` (Task 2); `Source` (Task 3).
- Produces:
  - `check(claim, sources) -> Gap | None`
  - `validate(claims, sources) -> ValidationResult`, where `ValidationResult` has `accepted: list[Claim]` and `gaps: list[Gap]`
  - the constant `UNVERIFIED = "SRC-UNVERIFIED"`

**Rule order** (the first failure wins): 2 → 1 → 5 → 9 → 3 → 6 → 10 → 7 → 8 → 4.

- [ ] **Step 1: Write the failing tests**

`tests/test_contract.py`:
```python
import pytest

from atlas.claims import Claim
from atlas.contract import validate
from atlas.registry import Source


def src(sid="S", **kw):
    base = dict(
        id=sid, title="t", publisher="p", url="https://example.org", license="CC0-1.0",
        license_class="ship", license_read=True, kind="measurement", independence="independent",
        supports=("nutrition", "molecules", "bioactivity", "narrative", "season"), attribution="a",
    )
    base.update(kw)
    return Source(**base)


def amount(**kw):
    base = dict(
        subject="food:apple", group="nutrition", field="nutrient:fdc:1162", v=4.6,
        unit="mg", basis="fresh_weight", food_part="whole", src="S", derivation="analytical",
    )
    base.update(kw)
    return Claim(**base)


def rules(claims, sources):
    return [g.rule for g in validate(claims, sources).gaps]


def test_clean_amount_is_accepted():
    r = validate([amount()], {"S": src()})
    assert len(r.accepted) == 1 and r.gaps == []


def test_rule2_unregistered_source():
    assert rules([amount(src="NOPE")], {"S": src()}) == [2]


def test_rule1_unknown_derivation():
    assert rules([amount(derivation="guessed")], {"S": src()}) == [1]


def test_rule5_unverified_is_quarantined():
    assert rules([amount(derivation="unverified")], {"S": src()}) == [5]


def test_rule9_unread_license():
    assert rules([amount()], {"S": src(license_read=False)}) == [9]


def test_rule9_adapter_source_cannot_ship():
    assert rules([amount()], {"S": src(license_class="adapter")}) == [9]


def test_rule9_cite_source_only_for_curated_facts():
    s = {"S": src(license_class="cite", supports=("season",))}
    kw = dict(subject="food:apple", group="season", field="season:DE", v="Aug–Oct", src="S", derivation="registry")
    assert rules([Claim(**kw), Claim(curated=True, **kw)], s) == [9]


def test_rule3_scope():
    assert rules([amount()], {"S": src(supports=("season",))}) == [3]


@pytest.mark.parametrize("change", [dict(basis=None), dict(basis="per_serving"), dict(food_part=None), dict(unit=None)])
def test_rule6_amount_needs_unit_basis_part(change):
    assert rules([amount(**change)], {"S": src()}) == [6]


def test_rule10_extracted_amount_becomes_gap():
    assert rules([amount(derivation="extracted")], {"S": src()}) == [10]


def test_rule10_extracted_presence_is_accepted():
    c = Claim(subject="food:apple", group="molecules", field="contains:CHEBI:16243", v="present",
              src="S", derivation="extracted", flags=("llm_extracted",))
    assert rules([c], {"S": src()}) == []


def test_rule10_secondhand_flag():
    assert rules([amount(flags=("secondhand",))], {"S": src()}) == [10]


def test_rule7_prediction_needs_model_and_version():
    kw = dict(group="bioactivity", v=0.8, derivation="predicted", flags=("evidence_only",))
    bad = amount(method="random forest", **kw)
    good = amount(method="model:frap-rf@2026.1", **kw)
    assert rules([bad, good], {"S": src()}) == [7]


def test_rule8_bioactivity_needs_evidence_flag():
    c = Claim(subject="food:apple", group="bioactivity", field="evidence:antioxidant",
              v="compound-level assay evidence", src="S", derivation="literature")
    assert rules([c], {"S": src()}) == [8]


def test_rule8_health_claim_wording():
    c = Claim(subject="food:apple", group="narrative", field="story",
              v="An anti-inflammatory food that prevents cancer.", src="S", derivation="editorial")
    assert rules([c], {"S": src()}) == [8]


def test_rule8_ordinary_wording_passes():
    c = Claim(subject="food:apple", group="narrative", field="story",
              v="The wax on the peel prevents water loss.", src="S", derivation="editorial")
    assert rules([c], {"S": src()}) == []


def test_rule4_broken_link_blocks_tiers_1_to_3_only():
    broken = {"S": src(link_status="broken")}
    assert rules([amount()], broken) == [4]
    assert rules([amount(derivation="borrowed")], broken) == []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_contract.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'atlas.contract'`

- [ ] **Step 3: Implement `src/atlas/contract.py`**

```python
"""The traceability contract (product.md §3): each claim passes rules 1–10 or becomes a gap."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from atlas.claims import BASES, DERIVATION_TIER, Claim, Gap
from atlas.registry import Source

UNVERIFIED = "SRC-UNVERIFIED"
PREDICTED_METHOD = re.compile(r"^model:[^@\s]+@[^@\s]+$")
HEALTH_CLAIM = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\banti-?(inflammatory|cancer|diabetic|oxidant|viral|bacterial|aging)\s+(foods?|fruits?|vegetables?)\b",
        r"\b(cures?|treats?|prevents?|heals?)\s+(cancer|diabetes|disease|inflammation|infections?)\b",
        r"\bsuper-?foods?\b",
    )
]
TEXT_GROUPS = ("bioactivity", "narrative", "sensory")
SETTLED_BY = {
    1: "A claim with a subject, a field and a known derivation.",
    2: "Register the source in data/registry/sources.yaml.",
    3: "A source whose scope covers this claim group.",
    4: "A working link to the source, or a replacement source.",
    5: "A named, traceable source for this value.",
    6: "Unit, basis (fresh weight, dry weight or as sold) and food part from the original study.",
    7: "The model name and version, written as model:<name>@<version>.",
    8: "Evidence wording without a health claim, flagged evidence_only.",
    9: "A read license that allows open redistribution, or a curated citation of a single fact.",
    10: "The primary study that measured this value.",
}


@dataclass
class ValidationResult:
    accepted: list[Claim] = field(default_factory=list)
    gaps: list[Gap] = field(default_factory=list)


def _gap(claim: Claim, rule: int, question: str) -> Gap:
    return Gap(
        subject=claim.subject, field=claim.field, rule=rule, question=question,
        would_be_settled_by=SETTLED_BY[rule], carried_value=claim.v, src=claim.src,
    )


def check(claim: Claim, sources: dict[str, Source]) -> Gap | None:
    source = sources.get(claim.src)
    if source is None:
        return _gap(claim, 2, f"Source {claim.src!r} is not registered.")
    if not claim.subject or not claim.field or claim.derivation not in DERIVATION_TIER:
        return _gap(claim, 1, f"Incomplete claim or unknown derivation {claim.derivation!r}.")
    if claim.derivation == "unverified" or claim.src == UNVERIFIED:
        return _gap(claim, 5, "Unverified value: the source does not state how it was obtained.")
    if not source.license_read:
        return _gap(claim, 9, f"The license of {source.id} has not been read yet.")
    if source.license_class == "cite" and not claim.curated:
        return _gap(claim, 9, f"{source.id} may only be cited fact by fact, not imported in bulk.")
    if source.license_class not in ("ship", "cite"):
        return _gap(claim, 9, f"{source.id} is {source.license_class}-only and cannot ship under MIT.")
    if claim.group not in source.supports:
        return _gap(claim, 3, f"{source.id} does not support claim group {claim.group!r}.")
    if claim.is_amount and (not claim.unit or claim.basis not in BASES or not claim.food_part):
        return _gap(claim, 6, "Amount without unit, basis or food part.")
    if claim.is_amount and claim.derivation == "extracted":
        return _gap(claim, 10, "Machine-extracted amount; the primary measurement is not confirmed.")
    if "secondhand" in claim.flags:
        return _gap(claim, 10, "Value quoted second-hand from another study.")
    if claim.derivation == "predicted" and not (claim.method and PREDICTED_METHOD.match(claim.method)):
        return _gap(claim, 7, "Prediction without model name and version.")
    if claim.group == "bioactivity" and "evidence_only" not in claim.flags:
        return _gap(claim, 8, "Bioactivity claim not marked as evidence.")
    if claim.group in TEXT_GROUPS and isinstance(claim.v, str) and any(p.search(claim.v) for p in HEALTH_CLAIM):
        return _gap(claim, 8, "The wording reads as a health claim.")
    if claim.tier <= 3 and source.link_status == "broken":
        return _gap(claim, 4, f"The link to {source.id} is broken.")
    return None


def validate(claims: list[Claim], sources: dict[str, Source]) -> ValidationResult:
    result = ValidationResult()
    for claim in claims:
        gap = check(claim, sources)
        if gap is None:
            result.accepted.append(claim)
        else:
            result.gaps.append(gap)
    return result
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_contract.py -q`
Expected: `20 passed`

- [ ] **Step 5: Commit**

```bash
git add src/atlas/contract.py tests/test_contract.py
git commit -m "feat: traceability contract, rules 1-10, failures become gaps"
```

---

### Task 5: Organisms, processes and typed food levels

**Files:**
- Create:
  - `src/atlas/foods.py`
  - `data/registry/organisms.yaml`, `data/registry/processes.yaml`, `data/registry/foods.yaml`, `data/registry/molecule_aliases.yaml`
  - `tests/test_foods.py`

**Interfaces:**
- Produces:
  - `Organism(id, name, rank, parent, ncbi_taxon)`
  - `FoodNode(id, level, name, name_de=None, derives_from=None, is_a=None, part_of=None, part=None, process=None, default_part="whole", foodon=None, foodatlas_ids=(), fdc_match=(), bls_codes=())`
  - `load_organisms(path) -> dict[str, Organism]`
  - `load_processes(path) -> dict[str, str]`
  - `load_foods(path, organisms, processes) -> tuple[dict[str, FoodNode], dict[str, str]]`, returning the nodes and the excluded FoodAtlas IDs mapped to their reasons
  - `food_part(node) -> str`, `basis(node) -> str`, `taxon_of(node, nodes) -> str`
  - the constants `LEVELS`, `PARTS`, `RANKS` and the exception `FoodModelError`

- [ ] **Step 1: Write the failing tests**

`tests/test_foods.py`:
```python
import textwrap
from pathlib import Path

import pytest

from atlas.foods import FoodModelError, basis, food_part, load_foods, load_organisms, load_processes, taxon_of

REPO = Path(__file__).resolve().parents[1]

ORGS = """
org:malus-domestica: {name: Malus domestica, rank: species, parent: null, ncbi_taxon: 3750}
org:brassica-oleracea: {name: Brassica oleracea, rank: species, parent: null, ncbi_taxon: 3712}
org:brassica-oleracea-italica: {name: Brassica oleracea convar. italica, rank: convar, parent: org:brassica-oleracea, ncbi_taxon: null}
"""
PROCS = "proc:drying: {name: Drying}\n"
FOODS = """
excluded_foodatlas:
  e1671: {name: chinese cabbage head, reason: "Brassica rapa, not B. oleracea"}
food:apple: {level: taxon_food, name: Apple, derives_from: org:malus-domestica, foodatlas_ids: [e897]}
food:apple.honeycrisp: {level: cultivar, name: "Apple 'Honeycrisp'", is_a: food:apple}
food:apple.peel: {level: part, name: Apple peel, part_of: food:apple, part: exocarp}
food:apple.dried: {level: form, name: Dried apple, derives_from: food:apple, process: proc:drying}
food:broccoli: {level: taxon_food, name: Broccoli, derives_from: org:brassica-oleracea-italica, default_part: inflorescence}
"""


def reg(tmp_path, foods=FOODS):
    for name, text in (("o.yaml", ORGS), ("p.yaml", PROCS), ("f.yaml", foods)):
        (tmp_path / name).write_text(textwrap.dedent(text), encoding="utf-8")
    orgs = load_organisms(tmp_path / "o.yaml")
    procs = load_processes(tmp_path / "p.yaml")
    return load_foods(tmp_path / "f.yaml", orgs, procs)


def test_valid_tree_and_helpers(tmp_path):
    nodes, excluded = reg(tmp_path)
    assert excluded == {"e1671": "Brassica rapa, not B. oleracea"}
    assert food_part(nodes["food:apple.peel"]) == "exocarp"
    assert food_part(nodes["food:broccoli"]) == "inflorescence"
    assert basis(nodes["food:apple.dried"]) == "as_sold"
    assert basis(nodes["food:apple.honeycrisp"]) == "fresh_weight"
    assert taxon_of(nodes["food:apple.dried"], nodes) == "org:malus-domestica"
    assert taxon_of(nodes["food:broccoli"], nodes) == "org:brassica-oleracea-italica"


def test_cultivar_must_hang_off_a_taxon_food(tmp_path):
    bad = FOODS + "food:x: {level: cultivar, name: X, is_a: food:apple.peel}\n"
    with pytest.raises(FoodModelError, match="cultivar must be is_a a taxon_food"):
        reg(tmp_path, bad)


def test_form_needs_a_process(tmp_path):
    bad = FOODS + "food:x: {level: form, name: X, derives_from: food:apple}\n"
    with pytest.raises(FoodModelError, match="registered process"):
        reg(tmp_path, bad)


def test_excluded_foodatlas_id_cannot_be_mapped(tmp_path):
    bad = FOODS + "food:x: {level: taxon_food, name: X, derives_from: org:brassica-oleracea, foodatlas_ids: [e1671]}\n"
    with pytest.raises(FoodModelError, match="excluded"):
        reg(tmp_path, bad)


def test_foodatlas_id_mapped_twice(tmp_path):
    bad = FOODS + "food:x: {level: taxon_food, name: X, derives_from: org:malus-domestica, foodatlas_ids: [e897]}\n"
    with pytest.raises(FoodModelError, match="mapped to both"):
        reg(tmp_path, bad)


def test_infraspecific_taxon_needs_parent(tmp_path):
    (tmp_path / "o.yaml").write_text("org:x: {name: X, rank: convar, parent: null}\n", encoding="utf-8")
    with pytest.raises(FoodModelError, match="needs a parent"):
        load_organisms(tmp_path / "o.yaml")


def test_repo_registry_loads_with_traps_excluded():
    orgs = load_organisms(REPO / "data/registry/organisms.yaml")
    procs = load_processes(REPO / "data/registry/processes.yaml")
    nodes, excluded = load_foods(REPO / "data/registry/foods.yaml", orgs, procs)
    assert {"e1671", "e7808", "e1673", "e1672", "e10084", "e1475", "e1548"} <= set(excluded)
    taxon_foods = {n.id for n in nodes.values() if n.level == "taxon_food"}
    assert taxon_foods == {
        "food:apple", "food:cabbage", "food:broccoli", "food:cauliflower",
        "food:kohlrabi", "food:brussels-sprout", "food:kale",
    }
    assert nodes["food:sauerkraut"].level == "form"
    assert taxon_of(nodes["food:sauerkraut"], nodes) == "org:brassica-oleracea-capitata"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_foods.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'atlas.foods'`

- [ ] **Step 3: Implement `src/atlas/foods.py`**

```python
"""Organisms, processes and the four typed food levels (product.md §4 Food levels)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

RANKS = ("species", "subspecies", "convar", "var")
LEVELS = ("taxon_food", "cultivar", "part", "form")
PARTS = (
    "whole", "head", "leaf", "inflorescence", "stem", "axillary_bud",
    "exocarp", "mesocarp", "seed", "seedling",
)


class FoodModelError(ValueError):
    pass


@dataclass(frozen=True)
class Organism:
    id: str
    name: str
    rank: str
    parent: str | None
    ncbi_taxon: int | None


@dataclass(frozen=True)
class FoodNode:
    id: str
    level: str
    name: str
    name_de: str | None = None
    derives_from: str | None = None
    is_a: str | None = None
    part_of: str | None = None
    part: str | None = None
    process: str | None = None
    default_part: str = "whole"
    foodon: str | None = None
    foodatlas_ids: tuple[str, ...] = ()
    fdc_match: tuple[str, ...] = ()
    bls_codes: tuple[str, ...] = ()


def _read(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_organisms(path: Path) -> dict[str, Organism]:
    out: dict[str, Organism] = {}
    for oid, d in _read(path).items():
        if not oid.startswith("org:"):
            raise FoodModelError(f"{oid}: organism ids start with 'org:'")
        if d["rank"] not in RANKS:
            raise FoodModelError(f"{oid}: rank {d['rank']!r} not in {RANKS}")
        out[oid] = Organism(oid, d["name"], d["rank"], d.get("parent"), d.get("ncbi_taxon"))
    for o in out.values():
        if o.rank == "species" and o.parent is not None:
            raise FoodModelError(f"{o.id}: a species has no parent in this register")
        if o.rank != "species" and o.parent is None:
            raise FoodModelError(f"{o.id}: an infraspecific taxon needs a parent")
        if o.parent is not None and o.parent not in out:
            raise FoodModelError(f"{o.id}: parent {o.parent!r} is not registered")
    return out


def load_processes(path: Path) -> dict[str, str]:
    return {pid: d["name"] for pid, d in _read(path).items()}


def load_foods(
    path: Path, organisms: dict[str, Organism], processes: dict[str, str]
) -> tuple[dict[str, FoodNode], dict[str, str]]:
    raw = _read(path)
    excluded = {fa: d["reason"] for fa, d in (raw.pop("excluded_foodatlas", None) or {}).items()}
    nodes: dict[str, FoodNode] = {}
    for fid, d in raw.items():
        d = dict(d)
        for key in ("foodatlas_ids", "fdc_match", "bls_codes"):
            d[key] = tuple(d.get(key) or ())
        nodes[fid] = FoodNode(id=fid, **d)
    errors = [e for n in nodes.values() for e in _node_errors(n, nodes, organisms, processes)]
    seen: dict[str, str] = {}
    for n in nodes.values():
        for fa in n.foodatlas_ids:
            if fa in excluded:
                errors.append(f"{n.id}: FoodAtlas {fa} is excluded ({excluded[fa]})")
            if fa in seen:
                errors.append(f"FoodAtlas {fa} mapped to both {seen[fa]} and {n.id}")
            seen[fa] = n.id
    if errors:
        raise FoodModelError("\n".join(errors))
    return nodes, excluded


def _node_errors(n: FoodNode, nodes, organisms, processes) -> list[str]:
    e: list[str] = []
    if not n.id.startswith("food:"):
        e.append(f"{n.id}: food ids start with 'food:'")
    if n.level not in LEVELS:
        return e + [f"{n.id}: level {n.level!r} not in {LEVELS}"]
    if n.default_part not in PARTS:
        e.append(f"{n.id}: default_part {n.default_part!r} not in {PARTS}")
    if n.level == "taxon_food" and n.derives_from not in organisms:
        e.append(f"{n.id}: taxon_food must derive from a registered organism")
    if n.level == "cultivar" and (n.is_a not in nodes or nodes[n.is_a].level != "taxon_food"):
        e.append(f"{n.id}: cultivar must be is_a a taxon_food")
    if n.level == "part":
        if n.part not in PARTS:
            e.append(f"{n.id}: part {n.part!r} not in {PARTS}")
        if n.part_of not in nodes or nodes[n.part_of].level not in ("taxon_food", "cultivar"):
            e.append(f"{n.id}: part must be part_of a taxon_food or cultivar")
    if n.level == "form":
        if n.derives_from not in nodes:
            e.append(f"{n.id}: form must derive from a registered food")
        if n.process not in processes:
            e.append(f"{n.id}: form needs a registered process")
    return e


def food_part(node: FoodNode) -> str:
    return node.part if node.level == "part" else node.default_part


def basis(node: FoodNode) -> str:
    """Raw foods are reported per 100 g fresh edible portion; processed forms as sold."""
    return "as_sold" if node.level == "form" else "fresh_weight"


def taxon_of(node: FoodNode, nodes: dict[str, FoodNode]) -> str:
    seen: set[str] = set()
    cur = node
    while cur.level != "taxon_food":
        if cur.id in seen:
            raise FoodModelError(f"cycle at {cur.id}")
        seen.add(cur.id)
        cur = nodes[cur.is_a or cur.part_of or cur.derives_from]
    return cur.derives_from
```

- [ ] **Step 4: Write the pilot registries**

`data/registry/organisms.yaml`. The NCBI IDs are checked in Step 5.
```yaml
# Species and infraspecific taxa. Ranks for Brassica oleracea follow Mansfeld's World Database.
org:malus-domestica: {name: Malus domestica, rank: species, parent: null, ncbi_taxon: 3750}
org:brassica-oleracea: {name: Brassica oleracea, rank: species, parent: null, ncbi_taxon: 3712}
org:brassica-oleracea-capitata: {name: Brassica oleracea convar. capitata, rank: convar, parent: org:brassica-oleracea, ncbi_taxon: null}
org:brassica-oleracea-italica: {name: Brassica oleracea convar. italica, rank: convar, parent: org:brassica-oleracea, ncbi_taxon: null}
org:brassica-oleracea-botrytis: {name: Brassica oleracea convar. botrytis, rank: convar, parent: org:brassica-oleracea, ncbi_taxon: null}
org:brassica-oleracea-gongylodes: {name: Brassica oleracea convar. gongylodes, rank: convar, parent: org:brassica-oleracea, ncbi_taxon: null}
org:brassica-oleracea-gemmifera: {name: Brassica oleracea convar. gemmifera, rank: convar, parent: org:brassica-oleracea, ncbi_taxon: null}
org:brassica-oleracea-acephala: {name: Brassica oleracea convar. acephala, rank: convar, parent: org:brassica-oleracea, ncbi_taxon: null}
```

`data/registry/processes.yaml`:
```yaml
proc:pressing: {name: Pressing}
proc:drying: {name: Drying}
proc:freezing: {name: Freezing}
proc:sprouting: {name: Sprouting}
proc:alcoholic-fermentation: {name: Alcoholic fermentation}
proc:lactic-fermentation: {name: Lactic acid fermentation}
proc:pureeing: {name: Cooking and puréeing}
```

`data/registry/foods.yaml`:
- FoodAtlas IDs were read from the v4.11 bundle on 2026-09-17.
- The `fdc_match` patterns are first drafts; Task 7 Step 6 checks them against the real files.
- `bls_codes` start empty and are filled in Task 8 Step 6.

```yaml
# Typed food levels (product.md §4). FoodAtlas IDs from bundle v4.11.
excluded_foodatlas:
  e1671: {name: chinese cabbage head, reason: "Brassica rapa, not B. oleracea"}
  e7808: {name: chinese cabbage head (raw), reason: "Brassica rapa, not B. oleracea"}
  e1673: {name: chinese cabbage leaf, reason: "Brassica rapa, not B. oleracea"}
  e1672: {name: chinese cabbage food product, reason: "Brassica rapa, not B. oleracea"}
  e10084: {name: cauliflower fungus, reason: "Sparassis, a fungus, not cauliflower"}
  e1475: {name: siberian kale leaf, reason: "Brassica napus, not B. oleracea"}
  e1548: {name: siberian kale bunch, reason: "Brassica napus, not B. oleracea"}

# ── Apple ────────────────────────────────────────────────────────────────
food:apple:
  level: taxon_food
  name: Apple
  derives_from: org:malus-domestica
  foodon: FOODON_00002473
  foodatlas_ids: [e897, e3974]
  fdc_match: ['Apples, raw, with skin(\b.*)?']
food:apple.flesh:
  level: part
  name: Apple flesh (without skin)
  part_of: food:apple
  part: mesocarp
  fdc_match: ['Apples, raw, without skin(\b.*)?']
food:apple.peel: {level: part, name: Apple peel, part_of: food:apple, part: exocarp, foodatlas_ids: [e8632]}
food:apple.fuji:
  level: cultivar
  name: "Apple 'Fuji'"
  is_a: food:apple
  foodatlas_ids: [e1129]
  fdc_match: ['Apples, (raw, )?fuji, with skin(, raw)?(\b.*)?']
food:apple.gala:
  level: cultivar
  name: "Apple 'Gala'"
  is_a: food:apple
  foodatlas_ids: [e1420]
  fdc_match: ['Apples, (raw, )?gala, with skin(, raw)?(\b.*)?']
food:apple.golden-delicious:
  level: cultivar
  name: "Apple 'Golden Delicious'"
  is_a: food:apple
  foodatlas_ids: [e1994]
  fdc_match: ['Apples, (raw, )?golden delicious, with skin(, raw)?(\b.*)?']
food:apple.granny-smith:
  level: cultivar
  name: "Apple 'Granny Smith'"
  is_a: food:apple
  foodatlas_ids: [e1125]
  fdc_match: ['Apples, (raw, )?granny smith, with skin(, raw)?(\b.*)?']
food:apple.honeycrisp:
  level: cultivar
  name: "Apple 'Honeycrisp'"
  is_a: food:apple
  foodatlas_ids: [e1536]
  fdc_match: ['Apples, (raw, )?honeycrisp, with skin(, raw)?(\b.*)?']
food:apple.red-delicious:
  level: cultivar
  name: "Apple 'Red Delicious'"
  is_a: food:apple
  foodatlas_ids: [e953]
  fdc_match: ['Apples, (raw, )?red delicious, with skin(, raw)?(\b.*)?']
food:apple.juice:
  level: form
  name: Apple juice
  derives_from: food:apple
  process: proc:pressing
  foodatlas_ids: [e61]
  fdc_match: ['Apple juice, canned or bottled, unsweetened(\b.*)?']
food:apple.sweet-cider: {level: form, name: Sweet cider (non-alcoholic), derives_from: food:apple, process: proc:pressing, foodatlas_ids: [e3621]}
food:apple.pomace: {level: form, name: Apple pomace, derives_from: food:apple, process: proc:pressing, foodatlas_ids: [e4089]}
food:apple.cider: {level: form, name: Cider (alcoholic), derives_from: food:apple.juice, process: proc:alcoholic-fermentation, foodatlas_ids: [e248]}
food:apple.dried:
  level: form
  name: Dried apple
  derives_from: food:apple
  process: proc:drying
  foodatlas_ids: [e4088]
  fdc_match: ['Apples, dried, sulfured, uncooked']
food:apple.sauce: {level: form, name: Applesauce, derives_from: food:apple, process: proc:pureeing, foodatlas_ids: [e3619]}

# ── Brassica oleracea ────────────────────────────────────────────────────
food:cabbage:
  level: taxon_food
  name: Cabbage
  derives_from: org:brassica-oleracea-capitata
  default_part: head
  foodatlas_ids: [e1443, e3752]
  fdc_match: ['Cabbage, raw']
food:cabbage.green: {level: cultivar, name: Green cabbage (cultivar group), is_a: food:cabbage, foodatlas_ids: [e7882, e1157], fdc_match: ['Cabbage, (common|green), raw']}
food:cabbage.red: {level: cultivar, name: Red cabbage (cultivar group), is_a: food:cabbage, foodatlas_ids: [e5090, e1158], fdc_match: ['Cabbage, red, raw']}
food:cabbage.savoy: {level: cultivar, name: Savoy cabbage (cultivar group), is_a: food:cabbage, foodatlas_ids: [e1220, e1692], fdc_match: ['Cabbage, savoy, raw']}
food:cabbage.leaf: {level: part, name: Cabbage leaf, part_of: food:cabbage, part: leaf, foodatlas_ids: [e1531]}
food:cabbage.juice: {level: form, name: Cabbage juice, derives_from: food:cabbage, process: proc:pressing, foodatlas_ids: [e4447]}
food:sauerkraut:
  level: form
  name: Sauerkraut
  derives_from: food:cabbage
  process: proc:lactic-fermentation
  foodatlas_ids: [e3796]
  fdc_match: ['Sauerkraut, canned, solids and liquids']
food:broccoli: {level: taxon_food, name: Broccoli, derives_from: org:brassica-oleracea-italica, default_part: inflorescence, foodatlas_ids: [e1442, e3975], fdc_match: ['Broccoli, raw']}
food:broccoli.leaf: {level: part, name: Broccoli leaf, part_of: food:broccoli, part: leaf, foodatlas_ids: [e3303]}
food:broccoli.stalk: {level: part, name: Broccoli stalk, part_of: food:broccoli, part: stem, foodatlas_ids: [e3305]}
food:broccoli.sprouts: {level: form, name: Broccoli sprouts, derives_from: food:broccoli, process: proc:sprouting, foodatlas_ids: [e1190]}
food:cauliflower: {level: taxon_food, name: Cauliflower, derives_from: org:brassica-oleracea-botrytis, default_part: inflorescence, foodatlas_ids: [e1447, e4372], fdc_match: ['Cauliflower, raw']}
food:cauliflower.leaf: {level: part, name: Cauliflower leaf, part_of: food:cauliflower, part: leaf, foodatlas_ids: [e1645]}
food:kohlrabi: {level: taxon_food, name: Kohlrabi, derives_from: org:brassica-oleracea-gongylodes, default_part: stem, foodatlas_ids: [e1458, e7824, e1174], fdc_match: ['Kohlrabi, raw']}
food:kohlrabi.leaf: {level: part, name: Kohlrabi leaf, part_of: food:kohlrabi, part: leaf, foodatlas_ids: [e1173]}
food:brussels-sprout: {level: taxon_food, name: Brussels sprout, derives_from: org:brassica-oleracea-gemmifera, default_part: axillary_bud, foodatlas_ids: [e8759], fdc_match: ['Brussels sprouts, raw']}
food:kale: {level: taxon_food, name: Kale, derives_from: org:brassica-oleracea-acephala, default_part: leaf, foodatlas_ids: [e3460, e5175, e1520, e3461, e1525], fdc_match: ['Kale, raw']}
food:kale.frozen: {level: form, name: Frozen kale, derives_from: food:kale, process: proc:freezing, foodatlas_ids: [e8267], fdc_match: ['Kale, frozen, unprepared']}
```

`data/registry/molecule_aliases.yaml`. The IDs were read from the v4.11 entities table.
```yaml
# FoodAtlas chemical → canonical molecule key, for duplicates the automatic keying misses.
# Automatic keys: fdc_nutrient → nutrient:fdc:<id>, else CHEBI:<id>, else PUBCHEM:<cid>, else FA:<id>.
e64602: {key: "nutrient:fdc:1162", reason: "L-ascorbate (CHEBI:38290) is the conjugate base of L-ascorbic acid (vitamin C)"}
e61395: {key: "nutrient:fdc:1217", reason: "L-phenylalanine is the FDC nutrient phenylalanine (1217)"}
e61593: {key: "nutrient:fdc:1044", reason: "(-)-quinic acid is the FDC nutrient quinic acid (1044)"}
```

- [ ] **Step 5: Verify the taxonomy facts before relying on them**

Open these pages in the browser pane and check each fact:
- **Species IDs:** https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=3750 must be *Malus domestica*, and `?id=3712` must be *Brassica oleracea*.
- **Convariety names:** in Mansfeld (https://mansfeld.ipk-gatersleben.de/), search *Brassica oleracea* and confirm the six convar. names. If Mansfeld uses a different rank or epithet for any of them (for example kale under convar. *acephala*), correct `organisms.yaml` and tell the user.
- **Infraspecific NCBI IDs:** fill in `ncbi_taxon` only where NCBI lists the matching *var.* name, for example "Brassica oleracea var. italica". Otherwise leave it `null`.
- **Licenses:** read the NCBI policy page and the Mansfeld terms, then set `license_read: true` for `SRC-NCBI-TAXONOMY` and `SRC-MANSFELD` in `sources.yaml`.

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest tests/test_foods.py -q`
Expected: `7 passed`

- [ ] **Step 7: Commit**

```bash
git add src/atlas/foods.py data/registry tests/test_foods.py
git commit -m "feat: organisms, processes and typed food levels for the apple + brassica pilot"
```

---

### Task 6: Downloads, provenance records, link checking

**Files:**
- Create: `src/atlas/fetch.py`, `src/atlas/links.py`, `data/registry/downloads.yaml`, `tests/test_fetch.py`
- Generated: `data/registry/link_status.yaml`, and `data/raw/<id>/SOURCE.md` for each download

**Interfaces:**
- Consumes: `Source` and `load_sources` (Task 3).
- Produces:
  - `Download(id, source, url, filename, dest, sha256, unzip, manual)`
  - `load_downloads(path) -> dict[str, Download]`
  - `sha256_of(path) -> str`
  - `fetch(dl, root, from_file=None) -> Path` (returns the destination folder)
  - `check_links(sources, out_path, opener=urllib.request.urlopen) -> dict[str, str]`

- [ ] **Step 1: Write the failing tests**

`tests/test_fetch.py`:
```python
import io
import urllib.error
import zipfile

import pytest
import yaml

from atlas.fetch import Download, fetch, sha256_of
from atlas.links import check_links
from atlas.registry import Source


def make_zip(path):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("inner/food.csv", "fdc_id,description\n1,Apples, raw\n")
    return path


def dl(tmp_path, url, **kw):
    base = dict(id="x", source="SRC-X", url=url, filename="x.zip", dest="data/raw/x",
                sha256=None, unzip=True, manual=None)
    base.update(kw)
    return Download(**base)


def test_fetch_downloads_unzips_and_records(tmp_path):
    z = make_zip(tmp_path / "src.zip")
    root = tmp_path / "proj"
    dest = fetch(dl(tmp_path, z.as_uri()), root)
    assert (dest / "inner/food.csv").exists()
    record = (dest / "SOURCE.md").read_text(encoding="utf-8")
    assert sha256_of(dest / "x.zip") in record and "SRC-X" in record


def test_fetch_rejects_wrong_checksum(tmp_path):
    z = make_zip(tmp_path / "src.zip")
    with pytest.raises(RuntimeError, match="sha256"):
        fetch(dl(tmp_path, z.as_uri(), sha256="0" * 64), tmp_path / "proj")


def test_manual_download_needs_from_file(tmp_path):
    z = make_zip(tmp_path / "src.zip")
    d = dl(tmp_path, "https://example.org/session", manual="Download it in a browser.")
    with pytest.raises(RuntimeError, match="manually"):
        fetch(d, tmp_path / "proj")
    assert (fetch(d, tmp_path / "proj", from_file=z) / "inner/food.csv").exists()


def test_existing_source_record_is_kept(tmp_path):
    z = make_zip(tmp_path / "src.zip")
    dest = tmp_path / "proj/data/raw/x"
    dest.mkdir(parents=True)
    (dest / "SOURCE.md").write_text("hand-written", encoding="utf-8")
    fetch(dl(tmp_path, z.as_uri()), tmp_path / "proj")
    assert (dest / "SOURCE.md").read_text(encoding="utf-8") == "hand-written"


class FakeResponse(io.BytesIO):
    def __init__(self, url):
        super().__init__(b"")
        self._url = url

    def geturl(self):
        return self._url


def test_check_links_classifies(tmp_path):
    def src(sid, url):
        return Source(id=sid, title="t", publisher="p", url=url, license="l", license_class="ship",
                      license_read=True, kind="registry", independence="independent",
                      supports=("identity",), attribution="a")

    def opener(req, timeout):
        url = req.full_url
        if "gone" in url:
            raise urllib.error.HTTPError(url, 404, "nf", {}, None)
        if "blocked" in url:
            raise urllib.error.HTTPError(url, 403, "forbidden", {}, None)
        if "moved" in url:
            return FakeResponse("https://example.org/new")
        return FakeResponse(url)

    sources = {s.id: s for s in (
        src("A", "https://example.org/a"), src("B", "https://example.org/gone"),
        src("C", "https://example.org/blocked"), src("D", "https://example.org/moved"),
    )}
    out = tmp_path / "link_status.yaml"
    assert check_links(sources, out, opener) == {"A": "ok", "B": "broken", "C": "unchecked", "D": "redirected"}
    assert yaml.safe_load(out.read_text(encoding="utf-8"))["B"]["status"] == "broken"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_fetch.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'atlas.fetch'`

- [ ] **Step 3: Implement `src/atlas/fetch.py`**

```python
"""Download raw sources with checksums and write a SOURCE.md provenance record."""
from __future__ import annotations

import hashlib
import shutil
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Download:
    id: str
    source: str
    url: str
    filename: str
    dest: str
    sha256: str | None
    unzip: bool
    manual: str | None


def load_downloads(path: Path) -> dict[str, Download]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {
        k: Download(id=k, source=d["source"], url=d["url"], filename=d["filename"], dest=d["dest"],
                    sha256=d.get("sha256"), unzip=bool(d.get("unzip", False)), manual=d.get("manual"))
        for k, d in raw.items()
    }


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(dl: Download, root: Path, from_file: Path | None = None) -> Path:
    dest = root / dl.dest
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / dl.filename
    if from_file is not None:
        shutil.copyfile(from_file, target)
    elif not target.exists():
        if dl.manual:
            raise RuntimeError(f"{dl.id}: download manually, then pass --from-file. {dl.manual}")
        request = urllib.request.Request(dl.url, headers={"User-Agent": "food-atlas-fetch"})
        with urllib.request.urlopen(request, timeout=300) as response, target.open("wb") as out:
            shutil.copyfileobj(response, out)
    digest = sha256_of(target)
    if dl.sha256 and digest != dl.sha256:
        raise RuntimeError(f"{dl.id}: sha256 {digest} does not match the manifest ({dl.sha256})")
    if dl.unzip:
        with zipfile.ZipFile(target) as z:
            z.extractall(dest)
    record = dest / "SOURCE.md"
    if not record.exists():
        record.write_text(
            f"# Source record — {dl.id}\n\n"
            "| Field | Value |\n| :--- | :--- |\n"
            f"| Source ID | `{dl.source}` |\n"
            f"| File | `{dl.filename}` ({target.stat().st_size:,} bytes) |\n"
            f"| URL | {dl.url} |\n"
            f"| SHA-256 | `{digest}` |\n"
            f"| Fetched | {date.today().isoformat()} |\n\n"
            "Raw files are never edited. License and attribution: `data/registry/sources.yaml`.\n",
            encoding="utf-8",
        )
    return dest
```

- [ ] **Step 4: Implement `src/atlas/links.py`**

```python
"""Rule 4: check every source URL and record the result (machine-owned file)."""
from __future__ import annotations

import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

import yaml

from atlas.registry import Source

UNCHECKABLE = (401, 403, 405, 429)  # servers that refuse automated checks; not proof of a dead link


def check_links(sources: dict[str, Source], out_path: Path, opener=urllib.request.urlopen) -> dict[str, str]:
    results: dict[str, str] = {}
    for s in sources.values():
        request = urllib.request.Request(s.url, method="HEAD", headers={"User-Agent": "food-atlas-linkcheck"})
        try:
            with opener(request, timeout=20) as response:
                same = response.geturl().rstrip("/") == s.url.rstrip("/")
                results[s.id] = "ok" if same else "redirected"
        except urllib.error.HTTPError as e:
            results[s.id] = "unchecked" if e.code in UNCHECKABLE else "broken"
        except (urllib.error.URLError, TimeoutError):
            results[s.id] = "broken"
    today = date.today().isoformat()
    out_path.write_text(
        "# MACHINE-OWNED — written by `atlas check-links`. Do not hand-edit.\n"
        + yaml.safe_dump({k: {"status": v, "checked": today} for k, v in sorted(results.items())}),
        encoding="utf-8",
    )
    return results
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_fetch.py -q`
Expected: `5 passed`

- [ ] **Step 6: Write `data/registry/downloads.yaml`**

```yaml
fdc-foundation:
  source: SRC-FDC-FOUNDATION-2026-04
  url: https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_foundation_food_csv_2026-04-30.zip
  filename: FoodData_Central_foundation_food_csv_2026-04-30.zip
  dest: data/raw/fdc-foundation
  unzip: true
fdc-srlegacy:
  source: SRC-FDC-SRLEGACY-2018-04
  url: https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_csv_2018-04.zip
  filename: FoodData_Central_sr_legacy_food_csv_2018-04.zip
  dest: data/raw/fdc-srlegacy
  unzip: true
bls:
  source: SRC-BLS-4.0
  url: https://blsdb.de/download
  filename: BLS_4_0_2025_DE.zip
  dest: data/raw/bls
  unzip: true
  manual: "Open https://blsdb.de/download and click 'Download BLS-Daten' (the link carries a session token)."
khoury2016:
  source: SRC-KHOURY-2016
  url: https://datadryad.org/dataset/doi:10.5061/dryad.s08t2
  filename: khoury2016-dryad.zip
  dest: data/raw/khoury2016
  unzip: true
  manual: "Open the Dryad page and use 'Download full dataset'."
foodatlas:
  source: SRC-FOODATLAS-V4.11
  url: https://foodatlasdownloadsstack-downloadsbucketb54b8c20-hfoegjgwag4w.s3.us-west-1.amazonaws.com/bundles/foodatlas-v4.11/foodatlas-v4.11.zip
  filename: foodatlas-v4.11.zip
  dest: data/raw/foodatlas
  sha256: 591176b9d2bf669c34b2127e4e25c434978f582cd93f8e214c3675d0cb25d320
  unzip: true
```

- [ ] **Step 7: Fetch the pilot data (ask the user first; see the Downloads table)**

After the user confirms in chat, run the following. The CLI arrives in Task 13, so call the functions directly:
```bash
uv run python -c "
from pathlib import Path
from atlas.fetch import fetch, load_downloads
root = Path('.'); d = load_downloads(root / 'data/registry/downloads.yaml')
for k in ('fdc-foundation', 'fdc-srlegacy', 'foodatlas'):
    print(fetch(d[k], root))
"
```

For BLS and Khoury:
1. Download each zip in the browser pane, after the user confirms.
2. Import each one with `fetch(d['bls'], root, from_file=Path('<downloaded zip>'))`, and the same for `khoury2016`.
3. Add each printed SHA-256 to `downloads.yaml`, so later fetches are verified.

Expected: `data/raw/fdc-foundation/…/food_nutrient.csv`, `data/raw/fdc-srlegacy/…/food_nutrient.csv`, `data/raw/bls/…/BLS_4_0_Daten_2025_DE.xlsx` and `data/raw/khoury2016/…` all exist, and each folder has a `SOURCE.md`.

- [ ] **Step 8: Check the links once**

```bash
uv run python -c "
from pathlib import Path
from atlas.links import check_links
from atlas.registry import load_sources
r = Path('data/registry'); print(check_links(load_sources(r/'sources.yaml'), r/'link_status.yaml'))
"
```
Expected: no source reports `broken`. If one does, find the current URL, fix `sources.yaml` and run the check again.

- [ ] **Step 9: Commit**

```bash
git add src/atlas/fetch.py src/atlas/links.py data/registry/downloads.yaml data/registry/link_status.yaml tests/test_fetch.py data/raw
git commit -m "feat: checksummed downloads, provenance records and link checking"
```

`git add data/raw` stages only the `SOURCE.md` files, because of `.gitignore`.

---

### Task 7: USDA FoodData Central importer

**Files:**
- Create:
  - `src/atlas/ingest/fdc.py`, `src/atlas/curate.py`
  - `tests/conftest.py` (FDC part), `tests/test_fdc.py`, `tests/test_real_data.py` (FDC part)

**Interfaces:**
- Consumes:
  - `Claim` and `UnmappedDerivation` (Task 2)
  - `FoodNode`, `basis` and `food_part` (Task 5)
- Produces:
  - `classify_derivation(description) -> str`
  - `find_csv_dir(root) -> Path`
  - `read_csv_rows(path) -> Iterator[dict]`
  - `match_foods(descriptions: dict[str, str], nodes) -> dict[str, str]`, mapping `fdc_id` to a food id
  - `load_fdc(root, src_id, nodes) -> tuple[list[Claim], dict[str, dict]]`, returning the claims and the nutrient definitions keyed `nutrient:fdc:<id>` → `{"name", "unit"}`
  - `FdcMappingError`
  - `atlas.curate.search_fdc(root, query) -> list[str]`

**FDC CSV columns used:**
- `food.csv`: `fdc_id`, `description`
- `nutrient.csv`: `id`, `name`, `unit_name`
- `food_nutrient_derivation.csv`: `id`, `description`
- `food_nutrient.csv`: `fdc_id`, `nutrient_id`, `amount`, `data_points`, `derivation_id`, `min`, `max`

Columns are read by name, so any extra columns are ignored.

- [ ] **Step 1: Add the FDC fixture to `tests/conftest.py`**

```python
import csv
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def write_csv(path: Path, header: list, rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


@pytest.fixture
def fdc_dir(tmp_path):
    d = tmp_path / "fdc" / "FoodData_Central_foundation_food_csv_2026-04-30"
    write_csv(d / "food_nutrient_derivation.csv", ["id", "code", "description"], [
        [1, "A", "Analytical"], [2, "AS", "Summed"], [3, "Z", "Assumed zero"],
        [4, "BFFN", "Based on another form of the food"], [5, "MA", "Manufacturer's analytical"],
    ])
    write_csv(d / "nutrient.csv", ["id", "name", "unit_name", "nutrient_nbr", "rank"], [
        [1162, "Vitamin C, total ascorbic acid", "MG", 401, 6300],
        [1008, "Energy", "KCAL", 208, 300],
    ])
    write_csv(d / "food.csv", ["fdc_id", "data_type", "description", "food_category_id", "publication_date"], [
        [100, "foundation_food", "Apples, honeycrisp, with skin, raw", 9, "2020-10-30"],
        [101, "foundation_food", "Apples, dried, sulfured, uncooked", 9, "2020-10-30"],
        [102, "foundation_food", "Bananas, raw", 9, "2020-10-30"],
    ])
    write_csv(d / "food_nutrient.csv",
              ["id", "fdc_id", "nutrient_id", "amount", "data_points", "derivation_id",
               "min", "max", "median", "footnote", "min_year_acquired"], [
        [1, 100, 1162, 4.6, 8, 1, 2.1, 6.0, 4.4, "", 2019],
        [2, 100, 1008, 58, "", 2, "", "", "", "", ""],
        [3, 100, 1162, "", "", 1, "", "", "", "", ""],
        [4, 101, 1162, 3.9, 2, "", "", "", "", "", ""],
        [5, 102, 1162, 8.7, 4, 1, "", "", "", "", ""],
    ])
    return tmp_path / "fdc"


@pytest.fixture
def mini_nodes():
    from atlas.foods import FoodNode
    return {
        "food:apple": FoodNode(id="food:apple", level="taxon_food", name="Apple",
                               derives_from="org:malus-domestica", foodatlas_ids=("e897",), bls_codes=("F110100",)),
        "food:apple.honeycrisp": FoodNode(id="food:apple.honeycrisp", level="cultivar", name="Apple 'Honeycrisp'",
                                          is_a="food:apple", foodatlas_ids=("e1536",),
                                          fdc_match=("Apples, honeycrisp, with skin, raw",)),
        "food:apple.dried": FoodNode(id="food:apple.dried", level="form", name="Dried apple",
                                     derives_from="food:apple", process="proc:drying",
                                     fdc_match=("Apples, dried, sulfured, uncooked",)),
    }
```
The fixture numbers are made up for the tests; they are not real nutrition facts.

- [ ] **Step 2: Write the failing tests**

`tests/test_fdc.py`:
```python
import pytest

from atlas.claims import UnmappedDerivation
from atlas.foods import FoodNode
from atlas.ingest.fdc import FdcMappingError, classify_derivation, load_fdc, match_foods


@pytest.mark.parametrize("text, expected", [
    ("Analytical", "analytical"),
    ("Summed", "calculated"),
    ("Assumed zero", "assumed_zero"),
    ("Based on another form of the food", "borrowed"),
    ("Manufacturer's analytical", "label"),
    ("Calculated from analytical data", "calculated"),
    ("Imputed", "imputed"),
])
def test_classify_derivation(text, expected):
    assert classify_derivation(text) == expected


def test_unknown_derivation_text_raises():
    with pytest.raises(UnmappedDerivation):
        classify_derivation("Vibes")


def test_load_fdc_claims(fdc_dir, mini_nodes):
    claims, nutrients = load_fdc(fdc_dir, "SRC-FDC", mini_nodes)
    by = {(c.subject, c.field): c for c in claims}
    vitc = by[("food:apple.honeycrisp", "nutrient:fdc:1162")]
    assert (vitc.v, vitc.unit, vitc.basis, vitc.food_part, vitc.derivation) == (4.6, "mg", "fresh_weight", "whole", "analytical")
    assert (vitc.v_min, vitc.v_max, vitc.n, vitc.ref) == (2.1, 6.0, 8, "fdc:100")
    assert by[("food:apple.honeycrisp", "nutrient:fdc:1008")].derivation == "calculated"
    dried = by[("food:apple.dried", "nutrient:fdc:1162")]
    assert dried.basis == "as_sold" and dried.derivation == "unverified"
    assert len(claims) == 3  # empty amount skipped, banana unmapped
    assert nutrients["nutrient:fdc:1162"] == {"name": "Vitamin C, total ascorbic acid", "unit": "mg"}


def test_processed_description_needs_a_form(mini_nodes):
    nodes = dict(mini_nodes)
    nodes.pop("food:apple.dried")
    nodes["food:apple.honeycrisp"] = FoodNode(id="food:apple.honeycrisp", level="cultivar", name="x",
                                              is_a="food:apple", fdc_match=("Apples, dried.*",))
    with pytest.raises(FdcMappingError, match="not a form"):
        match_foods({"101": "Apples, dried, sulfured, uncooked"}, nodes)


def test_one_description_two_foods_is_an_error(mini_nodes):
    nodes = dict(mini_nodes)
    nodes["food:apple.dried"] = FoodNode(id="food:apple.dried", level="form", name="x", derives_from="food:apple",
                                         process="proc:drying", fdc_match=("Apples, honeycrisp.*",))
    with pytest.raises(FdcMappingError, match="several foods"):
        match_foods({"100": "Apples, honeycrisp, with skin, raw"}, nodes)
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run pytest tests/test_fdc.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'atlas.ingest.fdc'`

- [ ] **Step 4: Implement `src/atlas/ingest/fdc.py`**

```python
"""USDA FoodData Central CSV (Foundation Foods, SR Legacy) → nutrition claims."""
from __future__ import annotations

import csv
import re
from collections.abc import Iterator
from pathlib import Path

from atlas.claims import Claim, UnmappedDerivation
from atlas.foods import FoodNode, basis, food_part

REQUIRED_FILES = ("food.csv", "food_nutrient.csv", "nutrient.csv", "food_nutrient_derivation.csv")
# Ordered: the first matching rule wins, so "calculated from analytical" is calculated.
DERIVATION_RULES = (
    (("assumed zero",), "assumed_zero"),
    (("manufacturer", "label"), "label"),
    (("based on", "another form", "similar food", "borrowed"), "borrowed"),
    (("calculated", "summed", "recipe", "formula", "ratio", "computed"), "calculated"),
    (("imputed", "estimated", "assumed"), "imputed"),
    (("analytical", "analysis"), "analytical"),
)
NOT_RAW = re.compile(
    r"\b(cooked|boiled|baked|fried|roasted|dried|dehydrated|frozen|canned|juice|sauce|pickled)\b", re.IGNORECASE
)


class FdcMappingError(ValueError):
    pass


def classify_derivation(description: str) -> str:
    text = description.lower()
    for keys, derivation in DERIVATION_RULES:
        if any(k in text for k in keys):
            return derivation
    raise UnmappedDerivation(f"FDC derivation {description!r}")


def find_csv_dir(root: Path) -> Path:
    hits = sorted(root.rglob("food_nutrient.csv"))
    if len(hits) != 1:
        raise FileNotFoundError(f"expected one food_nutrient.csv under {root}, found {len(hits)}")
    folder = hits[0].parent
    missing = [f for f in REQUIRED_FILES if not (folder / f).exists()]
    if missing:
        raise FileNotFoundError(f"{folder}: missing {missing}")
    return folder


def read_csv_rows(path: Path) -> Iterator[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        yield from csv.DictReader(f)


def match_foods(descriptions: dict[str, str], nodes: dict[str, FoodNode]) -> dict[str, str]:
    patterns = [(n.id, re.compile(p, re.IGNORECASE)) for n in nodes.values() for p in n.fdc_match]
    matched: dict[str, str] = {}
    for fdc_id, desc in descriptions.items():
        hits = sorted({node_id for node_id, p in patterns if p.fullmatch(desc)})
        if len(hits) > 1:
            raise FdcMappingError(f"FDC {fdc_id} {desc!r} matches several foods: {hits}")
        if hits:
            node_id = hits[0]
            if nodes[node_id].level != "form" and NOT_RAW.search(desc):
                raise FdcMappingError(f"FDC {fdc_id} {desc!r} is processed but {node_id} is not a form")
            matched[fdc_id] = node_id
    return matched


def _num(value: str | None) -> float | None:
    return float(value) if value not in (None, "") else None


def load_fdc(root: Path, src_id: str, nodes: dict[str, FoodNode]) -> tuple[list[Claim], dict[str, dict]]:
    folder = find_csv_dir(root)
    derivation_text = {r["id"]: r["description"] for r in read_csv_rows(folder / "food_nutrient_derivation.csv")}
    nutrients = {r["id"]: {"name": r["name"], "unit": r["unit_name"].lower()} for r in read_csv_rows(folder / "nutrient.csv")}
    matched = match_foods({r["fdc_id"]: r["description"] for r in read_csv_rows(folder / "food.csv")}, nodes)
    claims: list[Claim] = []
    used: dict[str, dict] = {}
    for r in read_csv_rows(folder / "food_nutrient.csv"):
        node_id = matched.get(r["fdc_id"])
        if node_id is None or r.get("amount", "") == "":
            continue
        node = nodes[node_id]
        derivation_id = r.get("derivation_id") or ""
        derivation = classify_derivation(derivation_text[derivation_id]) if derivation_id else "unverified"
        key = f"nutrient:fdc:{r['nutrient_id']}"
        used[key] = nutrients[r["nutrient_id"]]
        claims.append(Claim(
            subject=node_id, group="nutrition", field=key, v=float(r["amount"]),
            unit=used[key]["unit"], basis=basis(node), food_part=food_part(node),
            src=src_id, derivation=derivation, ref=f"fdc:{r['fdc_id']}",
            v_min=_num(r.get("min")), v_max=_num(r.get("max")),
            n=int(r["data_points"]) if r.get("data_points") else None,
        ))
    return claims, used
```

- [ ] **Step 5: Implement `src/atlas/curate.py` (FDC search)**

```python
"""Search helpers for mapping raw source rows onto food nodes (used while editing foods.yaml)."""
from __future__ import annotations

from pathlib import Path

from atlas.ingest.fdc import find_csv_dir, read_csv_rows

FDC_DIRS = ("data/raw/fdc-foundation", "data/raw/fdc-srlegacy")


def search_fdc(root: Path, query: str) -> list[str]:
    q = query.lower()
    out = []
    for rel in FDC_DIRS:
        folder = find_csv_dir(root / rel)
        for r in read_csv_rows(folder / "food.csv"):
            if q in r["description"].lower():
                out.append(f"{Path(rel).name}\t{r['fdc_id']}\t{r['description']}")
    return out
```

Run: `uv run pytest tests/test_fdc.py -q`
Expected: `11 passed`

- [ ] **Step 6: Map the real FDC foods and add the real-data test**

1. Print the candidate descriptions:
   ```bash
   uv run python -c "
   from pathlib import Path; from atlas.curate import search_fdc
   for q in ('apple', 'cabbage', 'broccoli', 'cauliflower', 'kohlrabi', 'brussels', 'kale', 'sauerkraut'):
       print('\n'.join(search_fdc(Path('.'), q)))"
   ```
2. **Adjust the `fdc_match` patterns** in `foods.yaml` so that each raw food matches its node:
   - raw whole foods and raw cultivars → the taxon or cultivar node;
   - "without skin" → `food:apple.flesh`;
   - dried, juice, frozen or sauerkraut → the form node.
3. **Leave everything else unmatched,** such as cooked dishes, baby food and unrelated brands. Do not invent nodes for them in this plan.

`tests/test_real_data.py`:
```python
from pathlib import Path

import pytest

from atlas.foods import load_foods, load_organisms, load_processes

REPO = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.data
FDC = {"data/raw/fdc-foundation": "SRC-FDC-FOUNDATION-2026-04", "data/raw/fdc-srlegacy": "SRC-FDC-SRLEGACY-2018-04"}


def need(rel: str) -> Path:
    path = REPO / rel
    if not path.exists():
        pytest.skip(f"{rel} not downloaded")
    return path


@pytest.fixture(scope="module")
def nodes():
    reg = REPO / "data/registry"
    orgs, procs = load_organisms(reg / "organisms.yaml"), load_processes(reg / "processes.yaml")
    return load_foods(reg / "foods.yaml", orgs, procs)[0]


def test_fdc_maps_pilot_foods_and_classifies_every_used_derivation(nodes):
    from atlas.ingest.fdc import load_fdc
    subjects = set()
    for rel, src in FDC.items():
        claims, _ = load_fdc(need(rel), src, nodes)  # raises on unmapped derivations or bad mappings
        subjects |= {c.subject for c in claims}
    expected = {n.id for n in nodes.values() if n.fdc_match}
    assert expected <= subjects, f"no FDC rows for {sorted(expected - subjects)}"
```

Run: `uv run pytest tests/test_real_data.py -q -m data`
Expected: `1 passed`.
- If a derivation is unmapped, add the missing keyword to `DERIVATION_RULES` (and a case to `test_classify_derivation`), based on the description text printed in the error.
- If a node has no rows, fix its pattern or remove its `fdc_match`.

- [ ] **Step 7: Commit**

```bash
git add src/atlas/ingest/fdc.py src/atlas/curate.py tests/conftest.py tests/test_fdc.py tests/test_real_data.py data/registry/foods.yaml
git commit -m "feat: FoodData Central importer with derivation-based tiers and pilot mapping"
```

---

### Task 8: BLS 4.0 importer

**Files:**
- Create: `src/atlas/ingest/bls.py`, `tests/test_bls.py`
- Modify:
  - `tests/conftest.py` (add the `bls_dir` fixture)
  - `src/atlas/curate.py` (add `search_bls`)
  - `tests/test_real_data.py` (add the BLS test)
  - `data/registry/foods.yaml` (fill in `bls_codes`)

**Interfaces:**
- Consumes: `Claim` and `UnmappedDerivation` (Task 2); `FoodNode`, `basis` and `food_part` (Task 5).
- Produces:
  - `HERKUNFT: dict[str, str]`
  - `find_workbook(root) -> Path`
  - `nutrient_columns(headers) -> list[tuple[int, int, int]]`
  - `parse_value_header(header) -> tuple[str, str, str | None]`
  - `load_bls(root, src_id, nodes) -> tuple[list[Claim], dict[str, dict], dict[str, str]]`, returning the claims, the nutrient definitions keyed `nutrient:bls:<TAG>`, and each food id's German name
  - `atlas.curate.search_bls(root, query) -> list[str]`

**File layout** (BLS FAQ 15, read 2026-09-17):
- The file is `BLS_4_0_Daten_2025_DE.xlsx`.
- Columns 1–3 hold the BLS code, the German name and the English name.
- Each of the 138 nutrients then has three columns: value, *Datenherkunft* (data origin) and *Referenz* (reference).
- All values are per 100 g edible portion.
- An empty value means **missing, not zero** (FAQ 11).
- The 13 data-origin categories come from FAQ 6.
- The FAQ says 418 columns in total, while 3 + 3 × 138 = 417. The parser therefore locates the triples by their "Datenherkunft" headers instead of by position.

- [ ] **Step 1: Add the `bls_dir` fixture to `tests/conftest.py`**

```python
@pytest.fixture
def bls_dir(tmp_path):
    from openpyxl import Workbook
    d = tmp_path / "bls" / "BLS_4_0_2025_DE"
    d.mkdir(parents=True)
    wb = Workbook()
    ws = wb.active
    ws.append(["BLS Code", "Lebensmittelbezeichnung", "Food name",
               "ENERCC Energie (Kilokalorien) [kcal/100g]", "ENERCC Datenherkunft", "ENERCC Referenz",
               "VITC Vitamin C [mg/100g]", "VITC Datenherkunft", "VITC Referenz"])
    ws.append(["F110100", "Apfel roh", "Apple raw", 52, "Aggregation", "R1", None, None, None])
    ws.append(["F999999", "Banane roh", "Banana raw", 93, "Analyse", "R2", 11, "Analyse", "R3"])
    wb.save(d / "BLS_4_0_Daten_2025_DE.xlsx")
    return tmp_path / "bls"
```

- [ ] **Step 2: Write the failing tests**

`tests/test_bls.py`:
```python
import pytest
from openpyxl import load_workbook

from atlas.claims import UnmappedDerivation
from atlas.ingest.bls import HERKUNFT, load_bls, nutrient_columns, parse_value_header


def test_all_thirteen_origin_categories_are_mapped():
    assert len(HERKUNFT) == 13


def test_parse_value_header():
    assert parse_value_header("ENERCC Energie (Kilokalorien) [kcal/100g]") == ("ENERCC", "Energie (Kilokalorien)", "kcal")
    assert parse_value_header("VITC Vitamin C [mg/100 g]") == ("VITC", "Vitamin C", "mg")
    assert parse_value_header("FIBT Ballaststoffe") == ("FIBT", "Ballaststoffe", None)


def test_nutrient_columns():
    headers = ["code", "de", "en", "A x [g]", "A Datenherkunft", "A Referenz", "B y [mg]", "B Datenherkunft", "B Referenz"]
    assert nutrient_columns(headers) == [(3, 4, 5), (6, 7, 8)]


def test_load_bls(bls_dir, mini_nodes):
    claims, nutrients, names_de = load_bls(bls_dir, "SRC-BLS", mini_nodes)
    assert len(claims) == 1  # apple energy only; empty vitamin C is missing, banana is unmapped
    c = claims[0]
    assert (c.subject, c.field, c.v, c.unit, c.basis, c.food_part, c.derivation) == (
        "food:apple", "nutrient:bls:ENERCC", 52.0, "kcal", "fresh_weight", "whole", "aggregated")
    assert c.ref == "bls:F110100; R1"
    assert nutrients["nutrient:bls:ENERCC"] == {"name": "Energie (Kilokalorien)", "unit": "kcal"}
    assert names_de == {"food:apple": "Apfel roh"}


def test_unknown_origin_raises(bls_dir, mini_nodes):
    path = next(bls_dir.rglob("*.xlsx"))
    wb = load_workbook(path)
    wb.active["E2"] = "Bauchgefühl"
    wb.save(path)
    with pytest.raises(UnmappedDerivation, match="Bauchgefühl"):
        load_bls(bls_dir, "SRC-BLS", mini_nodes)
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run pytest tests/test_bls.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'atlas.ingest.bls'`

- [ ] **Step 4: Implement `src/atlas/ingest/bls.py`**

```python
"""BLS 4.0 (Max Rubner-Institut, CC BY 4.0) → nutrition claims."""
from __future__ import annotations

import re
from pathlib import Path

from openpyxl import load_workbook

from atlas.claims import Claim, UnmappedDerivation
from atlas.foods import FoodNode, basis, food_part

# BLS FAQ 6: the 13 categories of Datenherkunft.
HERKUNFT = {
    "Analyse": "analytical",
    "Literatur": "literature",
    "Aggregation": "aggregated",
    "Rezeptberechnung": "calculated",
    "Musterberechnung": "calculated",
    "Formelberechnung": "calculated",
    "Reskalierung": "calculated",
    "Nährstoffdatenbank": "borrowed",
    "Übernommener Wert": "borrowed",
    "Labelangabe": "label",
    "Logische Null": "assumed_zero",
    "Logische Annahme": "imputed",
    "Spuren": "trace",
}
ORIGIN_HEADER = re.compile(r"herkunft", re.IGNORECASE)
UNIT = re.compile(r"\[\s*([^\]/]+?)\s*(?:/\s*100\s*g)?\s*\]")


def find_workbook(root: Path) -> Path:
    hits = sorted(root.rglob("BLS_4_0_Daten_*.xlsx"))
    if len(hits) != 1:
        raise FileNotFoundError(f"expected one BLS_4_0_Daten_*.xlsx under {root}, found {len(hits)}")
    return hits[0]


def nutrient_columns(headers: list[str]) -> list[tuple[int, int, int]]:
    """(value, origin, reference) column indexes, located by the 'Datenherkunft' header."""
    return [(i - 1, i, i + 1) for i, h in enumerate(headers) if i >= 4 and ORIGIN_HEADER.search(h)]


def parse_value_header(header: str) -> tuple[str, str, str | None]:
    tag, _, rest = header.strip().partition(" ")
    match = UNIT.search(rest)
    return tag, UNIT.sub("", rest).strip(), (match.group(1).strip() if match else None)


def load_bls(root: Path, src_id: str, nodes: dict[str, FoodNode]) -> tuple[list[Claim], dict[str, dict], dict[str, str]]:
    wb = load_workbook(find_workbook(root), read_only=True, data_only=True)
    rows = wb.worksheets[0].iter_rows(values_only=True)
    headers = ["" if h is None else str(h) for h in next(rows)]
    triples = nutrient_columns(headers)
    if not triples:
        raise ValueError("no 'Datenherkunft' columns found in the BLS workbook")
    wanted = {code: node for node in nodes.values() for code in node.bls_codes}
    claims: list[Claim] = []
    used: dict[str, dict] = {}
    names_de: dict[str, str] = {}
    for row in rows:
        node = wanted.get("" if row[0] is None else str(row[0]).strip())
        if node is None:
            continue
        names_de[node.id] = str(row[1])
        for vi, oi, ri in triples:
            value = row[vi] if vi < len(row) else None
            if value is None or value == "":
                continue  # missing, not zero (BLS FAQ 11)
            origin = "" if row[oi] is None else str(row[oi]).strip()
            if origin and origin not in HERKUNFT:
                raise UnmappedDerivation(f"BLS Datenherkunft {origin!r} in column {headers[oi]!r}")
            tag, name, unit = parse_value_header(headers[vi])
            key = f"nutrient:bls:{tag}"
            used[key] = {"name": name, "unit": unit}
            reference = row[ri] if ri < len(row) else None
            claims.append(Claim(
                subject=node.id, group="nutrition", field=key,
                v=float(value) if isinstance(value, (int, float)) else str(value),
                unit=unit, basis=basis(node), food_part=food_part(node), src=src_id,
                derivation=HERKUNFT.get(origin, "unverified"),
                ref=f"bls:{row[0]}" + (f"; {reference}" if reference else ""),
            ))
    return claims, used, names_de
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_bls.py -q`
Expected: `5 passed`

- [ ] **Step 6: Check the real header format, map the BLS codes and add the real-data test**

1. **Inspect the headers.** Run `uv run python -c "from pathlib import Path; from openpyxl import load_workbook; from atlas.ingest.bls import find_workbook; ws = load_workbook(find_workbook(Path('data/raw/bls')), read_only=True).worksheets[0]; print(next(ws.iter_rows(max_row=1, values_only=True))[:9])"`.
   - If the real value headers do not look like `TAG Name [unit/100g]`, adjust `parse_value_header` and `UNIT`.
   - Copy three real headers into `test_parse_value_header` as extra cases.
2. **Add `search_bls` to `src/atlas/curate.py`:**
   ```python
   def search_bls(root: Path, query: str) -> list[str]:
       from openpyxl import load_workbook
       from atlas.ingest.bls import find_workbook
       q = query.lower()
       ws = load_workbook(find_workbook(root / "data/raw/bls"), read_only=True).worksheets[0]
       return ["\t".join("" if x is None else str(x) for x in row)
               for row in ws.iter_rows(min_row=2, max_col=3, values_only=True)
               if any(x is not None and q in str(x).lower() for x in row)]
   ```
3. **Map the codes.** For each taxon food, look up the German names with `search_bls(Path('.'), q)`: Apfel, Weißkohl, Rotkohl, Wirsing, Brokkoli, Blumenkohl, Kohlrabi, Rosenkohl, Grünkohl, Sauerkraut.
   - Put the code of the **raw** entry into `bls_codes` on the matching node.
   - Cooked and composite entries stay unmapped in this plan.
4. **Add the real-data test** to `tests/test_real_data.py`:
   ```python
   def test_bls_layout_and_pilot_codes(nodes):
       from openpyxl import load_workbook
       from atlas.ingest.bls import find_workbook, load_bls, nutrient_columns, parse_value_header
       root = need("data/raw/bls")
       ws = load_workbook(find_workbook(root), read_only=True).worksheets[0]
       headers = ["" if h is None else str(h) for h in next(ws.iter_rows(max_row=1, values_only=True))]
       triples = nutrient_columns(headers)
       assert len(triples) == 138
       assert sum(parse_value_header(headers[v])[2] is not None for v, _, _ in triples) >= 130
       claims, _, names_de = load_bls(root, "SRC-BLS-4.0", nodes)
       mapped = {n.id for n in nodes.values() if n.bls_codes}
       assert mapped and mapped <= set(names_de)
   ```

Run: `uv run pytest tests/test_real_data.py -q -m data`
Expected: `2 passed`.
- If there are not 138 triples, the origin header is worded differently. Adjust `ORIGIN_HEADER`.
- If a data origin is unmapped, add it to `HERKUNFT` only if it is one of the 13 FAQ categories spelled differently. Otherwise stop and ask the user.

- [ ] **Step 7: Commit**

```bash
git add src/atlas/ingest/bls.py src/atlas/curate.py tests/conftest.py tests/test_bls.py tests/test_real_data.py data/registry/foods.yaml
git commit -m "feat: BLS 4.0 importer with data-origin tiers and German names"
```

---

### Task 9: FoodAtlas importer (presence claims, CTD-free, deduplicated molecules)

**Files:**
- Create: `src/atlas/ingest/foodatlas.py`, `tests/test_foodatlas.py`
- Modify:
  - `tests/conftest.py` (add the `foodatlas_dir` fixture)
  - `src/atlas/curate.py` (add `search_foodatlas`)
  - `tests/test_real_data.py` (add the FoodAtlas test)

**Interfaces:**
- Consumes: `Claim` (Task 2); `FoodNode` and `food_part` (Task 5).
- Produces:
  - `sql_path(path) -> str` (a quoted SQL string literal)
  - `load_aliases(path) -> dict[str, str]`
  - `molecule_key(fa_id, external_ids, aliases) -> str`
  - `load_foodatlas(bundle, src_id, nodes, aliases) -> tuple[list[Claim], dict[str, dict]]`, returning the claims and the molecules keyed by molecule key → `{"name", "chebi", "pubchem", "flavor", "foodatlas_ids"}`
  - `atlas.curate.search_foodatlas(root, query) -> list[str]`

**Claim shape:**
- **Presence:** one claim per (food, molecule): `group="molecules"`, `field="contains:<key>"`, `v="present"`, `derivation="extracted"`, `flags=("llm_extracted",)`, `ref` = the sorted PMC IDs, `n` = the number of distinct references.
- **Amount:** each attestation with `conc_value` becomes its own claim with `basis=None`. The validator turns it into a rule-6 gap that carries the value.
- **Excluded evidence:** only `lit2kg:*` attestations of `r1` (contains) links are read. CTD and FDC rows are never used.

- [ ] **Step 1: Add the `foodatlas_dir` fixture to `tests/conftest.py`**

```python
@pytest.fixture
def foodatlas_dir(tmp_path):
    import duckdb
    d = tmp_path / "fa"
    d.mkdir()
    con = duckdb.connect()

    def write(name: str, select: str) -> None:
        con.execute(f"COPY ({select}) TO '{d / name}' (FORMAT PARQUET)")

    write("entities.parquet", """select * from (values
        ('e897', 'food', 'apple', '', '[]', '{}', '{}'),
        ('e1536', 'food', 'Honeycrisp apple', '', '[]', '{}', '{}'),
        ('c1', 'chemical', 'l-ascorbic acid', '', '[]', '{"chebi": [29073], "fdc_nutrient": [1162]}', '{"flavor_descriptors": ["sour"]}'),
        ('c2', 'chemical', 'vitamin c', '', '[]', '{"chebi": [176783], "fdc_nutrient": [1162]}', '{}'),
        ('c3', 'chemical', 'l-ascorbate', '', '[]', '{"chebi": [38290]}', '{}'),
        ('c4', 'chemical', 'quercetin', '', '[]', '{"chebi": [16243]}', '{"flavor_descriptors": ["bitter"]}')
    ) t(foodatlas_id, entity_type, common_name, scientific_name, synonyms, external_ids, attributes)""")
    write("triplets.parquet", """select * from (values
        ('e897', 'r1', 'c1', '', '["a1"]'),
        ('e897', 'r1', 'c2', '', '["a2", "a5"]'),
        ('e897', 'r1', 'c3', '', '["a3"]'),
        ('e1536', 'r1', 'c4', '', '["a4"]'),
        ('c4', 'r3', 'e897', '', '["a6"]')
    ) t(head_id, relationship_id, tail_id, source, attestation_ids)""")
    write("attestations.parquet", """select * from (values
        ('a1', 'v1', 'lit2kg:claude-opus-4-8', 9.0::double, 'mg/100g'),
        ('a2', 'v2', 'lit2kg:gemma-4-31B-it', null::double, null),
        ('a3', 'v3', 'lit2kg:claude-opus-4-8', null::double, null),
        ('a4', 'v4', 'lit2kg:claude-opus-4-8', null::double, null),
        ('a5', 'v5', 'fdc', 4.6::double, 'mg/100g'),
        ('a6', 'v6', 'ctd', null::double, null)
    ) t(attestation_id, evidence_id, source, conc_value, conc_unit)""")
    write("evidence.parquet", """select * from (values
        ('v1', 'pubmed', '{"pmcid": "111", "text": "x"}'),
        ('v2', 'pubmed', '{"pmcid": "222", "text": "y"}'),
        ('v3', 'pubmed', '{"pmcid": "333", "text": "z"}'),
        ('v4', 'pubmed', '{"pmcid": "444", "text": "w"}'),
        ('v5', 'fdc', '{"source": "fdc"}'),
        ('v6', 'ctd', '{"source": "ctd"}')
    ) t(evidence_id, source_type, reference)""")
    (d / "aliases.yaml").write_text('c3: {key: "nutrient:fdc:1162", reason: "conjugate base"}\n', encoding="utf-8")
    return d
```

- [ ] **Step 2: Write the failing tests**

`tests/test_foodatlas.py`:
```python
from atlas.ingest.foodatlas import load_aliases, load_foodatlas, molecule_key


def test_molecule_key_preference():
    assert molecule_key("x", {"fdc_nutrient": [1162], "chebi": [29073]}, {}) == "nutrient:fdc:1162"
    assert molecule_key("x", {"chebi": [16243], "pubchem_compound": [5280343]}, {}) == "CHEBI:16243"
    assert molecule_key("x", {"pubchem_compound": [1]}, {}) == "PUBCHEM:1"
    assert molecule_key("x", {}, {}) == "FA:x"
    assert molecule_key("x", {"chebi": [1]}, {"x": "nutrient:fdc:9"}) == "nutrient:fdc:9"


def test_load_foodatlas(foodatlas_dir, mini_nodes):
    aliases = load_aliases(foodatlas_dir / "aliases.yaml")
    claims, molecules = load_foodatlas(foodatlas_dir, "SRC-FA", mini_nodes, aliases)
    presence = {(c.subject, c.field): c for c in claims if c.v == "present"}
    amounts = [c for c in claims if c.v != "present"]

    vitc = presence[("food:apple", "contains:nutrient:fdc:1162")]
    assert vitc.ref == "PMC111, PMC222, PMC333" and vitc.n == 3  # fdc row a5 not read
    assert vitc.flags == ("llm_extracted",) and vitc.derivation == "extracted"
    assert ("food:apple.honeycrisp", "contains:CHEBI:16243") in presence
    assert len(presence) == 2  # the r3 (CTD) row is never read

    assert len(amounts) == 1
    assert (amounts[0].v, amounts[0].basis, amounts[0].unit) == (9.0, None, "mg/100g")

    assert set(molecules) == {"nutrient:fdc:1162", "CHEBI:16243"}
    assert molecules["nutrient:fdc:1162"]["foodatlas_ids"] == ["c1", "c2", "c3"]
    assert molecules["CHEBI:16243"]["flavor"] == ["bitter"]
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run pytest tests/test_foodatlas.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'atlas.ingest.foodatlas'`

- [ ] **Step 4: Implement `src/atlas/ingest/foodatlas.py`**

```python
"""FoodAtlas v4.11 (Apache-2.0) → presence claims for pilot foods.

Only `contains` links backed by LLM literature extraction are read. CTD rows (commercial
reuse prohibited) and FDC rows (imported directly from USDA) are never used. Amounts carry
no basis, so the contract turns them into gaps. Evidence sentences are not shipped, only
PMC IDs.
"""
from __future__ import annotations

import json
from pathlib import Path

import duckdb
import yaml

from atlas.claims import Claim
from atlas.foods import FoodNode, food_part


def sql_path(path: Path) -> str:
    return "'" + str(path).replace("'", "''") + "'"


def load_aliases(path: Path) -> dict[str, str]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {fa_id: d["key"] for fa_id, d in raw.items()}


def molecule_key(fa_id: str, external_ids: dict, aliases: dict[str, str]) -> str:
    if fa_id in aliases:
        return aliases[fa_id]
    if external_ids.get("fdc_nutrient"):
        return f"nutrient:fdc:{external_ids['fdc_nutrient'][0]}"
    if external_ids.get("chebi"):
        return f"CHEBI:{external_ids['chebi'][0]}"
    if external_ids.get("pubchem_compound"):
        return f"PUBCHEM:{external_ids['pubchem_compound'][0]}"
    return f"FA:{fa_id}"


def load_foodatlas(
    bundle: Path, src_id: str, nodes: dict[str, FoodNode], aliases: dict[str, str]
) -> tuple[list[Claim], dict[str, dict]]:
    fa_to_node = {fa: n.id for n in nodes.values() for fa in n.foodatlas_ids}
    if not fa_to_node:
        return [], {}
    con = duckdb.connect()
    rows = con.execute(f"""
        with ta as (
            select head_id, tail_id, unnest(cast(json(attestation_ids) as varchar[])) as aid
            from read_parquet({sql_path(bundle / 'triplets.parquet')})
            where relationship_id = 'r1' and list_contains(?::varchar[], head_id)
        )
        select ta.head_id, ta.tail_id, a.conc_value, a.conc_unit, e.reference
        from ta
        join read_parquet({sql_path(bundle / 'attestations.parquet')}) a on a.attestation_id = ta.aid
        join read_parquet({sql_path(bundle / 'evidence.parquet')}) e on e.evidence_id = a.evidence_id
        where a.source like 'lit2kg:%'
        order by ta.head_id, ta.tail_id, a.attestation_id
    """, [sorted(fa_to_node)]).fetchall()
    tails = sorted({r[1] for r in rows})
    chemicals = {}
    if tails:
        for fa_id, name, ext, attrs in con.execute(f"""
            select foodatlas_id, common_name, external_ids, attributes
            from read_parquet({sql_path(bundle / 'entities.parquet')})
            where list_contains(?::varchar[], foodatlas_id)
        """, [tails]).fetchall():
            ext_d, attr_d = json.loads(ext or "{}"), json.loads(attrs or "{}")
            chemicals[fa_id] = (molecule_key(fa_id, ext_d, aliases), name, ext_d, attr_d)

    molecules: dict[str, dict] = {}
    refs: dict[tuple[str, str], set[str]] = {}
    claims: list[Claim] = []
    for head, tail, conc_value, conc_unit, reference in rows:
        key, name, ext_d, attr_d = chemicals[tail]
        m = molecules.setdefault(key, {"name": name, "chebi": [], "pubchem": [], "flavor": set(), "foodatlas_ids": set()})
        m["chebi"] = sorted(set(m["chebi"]) | set(ext_d.get("chebi", [])))
        m["pubchem"] = sorted(set(m["pubchem"]) | set(ext_d.get("pubchem_compound", [])))
        m["flavor"].update(attr_d.get("flavor_descriptors", []))
        m["foodatlas_ids"].add(tail)
        node = nodes[fa_to_node[head]]
        pmcid = json.loads(reference or "{}").get("pmcid")
        ref = f"PMC{pmcid}" if pmcid else None
        refs.setdefault((node.id, key), set()).update([ref] if ref else [])
        if conc_value is not None:
            claims.append(Claim(
                subject=node.id, group="molecules", field=f"contains:{key}", v=float(conc_value),
                unit=conc_unit, basis=None, food_part=food_part(node), src=src_id,
                derivation="extracted", ref=ref, flags=("llm_extracted",),
            ))
    for (subject, key), ids in sorted(refs.items()):
        claims.append(Claim(
            subject=subject, group="molecules", field=f"contains:{key}", v="present",
            food_part=food_part(nodes[subject]), src=src_id, derivation="extracted",
            ref=", ".join(sorted(ids)), n=len(ids), flags=("llm_extracted",),
        ))
    for m in molecules.values():
        m["flavor"] = sorted(m["flavor"])
        m["foodatlas_ids"] = sorted(m["foodatlas_ids"])
    return claims, molecules
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_foodatlas.py -q`
Expected: `2 passed`

- [ ] **Step 6: Add the FoodAtlas search helper and the real-data test**

Append to `src/atlas/curate.py`:
```python
def search_foodatlas(root: Path, query: str) -> list[str]:
    import duckdb
    from atlas.ingest.foodatlas import sql_path
    bundle = root / "data/raw/foodatlas/foodatlas-v4.11"
    rows = duckdb.connect().execute(
        f"select foodatlas_id, common_name from read_parquet({sql_path(bundle / 'entities.parquet')}) "
        "where entity_type = 'food' and common_name ilike ? order by common_name",
        [f"%{query}%"],
    ).fetchall()
    return [f"{fa_id}\t{name}" for fa_id, name in rows]
```

Append to `tests/test_real_data.py`:
```python
def test_foodatlas_pilot_is_ctd_free_and_deduplicated(nodes):
    from atlas.ingest.foodatlas import load_aliases, load_foodatlas
    bundle = need("data/raw/foodatlas/foodatlas-v4.11")
    claims, molecules = load_foodatlas(bundle, "SRC-FOODATLAS-V4.11", nodes, load_aliases(REPO / "data/registry/molecule_aliases.yaml"))
    apple = {c.field for c in claims if c.subject == "food:apple" and c.v == "present"}
    assert len(apple) > 100
    plain_vitamin_c = {"vitamin c", "l-ascorbic acid", "l-ascorbate", "ascorbic acid", "ascorbate"}
    keys = {k for k, m in molecules.items() if m["name"].lower() in plain_vitamin_c}
    assert keys <= {"nutrient:fdc:1162"}, keys
    assert all(c.flags == ("llm_extracted",) for c in claims)
```

Run: `uv run pytest tests/test_real_data.py -q -m data`
Expected: `3 passed`.
- If the vitamin C assertion fails, look up the FoodAtlas IDs behind the reported keys (the `foodatlas_ids` of each molecule).
- Add each one to `molecule_aliases.yaml` with key `nutrient:fdc:1162` and a reason, then run the test again.

- [ ] **Step 7: Commit**

```bash
git add src/atlas/ingest/foodatlas.py src/atlas/curate.py tests/conftest.py tests/test_foodatlas.py tests/test_real_data.py data/registry/molecule_aliases.yaml
git commit -m "feat: CTD-free FoodAtlas importer with presence claims and molecule keys"
```

---

### Task 10: Curated claims and pilot coverage

**Files:**
- Create: `src/atlas/curated.py`, `tests/test_curated.py`, `tests/test_pilot_coverage.py`
- Create one YAML per subject under `data/curated/`:
  - `org-malus-domestica.yaml`, `org-brassica-oleracea.yaml`
  - `apple.yaml`, `cabbage.yaml`, `broccoli.yaml`, `cauliflower.yaml`, `kohlrabi.yaml`, `brussels-sprout.yaml`, `kale.yaml`

**Interfaces:**
- Consumes: `Claim` (Task 2), `load_sources` (Task 3), `validate` (Task 4), `load_foods` (Task 5).
- Produces: `load_curated(folder) -> list[Claim]`. Every claim it returns has `curated=True`.

**Curated file format:**
```yaml
subject: <org:… or food:…>
claims:
  - {group: <claim group>, field: <field>, v: <value>, src: <SRC-…>, derivation: <derivation>, ref: <where in the source>}
```

**Required coverage** (enforced by `tests/test_pilot_coverage.py`):

| Subject | Groups and fields |
| :--- | :--- |
| `org:malus-domestica`, `org:brassica-oleracea` | `identity/ncbi_taxon` (src `SRC-NCBI-TAXONOMY`, derivation `registry`)<br>`origin/primary_region_of_diversity` (src `SRC-KHOURY-2016`, derivation `registry`; the value is copied from the Khoury 2016 dataset row for the matching crop commodity)<br>one or more `growing/*` facts (src `SRC-ECOCROP`, derivation `registry`, one fact per claim, e.g. `growing/temperature_optimal_c`, with `unit`) |
| each of the 7 taxon foods | `season/DE` (src `SRC-BZFE-SAISONKALENDER`, derivation `registry`; the months as listed by BZfE)<br>`sensory/colour`, `sensory/texture`, `sensory/taste` (src `SRC-EDITORIAL`, derivation `editorial`)<br>`narrative/eli5`, `narrative/story` (src `SRC-EDITORIAL`, derivation `editorial`) |
| each Brassica convariety organism | `identity/rank` (src `SRC-MANSFELD`, derivation `registry`; the convar. name as Mansfeld states it) |

**Curation rules** (rule 10, rule 8 and the license gate):
- Every non-editorial `v` is copied from the cited page or dataset row at the time of writing, and `ref` says exactly where it came from: a URL fragment, a table row or a dataset file plus row.
- No text is copied from `cite` sources, only the fact.
- Editorial text makes no health claims, and it describes cultivars and preparation neutrally.

- [ ] **Step 1: Write the failing tests**

`tests/test_curated.py`:
```python
import textwrap

from atlas.curated import load_curated


def test_load_curated_marks_claims(tmp_path):
    (tmp_path / "apple.yaml").write_text(textwrap.dedent("""
        subject: food:apple
        claims:
          - {group: sensory, field: texture, v: "Crisp to mealy", src: SRC-EDITORIAL, derivation: editorial}
          - {group: season, field: season:DE, v: "Aug–Oct", src: SRC-BZFE-SAISONKALENDER, derivation: registry, ref: "Saisonkalender, Äpfel"}
    """), encoding="utf-8")
    claims = load_curated(tmp_path)
    assert len(claims) == 2 and all(c.curated and c.subject == "food:apple" for c in claims)
    assert claims[1].ref == "Saisonkalender, Äpfel"
```
The season value in this fixture is made up; real values come from the BZfE page.

`tests/test_pilot_coverage.py`:
```python
from pathlib import Path

from atlas.contract import validate
from atlas.curated import load_curated
from atlas.foods import load_foods, load_organisms, load_processes
from atlas.registry import load_sources

REPO = Path(__file__).resolve().parents[1]
REG = REPO / "data/registry"


def test_curated_pilot_is_complete_and_passes_the_contract():
    sources = load_sources(REG / "sources.yaml", REG / "link_status.yaml")
    orgs = load_organisms(REG / "organisms.yaml")
    nodes, _ = load_foods(REG / "foods.yaml", orgs, load_processes(REG / "processes.yaml"))
    result = validate(load_curated(REPO / "data/curated"), sources)
    assert not result.gaps, [(g.subject, g.field, g.question) for g in result.gaps]
    have = {(c.subject, c.group, c.field) for c in result.accepted}
    groups = {(s, g) for s, g, _ in have}
    subjects = {s for s, _, _ in have}
    assert subjects <= set(orgs) | set(nodes), subjects - set(orgs) - set(nodes)
    for org in ("org:malus-domestica", "org:brassica-oleracea"):
        assert (org, "identity", "ncbi_taxon") in have
        assert (org, "origin", "primary_region_of_diversity") in have
        assert (org, "growing") in groups
    for org in (o for o in orgs.values() if o.rank == "convar"):
        assert (org.id, "identity", "rank") in have
    for node in (n for n in nodes.values() if n.level == "taxon_food"):
        for field in ("season:DE",):
            assert (node.id, "season", field) in have, node.id
        for field in ("colour", "texture", "taste"):
            assert (node.id, "sensory", field) in have, node.id
        for field in ("eli5", "story"):
            assert (node.id, "narrative", field) in have, node.id
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_curated.py tests/test_pilot_coverage.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'atlas.curated'`

- [ ] **Step 3: Implement `src/atlas/curated.py`**

```python
"""Curated claims: one YAML file per subject, every claim marked `curated`."""
from __future__ import annotations

from pathlib import Path

import yaml

from atlas.claims import Claim

OPTIONAL = ("unit", "basis", "food_part", "method", "ref", "v_min", "v_max", "n")


def load_curated(folder: Path) -> list[Claim]:
    claims: list[Claim] = []
    for path in sorted(folder.glob("*.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for c in doc.get("claims", []):
            claims.append(Claim(
                subject=doc["subject"], group=c["group"], field=c["field"], v=c["v"],
                src=c["src"], derivation=c["derivation"], flags=tuple(c.get("flags", ())),
                curated=True, **{k: c[k] for k in OPTIONAL if k in c},
            ))
    return claims
```

Run: `uv run pytest tests/test_curated.py -q`
Expected: `1 passed`. The coverage test still fails until Step 5.

- [ ] **Step 4: Unlock the cite sources and fetch origin data**

- Read the license or terms pages of `SRC-ECOCROP`, `SRC-BZFE-SAISONKALENDER` and `SRC-KHOURY-2016` (the Dryad terms), then set `license_read: true` for each.
- Khoury 2016 is imported from its downloaded dataset (Task 6 Step 7). Open the file in `data/raw/khoury2016/` that lists crop commodities with their primary regions of diversity, and find the rows for apples and for cabbages or brassicas.

- [ ] **Step 5: Write the curated files**

Write each file following the coverage table and the curation rules. Here is the structure for `data/curated/org-malus-domestica.yaml`:
```yaml
subject: org:malus-domestica
claims:
  - {group: identity, field: ncbi_taxon, v: 3750, src: SRC-NCBI-TAXONOMY, derivation: registry, ref: "https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=3750"}
  - {group: origin, field: primary_region_of_diversity, v: "<region string exactly as in the Khoury 2016 row for apples>", src: SRC-KHOURY-2016, derivation: registry, ref: "<dataset file name>, row '<commodity name>'"}
  - {group: growing, field: temperature_optimal_c, v: "<min–max as on the ECOCROP page for Malus domestica>", unit: "°C", src: SRC-ECOCROP, derivation: registry, ref: "https://gaez.fao.org/pages/ecocrop — Malus domestica"}
```
The angle-bracket values are read from the cited source during this step. They must never be filled from memory.

Here is the structure for `data/curated/apple.yaml`:
```yaml
subject: food:apple
claims:
  - {group: season, field: "season:DE", v: "<months as shown by the BZfE Saisonkalender for Äpfel>", src: SRC-BZFE-SAISONKALENDER, derivation: registry, ref: "BZfE Saisonkalender, Äpfel (checked <date>)"}
  - {group: sensory, field: colour, v: "Skin from green through yellow to red, often striped or blushed; flesh cream to white.", src: SRC-EDITORIAL, derivation: editorial}
  - {group: sensory, field: texture, v: "Crisp and juicy to soft and mealy, depending on cultivar and storage.", src: SRC-EDITORIAL, derivation: editorial}
  - {group: sensory, field: taste, v: "Sweet to sharply acidic, with fruity and floral notes.", src: SRC-EDITORIAL, derivation: editorial}
  - {group: narrative, field: eli5, v: "The fruit of a small tree in the rose family, grown in thousands of named cultivars.", src: SRC-EDITORIAL, derivation: editorial}
  - {group: narrative, field: story, v: "<two to four sentences: what makes the apple interesting as a food, which cultivars the atlas shows, and what it is made into (juice, cider, dried apple, pomace)>", src: SRC-EDITORIAL, derivation: editorial}
```

The other six taxon foods and the Brassica organisms follow the same structure, with their own sources:
- **BZfE entries:** Weißkohl/Rotkohl/Wirsing for cabbage, Brokkoli, Blumenkohl, Kohlrabi, Rosenkohl, Grünkohl.
- **ECOCROP entry:** *Brassica oleracea*.
- **Khoury row:** the brassica commodity.
- **Mansfeld:** each convariety's `identity/rank`.

If BZfE has no entry for a food, do not invent one. Leave the field out and tell the user; the coverage test then names the missing field.

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest tests/test_curated.py tests/test_pilot_coverage.py -q`
Expected: `2 passed`

- [ ] **Step 7: Commit**

```bash
git add src/atlas/curated.py data/curated data/registry/sources.yaml tests/test_curated.py tests/test_pilot_coverage.py
git commit -m "feat: curated origin, growing, season, sensory and story claims for the pilot"
```

---

### Task 11: Build pipeline, outputs and NOTICE

**Files:**
- Create: `src/atlas/build.py`, `tests/test_build.py`
- Modify: `tests/conftest.py` (add the `project` fixture)
- Generated: `data/build/{atlas.json, atlas.duckdb, claims.csv, gaps.csv}` and `NOTICE.md`

**Interfaces:**
- Consumes: everything from Tasks 2–10.
- Produces:
  - `RAW: dict[str, tuple[str, str]]`, mapping each source name to (raw folder, source id)
  - `build(root, require_raw=True) -> BuildResult`, where `BuildResult` has `validation: ValidationResult` and `payload: dict`
  - `make_payload(...) -> dict`
  - `write_outputs(out_dir, result, payload) -> None`
  - `write_notice(path, result, sources) -> None`

**Payload keys** (used by the site in Task 12): `sources`, `organisms`, `foods`, `processes`, `nutrients`, `molecules`, `gaps`, `excluded_foodatlas`, `stats`.
- Each entry in `foods` has every `FoodNode` field, plus `taxon`, `name_de`, `claims` (a list of claim dicts, each with `tier`) and `gaps`.
- Each entry in `sources` has every `Source` field, plus `claims` (the number of accepted claims).

- [ ] **Step 1: Add the `project` fixture to `tests/conftest.py`**

```python
import shutil
import textwrap

MINI_SOURCES = """
SRC-FDC-FOUNDATION-2026-04: &fdc
  title: FDC Foundation
  publisher: USDA ARS
  url: https://fdc.nal.usda.gov/download-datasets
  license: CC0-1.0
  license_class: ship
  license_read: true
  kind: measurement
  independence: independent
  supports: [identity, nutrition]
  attribution: "USDA ARS. FoodData Central."
SRC-FDC-SRLEGACY-2018-04: *fdc
SRC-BLS-4.0:
  title: BLS 4.0
  publisher: MRI
  url: https://blsdb.de/download
  license: CC-BY-4.0
  license_class: ship
  license_read: true
  kind: compilation
  independence: independent
  supports: [identity, nutrition]
  attribution: "Max Rubner-Institut (2025): BLS 4.0."
SRC-FOODATLAS-V4.11:
  title: FoodAtlas
  publisher: AIFS
  url: https://www.foodatlas.ai/food-composition-downloads
  license: Apache-2.0
  license_class: ship
  license_read: true
  kind: literature_extraction
  independence: independent
  supports: [identity, molecules]
  attribution: "Li, F. et al. (2026). FoodAtlas."
SRC-EDITORIAL:
  title: Editorial
  publisher: Food Atlas contributors
  url: https://github.com/
  license: CC-BY-4.0
  license_class: ship
  license_read: true
  kind: library_editorial
  independence: library_editorial
  supports: [sensory, narrative]
  attribution: "Food Atlas contributors."
"""
MINI_ORGANISMS = "org:malus-domestica: {name: Malus domestica, rank: species, parent: null, ncbi_taxon: 3750}\n"
MINI_PROCESSES = "proc:drying: {name: Drying}\n"
MINI_FOODS = """
excluded_foodatlas:
  e1671: {name: chinese cabbage head, reason: "Brassica rapa"}
food:apple: {level: taxon_food, name: Apple, derives_from: org:malus-domestica, foodatlas_ids: [e897], bls_codes: [F110100]}
food:apple.honeycrisp: {level: cultivar, name: "Apple 'Honeycrisp'", is_a: food:apple, foodatlas_ids: [e1536], fdc_match: ["Apples, honeycrisp, with skin, raw"]}
food:apple.dried: {level: form, name: Dried apple, derives_from: food:apple, process: proc:drying, fdc_match: ["Apples, dried, sulfured, uncooked"]}
"""
MINI_CURATED = """
subject: food:apple
claims:
  - {group: sensory, field: texture, v: "Crisp to mealy, depending on cultivar and storage.", src: SRC-EDITORIAL, derivation: editorial}
  - {group: narrative, field: story, v: "An anti-inflammatory food.", src: SRC-EDITORIAL, derivation: editorial}
"""


@pytest.fixture
def project(tmp_path, fdc_dir, bls_dir, foodatlas_dir):
    root = tmp_path / "proj"
    reg = root / "data/registry"
    reg.mkdir(parents=True)
    for name, text in {
        "sources.yaml": MINI_SOURCES, "organisms.yaml": MINI_ORGANISMS, "processes.yaml": MINI_PROCESSES,
        "foods.yaml": MINI_FOODS,
    }.items():
        (reg / name).write_text(textwrap.dedent(text), encoding="utf-8")
    shutil.copy(foodatlas_dir / "aliases.yaml", reg / "molecule_aliases.yaml")
    (root / "data/curated").mkdir(parents=True)
    (root / "data/curated/apple.yaml").write_text(textwrap.dedent(MINI_CURATED), encoding="utf-8")
    shutil.copytree(fdc_dir, root / "data/raw/fdc-foundation")
    shutil.copytree(fdc_dir, root / "data/raw/fdc-srlegacy")
    shutil.copytree(bls_dir, root / "data/raw/bls")
    shutil.copytree(foodatlas_dir, root / "data/raw/foodatlas/foodatlas-v4.11")
    return root
```
Place the imports at the top of `conftest.py`. The YAML anchor `&fdc` / `*fdc` gives both FDC sources the same fields.

- [ ] **Step 2: Write the failing tests**

`tests/test_build.py`:
```python
import json

import duckdb
import pytest

from atlas.build import build


def test_build_end_to_end(project):
    result = build(project)
    v = result.validation
    # FDC: 2 accepted per file (×2 files); BLS: 1; FoodAtlas presence: 2; curated: 1
    assert len(v.accepted) == 8
    # FDC dried apple has no derivation (×2) → 5; FoodAtlas amount → 6; health wording → 8
    assert sorted(g.rule for g in v.gaps) == [5, 5, 6, 8]

    out = project / "data/build"
    payload = json.loads((out / "atlas.json").read_text(encoding="utf-8"))
    foods = {f["id"]: f for f in payload["foods"]}
    hc = foods["food:apple.honeycrisp"]
    assert hc["taxon"] == "org:malus-domestica"
    assert {c["src"] for c in hc["claims"] if c["field"] == "nutrient:fdc:1162"} == {
        "SRC-FDC-FOUNDATION-2026-04", "SRC-FDC-SRLEGACY-2018-04"}
    assert foods["food:apple"]["name_de"] == "Apfel roh"
    assert any(g["rule"] == 6 for g in foods["food:apple"]["gaps"])
    assert "e1671" in payload["excluded_foodatlas"]
    assert payload["molecules"]["nutrient:fdc:1162"]["foodatlas_ids"] == ["c1", "c2", "c3"]

    con = duckdb.connect(str(out / "atlas.duckdb"), read_only=True)
    assert con.execute("select count(*) from claims").fetchone()[0] == 8
    assert con.execute("select count(*) from gaps").fetchone()[0] == 4

    notice = (project / "NOTICE.md").read_text(encoding="utf-8")
    assert "USDA ARS. FoodData Central." in notice and "Max Rubner-Institut" in notice
    assert "SRC-UNVERIFIED" not in notice


def test_build_requires_raw_data(project):
    import shutil
    shutil.rmtree(project / "data/raw/bls")
    with pytest.raises(FileNotFoundError, match="bls"):
        build(project)
    assert build(project, require_raw=False).validation.accepted
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run pytest tests/test_build.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'atlas.build'`

- [ ] **Step 4: Implement `src/atlas/build.py`**

```python
"""One entry point: registries + raw sources + curated files → validated claims → data/build."""
from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import duckdb

from atlas.claims import Claim
from atlas.contract import ValidationResult, validate
from atlas.curated import load_curated
from atlas.foods import load_foods, load_organisms, load_processes, taxon_of
from atlas.ingest.bls import load_bls
from atlas.ingest.fdc import load_fdc
from atlas.ingest.foodatlas import load_aliases, load_foodatlas, sql_path
from atlas.registry import Source, load_sources

RAW = {
    "fdc_foundation": ("data/raw/fdc-foundation", "SRC-FDC-FOUNDATION-2026-04"),
    "fdc_srlegacy": ("data/raw/fdc-srlegacy", "SRC-FDC-SRLEGACY-2018-04"),
    "bls": ("data/raw/bls", "SRC-BLS-4.0"),
    "foodatlas": ("data/raw/foodatlas/foodatlas-v4.11", "SRC-FOODATLAS-V4.11"),
}
CLAIM_COLUMNS = ["subject", "group", "field", "v", "unit", "basis", "food_part", "src", "tier",
                 "derivation", "method", "ref", "v_min", "v_max", "n", "flags", "curated"]
GAP_COLUMNS = ["subject", "field", "rule", "question", "would_be_settled_by", "carried_value", "src"]


@dataclass
class BuildResult:
    validation: ValidationResult
    payload: dict


def claim_dict(c: Claim) -> dict:
    d = asdict(c)
    d["tier"] = c.tier
    d["flags"] = list(c.flags)
    return d


def build(root: Path, require_raw: bool = True) -> BuildResult:
    reg = root / "data/registry"
    sources = load_sources(reg / "sources.yaml", reg / "link_status.yaml")
    organisms = load_organisms(reg / "organisms.yaml")
    processes = load_processes(reg / "processes.yaml")
    nodes, excluded = load_foods(reg / "foods.yaml", organisms, processes)
    claims: list[Claim] = []
    nutrients: dict[str, dict] = {}
    molecules: dict[str, dict] = {}
    names_de: dict[str, str] = {}
    for name, (rel, src_id) in RAW.items():
        path = root / rel
        if not path.exists():
            if require_raw:
                raise FileNotFoundError(f"{name}: {path} is missing — run `atlas fetch`")
            continue
        if name.startswith("fdc"):
            found, used = load_fdc(path, src_id, nodes)
            nutrients.update(used)
        elif name == "bls":
            found, used, de = load_bls(path, src_id, nodes)
            nutrients.update(used)
            names_de.update(de)
        else:
            found, molecules = load_foodatlas(path, src_id, nodes, load_aliases(reg / "molecule_aliases.yaml"))
        claims.extend(found)
    claims.extend(load_curated(root / "data/curated"))
    result = validate(claims, sources)
    payload = make_payload(result, sources, organisms, nodes, processes, nutrients, molecules, names_de, excluded)
    write_outputs(root / "data/build", result, payload)
    write_notice(root / "NOTICE.md", result, sources)
    return BuildResult(result, payload)


def make_payload(result, sources, organisms, nodes, processes, nutrients, molecules, names_de, excluded) -> dict:
    by_subject: dict[str, list[dict]] = {}
    for c in result.accepted:
        by_subject.setdefault(c.subject, []).append(claim_dict(c))
    gaps_by_subject: dict[str, list[dict]] = {}
    for g in result.gaps:
        gaps_by_subject.setdefault(g.subject, []).append(asdict(g))
    counts: dict[str, int] = {}
    for c in result.accepted:
        counts[c.src] = counts.get(c.src, 0) + 1
    return {
        "sources": [asdict(s) | {"claims": counts.get(s.id, 0)} for s in sources.values()],
        "organisms": [asdict(o) | {"claims": by_subject.get(o.id, [])} for o in organisms.values()],
        "foods": [
            asdict(n) | {
                "taxon": taxon_of(n, nodes),
                "name_de": n.name_de or names_de.get(n.id),
                "claims": by_subject.get(n.id, []),
                "gaps": gaps_by_subject.get(n.id, []),
            }
            for n in nodes.values()
        ],
        "processes": processes,
        "nutrients": nutrients,
        "molecules": molecules,
        "gaps": [asdict(g) for g in result.gaps],
        "excluded_foodatlas": excluded,
        "stats": {"accepted": len(result.accepted), "gaps": len(result.gaps), "sources_used": sorted(counts)},
    }


def _write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: (";".join(v) if isinstance(v, list) else v) for k, v in r.items()})


def write_outputs(out: Path, result: ValidationResult, payload: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "atlas.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    _write_csv(out / "claims.csv", CLAIM_COLUMNS, [claim_dict(c) for c in result.accepted])
    _write_csv(out / "gaps.csv", GAP_COLUMNS, [asdict(g) for g in result.gaps])
    db = out / "atlas.duckdb"
    db.unlink(missing_ok=True)
    con = duckdb.connect(str(db))
    for table in ("claims", "gaps"):
        con.execute(f"create table {table} as select * from read_csv({sql_path(out / f'{table}.csv')}, "
                    "header = true, all_varchar = true)")
    con.close()


def write_notice(path: Path, result: ValidationResult, sources: dict[str, Source]) -> None:
    used = sorted({c.src for c in result.accepted})
    lines = [
        "# NOTICE",
        "",
        "Generated by `atlas build`. Do not hand-edit.",
        "",
        "- Code: MIT (`LICENSE`).",
        "- Curated data in `data/registry/` and `data/curated/`: CC BY 4.0 (`LICENSE-DATA`).",
        "- Imported data keeps its upstream license:",
        "",
        "| Source | License | Attribution | URL |",
        "| :--- | :--- | :--- | :--- |",
    ]
    for sid in used:
        s = sources[sid]
        lines.append(f"| {s.title} (`{sid}`) | {s.license} | {s.attribution} | {s.url} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_build.py -q`
Expected: `2 passed`

- [ ] **Step 6: Build the real pilot**

Run: `uv run python -c "from pathlib import Path; from atlas.build import build; r = build(Path('.')); print(len(r.validation.accepted), len(r.validation.gaps))"`

Expected: both numbers print and nothing raises.

Then inspect `data/build/gaps.csv`:
- Rule 6 and 10 gaps (FoodAtlas amounts) and any rule 5 gaps (FDC rows without a derivation) are **expected**.
- Any rule 2, 3 or 9 gap means a registry mistake. Fix it in `sources.yaml` or in the curated files, and build again.

- [ ] **Step 7: Commit**

```bash
git add src/atlas/build.py tests/conftest.py tests/test_build.py NOTICE.md
git commit -m "feat: build pipeline writing atlas.json, DuckDB, CSVs and NOTICE"
```

---

### Task 12: Static site (Foods, Entry, Compare, Gaps, Sources)

**Files:**
- Create:
  - `src/atlas/site/build.py`
  - `src/atlas/site/templates/`: `base.html.j2`, `_chip.html.j2`, `index.html.j2`, `food.html.j2`, `compare.html.j2`, `gaps.html.j2`, `sources.html.j2`
  - `tests/test_site.py`

**Interfaces:**
- Consumes: the payload from `build()` (Task 11).
- Produces:
  - `render_site(payload, out) -> list[Path]`
  - `slug(food_id) -> str`
  - `index_rows(payload) -> list[dict]`
  - `sections(food, payload) -> list[tuple[str, list[dict]]]`
  - `compare_rows(food_ids, payload) -> list[dict]`
  - `TIER_LABEL`

**Design:**
- The palette follows the user's Victorinox library: background `#F1EEE7`, accent `#B10034`.
- Light and dark themes come from CSS tokens.
- Layout is phone-safe (16 px gutter, tables scroll horizontally).
- **Every value shows an evidence chip:** tier, derivation and source id, with title and license in a hover title.
- Machine-extracted molecules are labelled as such and link to their PMC articles.
- **Compare** shows *not stated* for blanks.
- **Gaps** are grouped by rule.

- [ ] **Step 1: Write the failing tests**

`tests/test_site.py`:
```python
from atlas.build import build
from atlas.site.build import compare_rows, render_site, slug


def test_slug():
    assert slug("food:apple.honeycrisp") == "apple--honeycrisp"


def test_render_site(project, tmp_path):
    payload = build(project).payload
    out = tmp_path / "site"
    written = {p.relative_to(out).as_posix() for p in render_site(payload, out)}
    assert {"index.html", "compare.html", "gaps.html", "sources.html", "foods/apple--honeycrisp.html"} <= written

    entry = (out / "foods/apple--honeycrisp.html").read_text(encoding="utf-8")
    assert "Vitamin C, total ascorbic acid" in entry
    assert "SRC-FDC-FOUNDATION-2026-04" in entry and "fresh_weight" in entry
    assert "machine-extracted" in entry and "PMC444" in entry

    apple = (out / "foods/apple.html").read_text(encoding="utf-8")
    assert "Apfel roh" in apple and "Amount without unit, basis or food part." in apple

    assert "CC0-1.0" in (out / "sources.html").read_text(encoding="utf-8")
    gaps = (out / "gaps.html").read_text(encoding="utf-8")
    assert "Rule 8" in gaps and "An anti-inflammatory food." in gaps
    index = (out / "index.html").read_text(encoding="utf-8")
    assert "apple--dried.html" in index and "not stated" in (out / "compare.html").read_text(encoding="utf-8")


def test_compare_rows_marks_blanks(project):
    payload = build(project).payload
    rows = {r["label"]: r["values"] for r in compare_rows(["food:apple", "food:apple.honeycrisp"], payload)}
    assert rows["Vitamin C, total ascorbic acid"][0] == "not stated"
    assert rows["Vitamin C, total ascorbic acid"][1].startswith("4.6 mg")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_site.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'atlas.site.build'`

- [ ] **Step 3: Implement `src/atlas/site/build.py`**

```python
"""Render the static pilot site from the build payload."""
from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

TIER_LABEL = {1: "Measured", 2: "Registry", 3: "Literature", 4: "Derived or declared", 5: "Unverified"}
GROUP_ORDER = ("narrative", "sensory", "nutrition", "molecules", "origin", "growing", "season", "identity")
LEVEL_ORDER = ("taxon_food", "cultivar", "part", "form")


def slug(food_id: str) -> str:
    return food_id.removeprefix("food:").replace(".", "--")


def _label(field: str, payload: dict) -> str:
    if field.startswith("contains:"):
        key = field.removeprefix("contains:")
        return payload["molecules"].get(key, {}).get("name", key)
    return payload["nutrients"].get(field, {}).get("name", field)


def _display(claim: dict) -> str:
    if claim["v"] == "present":
        return "present"
    unit = f" {claim['unit']}" if claim.get("unit") else ""
    return f"{claim['v']}{unit}"


def index_rows(payload: dict) -> list[dict]:
    organisms = {o["id"]: o["name"] for o in payload["organisms"]}
    rows = []
    for f in payload["foods"]:
        sensory = " ".join(str(c["v"]) for c in f["claims"] if c["group"] == "sensory")
        rows.append({
            "id": f["id"], "slug": slug(f["id"]), "name": f["name"], "level": f["level"],
            "taxon_name": organisms.get(f["taxon"], f["taxon"]), "claims": len(f["claims"]),
            "gaps": len(f["gaps"]), "search": f"{f['name']} {f.get('name_de') or ''} {sensory}".lower(),
        })
    return sorted(rows, key=lambda r: (r["taxon_name"], LEVEL_ORDER.index(r["level"]), r["name"]))


def sections(food: dict, payload: dict) -> list[tuple[str, list[dict]]]:
    out = []
    for group in GROUP_ORDER:
        claims = [c | {"label": _label(c["field"], payload), "display": _display(c)}
                  for c in food["claims"] if c["group"] == group]
        if claims:
            out.append((group, sorted(claims, key=lambda c: (c["label"], c["src"]))))
    return out


def compare_rows(food_ids: list[str], payload: dict) -> list[dict]:
    foods = {f["id"]: f for f in payload["foods"]}
    fields: dict[str, str] = {}
    for fid in food_ids:
        for c in foods[fid]["claims"]:
            if c["group"] == "nutrition":
                fields[c["field"]] = _label(c["field"], payload)
    rows = []
    for field, label in sorted(fields.items(), key=lambda kv: kv[1]):
        values = []
        for fid in food_ids:
            hits = [c for c in foods[fid]["claims"] if c["field"] == field]
            values.append("; ".join(f"{_display(c)} ({c['src']})" for c in hits) if hits else "not stated")
        rows.append({"field": field, "label": label, "values": values})
    return rows


def compare_data(payload: dict) -> dict:
    return {
        "foods": [{"id": f["id"], "name": f["name"]} for f in payload["foods"]],
        "rows": {f["id"]: {c["field"]: f"{_display(c)} ({c['src']})" for c in f["claims"] if c["group"] == "nutrition"}
                 for f in payload["foods"]},
        "labels": {k: v["name"] for k, v in payload["nutrients"].items()},
    }


def render_site(payload: dict, out: Path) -> list[Path]:
    env = Environment(loader=PackageLoader("atlas.site", "templates"), autoescape=select_autoescape())
    env.globals.update(tier_label=TIER_LABEL, slug=slug)
    sources = {s["id"]: s for s in payload["sources"]}
    organisms = {o["id"]: o for o in payload["organisms"]}
    (out / "foods").mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    def write(rel: str, template: str, root: str, **ctx) -> None:
        path = out / rel
        html = env.get_template(template).render(payload=payload, sources=sources, organisms=organisms, root=root, **ctx)
        path.write_text(html, encoding="utf-8")
        written.append(path)

    write("index.html", "index.html.j2", "", rows=index_rows(payload))
    for food in payload["foods"]:
        write(f"foods/{slug(food['id'])}.html", "food.html.j2", "../", food=food, sections=sections(food, payload))
    taxon_foods = [f["id"] for f in payload["foods"] if f["level"] == "taxon_food"][:3]
    write("compare.html", "compare.html.j2", "", default=compare_rows(taxon_foods, payload),
          default_ids=taxon_foods,
          data=json.dumps(compare_data(payload), ensure_ascii=False).replace("</", "<\\/"))
    by_rule: dict[int, list[dict]] = {}
    for g in payload["gaps"]:
        by_rule.setdefault(g["rule"], []).append(g)
    write("gaps.html", "gaps.html.j2", "", by_rule=dict(sorted(by_rule.items())))
    write("sources.html", "sources.html.j2", "")
    return written
```

- [ ] **Step 4: Write the templates**

`src/atlas/site/templates/base.html.j2`:
```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{% block title %}Food Atlas{% endblock %}</title>
<style>
:root{--bg:#F1EEE7;--fg:#1f1f1f;--muted:#6b665d;--accent:#B10034;--line:#d9d3c7;--card:#fbfaf6;
--t1:#1d6b3a;--t2:#2b5c8a;--t3:#7a5a00;--t4:#8a4b2b;--t5:#8a1c1c}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#171614;--fg:#ece8df;--muted:#a39d91;
--accent:#ff5a7a;--line:#34312c;--card:#201e1b;--t1:#6fcf97;--t2:#7fb2e5;--t3:#e2c26b;--t4:#e39a74;--t5:#ff8a8a}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
header,main,footer{max-width:1100px;margin:0 auto;padding:16px}
nav a{margin-right:16px;color:var(--accent);text-decoration:none;font-weight:600}
h1,h2,h3{line-height:1.2}
a{color:var(--accent)}
.muted{color:var(--muted)}
.scroll{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:15px}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
.chip{display:inline-block;font:12px/1.3 ui-monospace,Menlo,monospace;border:1px solid currentColor;border-radius:999px;padding:1px 8px;white-space:nowrap}
.tier-1{color:var(--t1)}.tier-2{color:var(--t2)}.tier-3{color:var(--t3)}.tier-4{color:var(--t4)}.tier-5{color:var(--t5)}
.badge{font-size:12px;border-radius:4px;padding:1px 6px;background:var(--line)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}
.card{display:block;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px;color:inherit;text-decoration:none}
.layers{display:grid;gap:24px}
@media (min-width:900px){.layers{grid-template-columns:1fr 2fr}}
input,select{font:inherit;padding:4px 8px;margin:0 12px 12px 0;max-width:100%}
</style>
</head>
<body>
<header><nav><a href="{{ root }}index.html">Foods</a><a href="{{ root }}compare.html">Compare</a><a href="{{ root }}gaps.html">Gaps</a><a href="{{ root }}sources.html">Sources</a></nav></header>
<main>{% block main %}{% endblock %}</main>
<footer class="muted">Code MIT · curated data CC BY 4.0 · imported data under its own license (see <a href="{{ root }}sources.html">Sources</a>)</footer>
</body>
</html>
```

Chip macro, `src/atlas/site/templates/_chip.html.j2`:
```html
{% macro chip(c, sources) -%}
<span class="chip tier-{{ c.tier }}" title="{{ sources[c.src].title }} · {{ sources[c.src].license }}{% if c.ref %} · {{ c.ref }}{% endif %}">T{{ c.tier }} · {{ c.derivation }} · {{ c.src }}</span>
{%- endmacro %}
```

`index.html.j2`:
```html
{% extends "base.html.j2" %}
{% block title %}Food Atlas — Foods{% endblock %}
{% block main %}
<h1>Foods</h1>
<p class="muted">{{ payload.stats.accepted }} sourced claims · {{ payload.stats.gaps }} open questions</p>
<label>Search <input id="q" type="search" placeholder="name, colour, texture, taste"></label>
<label>Level <select id="level"><option value="">all</option>{% for l in ["taxon_food", "cultivar", "part", "form"] %}<option>{{ l }}</option>{% endfor %}</select></label>
<div class="grid" id="grid">
{% for r in rows %}
<a class="card" href="foods/{{ r.slug }}.html" data-search="{{ r.search }}" data-level="{{ r.level }}">
<strong>{{ r.name }}</strong><br>
<span class="muted">{{ r.level }} · <em>{{ r.taxon_name }}</em></span><br>
<span class="muted">{{ r.claims }} claims · {{ r.gaps }} gaps</span>
</a>
{% endfor %}
</div>
<script>
const q = document.getElementById('q'), lv = document.getElementById('level');
function apply() {
  for (const c of document.querySelectorAll('#grid .card')) {
    c.hidden = !(c.dataset.search.includes(q.value.toLowerCase()) && (!lv.value || c.dataset.level === lv.value));
  }
}
q.addEventListener('input', apply); lv.addEventListener('change', apply);
</script>
{% endblock %}
```

`food.html.j2`:
```html
{% extends "base.html.j2" %}
{% from "_chip.html.j2" import chip %}
{% block title %}{{ food.name }} — Food Atlas{% endblock %}
{% block main %}
<h1>{{ food.name }}</h1>
<p class="muted">{% if food.name_de %}{{ food.name_de }} · {% endif %}{{ food.level }} · <em>{{ organisms[food.taxon].name }}</em>
{% if food.is_a %} · cultivar of <a href="{{ slug(food.is_a) }}.html">{{ food.is_a }}</a>{% endif %}
{% if food.part_of %} · part of <a href="{{ slug(food.part_of) }}.html">{{ food.part_of }}</a>{% endif %}
{% if food.derives_from and food.level == "form" %} · made from <a href="{{ slug(food.derives_from) }}.html">{{ food.derives_from }}</a> by {{ payload.processes[food.process] }}{% endif %}</p>
<div class="layers">
<section>
<h2>Editorial</h2>
{% for group, claims in sections if group in ("narrative", "sensory") %}
<h3>{{ group|capitalize }}</h3>
{% for c in claims %}<p><strong>{{ c.field }}:</strong> {{ c.display }} {{ chip(c, sources) }}</p>{% endfor %}
{% else %}<p class="muted">No editorial text yet.</p>{% endfor %}
</section>
<section>
<h2>Technical</h2>
{% for group, claims in sections if group not in ("narrative", "sensory") %}
<h3>{{ group|capitalize }}</h3>
<div class="scroll"><table>
<tr><th>What</th><th>Value</th><th>Basis · part</th><th>Evidence</th></tr>
{% for c in claims %}
<tr><td>{{ c.label }}{% if "llm_extracted" in c.flags %} <span class="badge">machine-extracted</span>{% endif %}</td>
<td>{{ c.display }}{% if c.v_min is not none %} <span class="muted">({{ c.v_min }}–{{ c.v_max }}, n={{ c.n }})</span>{% endif %}</td>
<td>{{ c.basis or "—" }} · {{ c.food_part or "—" }}</td>
<td>{{ chip(c, sources) }}{% if "llm_extracted" in c.flags and c.ref %}<br>{% for pmc in c.ref.split(", ") %}<a href="https://pmc.ncbi.nlm.nih.gov/articles/{{ pmc }}/">{{ pmc }}</a> {% endfor %}{% endif %}</td></tr>
{% endfor %}
</table></div>
{% else %}<p class="muted">No sourced technical values yet.</p>{% endfor %}
</section>
</div>
<h2>Open questions for this entry</h2>
{% for g in food.gaps %}<p><span class="chip tier-5">Rule {{ g.rule }}</span> {{ g.field }}: {{ g.question }} <span class="muted">Would be settled by: {{ g.would_be_settled_by }}</span></p>
{% else %}<p class="muted">None.</p>{% endfor %}
{% endblock %}
```

`compare.html.j2`:
```html
{% extends "base.html.j2" %}
{% block title %}Compare — Food Atlas{% endblock %}
{% block main %}
<h1>Compare</h1>
<p class="muted">Up to three foods side by side. A blank reads <em>not stated</em>, because that is a real answer.</p>
{% for i in range(3) %}<select class="pick">{% for f in payload.foods %}<option value="{{ f.id }}" {% if default_ids[i] == f.id %}selected{% endif %}>{{ f.name }}</option>{% endfor %}</select>{% endfor %}
<div class="scroll"><table id="cmp">
<tr><th>Nutrient</th>{% for fid in default_ids %}<th>{{ fid }}</th>{% endfor %}</tr>
{% for r in default %}<tr><td>{{ r.label }}</td>{% for v in r.values %}<td>{{ v }}</td>{% endfor %}</tr>{% endfor %}
</table></div>
<script>
const DATA = {{ data|safe }};
function render() {
  const ids = [...document.querySelectorAll('.pick')].map(s => s.value);
  const fields = [...new Set(ids.flatMap(id => Object.keys(DATA.rows[id] || {})))]
    .sort((a, b) => (DATA.labels[a] || a).localeCompare(DATA.labels[b] || b));
  const esc = s => String(s).replace(/[&<>"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch]));
  const names = Object.fromEntries(DATA.foods.map(f => [f.id, f.name]));
  let html = '<tr><th>Nutrient</th>' + ids.map(id => `<th>${esc(names[id])}</th>`).join('') + '</tr>';
  for (const f of fields) {
    html += `<tr><td>${esc(DATA.labels[f] || f)}</td>` +
      ids.map(id => `<td>${esc((DATA.rows[id] || {})[f] || 'not stated')}</td>`).join('') + '</tr>';
  }
  document.getElementById('cmp').innerHTML = html;
}
document.querySelectorAll('.pick').forEach(s => s.addEventListener('change', render));
</script>
{% endblock %}
```
`{{ data|safe }}` embeds JSON built by `json.dumps`. In that string, `render_site` has already replaced `</` with `<\/`, so a value can never close the script tag.

`gaps.html.j2`:
```html
{% extends "base.html.j2" %}
{% block title %}Gaps — Food Atlas{% endblock %}
{% block main %}
<h1>Open questions</h1>
<p class="muted">Every value that failed the traceability contract, with what would settle it.</p>
{% for rule, gaps in by_rule.items() %}
<h2>Rule {{ rule }} <span class="muted">({{ gaps|length }})</span></h2>
<div class="scroll"><table>
<tr><th>Subject</th><th>Field</th><th>Question</th><th>Carried value</th><th>Source</th><th>Would be settled by</th></tr>
{% for g in gaps %}<tr><td>{{ g.subject }}</td><td>{{ g.field }}</td><td>{{ g.question }}</td><td>{{ g.carried_value if g.carried_value is not none else "—" }}</td><td>{{ g.src }}</td><td>{{ g.would_be_settled_by }}</td></tr>{% endfor %}
</table></div>
{% else %}<p>No open questions.</p>{% endfor %}
{% endblock %}
```

`sources.html.j2`:
```html
{% extends "base.html.j2" %}
{% block title %}Sources — Food Atlas{% endblock %}
{% block main %}
<h1>Sources</h1>
<div class="scroll"><table>
<tr><th>ID</th><th>Title</th><th>License</th><th>Use</th><th>Kind</th><th>Independence</th><th>Link</th><th>Claims</th><th>Attribution</th></tr>
{% for s in payload.sources %}
<tr><td>{{ s.id }}</td><td><a href="{{ s.url }}">{{ s.title }}</a><br><span class="muted">{{ s.publisher }}</span></td>
<td>{{ s.license }}</td><td>{{ s.license_class }}</td><td>{{ s.kind }}</td><td>{{ s.independence }}</td>
<td>{{ s.link_status }}</td><td>{{ s.claims }}</td><td>{{ s.attribution }}</td></tr>
{% endfor %}
</table></div>
{% endblock %}
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_site.py -q`
Expected: `3 passed`

- [ ] **Step 6: Commit**

```bash
git add src/atlas/site tests/test_site.py
git commit -m "feat: static pilot site with evidence chips, compare, gaps and sources"
```

---

### Task 13: Command line and preview

**Files:**
- Create: `src/atlas/cli.py`, `tests/test_cli.py`, `.claude/launch.json`
- Modify: `README.md` (usage)

**Interfaces:**
- Consumes: `load_downloads` and `fetch` (Task 6), `check_links` (Task 6), `load_sources` (Task 3), `build` (Task 11), `render_site` (Task 12), and `search_fdc`, `search_bls` and `search_foodatlas` (Tasks 7–9).
- Produces: `main(argv=None) -> int`, with the subcommands `fetch`, `check-links`, `build`, `site` and `curate`, and a global `--root`.

- [ ] **Step 1: Write the failing tests**

`tests/test_cli.py`:
```python
from atlas.cli import main


def test_build_and_site(project, capsys):
    assert main(["--root", str(project), "build"]) == 0
    assert "accepted 8 · gaps 4" in capsys.readouterr().out
    assert main(["--root", str(project), "site"]) == 0
    assert (project / "data/build/site/index.html").exists()


def test_curate_fdc(project, capsys):
    assert main(["--root", str(project), "curate", "fdc", "honeycrisp"]) == 0
    assert "Apples, honeycrisp, with skin, raw" in capsys.readouterr().out


def test_curate_foodatlas(project, capsys):
    assert main(["--root", str(project), "curate", "foodatlas", "apple"]) == 0
    out = capsys.readouterr().out
    assert "e897\tapple" in out and "e1536\tHoneycrisp apple" in out
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_cli.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'atlas.cli'`

- [ ] **Step 3: Implement `src/atlas/cli.py`**

```python
"""`atlas` command line: fetch, check-links, build, site, curate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from atlas.build import build
from atlas.curate import search_bls, search_fdc, search_foodatlas
from atlas.fetch import fetch, load_downloads
from atlas.links import check_links
from atlas.registry import load_sources
from atlas.site.build import render_site

SEARCH = {"fdc": search_fdc, "bls": search_bls, "foodatlas": search_foodatlas}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="atlas")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch", help="download a raw source listed in data/registry/downloads.yaml")
    f.add_argument("id")
    f.add_argument("--from-file", type=Path)
    sub.add_parser("check-links", help="check every source URL (rule 4)")
    b = sub.add_parser("build", help="validate all claims and write data/build")
    b.add_argument("--no-raw", action="store_true", help="skip raw sources that are not downloaded")
    sub.add_parser("site", help="render data/build/site from data/build/atlas.json")
    c = sub.add_parser("curate", help="search raw sources while editing foods.yaml")
    c.add_argument("kind", choices=sorted(SEARCH))
    c.add_argument("query")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    registry = root / "data/registry"

    if args.cmd == "fetch":
        print(fetch(load_downloads(registry / "downloads.yaml")[args.id], root, args.from_file))
        return 0
    if args.cmd == "check-links":
        results = check_links(load_sources(registry / "sources.yaml"), registry / "link_status.yaml")
        for sid, status in sorted(results.items()):
            print(f"{status:10} {sid}")
        return 1 if "broken" in results.values() else 0
    if args.cmd == "build":
        result = build(root, require_raw=not args.no_raw)
        print(f"accepted {len(result.validation.accepted)} · gaps {len(result.validation.gaps)}")
        return 0
    if args.cmd == "site":
        payload = json.loads((root / "data/build/atlas.json").read_text(encoding="utf-8"))
        for path in render_site(payload, root / "data/build/site"):
            print(path)
        return 0
    if args.cmd == "curate":
        print("\n".join(SEARCH[args.kind](root, args.query)))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_cli.py -q`
Expected: `3 passed`

- [ ] **Step 5: Add the preview configuration and README usage**

`.claude/launch.json`:
```json
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "food-atlas-site",
      "runtimeExecutable": "python3",
      "runtimeArgs": ["-m", "http.server", "8765", "--directory", "data/build/site"],
      "port": 8765
    }
  ]
}
```

In `README.md`, document these commands:
- `uv run atlas fetch fdc-foundation`
- `uv run atlas fetch bls --from-file ~/Downloads/BLS_4_0_2025_DE.zip`
- `uv run atlas check-links`
- `uv run atlas build`
- `uv run atlas site`
- `uv run atlas curate fdc apple`
- `uv run pytest -q`, and `uv run pytest -q -m data` after the downloads

- [ ] **Step 6: Commit**

```bash
git add src/atlas/cli.py tests/test_cli.py .claude/launch.json README.md
git commit -m "feat: atlas command line and local site preview"
```

---

## Verification (end to end)

1. **Unit and integration tests:** `uv run pytest -q`. Everything should pass, with the `data`-marked tests skipped if raw files are missing.
2. **Real-data tests** (after Task 6's downloads): `uv run pytest -q -m data`. Expected: 3 passed.
3. **Link check:** `uv run atlas check-links`. Expected exit code 0, with no `broken` source.
4. **Build:** `uv run atlas build`. Expected: `accepted N · gaps M`. Then check `data/build/gaps.csv`:
   - It contains no rule 2, 3 or 9 gaps.
   - Rule 6 and 10 gaps (FoodAtlas amounts) and rule 5 gaps (FDC rows without a derivation) are expected, and each names what would settle it.
5. **Provenance and exclusions:**
   - `NOTICE.md` lists USDA FDC, BLS 4.0 (with its DOI), FoodAtlas, Khoury 2016, NCBI and the editorial sources.
   - `grep -c ctd data/build/claims.csv` prints 0.
   - `grep -E "e1671|e10084|e1475" data/build/claims.csv` prints nothing.
6. **Site:** `uv run atlas site`, then start the `food-atlas-site` preview and check these pages:
   - **Foods:** searching "crisp" filters the cards, and the Level filter works.
   - **Apple 'Honeycrisp':** USDA values show ranges and T1/T4 evidence chips; FoodAtlas molecules are labelled *machine-extracted* and link to PMC.
   - **Sauerkraut:** says "made from Cabbage by Lactic acid fermentation".
   - **Compare:** switching the three selects re-renders, and blanks read *not stated*.
   - **Gaps:** grouped by rule.
   - **Sources:** shows license, use class and link status.
   - **Themes and layout:** light and dark both work, with no horizontal scroll at 375 px width.
7. **Final pass:** run `superpowers:verification-before-completion` before reporting done.

## Roadmap (separate plans, written when Plan 1 is done)

- **Plan 2 — Molecules and bioactivity:**
  - ChEBI (CC BY 4.0) ontology import for structure-based deduplication (conjugate acids/bases, InChIKey), replacing hand aliases.
  - CDNO mapping.
  - Gupta et al. 2026 evidence layer, taken from the CC BY paper text and tables and flagged `evidence_only`.
  - Antioxidant values from Carlsen et al. 2010 (open access).
  - Molecules view, chemical-fingerprint map and bioactivity wheel.
- **Plan 3 — Organisms, map, season, growing at scale:**
  - Kew useful-plants checklist and WCVP (license check first), GBIF backbone, FAOSTAT production (CC BY 4.0), CROPGRIDS or SPAM 2020 (license check first), ECOCROP citations.
  - Ciqual, the Swiss database and CoFID as further nutrition tables.
  - World map and season calendar views.
- **Plan 4 — Processes, microbes, funnel:**
  - EFSA QPS list and cFMD metadata (license check first).
  - Ark of Taste citations; the underused-foods funnel view.
  - Pilot expansion to more species.
- **Optional adapters** (local only, never shipped): PTFI, FooDB, Phenol-Explorer, BioFoodComp.

## Execution handoff

After approval:
1. Copy this plan to `docs/superpowers/plans/2026-09-17-food-atlas-pilot-foundation.md` (Task 1, Step 5).
2. Choose the execution mode: **subagent-driven** (recommended; one fresh subagent per task, with review between tasks) or **inline** (`superpowers:executing-plans`, in batches with checkpoints).
