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


def test_missing_derivation_id_is_explicitly_unmapped(fdc_dir, mini_nodes):
    from conftest import write_csv
    path = next(fdc_dir.rglob("food_nutrient_derivation.csv"))
    write_csv(path, ["id", "code", "description"], [[2, "AS", "Summed"]])
    with pytest.raises(UnmappedDerivation, match="1"):
        load_fdc(fdc_dir, "SRC-FDC", mini_nodes)


def test_search_fdc(project):
    from atlas.curate import search_fdc
    rows = search_fdc(project, "HONEYCRISP")
    assert len(rows) == 2
    assert all("100\tApples, honeycrisp, with skin, raw" in r for r in rows)


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
