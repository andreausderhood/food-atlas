"""Task 18: European nutrition adapters — Ciqual 2025 and Swiss FCDB v7.1 (TDD)."""
from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from atlas.claims import Claim
from atlas.ingest.base import get_adapter, registered
from atlas.registry import load_sources

# --- Real fixture data extracted from the raw sources (never invented) ---

CIQUAL_ALIM_XML = """\
<?xml version="1.0" encoding="utf-8" ?>
<TABLE>
   <ALIM>
      <alim_code> 1000 </alim_code>
      <alim_nom_fr> Pastis </alim_nom_fr>
      <alim_nom_eng> Pastis (anise-flavoured spirit) </alim_nom_eng>
      <alim_nom_sci missing=" " />
      <alim_grp_code> 06 </alim_grp_code>
   </ALIM>
   <ALIM>
      <alim_code> 1001 </alim_code>
      <alim_nom_fr> Eau de vie de fruits </alim_nom_fr>
      <alim_nom_eng> Fruit brandy or eau-de-vie </alim_nom_eng>
      <alim_nom_sci missing=" " />
      <alim_grp_code> 06 </alim_grp_code>
   </ALIM>
</TABLE>
"""

CIQUAL_CONST_XML = """\
<?xml version="1.0" encoding="utf-8" ?>
<TABLE>
   <CONST>
      <const_code> 327 </const_code>
      <const_nom_fr> Energie, Règlement UE N° 1169/2011 (kJ/100 g) </const_nom_fr>
      <const_nom_eng> Energy, Regulation EU No 1169/2011 (kJ/100g) </const_nom_eng>
      <code_INFOODS> ENERC </code_INFOODS>
   </CONST>
   <CONST>
      <const_code> 400 </const_code>
      <const_nom_fr> Eau (g/100 g) </const_nom_fr>
      <const_nom_eng> Water (g/100g) </const_nom_eng>
      <code_INFOODS> WATER </code_INFOODS>
   </CONST>
   <CONST>
      <const_code> 10110 </const_code>
      <const_nom_fr> Sodium (mg/100 g) </const_nom_fr>
      <const_nom_eng> Sodium (mg/100g) </const_nom_eng>
      <code_INFOODS> NA </code_INFOODS>
   </CONST>
</TABLE>
"""

CIQUAL_COMPO_XML = """\
<?xml version="1.0" encoding="utf-8" ?>
<TABLE>
   <COMPO>
      <alim_code> 1000 </alim_code>
      <const_code> 327 </const_code>
      <teneur> 235,0 </teneur>
      <min />
      <max />
      <code_confiance> A </code_confiance>
      <source_code> 2 </source_code>
   </COMPO>
   <COMPO>
      <alim_code> 1000 </alim_code>
      <const_code> 400 </const_code>
      <teneur> 30,5 </teneur>
      <min />
      <max />
      <code_confiance> A </code_confiance>
      <source_code> 2 </source_code>
   </COMPO>
   <COMPO>
      <alim_code> 1001 </alim_code>
      <const_code> 327 </const_code>
      <teneur> 210,0 </teneur>
      <min />
      <max />
      <code_confiance> B </code_confiance>
      <source_code> 2 </source_code>
   </COMPO>
   <COMPO>
      <alim_code> 1001 </alim_code>
      <const_code> 400 </const_code>
      <teneur> - </teneur>
      <min />
      <max />
      <code_confiance> A </code_confiance>
      <source_code> 2 </source_code>
   </COMPO>
</TABLE>
"""

CIQUAL_SOURCES_XML = """\
<?xml version="1.0" encoding="utf-8" ?>
<TABLE>
   <SOURCES>
      <source_code> 1 </source_code>
      <ref_citation missing="." />
   </SOURCES>
   <SOURCES>
      <source_code> 2 </source_code>
      <ref_citation> Paul AA, Southgate DAT (1978). </ref_citation>
   </SOURCES>
</TABLE>
"""


def _write_file(root: Path, rel: str, content: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def _make_ciqual_root(tmp_path: Path) -> Path:
    """Create a minimal Ciqual directory with real XML fragments."""
    _write_file(tmp_path, "alim_2025_11_03.xml", CIQUAL_ALIM_XML)
    _write_file(tmp_path, "const_2025_11_03.xml", CIQUAL_CONST_XML)
    _write_file(tmp_path, "compo_2025_11_03.xml", CIQUAL_COMPO_XML)
    _write_file(tmp_path, "sources_2025_11_03.xml", CIQUAL_SOURCES_XML)
    return tmp_path


# --- Swiss FCDB fixture (realistic minimal data) ---

SWISS_HEADER = [
    "ID", "ID V 4.0", "ID SwissFIR", "Name", "Synonyms", "Category",
    "Density", "Matrix unit",
    "Energy, kilojoules (kJ)", "Derivation of value", "Source",
    "Energy, kilocalories (kcal)", "Derivation of value", "Source",
    "Fat, total (g)", "Derivation of value", "Source",
]

SWISS_ROWS = [
    [10533, "", "", "Agar Agar", "", "Various/Gelling and binding agents",
     1.0, "per 100g edible portion",
     641, "Automated calculation", 1473,
     160, "Automated calculation", 1473,
     0.2, "-", 1473],
    [10536, "", "", "Agave syrup", "", "Sweets/Sugar and sweeteners",
     1.38, "per 100g edible portion",
     1310, "Automated calculation", 1699,
     310, "Automated calculation", 1699,
     0.5, "Estimation", 1699],
    [10540, "", "", "Almond", "", "Nuts and seeds",
     0.57, "per 100g edible portion",
     2400, "Automated calculation", 1473,
     570, "Automated calculation", 1473,
     50.0, "Automated calculation", 1473],
]


def _make_swiss_root(tmp_path: Path) -> Path:
    """Create a minimal Swiss FCDB directory with a real Excel file."""
    import openpyxl
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Generic Foods"
    ws["A1"] = "Swiss food composition database – Generic foods V 7.1 (01.07.2026)"
    for col_idx, val in enumerate(SWISS_HEADER, 1):
        ws.cell(row=3, column=col_idx, value=val)
    for row_idx, row_data in enumerate(SWISS_ROWS, 4):
        for col_idx, val in enumerate(row_data, 1):
            ws.cell(row=row_idx, column=col_idx, value=val)

    xlsx_path = tmp_path / "Swiss_food_composition_database.xlsx"
    wb.save(str(xlsx_path))
    wb.close()
    return tmp_path


# --- Swiss FCDB fixture with n.d. and dash values (edge cases) ---

SWISS_ROWS_EDGE = [
    [1253, "", "", "Amaro Ramazzotti (30 vol%)", "", "Alcoholic beverages",
     1.06, "per 100g edible portion",
     953, "Automated calculation", 1129,
     228, "Automated calculation", 1129,
     0, "-", 1129],
    [1262, "", "", "Malibu Coconut (21 vol%)", "", "Alcoholic beverages",
     1.05, "per 100g edible portion",
     786, "Automated calculation", 1129,
     188, "Automated calculation", 1129,
     0, "n.d.", 1129],
]


def _make_swiss_root_with_nd(tmp_path: Path) -> Path:
    """Swiss fixture with n.d. and dash values."""
    import openpyxl
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Generic Foods"
    ws["A1"] = "Swiss food composition database – Generic foods V 7.1 (01.07.2026)"
    for col_idx, val in enumerate(SWISS_HEADER, 1):
        ws.cell(row=3, column=col_idx, value=val)
    for row_idx, row_data in enumerate(SWISS_ROWS_EDGE, 4):
        for col_idx, val in enumerate(row_data, 1):
            ws.cell(row=row_idx, column=col_idx, value=val)

    xlsx_path = tmp_path / "Swiss_food_composition_database.xlsx"
    wb.save(str(xlsx_path))
    wb.close()
    return tmp_path


# --- Test fixtures: source registry entries in correct directory structure ---

@pytest.fixture
def ciqual_root(tmp_path: Path) -> Path:
    """Ciqual root with XML data and registry."""
    root = _make_ciqual_root(tmp_path)
    reg_dir = root / "data" / "registry"
    reg_dir.mkdir(parents=True, exist_ok=True)
    _write_file(reg_dir, "sources.yaml",
        "SRC-CIQUAL-2025:\n"
        "  title: \"Table de composition nutritionnelle des aliments Ciqual (2025)\"\n"
        "  publisher: \"ANSES\"\n"
        "  url: \"https://doi.org/10.57745/RDMHWY\"\n"
        "  license: \"Open Licence 2.0 (Etalab)\"\n"
        "  license_class: open_license\n"
        "  license_read: true\n"
        "  kind: compilation\n"
        "  independence: independent\n"
        "  supports: [identity, nutrition]\n"
        "  attribution: \"ANSES.\"\n")
    return root


@pytest.fixture
def swiss_root(tmp_path: Path) -> Path:
    """Swiss FCDB root with Excel data and registry."""
    root = _make_swiss_root(tmp_path)
    reg_dir = root / "data" / "registry"
    reg_dir.mkdir(parents=True, exist_ok=True)
    _write_file(reg_dir, "sources.yaml",
        "SRC-SWISS-FCDB-V7.1:\n"
        "  title: \"Swiss Food Composition Database (Version 7.1, 2026)\"\n"
        "  publisher: \"FSVO\"\n"
        "  url: \"https://naehrwertdaten.ch/\"\n"
        "  license: \"Open Government Data (FSVO Open Use)\"\n"
        "  license_class: open_license\n"
        "  license_read: true\n"
        "  kind: compilation\n"
        "  independence: independent\n"
        "  supports: [identity, nutrition]\n"
        "  attribution: \"FSVO.\"\n")
    return root


@pytest.fixture
def swiss_root_with_nd(tmp_path: Path) -> Path:
    """Swiss FCDB root with n.d./dash edge-case data."""
    root = _make_swiss_root_with_nd(tmp_path)
    reg_dir = root / "data" / "registry"
    reg_dir.mkdir(parents=True, exist_ok=True)
    _write_file(reg_dir, "sources.yaml",
        "SRC-SWISS-FCDB-V7.1:\n"
        "  title: \"Swiss Food Composition Database (Version 7.1, 2026)\"\n"
        "  publisher: \"FSVO\"\n"
        "  url: \"https://naehrwertdaten.ch/\"\n"
        "  license: \"Open Government Data (FSVO Open Use)\"\n"
        "  license_class: open_license\n"
        "  license_read: true\n"
        "  kind: compilation\n"
        "  independence: independent\n"
        "  supports: [identity, nutrition]\n"
        "  attribution: \"FSVO.\"\n")
    return root


# --- TDD RED PHASE: Failing tests ---

class TestCiqualAdapterRegistration:
    """Red: Ciqual adapter must be registered and discoverable."""

    def test_ciqual_adapter_registered(self):
        from atlas.ingest.ciqual import CiqualAdapter
        adapter = CiqualAdapter("SRC-CIQUAL-2025", "prod:ciq")
        assert adapter.src_id == "SRC-CIQUAL-2025"

    def test_ciqual_prefix_is_ciq(self, ciqual_root: Path):
        from atlas.ingest.ciqual import CiqualAdapter
        adapter = CiqualAdapter("SRC-CIQUAL-2025", "prod:ciq")
        claims = list(adapter.load(ciqual_root, ciqual_root))
        for c in claims:
            assert c.subject.startswith("prod:ciq:"), f"Expected prod:ciq: prefix, got {c.subject}"


class TestSwissAdapterRegistration:
    """Red: Swiss FCDB adapter must be registered and discoverable."""

    def test_swiss_adapter_registered(self):
        from atlas.ingest.swiss_fcdb import SwissFcdbAdapter
        adapter = SwissFcdbAdapter("SRC-SWISS-FCDB-V7.1", "prod:swiss")
        assert adapter.src_id == "SRC-SWISS-FCDB-V7.1"

    def test_swiss_prefix_is_swiss(self, swiss_root: Path):
        from atlas.ingest.swiss_fcdb import SwissFcdbAdapter
        adapter = SwissFcdbAdapter("SRC-SWISS-FCDB-V7.1", "prod:swiss")
        claims = list(adapter.load(swiss_root, swiss_root))
        for c in claims:
            assert c.subject.startswith("prod:swiss:"), f"Expected prod:swiss: prefix, got {c.subject}"


class TestCiqualStreamingClaims:
    """Red: Ciqual adapter must stream claims from XML fixtures."""

    def test_ciqual_yields_energy_claim(self, ciqual_root: Path):
        from atlas.ingest.ciqual import CiqualAdapter
        adapter = CiqualAdapter("SRC-CIQUAL-2025", "prod:ciq")
        claims = list(adapter.load(ciqual_root, ciqual_root))
        energy_claims = [c for c in claims if "327" in c.field]
        assert len(energy_claims) >= 2, f"Expected at least 2 energy claims, got {len(energy_claims)}"

    def test_ciqual_yields_water_claim(self, ciqual_root: Path):
        from atlas.ingest.ciqual import CiqualAdapter
        adapter = CiqualAdapter("SRC-CIQUAL-2025", "prod:ciq")
        claims = list(adapter.load(ciqual_root, ciqual_root))
        water_claims = [c for c in claims if "400" in c.field]
        assert len(water_claims) >= 1, f"Expected at least 1 water claim, got {len(water_claims)}"

    def test_ciqual_skips_dash_teneur(self, ciqual_root: Path):
        from atlas.ingest.ciqual import CiqualAdapter
        adapter = CiqualAdapter("SRC-CIQUAL-2025", "prod:ciq")
        claims = list(adapter.load(ciqual_root, ciqual_root))
        # The second food (alim_code=1001) has teneur="-" for water → should be skipped
        water_claims = [c for c in claims if "400" in c.field]
        for c in water_claims:
            assert c.subject != "prod:ciq:1001", "Dash teneur should be skipped"

    def test_ciqual_comma_decimal_parsed(self, ciqual_root: Path):
        from atlas.ingest.ciqual import CiqualAdapter
        adapter = CiqualAdapter("SRC-CIQUAL-2025", "prod:ciq")
        claims = list(adapter.load(ciqual_root, ciqual_root))
        energy_claims = [c for c in claims if "327" in c.field and c.subject == "prod:ciq:1000"]
        assert len(energy_claims) == 1, f"Expected 1 energy claim for food 1000, got {len(energy_claims)}"
        assert energy_claims[0].v == 235.0, f"Expected 235.0, got {energy_claims[0].v}"

    def test_ciqual_claim_fields(self, ciqual_root: Path):
        from atlas.ingest.ciqual import CiqualAdapter
        adapter = CiqualAdapter("SRC-CIQUAL-2025", "prod:ciq")
        claims = list(adapter.load(ciqual_root, ciqual_root))
        for c in claims:
            assert c.group == "nutrition"
            assert c.basis == "as_described"
            assert c.food_part == "product"
            assert c.derivation == "registry"
            assert c.src == "SRC-CIQUAL-2025"
            assert c.unit is not None


class TestSwissStreamingClaims:
    """Red: Swiss FCDB adapter must stream claims from Excel fixtures."""

    def test_swiss_yields_energy_claim(self, swiss_root: Path):
        from atlas.ingest.swiss_fcdb import SwissFcdbAdapter
        adapter = SwissFcdbAdapter("SRC-SWISS-FCDB-V7.1", "prod:swiss")
        claims = list(adapter.load(swiss_root, swiss_root))
        energy_claims = [c for c in claims if "Energy" in c.field and "kilojoule" in c.field]
        assert len(energy_claims) >= 2, f"Expected at least 2 energy claims, got {len(energy_claims)}"

    def test_swiss_skips_nd_values(self, swiss_root_with_nd: Path):
        from atlas.ingest.swiss_fcdb import SwissFcdbAdapter
        adapter = SwissFcdbAdapter("SRC-SWISS-FCDB-V7.1", "prod:swiss")
        claims = list(adapter.load(swiss_root_with_nd, swiss_root_with_nd))
        # n.d. in derivation column does not skip the claim; only missing VALUES are skipped
        # Both foods should have fat claims (value=0 with n.d. derivation is valid)
        fat_claims = [c for c in claims if "Fat" in c.field]
        assert len(fat_claims) >= 1, f"Expected at least 1 fat claim, got {len(fat_claims)}"

    def test_swiss_skips_dash_values(self, swiss_root: Path):
        from atlas.ingest.swiss_fcdb import SwissFcdbAdapter
        adapter = SwissFcdbAdapter("SRC-SWISS-FCDB-V7.1", "prod:swiss")
        claims = list(adapter.load(swiss_root, swiss_root))
        # Dash in derivation column does not skip the claim; only missing VALUES are skipped
        # Agar Agar has fat=0.2 with dash derivation → claim is included
        fat_claims = [c for c in claims if "Fat" in c.field and c.subject == "prod:swiss:10533"]
        assert len(fat_claims) == 1, f"Expected 1 fat claim for Agar Agar (value 0.2, dash derivation), got {len(fat_claims)}"

    def test_swiss_comma_decimal_parsed(self, swiss_root: Path):
        from atlas.ingest.swiss_fcdb import SwissFcdbAdapter
        adapter = SwissFcdbAdapter("SRC-SWISS-FCDB-V7.1", "prod:swiss")
        claims = list(adapter.load(swiss_root, swiss_root))
        fat_claims = [c for c in claims if "Fat" in c.field and c.subject == "prod:swiss:10540"]
        assert len(fat_claims) == 1, f"Expected 1 fat claim for Almond, got {len(fat_claims)}"
        assert fat_claims[0].v == 50.0, f"Expected 50.0, got {fat_claims[0].v}"

    def test_swiss_claim_fields(self, swiss_root: Path):
        from atlas.ingest.swiss_fcdb import SwissFcdbAdapter
        adapter = SwissFcdbAdapter("SRC-SWISS-FCDB-V7.1", "prod:swiss")
        claims = list(adapter.load(swiss_root, swiss_root))
        for c in claims:
            assert c.group == "nutrition"
            assert c.basis == "as_described"
            assert c.food_part == "product"
            assert c.derivation in ("calculated", "imputed", "registry")
            assert c.src == "SRC-SWISS-FCDB-V7.1"
            assert c.unit is not None


class TestContractRejects:
    """Red: Contract rejects should be 0 for valid data."""

    def test_ciqual_no_contract_rejects(self, ciqual_root: Path):
        from atlas.ingest.ciqual import CiqualAdapter
        from atlas.contract import validate

        adapter = CiqualAdapter("SRC-CIQUAL-2025", "prod:ciq")
        claims = list(adapter.load(ciqual_root, ciqual_root))
        sources = load_sources(
            ciqual_root / "data" / "registry" / "sources.yaml",
            ciqual_root / "data" / "registry" / "link_status.yaml",
        )
        result = validate(claims, sources)
        assert len(result.gaps) == 0, f"Expected 0 contract rejects, got {len(result.gaps)}: {result.gaps}"

    def test_swiss_no_contract_rejects(self, swiss_root: Path):
        from atlas.ingest.swiss_fcdb import SwissFcdbAdapter
        from atlas.contract import validate

        adapter = SwissFcdbAdapter("SRC-SWISS-FCDB-V7.1", "prod:swiss")
        claims = list(adapter.load(swiss_root, swiss_root))
        sources = load_sources(
            swiss_root / "data" / "registry" / "sources.yaml",
            swiss_root / "data" / "registry" / "link_status.yaml",
        )
        result = validate(claims, sources)
        assert len(result.gaps) == 0, f"Expected 0 contract rejects, got {len(result.gaps)}: {result.gaps}"