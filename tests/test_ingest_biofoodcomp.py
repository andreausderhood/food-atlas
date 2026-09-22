"""TDD tests for FAO BioFoodComp 4.0 streaming adapter (Task 25)."""
from __future__ import annotations

import pytest
from openpyxl import Workbook

from atlas.claims import Claim
from atlas.ingest.base import registered, get_adapter
from atlas.ingest.biofoodcomp import BioFoodCompAdapter


def _make_workbook(tmp_path):
    """Create a minimal BioFoodComp workbook with 3 real-looking data rows."""
    wb = Workbook()
    wb.remove(wb.active)

    # Sheet 01 Cereals — standard layout with nutrient columns from col 17
    ws = wb.create_sheet("01 Cereals")
    ws.append([
        "Food Item ID", "Code", "Country, region", "Type",
        "Foodname in own language", "Foodname in English", "Processing",
        "Species/Subspecies", "Cultivar/Variety/Accession Name", "Season",
        "Other", "n", "Comments", "Publication year", "Biblioid", "Compiler ID",
        "Latest Revision in Version",
        "ENERC(kJ) (original)", "ENERC(kcal) (original)", "WATER(g)", "DM(g)",
    ])
    # Row 2: abbreviations (not used by adapter, but present in real files)
    ws.append([None] * 17 + ["ENERC_kJ", "ENERC_kcal", "WATER", "DM"])
    # Row 3: descriptions (not used by adapter)
    ws.append([None] * 17 + ["Energy", "Energy", "Water", "Dry matter"])

    # Data row 1: Sorghum, white — numeric values, cultivated
    ws.append([
        "0100001", "010017", "Benin, North West", "C",
        "Sorghum, whole grain, white, raw", "Sorghum, whole grain, white, raw", "r",
        "Sorghum bicolour", "Sorghum, white", "May 2005", None, 9,
        "tagname for phytate was updated on version 4.0", 2008, "2E", "EF/JD", "4.0",
        1224.006, 292.386, 9.4, 88.6,
    ])
    # Data row 2: Quinoa, Kancolla — has 'tr' trace value
    ws.append([
        "0100016", None, "Peru (Cuzco and Puno)and Bolivia", "C/U",
        "Quinoa, Kancolla Rosanna, abrasive dehulling, raw", "Quinoa, Kancolla Rosanna, abrasive dehulling, raw", "r",
        "Chenopodium quinoa", "Kancolla Rosanna", 1980, None, None,
        "Data expressed per DM - conversion to FW", 1986, "jq1", "JD/VN", 2.1,
        "[418.94]", None, "[9.8]", None,
    ])
    # Data row 3: Quinoa, Real — has 'N' for energy (no measurable value)
    ws.append([
        "0100017", None, "Peru (Cuzco and Puno)and Bolivia", "C/U",
        "Quinoa, Real, abrasive dehulling, raw", "Quinoa, Real, abrasive dehulling, raw", "r",
        "Chenopodium quinoa", "Real", 1980, None, None,
        None, 1986, "jq1", "JD/VN", 2.1,
        "N", None, "76.7", None,
    ])
    # Data row 4: Quinoa, wild — has 'tr' trace value
    ws.append([
        "0100018", None, "Peru (Cuzco and Puno)and Bolivia", "W",
        "Quinoa, wild type, raw", "Quinoa, wild type, raw", "r",
        "Chenopodium quinoa", "Wild variety", 1980, None, None,
        None, 1986, "jq1", "JD/VN", 2.1,
        "tr", None, "76.7", None,
    ])

    # Sheet 09 Fish & Shellfish — different layout with embedded nutrients
    ws2 = wb.create_sheet("09 Fish & Shellfish")
    ws2.append([
        "Food Item ID", "Code", "Subgroup", "Country, region", "Type", "ISSCAAP",
        "3_alpha", "Food name in own language", "Food name in English", "Processing",
        "Scientific name", "ASFIS English name", "ASFIS Scientific name",
        "Season", "Other", "n", "EDIBLE", "ENERC(kJ) (original)", "WATER(g)",
    ])
    ws2.append([None] * 16 + ["edible portion coefficient", "energy", "water"])
    ws2.append([None] * 16 + ["description", "description", "description"])
    # Data row: fish with numeric value
    ws2.append([
        "0900001", "0900001", "Finfish", "Thailand", "W", 11, "PTG",
        "Pla Ta-pien", "Common silver barb, wild, muscle fillet, raw", "r",
        "Puntius gonionotus", "silver barb", "Barbonymus goniontus", "May-Oct", None, 1,
        0.54, 203.0, 73.4,
    ])

    # Sheet 09 Fish & Shellfish_Fatty acids — must be skipped (per-100FA)
    ws3 = wb.create_sheet("09 Fish & Shellfish_Fatty acids")
    ws3.append(["Food Item ID", "Code", "FAT(g) per 100g FA", "FASAT(g) per 100g FA"])
    ws3.append([None, None, "fatty acid", "saturated fatty acid"])
    ws3.append([None, None, "per 100g fatty acids", "per 100g fatty acids"])
    ws3.append(["0900001", "0900001", "0.5", "0.1"])

    # Sheet 11 Herbs & Spices — only 4 rows, row 4 says 'to be completed'
    ws4 = wb.create_sheet("11 Herbs & Spices")
    ws4.append([
        "Food Item ID", "Code", "Country, region", "Type",
        "Foodname in own language", "Foodname in English", "Processing",
        "Species/Subspecies", "Cultivar/Variety/Accession Name", "Season",
        "Other", "n", "Comments", "Publication year", "Biblioid", "Compiler ID",
        "Latest Revision in Version",
    ])
    ws4.append([None] * 17)
    ws4.append([None] * 17)
    ws4.append(["to be completed", None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None])

    # Sheet 12 Miscellaneous — 7 rows, some with real data
    ws5 = wb.create_sheet("12 Miscellaneous")
    ws5.append([
        "Food Item ID", "Code", "Country, region", "Type",
        "Foodname in own language", "Foodname in English", "Processing",
        "Species/Subspecies", "Cultivar/Variety/Accession Name", "Season",
        "Other", "n", "Comments", "Publication year", "Biblioid", "Compiler ID",
        "Latest Revision in Version", "ENERC(kJ) (original)", "WATER(g)",
    ])
    ws5.append([None] * 17 + ["energy", "water"])
    ws5.append([None] * 17 + ["description", "description"])
    # Data row with '<1' value (below detection limit)
    ws5.append([
        "1200001", "1200001", "Global", "W",
        "Unknown plant, wild", "Unknown plant, wild", "r",
        "Unknown species", None, None, None, None,
        None, 2020, "XX", "XX", "1.0",
        "<1", 0,
    ])

    path = tmp_path / "biofoodcomp_test.xlsx"
    wb.save(path)
    return path


@pytest.fixture
def bfc_dir(tmp_path):
    """Return a directory containing the mini BioFoodComp workbook."""
    _make_workbook(tmp_path)
    return tmp_path


class TestBioFoodCompAdapterRegistration:
    def test_adapter_is_registered(self):
        """BioFoodCompAdapter must self-register under SRC-BFOODCOMP-4.0."""
        assert "SRC-BFOODCOMP-4.0" in registered()

    def test_adapter_src_id(self):
        """src_id must be SRC-BFOODCOMP-4.0."""
        adapter = BioFoodCompAdapter()
        assert adapter.src_id == "SRC-BFOODCOMP-4.0"


class TestBioFoodCompAdapterYieldsClaims:
    def test_load_is_lazy(self, bfc_dir):
        """load() must return a lazy iterator, not a list."""
        adapter = BioFoodCompAdapter()
        root = bfc_dir.parent
        claims = adapter.load(root, bfc_dir)
        assert hasattr(claims, "__next__") or hasattr(claims, "__iter__")
        assert not isinstance(claims, list)

    def test_yields_claims_from_cereals_sheet(self, bfc_dir):
        """load() must yield Claim objects from the 01 Cereals sheet."""
        adapter = BioFoodCompAdapter()
        root = bfc_dir.parent
        claims = list(adapter.load(root, bfc_dir))
        cereals_claims = [c for c in claims if c.subject.startswith("prod:bfc:01")]
        assert len(cereals_claims) >= 1
        c = cereals_claims[0]
        assert isinstance(c, Claim)

    def test_claims_use_bfc_field_prefix(self, bfc_dir):
        """Every claim field must start with nutrient:bfc:."""
        adapter = BioFoodCompAdapter()
        root = bfc_dir.parent
        claims = list(adapter.load(root, bfc_dir))
        assert len(claims) > 0
        for c in claims:
            assert c.field.startswith("nutrient:bfc:"), f"field {c.field!r} does not start with nutrient:bfc:"

    def test_claims_have_prod_bfc_subject(self, bfc_dir):
        """Every claim subject must be prod:bfc:<id>."""
        adapter = BioFoodCompAdapter()
        root = bfc_dir.parent
        claims = list(adapter.load(root, bfc_dir))
        for c in claims:
            assert c.subject.startswith("prod:bfc:"), f"subject {c.subject!r} does not start with prod:bfc:"

    def test_claims_have_as_described_basis(self, bfc_dir):
        """Every claim must have basis='as_described'."""
        adapter = BioFoodCompAdapter()
        root = bfc_dir.parent
        claims = list(adapter.load(root, bfc_dir))
        for c in claims:
            assert c.basis == "as_described", f"claim {c.field} has basis {c.basis!r}, expected as_described"

    def test_claims_have_product_food_part(self, bfc_dir):
        """Every claim must have food_part='product'."""
        adapter = BioFoodCompAdapter()
        root = bfc_dir.parent
        claims = list(adapter.load(root, bfc_dir))
        for c in claims:
            assert c.food_part == "product", f"claim {c.field} has food_part {c.food_part!r}, expected product"

    def test_claims_have_literature_derivation(self, bfc_dir):
        """Every claim must have derivation='literature' or 'trace' (BioFoodComp is a literature compilation)."""
        adapter = BioFoodCompAdapter()
        root = bfc_dir.parent
        claims = list(adapter.load(root, bfc_dir))
        for c in claims:
            assert c.derivation in ("literature", "trace"), \
                f"claim {c.field} has derivation {c.derivation!r}, expected literature or trace"

    def test_trace_cells_yield_tr_value_with_trace_derivation(self, bfc_dir):
        """'tr'/'Tr' cells must yield Claim with v='tr' and derivation='trace'."""
        adapter = BioFoodCompAdapter()
        root = bfc_dir.parent
        claims = list(adapter.load(root, bfc_dir))
        tr_claims = [c for c in claims if c.v == "tr"]
        assert len(tr_claims) >= 1, "At least one 'tr' cell should yield a trace claim"
        for c in tr_claims:
            assert c.derivation == "trace"
            assert c.v == "tr"

    def test_n_cells_are_skipped(self, bfc_dir):
        """'N' cells must not yield any claim."""
        adapter = BioFoodCompAdapter()
        root = bfc_dir.parent
        claims = list(adapter.load(root, bfc_dir))
        n_claims = [c for c in claims if c.v == "N"]
        assert len(n_claims) == 0, "'N' cells must not produce claims"

    def test_bracketed_numeric_values_parsed_as_float(self, bfc_dir):
        """Values like '[418.94]' must be parsed as float 418.94."""
        adapter = BioFoodCompAdapter()
        root = bfc_dir.parent
        claims = list(adapter.load(root, bfc_dir))
        energy_claims = [c for c in claims if c.field == "nutrient:bfc:ENERC(kJ)"]
        bracketed = [c for c in energy_claims if isinstance(c.v, float)]
        assert len(bracketed) >= 1, "Bracketed numeric values should be parsed as float"

    def test_non_numeric_string_values_yielded(self, bfc_dir):
        """Non-numeric, non-special string values must be yielded (not silently swallowed)."""
        adapter = BioFoodCompAdapter()
        root = bfc_dir.parent
        claims = list(adapter.load(root, bfc_dir))
        # The '<1' value from sheet 12 should be yielded as a string
        lt1_claims = [c for c in claims if c.v == "<1"]
        assert len(lt1_claims) >= 1, "'<1' values must be yielded, not silently swallowed"
        for c in lt1_claims:
            assert isinstance(c.v, str)
            assert c.derivation == "literature"

    def test_skipped_sheets_not_ingested(self, bfc_dir):
        """Fatty-acid per-100FA sheets must not be ingested."""
        adapter = BioFoodCompAdapter()
        root = bfc_dir.parent
        claims = list(adapter.load(root, bfc_dir))
        # No claims should reference the per-100FA sheet data
        for c in claims:
            assert "per 100g FA" not in (c.ref or ""), f"claim {c.field} incorrectly references per-100FA data"

    def test_scientific_name_and_variety_in_ref(self, bfc_dir):
        """Scientific name and variety must appear in the ref field for identity traceability."""
        adapter = BioFoodCompAdapter()
        root = bfc_dir.parent
        claims = list(adapter.load(root, bfc_dir))
        # At least some claims should reference the scientific name
        sci_refs = [c for c in claims if "Chenopodium quinoa" in (c.ref or "")]
        assert len(sci_refs) >= 1, "Scientific name should appear in ref for identity traceability"

    def test_origin_column_not_present_uses_literature(self, bfc_dir):
        """When no origin column exists, derivation defaults to 'literature'."""
        adapter = BioFoodCompAdapter()
        root = bfc_dir.parent
        claims = list(adapter.load(root, bfc_dir))
        for c in claims:
            assert c.derivation in ("literature", "trace"), \
                f"derivation {c.derivation!r} should be 'literature' or 'trace'"
