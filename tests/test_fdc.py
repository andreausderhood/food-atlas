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


@pytest.mark.parametrize("text, expected", [
    ("Aggregated data involving combinations of data with only source codes 1 and 12 and/or 13", "aggregated"),
    ("Aggregated data involving combinations of data with different source codes when at least one code is not 1, 6, 12, or 13", "aggregated"),
    ("Other procedure used from imputing", "imputed"),
    ("Taken from another source--other tables of food composition", "borrowed"),
    ("Analytical data; derived by linear regression", "calculated"),
    ("Concentration adjustment using factor; derived from analytical data", "calculated"),
    ("Analytical data; from the literature or  government;  incomplete documentation", "literature"),
    ("Nutrient that is based on other nutrient/s; calculated by difference or summed", "calculated"),
])
def test_real_derivation_descriptions(text, expected):
    assert classify_derivation(text) == expected


def test_unrecognized_analytical_description_is_not_promoted():
    with pytest.raises(UnmappedDerivation):
        classify_derivation("Unknown non-analytical procedure")


def test_missing_derivation_table_uses_documented_ids_not_dataset_name(fdc_dir, mini_nodes):
    from conftest import write_csv
    folder = next(fdc_dir.rglob("food_nutrient.csv")).parent
    (folder / "food_nutrient_derivation.csv").unlink()
    write_csv(folder / "food_nutrient.csv",
              ["id", "fdc_id", "nutrient_id", "amount", "derivation_id"], [
                  [1, 100, 1162, 4.6, 1],
                  [2, 100, 1008, 58, 4],
                  [3, 100, 1008, 58, 49],
                  [4, 100, 1162, 0, ""],
                  [5, 100, 1162, 3, 9999],
              ])
    claims, _ = load_fdc(fdc_dir, "SRC-NOT-A-DATASET-HINT", mini_nodes)
    assert [c.derivation for c in claims] == ["analytical", "calculated", "calculated", "unverified", "unverified"]
    assert claims[3].v == 0  # retain zero, without inventing assumed-zero provenance
    assert claims[4].tier == 5
    assert "9999" in claims[4].method
    assert "missing_derivation_table" in claims[4].flags
    assert "SR Legacy" in claims[0].method


@pytest.mark.parametrize("data_type", ["sample_food", "sub_sample_food", "market_acquisition", "agricultural_acquisition"])
def test_sample_foods_do_not_duplicate_published_claims(fdc_dir, mini_nodes, data_type):
    from conftest import write_csv
    folder = next(fdc_dir.rglob("food.csv")).parent
    write_csv(folder / "food.csv", ["fdc_id", "data_type", "description"], [
        [100, data_type, "Apples, honeycrisp, with skin, raw"],
        [101, "foundation_food", "Apples, dried, sulfured, uncooked"],
    ])
    claims, _ = load_fdc(fdc_dir, "SRC-FDC", mini_nodes)
    assert len(claims) == 1 and claims[0].subject == "food:apple.dried"


def test_local_derivation_table_takes_precedence_over_fallback(fdc_dir, mini_nodes):
    from conftest import write_csv
    path = next(fdc_dir.rglob("food_nutrient_derivation.csv"))
    write_csv(path, ["id", "code", "description"], [[1, "Z", "Assumed zero"], [2, "AS", "Summed"]])
    claims, _ = load_fdc(fdc_dir, "SRC-FDC", mini_nodes)
    assert claims[0].derivation == "assumed_zero"
    assert "Z" in claims[0].method


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
    matched, skipped = match_foods({"101": "Apples, dried, sulfured, uncooked"}, nodes)
    assert matched == {} and skipped == {("101", "Apples, dried, sulfured, uncooked", "food:apple.honeycrisp")}


def test_one_description_two_foods_is_an_error(mini_nodes):
    nodes = dict(mini_nodes)
    nodes["food:apple.dried"] = FoodNode(id="food:apple.dried", level="form", name="x", derives_from="food:apple",
                                         process="proc:drying", fdc_match=("Apples, honeycrisp.*",))
    with pytest.raises(FdcMappingError, match="several foods"):
        match_foods({"100": "Apples, honeycrisp, with skin, raw"}, nodes)
