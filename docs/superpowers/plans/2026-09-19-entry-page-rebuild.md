# Entry Page Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the Food Atlas entry page on the Micrographics token layer in a botanical register, with per-section disclosure, conflicts shown as ranges, and a two-stage nutrition composition bar.

**Architecture:** The data layer, contract and claim validation are untouched. A new pure module `src/atlas/site/composition.py` collapses a nutrient's claims into a value-or-range and splits macronutrients into water plus dry matter. The Jinja templates gain a token layer and a rewritten entry page; `build.py` changes only to pass labelled claims and the composition to the template.

**Tech Stack:** Python 3.12+, Jinja2, pytest, DuckDB (data layer, untouched), Playwright via Node (optional browser regression).

**Spec:** `docs/superpowers/specs/2026-09-19-entry-page-design.md`

**Concurrent work:** A separate session is rewriting rule 8 in `src/atlas/contract.py` and `product.md` (task_1ce2cff2). This plan does not touch either file. If `tests/test_contract.py` conflicts on merge, that task owns it.

## Global Constraints

- **English UI only.** `name_de` is never rendered. Source titles stay verbatim as published — `Bundeslebensmittelschlüssel (BLS), Version 4.0 — Deutsche Nährstoffdatenbank` is a citation, not UI copy.
- **Tokens verbatim** from `SPOTIFY/Playlist spotify/MIcrographics v2 Design System/colors_and_type.css`: `--paper` `#F2EFE8`, `--paper-2` `#E8E4DA`, `--ink` `#0B0B0B` with alpha scale `.90/.55/.30/.15/.08`, `--accent` `#FF4F00`, `--cobalt` `#1530FF`.
- **Fonts:** Archivo (display), Inter Tight (body), JetBrains Mono (metadata only), Instrument Serif (editorial).
- **Dropped ornament:** no crop marks, no persistent data header, no rubber stamps, no dot-grid backdrop, no mono-as-chrome.
- **Square corners.** `border-radius: 0`. No shadows.
- **One accent per surface, under 5% of area.** `--cobalt` is reserved for marking traditional knowledge only.
- **No tier labels on the reading surface.** `T1`…`T5` are internal vocabulary. Tiers still drive ordering and selection.
- **Missing is never zero.** An absent nutrient renders as absent, not as `0`.
- **No %DV, no reference intake, no health score.**
- **Tests:** `uv run pytest -q`. Record the baseline counts before Task 1 and
  compare against them; never hard-code an absolute total, because the baseline
  moves. Two things already moved it:
  - The rule 8 rewrite landed after this plan was written, adding 8 tests to
    `tests/test_contract.py` and changing `SETTLED_BY[8]` to
    `"Compound-level evidence linking this food to the claimed activity."`
  - **In a fresh worktree, four `tests/test_real_data.py` tests fail rather than
    skip.** `.gitignore` keeps `data/raw/**/SOURCE.md` and the directory shells but
    not the data, so `need()`'s `path.exists()` guard passes on an empty directory
    and the loader raises `FileNotFoundError`. These four failures are
    environmental and unrelated to this plan. Treat the baseline as
    "no NEW failures", not "zero failures".

---

### Task 1: Composition reader — conflicts as ranges

**Files:**
- Create: `src/atlas/site/composition.py`
- Test: `tests/test_composition.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `reading(claims: list[dict], label: str) -> dict | None`. Claims are payload claim dicts that already carry a `"label"` key. Returns `{"label": str, "low": float, "high": float, "text": str, "is_range": bool, "unit": str, "sources": int}` or `None` when absent.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_composition.py
"""The composition model: a whole is 100% of a declared basis (spec §5)."""


def claim(label, value, src="SRC-A", tier=1, unit="g"):
    return dict(group="nutrition", label=label, v=value, unit=unit, src=src,
                tier=tier, derivation="analytical")


def test_single_source_reads_as_one_value():
    from atlas.site.composition import reading
    r = reading([claim("Protein", 2.92)], "Protein")
    assert r["text"] == "2.92"
    assert r["is_range"] is False
    assert r["unit"] == "g"
    assert r["sources"] == 1


def test_disagreeing_sources_read_as_a_range():
    from atlas.site.composition import reading
    claims = [claim("Carotene, beta", 2870.0, src="SRC-A", unit="ug"),
              claim("Carotene, beta", 2873.0, src="SRC-B", unit="ug")]
    r = reading(claims, "Carotene, beta")
    assert r["text"] == "2870–2873"
    assert r["is_range"] is True
    assert (r["low"], r["high"]) == (2870.0, 2873.0)
    assert r["sources"] == 2


def test_agreeing_sources_do_not_produce_a_range():
    from atlas.site.composition import reading
    claims = [claim("Calcium, Ca", 254.0, src="SRC-A", unit="mg"),
              claim("Calcium, Ca", 254.0, src="SRC-B", unit="mg")]
    r = reading(claims, "Calcium, Ca")
    assert r["is_range"] is False
    assert r["text"] == "254"
    assert r["sources"] == 2


def test_absent_nutrient_is_none_never_zero():
    from atlas.site.composition import reading
    assert reading([claim("Protein", 2.92)], "Water") is None


def test_non_numeric_and_boolean_values_are_ignored():
    from atlas.site.composition import reading
    assert reading([claim("Protein", "present")], "Protein") is None
    assert reading([claim("Protein", True)], "Protein") is None


def test_unit_and_tier_come_from_the_best_evidenced_claim():
    from atlas.site.composition import reading
    claims = [claim("Protein", 4.16, src="SRC-BLS", tier=3),
              claim("Protein", 2.92, src="SRC-FDC", tier=1)]
    r = reading(claims, "Protein")
    assert r["tier"] == 1
    assert r["text"] == "2.92–4.16"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_composition.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'atlas.site.composition'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/atlas/site/composition.py
"""Composition: a whole is 100% of a declared basis; components are fractions.

Spec: docs/superpowers/specs/2026-09-19-entry-page-design.md §5. Where sources
disagree the spread is shown, so the reader is never asked to arbitrate and
disagreement is never hidden. An absent nutrient is absent, never zero.
"""
from __future__ import annotations


def _fmt(value: float) -> str:
    return f"{value:g}"


def _matching(claims: list[dict], label: str) -> list[dict]:
    return [c for c in claims
            if c.get("group") == "nutrition" and c.get("label") == label]


def reading(claims: list[dict], label: str) -> dict | None:
    """Collapse one nutrient's claims into a value or a range.

    Returns None when the nutrient is absent. Callers must render that as
    absent: a missing measurement is not a measurement of zero.
    """
    matching = _matching(claims, label)
    values = sorted({
        c["v"] for c in matching
        if isinstance(c.get("v"), (int, float)) and not isinstance(c.get("v"), bool)
    })
    if not values:
        return None
    best = min(matching, key=lambda c: c.get("tier", 5))
    return {
        "label": label,
        "low": values[0],
        "high": values[-1],
        "text": _fmt(values[0]) if len(values) == 1
                else f"{_fmt(values[0])}–{_fmt(values[-1])}",
        "is_range": len(values) > 1,
        "unit": best.get("unit") or "",
        "tier": best.get("tier", 5),
        "sources": len({c["src"] for c in matching}),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_composition.py -q`
Expected: PASS, 6 passed

- [ ] **Step 5: Run the whole suite**

Run: `uv run pytest -q`
Expected: green. This plan has added 6 tests so far; nothing previously passing may fail. (235 + 6)

- [ ] **Step 6: Commit**

```bash
git add src/atlas/site/composition.py tests/test_composition.py
git commit -m "feat(site): composition reader — conflicting sources read as ranges

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: Macro split — water and dry matter at two scales

**Files:**
- Modify: `src/atlas/site/composition.py`
- Test: `tests/test_composition.py`

**Interfaces:**
- Consumes: `reading()` from Task 1.
- Produces: `macro_split(claims: list[dict]) -> dict | None` returning `{"water": reading, "dry_total": float, "dry": list[reading + {"display": str}], "total": float}`, or `None` when water or all dry components are absent.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_composition.py

KALE = [  # real values, data/build/atlas.json, per 100 g
    claim("Water", 89.6), claim("Water", 89.63, src="SRC-B"),
    claim("Carbohydrate, by difference", 4.42, tier=4),
    claim("Protein", 2.92), claim("Ash", 1.54), claim("Total lipid (fat)", 1.49),
]


def test_macro_split_separates_water_from_everything_else():
    from atlas.site.composition import macro_split
    split = macro_split(KALE)
    assert split["water"]["text"] == "89.6–89.63"
    assert split["dry_total"] == 10.37
    assert split["total"] == 100.0


def test_macro_split_orders_dry_matter_largest_first_with_display_names():
    from atlas.site.composition import macro_split
    split = macro_split(KALE)
    assert [(d["display"], d["text"]) for d in split["dry"]] == [
        ("Carbohydrate", "4.42"), ("Protein", "2.92"),
        ("Minerals (ash)", "1.54"), ("Fat", "1.49")]


def test_macro_split_is_none_without_water():
    from atlas.site.composition import macro_split
    assert macro_split([claim("Protein", 2.92)]) is None


def test_macro_split_is_none_without_any_dry_component():
    from atlas.site.composition import macro_split
    assert macro_split([claim("Water", 89.6)]) is None


def test_macro_split_tolerates_partial_dry_matter():
    from atlas.site.composition import macro_split
    split = macro_split([claim("Water", 89.6), claim("Protein", 2.92)])
    assert split["dry_total"] == 2.92
    assert [d["display"] for d in split["dry"]] == ["Protein"]
    assert split["total"] == 92.52
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_composition.py -q`
Expected: FAIL with `ImportError: cannot import name 'macro_split'`

- [ ] **Step 3: Write minimal implementation**

```python
# append to src/atlas/site/composition.py

WATER = "Water"
# FDC dictionary label -> display name. These five compose 100 g exactly:
# carbohydrate is "by difference", i.e. the remainder after the other four.
DRY_MATTER = (
    ("Carbohydrate, by difference", "Carbohydrate"),
    ("Protein", "Protein"),
    ("Ash", "Minerals (ash)"),
    ("Total lipid (fat)", "Fat"),
)


def macro_split(claims: list[dict]) -> dict | None:
    """Water and dry matter on a true 0-100 g scale, dry matter reopened.

    A single 0-100 g bar on a 90%-water vegetable collapses everything that
    distinguishes it into invisible slivers, so the dry matter is reopened at
    its own scale, which the page states in words (spec §5).
    """
    water = reading(claims, WATER)
    parts = [(display, reading(claims, label)) for label, display in DRY_MATTER]
    parts = [(display, r) for display, r in parts if r is not None]
    if water is None or not parts:
        return None
    parts.sort(key=lambda pair: -pair[1]["high"])
    dry_total = round(sum(r["high"] for _, r in parts), 2)
    return {
        "water": water,
        "dry": [dict(r, display=display) for display, r in parts],
        "dry_total": dry_total,
        "total": round(water["high"] + dry_total, 2),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_composition.py -q`
Expected: PASS, 11 passed

- [ ] **Step 5: Verify against real data**

Run:
```bash
uv run python -c "
import json
from atlas.site.composition import macro_split
p = json.load(open('data/build/atlas.json'))
N = p['nutrients']
kale = next(f for f in p['foods'] if f['id'] == 'food:kale')
labelled = [c | {'label': N.get(c['field'], {}).get('name', c['field'])} for c in kale['claims']]
s = macro_split(labelled)
print(s['water']['text'], s['dry_total'], s['total'])
assert s['total'] == 100.0, s['total']
print('OK')
"
```
Expected: `89.6–89.63 10.37 100.0` then `OK`

- [ ] **Step 6: Commit**

```bash
git add src/atlas/site/composition.py tests/test_composition.py
git commit -m "feat(site): macro split — water and dry matter at two declared scales

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: Micronutrient readings

**Files:**
- Modify: `src/atlas/site/composition.py`
- Test: `tests/test_composition.py`

**Interfaces:**
- Consumes: `reading()` from Task 1.
- Produces: `micro_readings(claims: list[dict], limit: int = 5) -> list[dict]` — readings for the headline micronutrients that are present, in `MICRONUTRIENTS` order, at most `limit`.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_composition.py

def test_micro_readings_keep_declared_order_and_skip_absent():
    from atlas.site.composition import micro_readings
    claims = [claim("Vitamin C, total ascorbic acid", 93.4, unit="mg"),
              claim("Calcium, Ca", 254.0, unit="mg"),
              claim("Vitamin K (phylloquinone)", 389.6, unit="ug"),
              claim("Vitamin K (phylloquinone)", 390.0, src="SRC-B", unit="ug")]
    rows = micro_readings(claims)
    assert [r["label"] for r in rows] == [
        "Vitamin K (phylloquinone)", "Vitamin C, total ascorbic acid", "Calcium, Ca"]
    assert rows[0]["text"] == "389.6–390"
    assert rows[0]["unit"] == "ug"


def test_micro_readings_respect_the_limit():
    from atlas.site.composition import micro_readings
    claims = [claim("Vitamin C, total ascorbic acid", 1.0, unit="mg"),
              claim("Calcium, Ca", 2.0, unit="mg"),
              claim("Iron, Fe", 3.0, unit="mg")]
    assert len(micro_readings(claims, limit=2)) == 2


def test_micro_readings_empty_when_nothing_present():
    from atlas.site.composition import micro_readings
    assert micro_readings([claim("Protein", 2.92)]) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_composition.py -q`
Expected: FAIL with `ImportError: cannot import name 'micro_readings'`

- [ ] **Step 3: Write minimal implementation**

```python
# append to src/atlas/site/composition.py

# Headline micronutrients in reading order. Micronutrients span 0.053 mg to
# 6260 ug and share no meaningful axis, so they are listed, never drawn on a
# common scale (spec §5).
MICRONUTRIENTS = (
    "Vitamin K (phylloquinone)",
    "Vitamin C, total ascorbic acid",
    "Lutein + zeaxanthin",
    "Carotene, beta",
    "Calcium, Ca",
    "Potassium, K",
    "Manganese, Mn",
    "Iron, Fe",
)


def micro_readings(claims: list[dict], limit: int = 5) -> list[dict]:
    """Headline micronutrients that are present, in declared order."""
    rows = []
    for label in MICRONUTRIENTS:
        r = reading(claims, label)
        if r is not None:
            rows.append(r)
        if len(rows) == limit:
            break
    return rows
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_composition.py -q`
Expected: PASS, 14 passed

- [ ] **Step 5: Commit**

```bash
git add src/atlas/site/composition.py tests/test_composition.py
git commit -m "feat(site): headline micronutrient readings

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: Expose composition to templates

**Files:**
- Modify: `src/atlas/site/build.py` (the `render_site` food loop, and a new `labelled_claims` helper)
- Test: `tests/test_composition.py`

**Interfaces:**
- Consumes: `macro_split`, `micro_readings` from Tasks 2–3.
- Produces: `labelled_claims(food: dict, payload: dict) -> list[dict]` in `atlas.site.build`. Every food template render receives `composition={"macro": ..., "micro": ...}`.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_composition.py

def test_labelled_claims_resolve_nutrient_and_molecule_names():
    from atlas.site.build import labelled_claims
    payload = dict(nutrients={"nutrient:fdc:1003": {"name": "Protein"}},
                   molecules={"quercetin": {"name": "Quercetin"}})
    food = dict(claims=[
        dict(group="nutrition", field="nutrient:fdc:1003", v=2.92, src="SRC-A", tier=1),
        dict(group="molecules", field="contains:quercetin", v="present", src="SRC-B", tier=3),
        dict(group="nutrition", field="nutrient:fdc:9999", v=1.0, src="SRC-A", tier=1),
    ])
    rows = labelled_claims(food, payload)
    assert [r["label"] for r in rows] == ["Protein", "Quercetin", "nutrient:fdc:9999"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_composition.py::test_labelled_claims_resolve_nutrient_and_molecule_names -q`
Expected: FAIL with `ImportError: cannot import name 'labelled_claims'`

- [ ] **Step 3: Write minimal implementation**

In `src/atlas/site/build.py`, add the import at the top alongside the other site imports:

```python
from atlas.site.composition import macro_split, micro_readings
```

Add the helper immediately after the existing `_label` function:

```python
def labelled_claims(food: dict, payload: dict) -> list[dict]:
    """Attach the display label the composition model matches on."""
    return [c | {"label": _label(c["field"], payload)} for c in food["claims"]]
```

In `render_site`, inside the `for food in payload["foods"]:` loop, build the
composition before the `write(...)` call and pass it through:

```python
    for food in payload["foods"]:
        related = [r for r in rows if r["family"] == row_map[food["id"]]["family"] and r["id"] != food["id"]]
        labelled = labelled_claims(food, payload)
        write(f"foods/{slug(food['id'])}.html", "food.html.j2", "../",
              food=food, row=row_map[food["id"]], related=related, sections=sections(food, payload),
              composition={"macro": macro_split(labelled), "micro": micro_readings(labelled)},
              nutrition=nutrition_profile(food), research=research_profile(food["claims"]),
              organism_claims=organisms[food["taxon"]].get("claims", []))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_composition.py -q`
Expected: PASS, 15 passed

- [ ] **Step 5: Run the whole suite**

Run: `uv run pytest -q`
Expected: green. This plan has added 15 tests so far; nothing previously passing may fail.. No existing test asserts on `composition`, so nothing should break.

- [ ] **Step 6: Commit**

```bash
git add src/atlas/site/build.py tests/test_composition.py
git commit -m "feat(site): pass composition to the entry template

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: Micrographics token layer

**Files:**
- Create: `src/atlas/site/templates/_tokens.css.j2`
- Modify: `src/atlas/site/templates/_style.css.j2` (delete the three `:root` lines, lines 5–7, and the `body`/`*` reset that follows them on line 8)
- Modify: `src/atlas/site/templates/base.html.j2` (include `_tokens.css.j2` before `_style.css.j2`)
- Test: `tests/test_site.py`

**Interfaces:**
- Consumes: nothing.
- Produces: CSS custom properties available to every template: `--paper`, `--paper-2`, `--ink`, `--ink-90`, `--ink-55`, `--ink-30`, `--ink-15`, `--ink-08`, `--accent`, `--cobalt`, `--f-display`, `--f-body`, `--f-mono`, `--f-serif`, the `--t-*` scale, the `--s-*` spacing scale, `--hairline-w`.

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_site.py

def test_token_layer_replaces_the_invented_palette(payload, tmp_path):
    from atlas.site.build import render_site
    render_site(payload, tmp_path)
    index = (tmp_path / "index.html").read_text()
    for token, value in [("--paper", "#F2EFE8"), ("--paper-2", "#E8E4DA"),
                         ("--ink", "#0B0B0B"), ("--accent", "#FF4F00"),
                         ("--cobalt", "#1530FF")]:
        assert f"{token}:{value}" in index or f"{token}: {value}" in index, token
    for retired in ("#B10034", "#F1EEE7", "#25251f"):
        assert retired not in index, retired
    for family in ("Archivo", "Inter Tight", "JetBrains Mono", "Instrument Serif"):
        assert family in index, family


def test_square_corners_and_no_shadows(payload, tmp_path):
    from atlas.site.build import render_site
    render_site(payload, tmp_path)
    index = (tmp_path / "index.html").read_text()
    assert "border-radius:6px" not in index and "border-radius:10px" not in index
    assert "box-shadow:0 8px 36px" not in index
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_site.py::test_token_layer_replaces_the_invented_palette -q`
Expected: FAIL — `--paper` is not defined and `#B10034` is still present.

- [ ] **Step 3: Create the token layer**

```css
/* src/atlas/site/templates/_tokens.css.j2
   Micrographics v2 tokens, verbatim. Single source of truth for colour, type,
   spacing and rules. Never invent a colour: if a third weight is needed, drop
   opacity rather than adding a token. */
:root{
  --paper:#F2EFE8; --paper-2:#E8E4DA;
  --ink:#0B0B0B;
  --ink-90:rgba(11,11,11,.90); --ink-55:rgba(11,11,11,.55);
  --ink-30:rgba(11,11,11,.30); --ink-15:rgba(11,11,11,.15); --ink-08:rgba(11,11,11,.08);
  --accent:#FF4F00;
  --cobalt:#1530FF;
  --f-display:'Archivo','Helvetica Neue',Helvetica,Arial,sans-serif;
  --f-body:'Inter Tight','Helvetica Neue',Helvetica,Arial,sans-serif;
  --f-mono:'JetBrains Mono',ui-monospace,'SF Mono',Menlo,monospace;
  --f-serif:'Instrument Serif','Times New Roman',serif;
  --t-micro:10px; --t-mini:12px; --t-small:13px; --t-body:15px; --t-lead:18px;
  --t-h4:24px; --t-h3:36px; --t-h2:64px;
  --tr-tight:-0.02em; --tr-wide:0.08em; --tr-xwide:0.14em;
  --lh-tight:1.0; --lh-snug:1.15; --lh-body:1.45;
  --s-1:4px; --s-2:8px; --s-3:12px; --s-4:16px; --s-5:20px; --s-6:24px;
  --s-8:32px; --s-10:40px; --s-12:48px; --s-16:64px; --s-20:80px; --s-24:96px;
  --hairline-w:0.5px;
  color-scheme:light;
}
:root[data-theme=dark]{
  --paper:#0B0B0B; --paper-2:#161616;
  --ink:#EDEAE2;
  --ink-90:rgba(237,234,226,.90); --ink-55:rgba(237,234,226,.55);
  --ink-30:rgba(237,234,226,.30); --ink-15:rgba(237,234,226,.18); --ink-08:rgba(237,234,226,.10);
  color-scheme:dark;
}
@media(prefers-color-scheme:dark){
  :root:not([data-theme=light]){
    --paper:#0B0B0B; --paper-2:#161616;
    --ink:#EDEAE2;
    --ink-90:rgba(237,234,226,.90); --ink-55:rgba(237,234,226,.55);
    --ink-30:rgba(237,234,226,.30); --ink-15:rgba(237,234,226,.18); --ink-08:rgba(237,234,226,.10);
    color-scheme:dark;
  }
}
*{box-sizing:border-box}
[hidden]{display:none!important}
html,body{
  margin:0;background:var(--paper);color:var(--ink);
  font-family:var(--f-body);font-size:var(--t-body);line-height:var(--lh-body);
  -webkit-font-smoothing:antialiased;text-rendering:geometricPrecision;
}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
button,input,select{font:inherit;color:inherit;border-radius:0}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
```

- [ ] **Step 4: Wire it into the base template**

In `src/atlas/site/templates/base.html.j2`, find the line that includes the
stylesheet and put the token layer immediately before it, inside the same
`<style>` element:

```jinja
<style>{% include "_tokens.css.j2" %}{% include "_style.css.j2" %}</style>
```

- [ ] **Step 5: Remove the retired palette from `_style.css.j2`**

Delete the three `:root` lines (the light palette, the `[data-theme=dark]`
palette, and the `prefers-color-scheme` block) and the `*{box-sizing…}` reset
line that follows, since `_tokens.css.j2` now owns all four. Then replace every
remaining reference to the retired variable names:

| Retired | Replacement |
|---|---|
| `var(--bg)` | `var(--paper)` |
| `var(--fg)` | `var(--ink)` |
| `var(--muted)` | `var(--ink-55)` |
| `var(--line)` | `var(--ink-15)` |
| `var(--card)` | `var(--paper-2)` |
| `var(--soft)` | `var(--paper-2)` |

Run this to find any you missed:
```bash
grep -o 'var(--\(bg\|fg\|muted\|line\|card\|soft\))' src/atlas/site/templates/_style.css.j2 | sort -u
```
Expected after the edit: no output.

Then remove every `border-radius` and `box-shadow` declaration:
```bash
grep -n 'border-radius\|box-shadow' src/atlas/site/templates/_style.css.j2
```
Expected after the edit: no output.

- [ ] **Step 6: Run the new tests**

Run: `uv run pytest tests/test_site.py::test_token_layer_replaces_the_invented_palette tests/test_site.py::test_square_corners_and_no_shadows -q`
Expected: PASS, 2 passed

- [ ] **Step 7: Update the existing palette assertion**

`test_render_site_evidence_and_navigation` asserts the retired palette. In
`tests/test_site.py`, replace:

```python
    assert "#F1EEE7" in index and "#B10034" in index
```

with:

```python
    assert "#F2EFE8" in index and "#FF4F00" in index
```

- [ ] **Step 8: Run the whole suite**

Run: `uv run pytest -q`
Expected: green. This plan has added 17 tests so far; nothing previously passing may fail.

- [ ] **Step 9: Commit**

```bash
git add src/atlas/site/templates/_tokens.css.j2 src/atlas/site/templates/_style.css.j2 src/atlas/site/templates/base.html.j2 tests/test_site.py
git commit -m "feat(site): Micrographics token layer replaces the invented palette

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: English-only UI

**Files:**
- Modify: `src/atlas/site/build.py` (the `search` field in `index_rows`)
- Modify: `src/atlas/site/templates/food.html.j2` (remove the `name_de` rendering)
- Test: `tests/test_site.py`, `tests/test_interview.py`

**Interfaces:**
- Consumes: nothing.
- Produces: no rendered page contains `name_de`. Source titles are unchanged.

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_site.py

def test_german_food_names_never_reach_the_ui(payload, tmp_path):
    from atlas.site.build import render_site
    render_site(payload, tmp_path)
    entry = (tmp_path / "foods/apple.html").read_text()
    index = (tmp_path / "index.html").read_text()
    assert "Apfel roh" not in entry
    assert "Apfel roh" not in index and "apfel roh" not in index
    assert "Malus domestica" in entry


def test_source_titles_stay_verbatim(payload, tmp_path):
    """A published title is a citation, not UI copy (spec, Global Constraints)."""
    from atlas.site.build import render_site
    payload["sources"][0]["title"] = "Bundeslebensmittelschlüssel (BLS), Version 4.0"
    render_site(payload, tmp_path)
    assert "Bundeslebensmittelschlüssel (BLS), Version 4.0" in (tmp_path / "sources.html").read_text()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_site.py::test_german_food_names_never_reach_the_ui -q`
Expected: FAIL — `"Apfel roh" not in entry` is False.

- [ ] **Step 3: Remove `name_de` from the search index**

In `src/atlas/site/build.py`, in `index_rows`, change the `search` field from:

```python
            "search": " ".join([food["name"], food.get("name_de") or "", taxon_name,
```

to:

```python
            "search": " ".join([food["name"], taxon_name,
```

- [ ] **Step 4: Remove `name_de` from the entry template**

In `src/atlas/site/templates/food.html.j2`, find the line rendering the German
name and delete it. Locate it with:

```bash
grep -n "name_de" src/atlas/site/templates/*.j2
```
Expected after the edit: no output.

- [ ] **Step 5: Run the new tests**

Run: `uv run pytest tests/test_site.py::test_german_food_names_never_reach_the_ui tests/test_site.py::test_source_titles_stay_verbatim -q`
Expected: PASS, 2 passed

- [ ] **Step 6: Update the three existing assertions that expect German**

In `tests/test_site.py`, in `test_render_site_evidence_and_navigation`, replace:
```python
    assert "Apfel roh" in entry and "Malus domestica" in entry
```
with:
```python
    assert "Malus domestica" in entry
```

In the same file, in `test_render_site_evidence_and_navigation`, replace:
```python
    assert "apple--honeycrisp.html" in index and "apfel roh" in index
```
with:
```python
    assert "apple--honeycrisp.html" in index
```

In `test_render_site_from_build`, replace:
```python
    assert "Apfel roh" in apple and "Amount without unit, basis or food part." in apple
```
with:
```python
    assert "Amount without unit, basis or food part." in apple
```

- [ ] **Step 7: Update the browser regression that searches in German**

In `tests/test_site.py`, in `test_mobile_filters_and_live_compare`, the script
fills the search box with `'apfel'`. Replace both occurrences of the Playwright
filter value so the test searches an English name instead:

```javascript
    await page.locator('#q').fill('apple');
```

The subsequent `selectOption('cultivar')` assertion expects 0 visible cards
after filtering, which still holds: the payload's only cultivar is named
"Honeycrisp", which does not contain "apple".

- [ ] **Step 8: Run the whole suite**

Run: `uv run pytest -q`
Expected: green. This plan has added 19 tests so far; nothing previously passing may fail.

- [ ] **Step 9: Commit**

```bash
git add src/atlas/site/build.py src/atlas/site/templates/food.html.j2 tests/test_site.py
git commit -m "feat(site): English-only UI; source titles stay verbatim

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 7: Entry masthead

**Files:**
- Create: `src/atlas/site/templates/_masthead.html.j2`
- Create: `src/atlas/site/templates/_entry.css.j2`
- Modify: `src/atlas/site/templates/food.html.j2` (replace the `entry-header` block with the include)
- Modify: `src/atlas/site/templates/base.html.j2` (include `_entry.css.j2`)
- Modify: `src/atlas/site/build.py` (register a `month_name` filter)
- Test: `tests/test_site.py`

**Interfaces:**
- Consumes: `food`, `row`, `organisms`, `image_for`, `level_label` — already in the
  template context. `row.family_name`, `row.molecules` and `row.seasons` come from
  `index_rows`; `image_for` and `level_label` are `env.globals`.
- Produces: markup with classes `entry-masthead`, `entry-identity`, `entry-fam`,
  `entry-binomial`, `entry-lede`, `entry-tags`, `entry-plate`, and a Jinja filter
  `month_name(int) -> str` mapping `1` to `"Jan"` … `12` to `"Dec"`.

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_site.py

def test_masthead_order_identity_then_plate_then_profiles(payload, tmp_path):
    """Composition C: identity first, then the plate, then the profiles (spec §4)."""
    from atlas.site.build import render_site
    payload["foods"][0]["claims"].append(
        dict(subject="food:apple", group="narrative", field="eli5",
             v="An apple is a fruit you can hold in one hand.",
             src="SRC-A", tier=4, derivation="editorial", flags=[], ref=None))
    render_site(payload, tmp_path)
    entry = (tmp_path / "foods/apple.html").read_text()
    assert entry.index('class="entry-masthead"') < entry.index('class="entry-plate"')
    assert entry.index('class="entry-plate"') < entry.index('class="entry-profiles"')


def test_masthead_carries_identity_and_lede(payload, tmp_path):
    from atlas.site.build import render_site
    payload["foods"][0]["claims"].append(
        dict(subject="food:apple", group="narrative", field="eli5",
             v="An apple is a fruit you can hold in one hand.",
             src="SRC-A", tier=4, derivation="editorial", flags=[], ref=None))
    render_site(payload, tmp_path)
    entry = (tmp_path / "foods/apple.html").read_text()
    assert 'class="entry-binomial"' in entry and "Malus domestica" in entry
    assert "An apple is a fruit you can hold in one hand." in entry
    assert 'class="entry-tags"' in entry


def test_season_tag_shows_month_names_not_numbers(payload, tmp_path):
    from atlas.site.build import render_site
    payload["foods"][0]["claims"].append(
        dict(subject="food:apple", group="season", field="season:CH:fresh",
             v=[10, 11, 12], src="SRC-A", tier=3, derivation="extracted",
             flags=[], ref=None))
    render_site(payload, tmp_path)
    entry = (tmp_path / "foods/apple.html").read_text()
    assert "In season:" in entry and "Oct, Nov, Dec" in entry
    assert "10, 11, 12" not in entry
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_site.py::test_masthead_order_identity_then_plate_then_profiles -q`
Expected: FAIL with `ValueError: substring not found`

- [ ] **Step 3: Register the month-name filter**

`row.seasons[0].months` is a list of month numbers, so rendering it directly
prints `10, 11, 12`. In `src/atlas/site/build.py`, add above `render_site`:

```python
MONTH_NAMES = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def month_name(number: int) -> str:
    """Month number to short English name; unknown numbers pass through."""
    return MONTH_NAMES[number - 1] if 1 <= number <= 12 else str(number)
```

and register it inside `render_site`, next to `env.globals.update(...)`:

```python
    env.filters["month_name"] = month_name
```

- [ ] **Step 4: Create the masthead partial**

```jinja
{# src/atlas/site/templates/_masthead.html.j2
   Composition C (spec §4): identity at large scale, tags beside it, plate below.
   No data header, no crop marks, no stamps. #}
{% set organism = organisms[food.taxon] %}
{% set lede = (food.claims | selectattr("group", "equalto", "narrative")
                           | selectattr("field", "equalto", "eli5") | list) %}
<header class="entry-masthead">
  <div class="entry-identity">
    <p class="entry-fam">{{ row.family_name }} &middot; {{ level_label[food.level] }}</p>
    <h1>{{ food.name }}</h1>
    <p class="entry-binomial">{{ organism.name }}</p>
    {% if lede %}<p class="entry-lede">{{ lede[0].v }}</p>{% endif %}
  </div>
  <div class="entry-tags">
    <span class="tag">{{ level_label[food.level] }}</span>
    <span class="tag">{{ row.family_name }}</span>
    {% if row.seasons %}
      <span class="tag">In season:
        {{ row.seasons[0].months | map("month_name") | join(", ") }}</span>
    {% endif %}
    {% if row.molecules %}<span class="tag">{{ row.molecules }} molecules studied</span>{% endif %}
  </div>
</header>
{% set image = image_for(food) %}
{% if image %}
<figure class="entry-plate">
  <img src="{{ root }}{{ image.url }}" alt="{{ image.alt }}" width="{{ image.width }}" height="{{ image.height }}">
  <figcaption>
    {{ image.reference_label }}
    &copy; {{ image.credit }} &middot; {{ image.license }} &middot; retrieved {{ image.retrieved }}
  </figcaption>
</figure>
{% endif %}
```

- [ ] **Step 5: Create the entry stylesheet**

```css
/* src/atlas/site/templates/_entry.css.j2
   Botanical register on Micrographics tokens: warmth from photography, serif
   editorial and space — never from rounded corners or shadows. */
.entry-masthead{display:grid;grid-template-columns:minmax(0,1fr) minmax(280px,.55fr);
  gap:var(--s-16);align-items:end;margin-bottom:var(--s-8)}
.entry-fam{margin:0;font-size:var(--t-mini);font-weight:600;letter-spacing:var(--tr-wide);
  text-transform:uppercase;color:var(--ink-55)}
.entry-masthead h1{margin:var(--s-2) 0 0;font-family:var(--f-display);font-weight:800;
  font-size:clamp(52px,6vw,92px);line-height:.95;letter-spacing:var(--tr-tight)}
.entry-binomial{font-family:var(--f-serif);font-style:italic;font-size:var(--t-h3);
  margin:var(--s-2) 0 0;color:var(--ink-90);line-height:var(--lh-snug)}
.entry-lede{font-family:var(--f-serif);font-size:var(--t-h4);line-height:1.45;
  margin:var(--s-5) 0 0;max-width:52ch;color:var(--ink-90)}
.entry-tags{display:flex;flex-wrap:wrap;gap:var(--s-2)}
.tag{display:inline-flex;align-items:center;gap:6px;padding:5px 11px;
  border:1px solid var(--ink-15);background:var(--paper-2);font-size:var(--t-small)}
.entry-plate{margin:0 0 var(--s-12)}
.entry-plate img{display:block;width:100%;height:auto;max-height:420px;object-fit:cover}
.entry-plate figcaption{font-family:var(--f-mono);font-size:var(--t-micro);line-height:1.6;
  color:var(--ink-55);margin-top:var(--s-2)}
@media(max-width:900px){
  .entry-masthead{grid-template-columns:1fr;gap:var(--s-6);align-items:start}
}
```

- [ ] **Step 6: Include the stylesheet and the partial**

In `base.html.j2`, extend the style include:
```jinja
<style>{% include "_tokens.css.j2" %}{% include "_style.css.j2" %}{% include "_entry.css.j2" %}</style>
```

In `food.html.j2`, replace the existing `<header class="entry-header">…</header>`
block with:
```jinja
{% include "_masthead.html.j2" %}
```

- [ ] **Step 7: Run the new tests**

Run: `uv run pytest tests/test_site.py::test_masthead_order_identity_then_plate_then_profiles tests/test_site.py::test_masthead_carries_identity_and_lede -q`
Expected: FAIL on the first test only — `entry-profiles` does not exist yet. That class arrives in Task 8. Mark this task's first test `@pytest.mark.xfail(reason="entry-profiles lands in Task 8", strict=True)` and remove the marker in Task 8.

- [ ] **Step 8: Run the whole suite**

Run: `uv run pytest -q`
Expected: green. This plan has added 22 tests so far; nothing previously passing may fail. (one xfail counts as passed)

- [ ] **Step 9: Commit**

```bash
git add src/atlas/site/templates/_masthead.html.j2 src/atlas/site/templates/_entry.css.j2 src/atlas/site/templates/food.html.j2 src/atlas/site/templates/base.html.j2 tests/test_site.py
git commit -m "feat(site): entry masthead — composition C

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 8: At-a-glance profiles

**Files:**
- Create: `src/atlas/site/templates/_profiles.html.j2`
- Modify: `src/atlas/site/templates/_entry.css.j2`
- Modify: `src/atlas/site/templates/food.html.j2`
- Test: `tests/test_site.py`

**Interfaces:**
- Consumes: `composition` from Task 4 (`composition.macro`, `composition.micro`).
- Produces: markup with classes `entry-profiles`, `prof`, `macro-bar`, `macro-key`, `dry-bar`, `micro-row`.

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_site.py

def test_nutrition_profile_states_both_scales(payload, tmp_path):
    """Water/dry split at 0-100 g, then dry matter at its own stated scale."""
    from atlas.site.build import render_site
    food = payload["foods"][0]
    for label, field, value in [("Water", "water", 89.6), ("Protein", "protein", 2.92)]:
        payload["nutrients"][field] = {"name": label}
        food["claims"].append(dict(subject="food:apple", group="nutrition", field=field,
                                   v=value, unit="g", basis="fresh_weight", food_part="flesh",
                                   src="SRC-A", tier=1, derivation="analytical", flags=[], ref=None))
    render_site(payload, tmp_path)
    entry = (tmp_path / "foods/apple.html").read_text()
    assert 'class="entry-profiles"' in entry
    assert "89.6" in entry and "2.92" in entry
    assert "at its own scale" in entry
    assert "%DV" not in entry and "Daily Value" not in entry


def test_profiles_omitted_when_composition_absent(payload, tmp_path):
    """No water means no honest 0-100 g bar; render nothing rather than a fake one."""
    from atlas.site.build import render_site
    render_site(payload, tmp_path)
    entry = (tmp_path / "foods/apple.html").read_text()
    assert "at its own scale" not in entry
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_site.py::test_nutrition_profile_states_both_scales -q`
Expected: FAIL — `'class="entry-profiles"' in entry` is False.

- [ ] **Step 3: Create the profiles partial**

```jinja
{# src/atlas/site/templates/_profiles.html.j2
   The visible top of the iceberg (spec §4): a self-sufficient read, not a teaser.
   No tier marks on any value — evidence lives behind each register's own control. #}
{% set sensory = food.claims | selectattr("group", "equalto", "sensory") | list %}
<div class="entry-profiles">

  <section class="prof">
    <h2>Nutrition <em>per 100 g</em></h2>
    {% if composition.macro %}
      {% set macro = composition.macro %}
      <div class="macro-bar">
        <div class="seg seg-water" style="flex:{{ macro.water.high }}"></div>
        <div class="seg seg-dry" style="flex:{{ macro.dry_total }}"></div>
      </div>
      <div class="macro-key">
        <div class="key"><i class="seg-water"></i><span>Water</span>
          <b>{{ macro.water.text }}<em>g</em></b></div>
        <div class="key"><i class="seg-dry"></i><span>Everything else</span>
          <b>{{ macro.dry_total }}<em>g</em></b></div>
      </div>
      <p class="scale-note">Everything else, {{ macro.dry_total }} g, at its own scale</p>
      <div class="macro-bar dry-bar">
        {% for part in macro.dry %}
          <div class="seg seg-d{{ loop.index0 }}" style="flex:{{ part.high }}"></div>
        {% endfor %}
      </div>
      <div class="macro-key">
        {% for part in macro.dry %}
          <div class="key"><i class="seg-d{{ loop.index0 }}"></i><span>{{ part.display }}</span>
            <b>{{ part.text }}<em>g</em></b></div>
        {% endfor %}
      </div>
    {% else %}
      <p class="empty-note">Composition not yet recorded.</p>
    {% endif %}
    {% if composition.micro %}
      <div class="micros">
        {% for row in composition.micro %}
          <div class="micro-row"><span>{{ row.label }}</span>
            <b>{{ row.text }}<em>{{ row.unit }}</em></b></div>
        {% endfor %}
      </div>
    {% endif %}
  </section>

  <section class="prof">
    <h2>Sensory <em>described</em></h2>
    {% if sensory %}
      {% for claim in sensory %}
        <div class="sens-row"><span>{{ claim.field | title }}</span><p>{{ claim.v }}</p></div>
      {% endfor %}
    {% else %}
      <p class="empty-note">Sensory description not yet recorded.</p>
    {% endif %}
  </section>

  <section class="prof">
    <h2>Research <em>what is studied</em></h2>
    <div class="stat"><b>{{ row.molecules }}</b><span>molecules recorded as present</span></div>
    <p class="empty-note">Occurrence only. The atlas does not yet record what these
      molecules do, or any traditional-medicine correspondence.</p>
  </section>

</div>
```

- [ ] **Step 4: Add the profile styles**

Append to `src/atlas/site/templates/_entry.css.j2`:

```css
.entry-profiles{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));
  gap:var(--s-10);margin-bottom:var(--s-12)}
.prof{border-top:1px solid var(--ink);padding-top:var(--s-3);min-width:0}
.prof h2{margin:0 0 var(--s-4);font-family:var(--f-display);font-size:var(--t-mini);
  font-weight:700;text-transform:uppercase;letter-spacing:var(--tr-xwide);
  display:flex;gap:var(--s-2)}
.prof h2 em{font-style:normal;font-weight:400;color:var(--ink-30);font-family:var(--f-mono);
  font-size:var(--t-micro);letter-spacing:var(--tr-wide);margin-left:auto;
  align-self:center;text-transform:none}
.macro-bar{display:flex;height:30px;gap:1px}
.dry-bar{height:22px}
.seg{min-width:2px}
.seg-water,i.seg-water{background:var(--ink-15)}
.seg-dry,i.seg-dry{background:var(--ink)}
.seg-d0,i.seg-d0{background:var(--ink)}
.seg-d1,i.seg-d1{background:var(--ink-55)}
.seg-d2,i.seg-d2{background:var(--ink-30)}
.seg-d3,i.seg-d3{background:var(--ink-15)}
.macro-key{margin-top:var(--s-3)}
.key{display:flex;align-items:baseline;gap:var(--s-2);padding:3px 0;font-size:var(--t-small)}
.key i{width:9px;height:9px;flex:none;align-self:center}
.key b,.micro-row b{margin-left:auto;font-family:var(--f-mono);font-size:var(--t-small);
  font-weight:500;font-variant-numeric:tabular-nums}
.key b em,.micro-row b em{font-style:normal;color:var(--ink-30);margin-left:3px;
  font-size:var(--t-micro)}
.scale-note{margin:var(--s-5) 0 var(--s-2);font-family:var(--f-mono);font-size:var(--t-micro);
  letter-spacing:var(--tr-wide);text-transform:uppercase;color:var(--ink-55);
  border-top:1px solid var(--ink-15);padding-top:var(--s-3)}
.micros{margin-top:var(--s-4);border-top:1px solid var(--ink-15);padding-top:var(--s-2)}
.micro-row{display:flex;align-items:baseline;gap:var(--s-2);padding:4px 0;font-size:var(--t-small)}
.sens-row{padding:var(--s-2) 0;border-bottom:1px solid var(--ink-15)}
.sens-row span{font-family:var(--f-mono);font-size:var(--t-micro);letter-spacing:var(--tr-wide);
  text-transform:uppercase;color:var(--ink-55)}
.sens-row p{margin:3px 0 0;font-size:var(--t-small);line-height:1.5}
.stat{display:flex;align-items:baseline;gap:var(--s-3);padding:var(--s-2) 0;
  border-bottom:1px solid var(--ink-15)}
.stat b{font-family:var(--f-display);font-size:var(--t-h4);font-weight:700;line-height:1}
.stat span{font-size:var(--t-small);color:var(--ink-55)}
.empty-note{font-size:var(--t-small);color:var(--ink-55);margin:var(--s-3) 0 0;line-height:1.5}
@media(max-width:900px){.entry-profiles{grid-template-columns:1fr;gap:var(--s-6)}}
```

- [ ] **Step 5: Include the partial**

In `food.html.j2`, immediately after the `_masthead.html.j2` include, add:
```jinja
{% include "_profiles.html.j2" %}
```

- [ ] **Step 6: Remove the xfail marker from Task 7**

Delete the `@pytest.mark.xfail(...)` line above
`test_masthead_order_identity_then_plate_then_profiles` in `tests/test_site.py`.

- [ ] **Step 7: Run the new tests**

Run: `uv run pytest tests/test_site.py -q -k "profile or masthead"`
Expected: PASS, 4 passed

- [ ] **Step 8: Run the whole suite**

Run: `uv run pytest -q`
Expected: green. This plan has added 24 tests so far; nothing previously passing may fail.

- [ ] **Step 9: Commit**

```bash
git add src/atlas/site/templates/_profiles.html.j2 src/atlas/site/templates/_entry.css.j2 src/atlas/site/templates/food.html.j2 tests/test_site.py
git commit -m "feat(site): at-a-glance profiles with two-stage composition bar

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 9: Per-section disclosure replaces global science mode

**Files:**
- Modify: `src/atlas/site/templates/base.html.j2` (remove the `science-mode` button)
- Modify: `src/atlas/site/templates/_app.js.j2` (remove the `setScience` wiring, lines 39–40)
- Modify: `src/atlas/site/templates/food.html.j2` (each register gets its own `<details>`)
- Modify: `src/atlas/site/templates/_entry.css.j2`
- Test: `tests/test_site.py`, `tests/test_interview.py`

**Interfaces:**
- Consumes: nothing.
- Produces: no element with `id="science-mode"`. Each register is a `<details class="register">` with its own `<summary>`.

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_site.py

def test_global_science_mode_is_retired(payload, tmp_path):
    """Disclosure is per-section, never global (spec §4)."""
    from atlas.site.build import render_site
    render_site(payload, tmp_path)
    for name in ("index.html", "foods/apple.html", "compare.html"):
        page = (tmp_path / name).read_text()
        assert 'id="science-mode"' not in page, name
        assert "data-science" not in page, name


def test_each_register_discloses_independently(payload, tmp_path):
    from atlas.site.build import render_site
    render_site(payload, tmp_path)
    entry = (tmp_path / "foods/apple.html").read_text()
    assert entry.count('<details class="register"') >= 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_site.py::test_global_science_mode_is_retired -q`
Expected: FAIL — `'id="science-mode"' not in page` is False.

- [ ] **Step 3: Remove the global toggle**

In `src/atlas/site/templates/base.html.j2`, delete line 14:
```html
<button id="science-mode" type="button" aria-pressed="false">Science mode</button>
```

In `src/atlas/site/templates/_app.js.j2`, delete lines 39–40 (the `science`
lookup and the `setScience` function), plus any call site. Find them with:
```bash
grep -n "science" src/atlas/site/templates/_app.js.j2
```
Expected after the edit: no output.

- [ ] **Step 4: Convert registers to independent disclosure**

In `src/atlas/site/templates/food.html.j2`, replace every
`data-science` attribute with the register class. The scientific record block
becomes:

```jinja
<details class="register"><summary>Measurements &amp; sources
  <span>Every quantity with its unit, basis, food part and source</span></summary>
```

In `src/atlas/site/templates/_nutrition.html.j2`, replace:
```jinja
  <details data-science><summary>Minerals, vitamins &amp; energy</summary>
```
with:
```jinja
  <details class="register"><summary>Minerals, vitamins &amp; energy</summary>
```
and delete the `data-science-label` attribute on the `<h3>`.

- [ ] **Step 5: Style the register**

Append to `src/atlas/site/templates/_entry.css.j2`:

```css
.register{border-top:1px solid var(--ink);padding:var(--s-4) 0;margin:0}
.register>summary{cursor:pointer;font-family:var(--f-display);font-size:var(--t-mini);
  font-weight:700;text-transform:uppercase;letter-spacing:var(--tr-xwide);
  display:flex;gap:var(--s-3);align-items:baseline}
.register>summary span{font-family:var(--f-body);font-size:var(--t-small);font-weight:400;
  text-transform:none;letter-spacing:0;color:var(--ink-55);margin-left:auto}
.register[open]>summary{margin-bottom:var(--s-4)}
```

- [ ] **Step 6: Run the new tests**

Run: `uv run pytest tests/test_site.py -q -k "science or register"`
Expected: PASS, 2 passed

- [ ] **Step 7: Update the interview test**

In `tests/test_interview.py`, `test_profiles_integrated_and_science_mode_available`
asserts the retired toggle. Rename it and update its expectations:

```python
def test_profiles_integrated_and_disclosure_is_per_section(payload, tmp_path):
    from atlas.site.build import render_site
    render_site(payload, tmp_path)
    entry = (tmp_path / 'foods/apple.html').read_text()
    for text in ['Nutrition', 'Sensory', 'Research',
                 'Varieties &amp; relatives', 'Growing here', 'Culinary &amp; technical uses',
                 'id="season-region"', 'id="season-month"', 'id="season-mode"',
                 '<details class="register"']:
        assert text in entry
    assert 'id="science-mode"' not in entry
    assert entry.index('class="entry-masthead"') < entry.index('class="entry-profiles"')
    assert 'href="apple--honeycrisp.html"' in entry
    assert 'Missing regional data' in entry
    assert 'Linked by top-level registered taxon' in entry
    assert 'botanical family' not in entry
```

- [ ] **Step 8: Run the whole suite**

Run: `uv run pytest -q`
Expected: green. This plan has added 26 tests so far; nothing previously passing may fail.

- [ ] **Step 9: Commit**

```bash
git add src/atlas/site/templates/ tests/test_site.py tests/test_interview.py
git commit -m "feat(site): per-section disclosure replaces the global science toggle

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 10: Remove tier marks from the reading surface

**Files:**
- Modify: `src/atlas/site/templates/food.html.j2`, `src/atlas/site/templates/_chip.html.j2`
- Test: `tests/test_site.py`

**Interfaces:**
- Consumes: nothing.
- Produces: no `class="chip tier-N"` outside a `<details class="register">`. Tier data stays in the payload and still orders claims.

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_site.py

def test_tier_marks_never_appear_on_the_reading_surface(payload, tmp_path):
    """T1-T5 is internal vocabulary (spec §5, Global Constraints)."""
    import re
    from atlas.site.build import render_site
    food = payload["foods"][0]
    food["claims"].append(
        dict(subject="food:apple", group="sensory", field="taste", v="crisp",
             src="SRC-A", tier=4, derivation="editorial", flags=[], ref=None))
    render_site(payload, tmp_path)
    entry = (tmp_path / "foods/apple.html").read_text()
    surface = entry.split('<details class="register"')[0]
    assert 'class="chip tier-' not in surface
    assert not re.search(r"\bT[1-5]\b", surface)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_site.py::test_tier_marks_never_appear_on_the_reading_surface -q`
Expected: FAIL — tier chips are rendered in the editorial block above the registers.

- [ ] **Step 3: Move every tier chip inside a register**

In `src/atlas/site/templates/food.html.j2`, find each
`{% include "_chip.html.j2" %}` that sits outside a `<details class="register">`
and delete it. Locate them with:
```bash
grep -n "_chip.html.j2" src/atlas/site/templates/*.j2
```
Keep only the includes that are lexically inside a register block.

- [ ] **Step 4: Run the new test**

Run: `uv run pytest tests/test_site.py::test_tier_marks_never_appear_on_the_reading_surface -q`
Expected: PASS

- [ ] **Step 5: Update the chip-count assertion**

In `tests/test_site.py`, `test_render_site_evidence_and_navigation` asserts
`entry.count('class="chip tier-') == 5`. Chips now appear only inside registers.
Replace that line with:

```python
    assert entry.count('class="chip tier-') == entry.split('<details class="register"', 1)[1].count('class="chip tier-')
```

- [ ] **Step 6: Run the whole suite**

Run: `uv run pytest -q`
Expected: green. This plan has added 27 tests so far; nothing previously passing may fail.

- [ ] **Step 7: Commit**

```bash
git add src/atlas/site/templates/food.html.j2 tests/test_site.py
git commit -m "feat(site): tier marks live inside registers, not on the surface

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 11: Gaps summary line

**Files:**
- Modify: `src/atlas/site/templates/food.html.j2`
- Modify: `src/atlas/site/templates/_entry.css.j2`
- Test: `tests/test_site.py`

**Interfaces:**
- Consumes: `food.gaps`, `root` — already in context.
- Produces: one `<p class="gaps-summary">` linking to `gaps.html`.

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_site.py

def test_gaps_are_summarised_and_linked_not_listed(payload, tmp_path):
    """One line on the entry page, full register elsewhere (spec §5)."""
    from atlas.site.build import render_site
    food = payload["foods"][0]
    gaps = [dict(subject=food["id"], field=f"f{i}", rule=6,
                 question="Amount without unit, basis or food part.",
                 would_be_settled_by="Unit, basis and food part from the original study.",
                 carried_value=None, src="SRC-A") for i in range(3)]
    payload["gaps"] = food["gaps"] = gaps
    render_site(payload, tmp_path)
    entry = (tmp_path / "foods/apple.html").read_text()
    assert 'class="gaps-summary"' in entry
    assert "3 open questions" in entry
    assert 'href="../gaps.html"' in entry
    assert entry.count("Amount without unit, basis or food part.") <= 1


def test_no_gaps_means_no_summary_line(payload, tmp_path):
    from atlas.site.build import render_site
    render_site(payload, tmp_path)
    assert 'class="gaps-summary"' not in (tmp_path / "foods/apple.html").read_text()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_site.py::test_gaps_are_summarised_and_linked_not_listed -q`
Expected: FAIL — `'class="gaps-summary"' in entry` is False.

- [ ] **Step 3: Replace the gaps block with a summary line**

In `src/atlas/site/templates/food.html.j2`, find the `entry-gaps` block and
replace it with:

```jinja
{% if food.gaps %}
<p class="gaps-summary">
  <strong>{{ food.gaps | length }} open question{{ "s" if food.gaps | length != 1 }}</strong>
  recorded for this entry &mdash; values the atlas will not publish until a rule is satisfied.
  <a href="{{ root }}gaps.html">Read the register</a>
</p>
{% endif %}
```

- [ ] **Step 4: Style it**

Append to `src/atlas/site/templates/_entry.css.j2`:

```css
.gaps-summary{border-top:1px solid var(--ink-15);padding-top:var(--s-3);
  margin:var(--s-8) 0 0;font-size:var(--t-small);color:var(--ink-55);max-width:74ch}
.gaps-summary strong{color:var(--ink);font-weight:600}
```

- [ ] **Step 5: Run the new tests**

Run: `uv run pytest tests/test_site.py -q -k gaps`
Expected: PASS, 2 passed

- [ ] **Step 6: Run the whole suite**

Run: `uv run pytest -q`
Expected: green. This plan has added 29 tests so far; nothing previously passing may fail.

- [ ] **Step 7: Commit**

```bash
git add src/atlas/site/templates/food.html.j2 src/atlas/site/templates/_entry.css.j2 tests/test_site.py
git commit -m "feat(site): gaps summarised on the entry page, listed in the register

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 12: Self-hosted fonts

**Files:**
- Create: `data/site-assets/fonts/` (four woff2 files plus `LICENSE.txt` per family)
- Modify: `src/atlas/site/templates/_tokens.css.j2` (add `@font-face` blocks)
- Modify: `src/atlas/site/build.py` (copy fonts into the output)
- Test: `tests/test_site.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `fonts/` directory in the rendered site; no request to `fonts.googleapis.com`.

**Requires network access** to download the font files. If the environment has
no network, stop here and report; do not fall back to the CDN, because the spec
requires a static artifact with no third-party runtime dependency.

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_site.py

def test_no_runtime_dependency_on_a_third_party_cdn(payload, tmp_path):
    """Static, offline-capable artifact (spec §3)."""
    from atlas.site.build import render_site
    render_site(payload, tmp_path)
    for page in tmp_path.rglob("*.html"):
        text = page.read_text()
        assert "fonts.googleapis.com" not in text, page.name
        assert "fonts.gstatic.com" not in text, page.name


def test_fonts_are_shipped_with_the_site(payload, tmp_path):
    from atlas.site.build import render_site
    render_site(payload, tmp_path)
    shipped = {p.name for p in (tmp_path / "fonts").glob("*.woff2")}
    assert shipped, "no woff2 files copied into the site"
    assert "@font-face" in (tmp_path / "index.html").read_text()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_site.py -q -k "cdn or fonts"`
Expected: FAIL — the `fonts` directory does not exist.

- [ ] **Step 3: Download the four families**

Each family is published on Google Fonts under an open licence. Confirm the
exact licence text shipped with each download and place it beside the files —
rule 9 applies to fonts as much as to data.

```bash
mkdir -p data/site-assets/fonts
# Fetch each family's latin woff2 and its licence into data/site-assets/fonts/.
# Archivo (800), Inter Tight (400,600), JetBrains Mono (400,500), Instrument Serif (400 italic).
```

Verify before continuing:
```bash
ls data/site-assets/fonts/*.woff2 && ls data/site-assets/fonts/*LICENSE*
```
Expected: at least four woff2 files and one licence file per family.

- [ ] **Step 4: Replace the CDN import with `@font-face`**

In `_tokens.css.j2`, there is no `@import` yet (the prototypes used one, the
templates did not). Add the faces at the very top of the file, before `:root`,
using the filenames you actually downloaded:

```css
@font-face{font-family:'Archivo';src:url('fonts/archivo-800.woff2') format('woff2');
  font-weight:800;font-style:normal;font-display:swap}
@font-face{font-family:'Inter Tight';src:url('fonts/inter-tight-400.woff2') format('woff2');
  font-weight:400;font-style:normal;font-display:swap}
@font-face{font-family:'Inter Tight';src:url('fonts/inter-tight-600.woff2') format('woff2');
  font-weight:600;font-style:normal;font-display:swap}
@font-face{font-family:'JetBrains Mono';src:url('fonts/jetbrains-mono-400.woff2') format('woff2');
  font-weight:400;font-style:normal;font-display:swap}
@font-face{font-family:'Instrument Serif';src:url('fonts/instrument-serif-400-italic.woff2') format('woff2');
  font-weight:400;font-style:italic;font-display:swap}
```

Note: entry pages live at `foods/<slug>.html`, one directory down. The `src`
paths above are relative to the stylesheet, which is inlined into each page, so
they resolve differently per directory. Make them root-relative instead:
`url('/fonts/archivo-800.woff2')` only works when the site is served from the
domain root. Since the site must also open from `file://`, emit the font
directory at both levels instead — see the next step.

- [ ] **Step 5: Copy fonts into the output**

In `src/atlas/site/build.py`, `render_site` already copies images:

```python
    if (DATA_DIR / "images").is_dir():
        shutil.copytree(DATA_DIR / "images", out / "images", dirs_exist_ok=True)
```

Add, immediately after it:

```python
    fonts = DATA_DIR / "site-assets" / "fonts"
    if fonts.is_dir():
        # Emitted at both levels: the stylesheet is inlined into pages at the
        # site root and in foods/, and the site must also open from file://.
        shutil.copytree(fonts, out / "fonts", dirs_exist_ok=True)
        shutil.copytree(fonts, out / "foods" / "fonts", dirs_exist_ok=True)
```

- [ ] **Step 6: Run the new tests**

Run: `uv run pytest tests/test_site.py -q -k "cdn or fonts"`
Expected: PASS, 2 passed

- [ ] **Step 7: Run the whole suite**

Run: `uv run pytest -q`
Expected: green. This plan has added 31 tests so far; nothing previously passing may fail.

- [ ] **Step 8: Commit**

```bash
git add data/site-assets/fonts src/atlas/site/templates/_tokens.css.j2 src/atlas/site/build.py tests/test_site.py
git commit -m "feat(site): self-hosted fonts, no third-party CDN at runtime

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 13: Browser regression for the rebuilt entry page

**Files:**
- Modify: `tests/test_site.py` (`test_mobile_filters_and_live_compare`)

**Interfaces:**
- Consumes: the rendered site from all earlier tasks.
- Produces: no new interfaces.

The existing browser test asserts against selectors this rebuild removed:
`.brand` alignment against `h1`, `.card-actions button` heights and
`.card-meta` heights. `.brand` still exists in the masthead of index pages, but
the entry page `h1` is now inside `.entry-masthead`, so the alignment assertion
no longer describes anything true.

- [ ] **Step 1: Run the browser test to see it fail**

Run: `uv run pytest tests/test_site.py::test_mobile_filters_and_live_compare -q`
Expected: FAIL on the header-alignment assertion, or SKIP if Node/Playwright is
absent. If it skips, install Playwright or mark this task blocked and report —
do not delete the test.

- [ ] **Step 2: Replace the entry-page assertions**

In the embedded Playwright script, replace the header-alignment loop body for
`/foods/apple.html` with checks that describe the new composition:

```javascript
    for (const width of [320, 375, 768, 1050, 1280, 1920]) {
      await page.setViewportSize({width, height: 812});
      for (const path of ['/index.html', '/foods/apple.html']) {
        await page.goto(process.argv[1] + path);
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${path} overflow at ${width}`);
      }
      await page.goto(process.argv[1] + '/foods/apple.html');
      assert.equal(await page.locator('.entry-masthead h1').count(), 1, `masthead at ${width}`);
      assert.ok(await page.locator('.prof').evaluateAll(
        sections => sections.every(section => section.getBoundingClientRect().width > 0)),
        `collapsed profile at ${width}`);
      assert.equal(await page.locator('#science-mode').count(), 0, `science toggle at ${width}`);
    }
```

- [ ] **Step 3: Run the browser test**

Run: `uv run pytest tests/test_site.py::test_mobile_filters_and_live_compare -q`
Expected: PASS

- [ ] **Step 4: Render the real site and look at it**

Run:
```bash
uv run atlas site
```
Then open `data/build/site/foods/kale.html` and confirm by eye: identity above
the plate, plate above the profiles, the two-stage nutrition bar with its stated
scale, no `T1`-style marks on the surface, no German, square corners.

- [ ] **Step 5: Run the whole suite**

Run: `uv run pytest -q`
Expected: green. This plan has added 31 tests so far; nothing previously passing may fail.

- [ ] **Step 6: Commit**

```bash
git add tests/test_site.py
git commit -m "test(site): browser regression covers the rebuilt entry page

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Out of scope

Named here so no task drifts into them. Each needs its own spec section or plan.

- **Index, compare, molecules, gaps and sources pages.** They inherit the token layer from Task 5 and will change appearance, but their composition is undecided (spec §8).
- **The bioactivity rabbit hole** (spec §6). Needs a `bioactivity` claim group with data behind it; `research_profile()` already handles the group and returns empty today.
- **Compilations** — dishes, traditional formulas, products (spec §7.4).
- **Preparation controls** (spec §7.3). The `process` and `derives_from` relations exist; the retention data does not.
- **`composed_of`, fraction claims and the nutrient hierarchy** (spec §5).
- **Rule 8** — done. The rewrite landed in worktree
  `.claude/worktrees/jovial-visvesvaraya-664c76` (uncommitted at time of review).
  A food-level bioactivity tag is now accepted when the food carries accepted
  compound-level evidence with a reference; `check()` takes a `supported` set and
  fails closed for standalone callers. This plan does not touch `contract.py`.
  Task 8's Research-profile copy stays accurate: the payload still holds zero
  `bioactivity` claims, so nothing renders from the new branch yet.
- **Dark-mode plate treatment** (spec §9). Task 5 ships the inverted palette; the white-background photographs will read as bright blocks and that is a known open question.
