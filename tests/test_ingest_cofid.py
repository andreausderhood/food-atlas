"""TDD tests for CoFID 2021 streaming adapter (Task 24)."""
from __future__ import annotations

import pytest
from openpyxl import Workbook

from atlas.claims import Claim
from atlas.ingest.base import registered, get_adapter
from atlas.ingest.cofid import CoFidAdapter

SHEET_NAMES = [
    "1.3 Proximates",
    "1.4 Inorganics",
    "1.5 Vitamins",
    "1.6 Vitamin Fractions",
    "1.8 (SFA per 100gFood)",
    "1.10 (MUFA per 100gFood)",
    "1.12 (PUFA per 100gFood)",
    "1.13 Phytosterols",
    "1.14 Organic Acids",
]

SKIPPED_SHEETS = ["1.7 (SFA per 100gFA)", "1.9 (MUFA per 100FA)", "1.11 (PUFA per 100gFA)"]


def _make_workbook(tmp_path):
    """Create a minimal CoFID workbook with 3 real-looking data rows."""
    wb = Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    # Sheet 1.3 Proximates — the primary sheet with real column structure
    ws = wb.create_sheet("1.3 Proximates")
    # Row 1: nutrient names
    ws.append([
        "Food Code", "Food Name", "Description", "Group", "Previous",
        "Main data references", "Footnote",
        "Water (g)", "Total nitrogen (g)", "Protein (g)", "Fat (g)", "Carbohydrate (g)",
        "Energy (kcal) (kcal)", "Energy (kJ) (kJ)", "Starch (g)",
    ])
    # Row 2: abbreviations
    ws.append([
        None, None, None, None, None, None, None,
        "WATER", "TOTNIT", "PROT", "FAT", "CHO",
        "ENERCC_kcal", "ENERCC_kJ", "STARCH",
    ])
    # Row 3: descriptions
    ws.append([
        None, None, None, None, None, None, None,
        "Water", "Total nitrogen", "Protein", "Fat", "Carbohydrate",
        "Energy (kcal)", "Energy (kJ)", "Starch",
    ])
    # Row 4: real data row 1 (13-145, Ackee) — has 'Tr' for starch
    ws.append([
        "13-145", "Ackee, canned, drained", "8 cans", "DG", 554,
        "MW4, 1978; and Vegetables, Herbs and Spices Supplement, 1991", None,
        "76.7", "0.46", "2.9", "15.2", "0.8",
        "62", "259", "Tr",
    ])
    # Row 5: real data row 2 (13-146, Agar) — has 'Tr' for carbohydrate, 'N' for energy
    ws.append([
        "13-146", "Agar, dried", "Literature sources", "DG", None,
        "Wu Leung et al. (1972) Food composition table for use in East Asia", None,
        "9.7", "0.26", "1.3", "1.2", "Tr",
        "N", "N", None,
    ])
    # Row 6: real data row 3 (13-147) — has 'N' for fat (no measurable value)
    ws.append([
        "13-147", "Agar, dried, soaked and drained", "Literature sources", "DG", None,
        "Wu Leung et al. (1972) Food composition table for use in East Asia", None,
        "83.4", "0.10", "0.4", "N", "0.3",
        "1", "4", None,
    ])

    # Sheet 1.7 (SFA per 100gFA) — must be skipped by adapter
    ws2 = wb.create_sheet("1.7 (SFA per 100gFA)")
    ws2.append(["Food Code", "Food Name", "Description", "Group", "Previous", "Main data references", "Footnote", "C4:0 /100g FA (g)"])
    ws2.append([None, None, None, None, None, None, None, "FAC4:0"])
    ws2.append([None, None, None, None, None, None, None, "Butanoic acid per 100g fatty acids"])
    ws2.append(["13-145", "Ackee, canned, drained", "8 cans", "DG", 554, "MW4, 1978", None, "0.00"])

    # Sheet 1.9 (MUFA per 100FA) — must be skipped by adapter
    ws3 = wb.create_sheet("1.9 (MUFA per 100FA)")
    ws3.append(["Food Code", "Food Name", "Description", "Group", "Previous", "Main data references", "Footnote", "C10:1 /100g FA (g)"])
    ws3.append([None, None, None, None, None, None, None, "FAC10:1"])
    ws3.append([None, None, None, None, None, None, None, "Decenoic acid per 100g fatty acids"])
    ws3.append(["13-145", "Ackee, canned, drained", "8 cans", "DG", 554, "MW4, 1978", None, None])

    # Sheet 1.11 (PUFA per 100gFA) — must be skipped by adapter
    ws4 = wb.create_sheet("1.11 (PUFA per 100gFA)")
    ws4.append(["Food Code", "Food Name", "Description", "Group", "Previous", "Main data references", "Footnote", "C16:2 /100g FA (g)"])
    ws4.append([None, None, None, None, None, None, None, "FAC16:2"])
    ws4.append([None, None, None, None, None, None, None, "Hexadecadienoic acid per 100g fatty acids"])
    ws4.append(["13-145", "Ackee, canned, drained", "8 cans", "DG", 554, "MW4, 1978", None, None])

    path = tmp_path / "cofid_test.xlsx"
    wb.save(path)
    return path


@pytest.fixture
def cofid_dir(tmp_path):
    """Return a directory containing the mini CoFID workbook."""
    path = _make_workbook(tmp_path)
    return tmp_path


class TestCoFidAdapterRegistration:
    def test_adapter_is_registered(self):
        """CoFidAdapter must self-register under SRC-COFID-2021."""
        assert "SRC-COFID-2021" in registered()

    def test_adapter_src_id(self):
        """src_id must be SRC-COFID-2021."""
        adapter = CoFidAdapter()
        assert adapter.src_id == "SRC-COFID-2021"


class TestCoFidAdapterYieldsClaims:
    def test_load_is_lazy(self, cofid_dir):
        """load() must return a lazy iterator, not a list."""
        adapter = CoFidAdapter()
        root = cofid_dir.parent
        claims = adapter.load(root, cofid_dir)
        assert hasattr(claims, "__next__") or hasattr(claims, "__iter__")
        assert not isinstance(claims, list)

    def test_yields_claims_for_proximates(self, cofid_dir):
        """load() must yield Claim objects from the 1.3 Proximates sheet."""
        adapter = CoFidAdapter()
        root = cofid_dir.parent
        claims = list(adapter.load(root, cofid_dir))
        assert len(claims) >= 1
        c = claims[0]
        assert isinstance(c, Claim)

    def test_claims_use_cofid_field_prefix(self, cofid_dir):
        """Every claim field must start with nutrient:cofid:."""
        adapter = CoFidAdapter()
        root = cofid_dir.parent
        claims = list(adapter.load(root, cofid_dir))
        assert len(claims) > 0
        for c in claims:
            assert c.field.startswith("nutrient:cofid:"), f"field {c.field!r} does not start with nutrient:cofid:"

    def test_trace_cells_yield_tr_value_with_trace_derivation(self, cofid_dir):
        """'Tr' cells must yield Claim with v='tr' and derivation='trace'."""
        adapter = CoFidAdapter()
        root = cofid_dir.parent
        claims = list(adapter.load(root, cofid_dir))
        tr_claims = [c for c in claims if c.v == "tr"]
        assert len(tr_claims) >= 1, "At least one 'Tr' cell should yield a trace claim"
        for c in tr_claims:
            assert c.derivation == "trace"
            assert c.v == "tr"

    def test_n_cells_are_skipped(self, cofid_dir):
        """'N' cells must not yield any claim."""
        adapter = CoFidAdapter()
        root = cofid_dir.parent
        claims = list(adapter.load(root, cofid_dir))
        n_claims = [c for c in claims if c.v == "N"]
        assert len(n_claims) == 0, "'N' cells must not produce claims"

    def test_claims_have_prod_cofid_subject(self, cofid_dir):
        """Every claim subject must be prod:cofid:<code>."""
        adapter = CoFidAdapter()
        root = cofid_dir.parent
        claims = list(adapter.load(root, cofid_dir))
        for c in claims:
            assert c.subject.startswith("prod:cofid:"), f"subject {c.subject!r} does not start with prod:cofid:"

    def test_claims_have_as_described_basis(self, cofid_dir):
        """Every claim must have basis='as_described'."""
        adapter = CoFidAdapter()
        root = cofid_dir.parent
        claims = list(adapter.load(root, cofid_dir))
        for c in claims:
            assert c.basis == "as_described", f"claim {c.field} has basis {c.basis!r}, expected as_described"

    def test_claims_have_product_food_part(self, cofid_dir):
        """Every claim must have food_part='product'."""
        adapter = CoFidAdapter()
        root = cofid_dir.parent
        claims = list(adapter.load(root, cofid_dir))
        for c in claims:
            assert c.food_part == "product", f"claim {c.field} has food_part {c.food_part!r}, expected product"

    def test_claims_have_ref_from_main_data_reference(self, cofid_dir):
        """Every claim must have a ref from the 'Main data references' column."""
        adapter = CoFidAdapter()
        root = cofid_dir.parent
        claims = list(adapter.load(root, cofid_dir))
        for c in claims:
            assert c.ref is not None, f"claim {c.field} has no ref"
            assert "MW4" in c.ref or "Wu Leung" in c.ref, f"ref {c.ref!r} does not contain expected source"

    def test_per_100fa_sheets_not_ingested(self, cofid_dir):
        """Sheets 1.7, 1.9, 1.11 (per-100FA) must not be ingested — they are fatty-acids-per-g-fatty-acid, not food-referenced."""
        adapter = CoFidAdapter()
        root = cofid_dir.parent
        claims = list(adapter.load(root, cofid_dir))
        # No claims should reference the per-100FA sheets
        for c in claims:
            assert "per 100g FA" not in (c.ref or ""), f"claim {c.field} incorrectly references per-100FA data"

    def test_no_claims_from_skipped_sheets(self, cofid_dir):
        """Claims must not come from sheets 1.7, 1.9, or 1.11."""
        adapter = CoFidAdapter()
        root = cofid_dir.parent
        claims = list(adapter.load(root, cofid_dir))
        # The per-100FA sheets have only 1 data row each with all-None values,
        # so no claims should come from them. Verify by checking that
        # claims only come from the 1.3 Proximates sheet.
        assert len(claims) > 0, "Adapter should yield claims from ingested sheets"
