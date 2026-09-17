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


def test_search_bls(project):
    from atlas.curate import search_bls
    assert search_bls(project, "APFEL") == ["F110100\tApfel roh\tApple raw"]


def test_unknown_origin_raises(bls_dir, mini_nodes):
    path = next(bls_dir.rglob("*.xlsx"))
    wb = load_workbook(path)
    wb.active["E2"] = "Bauchgefühl"
    wb.save(path)
    with pytest.raises(UnmappedDerivation, match="Bauchgefühl"):
        load_bls(bls_dir, "SRC-BLS", mini_nodes)
