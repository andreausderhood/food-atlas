import csv
import shutil
import textwrap
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
    con.close()
    return d

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


