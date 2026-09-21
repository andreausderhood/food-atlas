"""Task 17: FDC Foundation & SR Legacy streaming bulk adapter tests (TDD red phase)."""
from __future__ import annotations

import csv
from collections.abc import Iterator
from pathlib import Path

import pytest

from atlas.claims import Claim
from atlas.ingest.base import get_adapter, registered, unregister
from atlas.registry import load_sources


FOUNDATION_SOURCES_YAML = """\
SRC-FDC-FOUNDATION-2026-04:
  title: "USDA FoodData Central — Foundation Foods (April 2026)"
  publisher: "U.S. Department of Agriculture, Agricultural Research Service"
  url: "https://fdc.nal.usda.gov/download-datasets"
  identifier: "FoodData_Central_foundation_food_csv_2026-04-30.zip"
  license: "CC0-1.0"
  license_class: ship
  license_read: true
  kind: measurement
  independence: independent
  supports: [identity, nutrition]
  attribution: "U.S. Department of Agriculture."
SRC-FDC-SRLEGACY-2018-04:
  title: "USDA FoodData Central — SR Legacy (April 2018, final release)"
  publisher: "U.S. Department of Agriculture, Agricultural Research Service"
  url: "https://fdc.nal.usda.gov/download-datasets"
  identifier: "FoodData_Central_sr_legacy_food_csv_2018-04.zip"
  license: "CC0-1.0"
  license_class: ship
  license_read: true
  kind: compilation
  independence: independent
  supports: [identity, nutrition]
  attribution: "U.S. Department of Agriculture."
"""


def _write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def _make_foundation_dir(root: Path) -> Path:
    d = root / "fdc" / "FoodData_Central_foundation_food_csv_2026-04-30"
    d.mkdir(parents=True)
    _write_csv(d / "food.csv",
               ["fdc_id", "data_type", "description", "food_category_id", "publication_date"],
               [["100", "foundation_food", "Apples, honeycrisp, raw", "9", "2020-10-30"],
                ["101", "foundation_food", "Bananas, raw", "9", "2020-10-30"],
                ["102", "sample_food", "Apples, processed", "9", "2020-10-30"],
                ["103", "market_acquisition", "Apples, store", "9", "2020-10-30"]])
    _write_csv(d / "food_nutrient.csv",
               ["id", "fdc_id", "nutrient_id", "amount", "data_points", "derivation_id",
                "min", "max", "median", "footnote", "min_year_acquired"],
               [["1", "100", "1162", "4.6", "8", "1", "2.1", "6.0", "4.4", "", "2019"],
                ["2", "100", "1008", "58", "", "2", "", "", "", "", ""],
                ["3", "100", "1162", "", "", "1", "", "", "", "", ""],
                ["4", "101", "1162", "3.9", "2", "", "", "", "", "", ""],
                ["5", "102", "1162", "8.7", "4", "1", "", "", "", "", ""],
                ["6", "103", "1162", "2.1", "1", "1", "", "", "", "", ""]])
    _write_csv(d / "nutrient.csv",
               ["id", "name", "unit_name", "nutrient_nbr", "rank"],
               [["1162", "Vitamin C, total ascorbic acid", "MG", "401", "6300"],
                ["1008", "Energy", "KCAL", "208", "300"]])
    return root / "fdc"


def _make_sr_legacy_dir(root: Path) -> Path:
    d = root / "fdc" / "FoodData_Central_sr_legacy_food_csv_2018-04"
    d.mkdir(parents=True)
    _write_csv(d / "food.csv",
               ["fdc_id", "data_type", "description", "food_category_id", "publication_date"],
               [["200", "sr_legacy_food", "Pillsbury biscuits", "18", "2019-04-01"],
                ["201", "sr_legacy_food", "Milk, whole", "1", "2019-04-01"]])
    _write_csv(d / "food_nutrient.csv",
               ["id", "fdc_id", "nutrient_id", "amount", "data_points", "derivation_id",
                "min", "max", "median", "footnote", "min_year_acquired"],
               [["1", "200", "1162", "5.2", "3", "1", "", "", "", "", ""],
                ["2", "200", "1008", "", "", "", "", "", "", "", ""],
                ["3", "201", "1162", "1.2", "2", "1", "", "", "", "", ""]])
    _write_csv(d / "nutrient.csv",
               ["id", "name", "unit_name", "nutrient_nbr", "rank"],
               [["1162", "Vitamin C, total ascorbic acid", "MG", "401", "6300"],
                ["1008", "Energy", "KCAL", "208", "300"]])
    return root / "fdc"


@pytest.fixture
def clean_registry():
    before = set(registered())
    yield
    for sid in set(registered()) - before:
        unregister(sid)


@pytest.fixture
def foundation_root(tmp_path):
    return _make_foundation_dir(tmp_path)


@pytest.fixture
def sr_legacy_root(tmp_path):
    return _make_sr_legacy_dir(tmp_path)


class TestBulkFdcAdapterRegistration:
    def test_foundation_adapter_is_registered(self):
        assert "SRC-FDC-FOUNDATION-2026-04" in registered()

    def test_sr_legacy_adapter_is_registered(self):
        assert "SRC-FDC-SRLEGACY-2018-04" in registered()

    def test_foundation_adapter_prefix(self):
        adapter = get_adapter("SRC-FDC-FOUNDATION-2026-04")
        assert adapter.prefix == "prod:fdcf"
        assert adapter.food_type == "foundation_food"

    def test_sr_legacy_adapter_prefix(self):
        adapter = get_adapter("SRC-FDC-SRLEGACY-2018-04")
        assert adapter.prefix == "prod:fdcs"
        assert adapter.food_type is None


class TestBulkFdcAdapterFoundationClaims:
    def test_produces_prod_fdcf_subjects(self, foundation_root):
        adapter = get_adapter("SRC-FDC-FOUNDATION-2026-04")
        claims = list(adapter.load(foundation_root.parent.parent, foundation_root.parent))
        subjects = {c.subject for c in claims}
        assert all(s.startswith("prod:fdcf:") for s in subjects)

    def test_foundation_claims_have_as_described_basis(self, foundation_root):
        adapter = get_adapter("SRC-FDC-FOUNDATION-2026-04")
        claims = list(adapter.load(foundation_root.parent.parent, foundation_root.parent))
        assert all(c.basis == "as_described" for c in claims)

    def test_foundation_claims_have_product_food_part(self, foundation_root):
        adapter = get_adapter("SRC-FDC-FOUNDATION-2026-04")
        claims = list(adapter.load(foundation_root.parent.parent, foundation_root.parent))
        assert all(c.food_part == "product" for c in claims)

    def test_foundation_claims_have_nutrition_group(self, foundation_root):
        adapter = get_adapter("SRC-FDC-FOUNDATION-2026-04")
        claims = list(adapter.load(foundation_root.parent.parent, foundation_root.parent))
        assert all(c.group == "nutrition" for c in claims)

    def test_foundation_excludes_non_foundation_food_types(self, foundation_root):
        adapter = get_adapter("SRC-FDC-FOUNDATION-2026-04")
        claims = list(adapter.load(foundation_root.parent.parent, foundation_root.parent))
        subjects = {c.subject for c in claims}
        assert "prod:fdcf:102" not in subjects
        assert "prod:fdcf:103" not in subjects
        assert "prod:fdcf:100" in subjects
        assert "prod:fdcf:101" in subjects

    def test_foundation_claims_have_correct_field_format(self, foundation_root):
        adapter = get_adapter("SRC-FDC-FOUNDATION-2026-04")
        claims = list(adapter.load(foundation_root.parent.parent, foundation_root.parent))
        fields = {c.field for c in claims}
        assert all(f.startswith("nutrient:fdc:") for f in fields)

    def test_foundation_claims_have_analytical_derivation(self, foundation_root):
        adapter = get_adapter("SRC-FDC-FOUNDATION-2026-04")
        claims = list(adapter.load(foundation_root.parent.parent, foundation_root.parent))
        assert all(c.derivation == "analytical" for c in claims)


class TestBulkFdcAdapterSrLegacyClaims:
    def test_produces_prod_fdcs_subjects(self, sr_legacy_root):
        adapter = get_adapter("SRC-FDC-SRLEGACY-2018-04")
        claims = list(adapter.load(sr_legacy_root.parent.parent, sr_legacy_root.parent))
        subjects = {c.subject for c in claims}
        assert all(s.startswith("prod:fdcs:") for s in subjects)

    def test_sr_legacy_claims_have_as_described_basis(self, sr_legacy_root):
        adapter = get_adapter("SRC-FDC-SRLEGACY-2018-04")
        claims = list(adapter.load(sr_legacy_root.parent.parent, sr_legacy_root.parent))
        assert all(c.basis == "as_described" for c in claims)

    def test_sr_legacy_claims_have_product_food_part(self, sr_legacy_root):
        adapter = get_adapter("SRC-FDC-SRLEGACY-2018-04")
        claims = list(adapter.load(sr_legacy_root.parent.parent, sr_legacy_root.parent))
        assert all(c.food_part == "product" for c in claims)

    def test_sr_legacy_excludes_empty_amounts(self, sr_legacy_root):
        adapter = get_adapter("SRC-FDC-SRLEGACY-2018-04")
        claims = list(adapter.load(sr_legacy_root.parent.parent, sr_legacy_root.parent))
        fields = {c.field for c in claims if c.subject == "prod:fdcs:200"}
        assert "nutrient:fdc:1008" not in fields


class TestBulkFdcAdapterStreaming:
    def test_load_is_lazy(self, foundation_root):
        adapter = get_adapter("SRC-FDC-FOUNDATION-2026-04")
        result = adapter.load(foundation_root.parent.parent, foundation_root.parent)
        assert isinstance(result, Iterator)

    def test_does_not_load_all_into_memory(self, foundation_root):
        adapter = get_adapter("SRC-FDC-FOUNDATION-2026-04")
        result = adapter.load(foundation_root.parent.parent, foundation_root.parent)
        assert not isinstance(result, list)


class TestBulkFdcAdapterEndToEnd:
    def test_foundation_ingest_produces_correct_counts(self, foundation_root):
        from atlas.unified.store import Store
        from atlas.unified.collectors import STORE_PATH

        adapter = get_adapter("SRC-FDC-FOUNDATION-2026-04")

        reg = foundation_root.parent.parent / "data" / "registry"
        reg.mkdir(parents=True, exist_ok=True)
        (reg / "sources.yaml").write_text(FOUNDATION_SOURCES_YAML, encoding="utf-8")
        sources = load_sources(reg / "sources.yaml", reg / "link_status.yaml")

        store = Store(foundation_root.parent.parent / STORE_PATH)
        try:
            batch = "20260101T000000Z"
            stats = store.replace_source(adapter.src_id, adapter.load(foundation_root.parent.parent, foundation_root.parent), sources, batch)
            assert stats.accepted == 3
            assert stats.rejected == 0
        finally:
            store.close()

    def test_sr_legacy_ingest_produces_correct_counts(self, sr_legacy_root):
        from atlas.unified.store import Store
        from atlas.unified.collectors import STORE_PATH

        adapter = get_adapter("SRC-FDC-SRLEGACY-2018-04")

        reg = sr_legacy_root.parent.parent / "data" / "registry"
        reg.mkdir(parents=True, exist_ok=True)
        (reg / "sources.yaml").write_text(FOUNDATION_SOURCES_YAML, encoding="utf-8")
        sources = load_sources(reg / "sources.yaml", reg / "link_status.yaml")

        store = Store(sr_legacy_root.parent.parent / STORE_PATH)
        try:
            batch = "20260101T000000Z"
            stats = store.replace_source(adapter.src_id, adapter.load(sr_legacy_root.parent.parent, sr_legacy_root.parent), sources, batch)
            assert stats.accepted == 2
            assert stats.rejected == 0
        finally:
            store.close()
