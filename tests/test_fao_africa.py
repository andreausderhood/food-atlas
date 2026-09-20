"""Offline FAO-Africa-1968 ingest tests; fixtures are hand-built page rows."""
from __future__ import annotations

from pathlib import Path

import pytest

from atlas.ingest.fao_africa import ingest


def _row(*cells: str) -> str:
    cells = cells + ("",) * (21 - len(cells))
    return "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"


PAGE = ("<table>"
        + _row("Item No.", "Food and Description", "French Name",
               "Composition in Terms of 100 Grams Edible Portion")
        + _row("", "Food Energy", "Moisture", "Protein", "Fat", "Carbohydrate, total",
               "Fiber", "Ash", "Calcium", "Phosphorus", "Iron", "Retinol",
               "B-carotene Equivalent", "Thiamine", "Riboflavin", "Niacin",
               "Tryptophan", "Ascorbic acid", "Refuse in as purchased")
        + _row("", "1.CEREALS AND GRAIN PRODUCTS:", "Calories", "Percent", "Grams",
               "Grams", "Grams", "Grams", "Grams", "Milligrams", "Milligrams",
               "Milligrams", "Micrograms", "Micrograms", "Milligrams", "Milligrams",
               "Milligrams", "Milligrams", "Milligrams", "Percent")
        + _row("", "Fonio (Digitaria spp.):", "Fonio")
        + _row("1.", "Black (D. iburua):", "Fonio noir")
        + _row("", "Whole-grain", "", "343", "10.3", "8.9")
        + _row("", "(2)", "", "(2)")
        + _row("2.", "Meal:", "Farine", "360", "10.7", "10.5")
        + _row("", "14.MISCELLANEOUS:")
        + _row("1594.", "Chocolate:", "Chocolat", "351", "1.0", "4.4")
        + "</table>")

INDEX = ("<table>"
         + _row("SCIENTIFIC NAME", "NAME USED FOR", "ITEM", "NAME USED FOR")
         + _row("Digitaria iburua", "Black fonio", "1.", "Fonio noir")
         + _row("", "Grain, dried", "1.", "Grain seche")
         + _row("Theobroma cacao", "Cocoa", "1594", "Chocolat")
         + "</table>")


@pytest.fixture
def bundle(tmp_path: Path) -> Path:
    for name in ("X6877E05.htm", "X6877E19.htm"):
        (tmp_path / name).write_text(PAGE, encoding="utf-8")
    for name in ("X6877E23.htm", "X6877E24.htm"):
        (tmp_path / name).write_text(INDEX, encoding="utf-8")
    return tmp_path


def test_items_groups_variants_and_values(bundle: Path):
    result = ingest(bundle)
    foods = result["foods"]
    # the banner repeats on both pages but is a group marker, not a food
    assert [k for k in foods] == ["1", "2", "1594"]
    assert foods["1"]["group"] == "CEREALS AND GRAIN PRODUCTS"
    assert foods["1"]["variants"][0]["values"]["energy_cal"] == 343.0
    # annotation rows ('(2)') never become values
    assert foods["2"]["variants"][0]["values"]["protein_g"] == 10.5
    assert foods["1594"]["group"] == "MISCELLANEOUS"


def test_species_index_attaches_by_item_no(bundle: Path):
    result = ingest(bundle)
    foods = result["foods"]
    # two index entries for item 1, one species each → deduplicated list
    assert foods["1"]["species"] == ["Digitaria iburua"]
    assert foods["1594"]["species"] == ["Theobroma cacao"]
    assert result["stats"]["species_total"] == 2
