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


@pytest.mark.parametrize("self_cycle", [False, True])
def test_food_cycles_rejected_during_load(tmp_path, self_cycle):
    parent = "food:apple.dried" if self_cycle else "food:apple.twice-dried"
    foods = FOODS.replace("derives_from: food:apple, process:", f"derives_from: {parent}, process:")
    if not self_cycle:
        foods += "food:apple.twice-dried: {level: form, name: Twice-dried apple, derives_from: food:apple.dried, process: proc:drying}\n"
    with pytest.raises(FoodModelError, match="cycle"):
        reg(tmp_path, foods)


def test_organism_cycles_rejected_during_load(tmp_path):
    path = tmp_path / "organisms.yaml"
    path.write_text("org:a: {name: A, rank: var, parent: org:b}\norg:b: {name: B, rank: var, parent: org:a}\n")
    with pytest.raises(FoodModelError, match="cycle"):
        load_organisms(path)


def test_duplicate_bls_codes_are_rejected(tmp_path):
    bad = FOODS + "food:x: {level: taxon_food, name: X, derives_from: org:malus-domestica, bls_codes: [IV A 1]}\n"
    worse = bad + "food:y: {level: taxon_food, name: Y, derives_from: org:brassica-oleracea, bls_codes: [IV A 1]}\n"
    with pytest.raises(FoodModelError, match="bls code 'IV A 1'"):
        reg(tmp_path, worse)


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
