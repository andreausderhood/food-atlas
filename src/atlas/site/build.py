"""Render the static pilot site from accepted claims in the build payload."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

from jinja2 import Environment, PackageLoader

from atlas.site.composition import macro_split, micro_readings
from atlas.site.images import DATA_DIR, image_for
from atlas.site.profiles import research_profile, season_records

TIER_LABEL = {1: "Measured", 2: "Registry", 3: "Literature", 4: "Derived or declared", 5: "Unverified"}
GROUP_ORDER = ("narrative", "sensory", "nutrition", "molecules", "origin", "growing", "season", "identity")
LEVEL_ORDER = ("taxon_food", "cultivar", "part", "form")


def _label(field: str, payload: dict) -> str:
    if field.startswith("contains:"):
        key = field.removeprefix("contains:")
        return payload["molecules"].get(key, {}).get("name", key)
    return payload["nutrients"].get(field, {}).get("name", field)


def labelled_claims(food: dict, payload: dict) -> list[dict]:
    """Attach the display label the composition model matches on."""
    return [c | {"label": _label(c["field"], payload)} for c in food["claims"]]


def _amount(claim: dict) -> str:
    """Nutrition imports are per 100 g; molecule units retain their source denominator."""
    if claim.get("v") == "present":
        return "present"
    value = claim["v"]
    if (claim.get("group") == "season" and isinstance(value, list) and value
            and all(isinstance(m, int) for m in value)):
        # Season month lists read as names, not raw ISO numbers, wherever a claim's
        # amount is displayed (not just the masthead's own "In season" tag).
        value = ", ".join(month_name(m) for m in value)
    unit = f" {claim['unit']}" if claim.get("unit") else ""
    text = f"{value}{unit}"
    if claim.get("group") == "nutrition":
        text += " per 100 g"
    if claim.get("v_min") is not None:
        text += f" ({claim['v_min']}–{claim['v_max']}, n={claim['n']})"
    return text


def _context(claim: dict) -> str:
    """Basis and food part are part of the claim; dropping them misstates the value."""
    bits = [claim.get("basis"), claim.get("food_part")]
    return " · ".join(b for b in bits if b)


def compare_rows(food_ids: list[str], payload: dict) -> list[dict]:
    foods = {f["id"]: f for f in payload["foods"]}
    labels = {c["field"]: _label(c["field"], payload) for fid in food_ids
              for c in foods[fid]["claims"] if c["group"] == "nutrition"}
    rows = []
    for field, label in sorted(labels.items(), key=lambda kv: kv[1]):
        values = []
        for fid in food_ids:
            hits = [c for c in foods[fid]["claims"] if c["field"] == field and c["group"] == "nutrition"]
            values.append(
                "; ".join(f"{_amount(c)} ({_context(c)}) [{c['src']}]" for c in hits) if hits else "not stated")
        rows.append({"field": field, "label": label, "values": values})
    return rows


def compare_data(payload: dict) -> dict:
    """Client-side compare keeps every source claim: value, context and evidence metadata."""
    rows = {}
    for food in payload["foods"]:
        fields = rows[food["id"]] = {}
        for c in food["claims"]:
            if c["group"] == "nutrition":
                fields.setdefault(c["field"], []).append(c | {
                    "label": _label(c["field"], payload), "display": _amount(c),
                    "context": _context(c),
                })
    return {
        "foods": [{"id": f["id"], "name": f["name"]} for f in payload["foods"]],
        "rows": rows,
        "labels": {k: v["name"] for k, v in payload["nutrients"].items()},
    }


def family_of(taxon: str, organisms: dict) -> str:
    """Food families are top-level registered taxa, not invented botanical ranks."""
    seen = set()
    while taxon in organisms and organisms[taxon].get("parent") and taxon not in seen:
        seen.add(taxon)
        taxon = organisms[taxon]["parent"]
    return taxon


def index_rows(payload: dict) -> list[dict]:
    organisms = {o["id"]: o for o in payload["organisms"]}
    rows = []
    for food in payload["foods"]:
        family = family_of(food["taxon"], organisms)
        taxon_name = organisms.get(food["taxon"], {}).get("name", food["taxon"])
        editorial = [c for c in food["claims"] if c["group"] in ("sensory", "narrative")]
        preview = next((c for c in editorial if c["field"] == "taste"), None)
        if preview is None:
            preview = next(iter(editorial), None)
        rows.append({
            "id": food["id"], "slug": slug(food["id"]), "name": food["name"], "level": food["level"],
            "taxon_name": taxon_name, "family": family,
            "family_name": organisms.get(family, {}).get("name", family),
            "claims": len(food["claims"]), "gaps": len(food["gaps"]),
            "nutrition": sum(c["group"] == "nutrition" for c in food["claims"]),
            "molecules": len({c["field"] for c in food["claims"] if c["group"] == "molecules"}),
            "tiers": sorted({c["tier"] for c in food["claims"]}),
            "preview": preview,
            "seasons": season_records(food["claims"]),
            "research": [g["label"] for g in research_profile(food["claims"])],
            "search": " ".join([food["name"], taxon_name,
                organisms.get(family, {}).get("name", family),
                *[f"{_label(c['field'], payload)} {c['v']}" for c in food["claims"]]]).lower(),
        })
    return sorted(rows, key=lambda r: (r["family_name"], r["taxon_name"], LEVEL_ORDER.index(r["level"]), r["name"]))


def molecule_rows(payload: dict) -> list[dict]:
    """Invert accepted food claims only; registry presence is not evidence of occurrence."""
    molecules = {}
    for food in payload["foods"]:
        for group, claims in sections(food, payload):
            if group != "molecules":
                continue
            for claim in claims:
                key = claim["field"].removeprefix("contains:")
                row = molecules.setdefault(key, {"id": key, "name": claim["label"], "claims": [], "foods": set()})
                row["claims"].append(claim | {"food_name": food["name"], "food_slug": slug(food["id"])})
                row["foods"].add(food["id"])
    return sorted([r | {"food_count": len(r["foods"]), "foods": sorted(r["foods"])}
                   for r in molecules.values()], key=lambda r: r["name"].casefold())


def sections(food: dict, payload: dict) -> list[tuple[str, list[dict]]]:
    groups = {}
    for c in food["claims"]:
        groups.setdefault(c["group"], []).append(c | {
            "label": _label(c["field"], payload), "display": _amount(c),
            "machine_extracted": c["group"] == "molecules" and (
                c["tier"] == 3 or c["derivation"] in ("literature", "extracted")
                or "llm_extracted" in c.get("flags", [])),
            "pmcs": sorted(set(re.findall(r"\bPMC[0-9]+\b", c.get("ref") or ""))),
        })
    order = list(GROUP_ORDER) + sorted(set(groups) - set(GROUP_ORDER))
    return [(group, sorted(groups[group], key=lambda c: (c["label"], c["src"])))
            for group in order if group in groups]


MONTH_NAMES = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def month_name(number: int) -> str:
    """Month number to short English name; unknown numbers pass through."""
    return MONTH_NAMES[number - 1] if 1 <= number <= 12 else str(number)


def render_site(payload: dict, out: Path) -> list[Path]:
    # All templates are HTML despite the .j2 suffix.
    env = Environment(loader=PackageLoader("atlas.site", "templates"), autoescape=True)
    env.filters["month_name"] = month_name
    # Compact tojson output (no space after separators) is functionally identical for
    # JSON.parse consumers (e.g. _season.js.j2's data-entry-seasons) and avoids "10, 11, 12"
    # style number runs leaking into raw HTML text via embedded JSON.
    env.policies["json.dumps_kwargs"] = {"separators": (",", ":")}
    rows = index_rows(payload)
    food_map = {f["id"]: f for f in payload["foods"]}
    row_map = {r["id"]: r for r in rows}
    families = {r["family"]: r["family_name"] for r in rows}
    env.globals.update(image_for=image_for, tier_label=TIER_LABEL, slug=slug, food_map=food_map,
                       atlas_rows=rows, families=families,
                       level_label={"taxon_food": "Food", "cultivar": "Cultivar", "part": "Part", "form": "Form"})
    sources = {s["id"]: s for s in payload["sources"]}
    organisms = {o["id"]: o for o in payload["organisms"]}
    out = Path(out)
    (out / "foods").mkdir(parents=True, exist_ok=True)
    if (DATA_DIR / "images").is_dir():
        shutil.copytree(DATA_DIR / "images", out / "images", dirs_exist_ok=True)
    fonts = DATA_DIR / "site-assets" / "fonts"
    if fonts.is_dir():
        # Emitted at both levels: the stylesheet is inlined into pages at the
        # site root and in foods/, and the site must also open from file://.
        shutil.copytree(fonts, out / "fonts", dirs_exist_ok=True)
        shutil.copytree(fonts, out / "foods" / "fonts", dirs_exist_ok=True)
    written = []

    def write(rel: str, template: str, root: str, **ctx) -> None:
        path = out / rel
        html = env.get_template(template).render(
            payload=payload, sources=sources, organisms=organisms, root=root, **ctx)
        path.write_text(html, encoding="utf-8")
        written.append(path)

    write("index.html", "index.html.j2", "", rows=rows)
    write("molecules.html", "molecules.html.j2", "", molecules=molecule_rows(payload))
    for food in payload["foods"]:
        related = [r for r in rows if r["family"] == row_map[food["id"]]["family"] and r["id"] != food["id"]]
        labelled = labelled_claims(food, payload)
        write(f"foods/{slug(food['id'])}.html", "food.html.j2", "../",
              food=food, row=row_map[food["id"]], related=related, sections=sections(food, payload),
              composition={"macro": macro_split(labelled), "micro": micro_readings(labelled)},
              research=research_profile(food["claims"]),
              organism_claims=organisms[food["taxon"]].get("claims", []))
    ids = [f["id"] for f in payload["foods"] if f["level"] == "taxon_food"][:3]
    data = compare_data(payload)
    write("compare.html", "compare.html.j2", "", default=compare_rows(ids, payload),
          default_ids=ids, data=data)
    by_rule = {}
    for gap in payload["gaps"]:
        by_rule.setdefault(gap["rule"], []).append(gap)
    write("gaps.html", "gaps.html.j2", "", by_rule=dict(sorted(by_rule.items())))
    write("sources.html", "sources.html.j2", "")
    return written


def slug(food_id: str) -> str:
    return food_id.removeprefix("food:").replace(".", "--")
