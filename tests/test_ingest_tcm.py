"""Task 30: IMPPAT 2.0 and HERB TCM Ingest Adapters (Traditional Use).

Tests adapter registration, claim generation, epistemic separation (Rule 14b),
authentic vocabulary preservation (tcm:*, ayurveda:*), and contract compliance.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from atlas.claims import Claim
from atlas.contract import check
from atlas.ingest.base import get_adapter
from atlas.registry import load_sources


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_HERB_RECORD = {
    "herb_id": "HERB001850",
    "pinyin_name": "GAO LI SHEN",
    "chinese_name": "高丽参",
    "english_name": "Korea ginseng",
    "latin_name": "Radix Ginseng Korea",
    "properties": "Minor Warm; Sweet; Slightly Bitter",
    "meridians": "Lung; Spleen; Heart",
    "species_name": "Panax ginseng",
    "ingredients": [
        {"id": "HBIN015954", "name": "amylum", "alias": "corn starch"},
        {"id": "HBIN025006", "name": "ellagic acid", "alias": "4,4',5,5',6,6'-hexahydroxydiphenic acid"},
    ],
}

SAMPLE_IMPPAT_RECORD = {
    "plant_name": "Zingiber officinale",
    "ayurvedic_properties": {
        "rasa": ["Katu", "Tikta"],
        "guna": ["Laghu", "Snigdha", "Tikshna"],
        "virya": "Ushna",
        "vipaka": "Madhura",
        "dosha": ["Kapha-Vata hara"],
    },
    "therapeutics": [
        {
            "therapeutic_use": "Abdominal pain",
            "plant_part": "rhizome",
            "mesh_id": "MESH:D015746",
            "reference": "The Ayurvedic Pharmacopoeia of India Part-1 Volume-9",
        },
        {
            "therapeutic_use": "Anemia",
            "plant_part": "rhizome",
            "mesh_id": "MESH:D000740",
            "reference": "The Ayurvedic Pharmacopoeia of India Part-1 Volume-9",
        },
    ],
    "phytochemicals": [
        {
            "phytochemical_id": "IMPHY000448",
            "name": "Gingerglycolipid B",
            "plant_part": "aerial part",
            "reference": "ISBN:9788171360536",
        },
        {
            "phytochemical_id": "IMPHY001235",
            "name": "Gingerglycolipid A",
            "plant_part": "aerial part",
            "reference": "ISBN:9788171360536",
        },
    ],
}


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def sources(repo_root: Path):
    return load_sources(
        repo_root / "data/registry/sources.yaml",
        repo_root / "data/registry/link_status.yaml",
    )


@pytest.fixture
def tmp_tcm_file(tmp_path: Path) -> Path:
    p = tmp_path / "herb_sample.jsonl"
    p.write_text(json.dumps(SAMPLE_HERB_RECORD) + "\n", encoding="utf-8")
    return p


@pytest.fixture
def tmp_imppat_file(tmp_path: Path) -> Path:
    p = tmp_path / "imppat_sample.jsonl"
    p.write_text(json.dumps(SAMPLE_IMPPAT_RECORD) + "\n", encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Tests: Adapter Registration
# ---------------------------------------------------------------------------

def test_tcm_adapter_registered():
    from atlas.ingest.tcm import TcmAdapter

    adapter = get_adapter("SRC-HERB-TCM")
    assert isinstance(adapter, TcmAdapter)
    assert adapter.src_id == "SRC-HERB-TCM"


def test_imppat_adapter_registered():
    from atlas.ingest.imppat import ImppatAdapter

    adapter = get_adapter("SRC-IMPPAT-2.0")
    assert isinstance(adapter, ImppatAdapter)
    assert adapter.src_id == "SRC-IMPPAT-2.0"


# ---------------------------------------------------------------------------
# Tests: HERB TCM Claim Generation & Contract Check
# ---------------------------------------------------------------------------

def test_tcm_claims_generation_and_contract(repo_root: Path, sources, tmp_tcm_file: Path):
    from atlas.ingest.tcm import TcmAdapter

    adapter = TcmAdapter()
    claims = list(adapter.load(repo_root, tmp_tcm_file))
    assert len(claims) >= 6

    # Verify subjects use canonical species identifier
    for c in claims:
        assert c.subject == "org:panax-ginseng"
        assert c.src == "SRC-HERB-TCM"
        assert c.derivation == "literature"
        # Verify contract compliance: no gap returned
        gap = check(c, sources)
        assert gap is None, f"Claim {c} rejected by contract: {gap}"

    # Verify TCM traditional_use fields
    groups = {c.field: c.v for c in claims if c.group == "traditional_use"}
    assert "tcm:pinyin" in groups and groups["tcm:pinyin"] == "GAO LI SHEN"
    assert "tcm:chinese_name" in groups and groups["tcm:chinese_name"] == "高丽参"
    assert "tcm:english_name" in groups and groups["tcm:english_name"] == "Korea ginseng"

    # Properties split into nature and flavor
    natures = [c.v for c in claims if c.field == "tcm:nature"]
    assert "Minor Warm" in natures

    flavors = [c.v for c in claims if c.field == "tcm:flavor"]
    assert "Sweet" in flavors
    assert "Slightly Bitter" in flavors

    # Meridians
    meridians = [c.v for c in claims if c.field == "tcm:meridian"]
    assert "Lung" in meridians
    assert "Spleen" in meridians
    assert "Heart" in meridians

    # Molecules
    mol_claims = [c for c in claims if c.group == "molecules"]
    assert len(mol_claims) == 2
    mol_names = {c.v for c in mol_claims}
    assert "amylum" in mol_names
    assert "ellagic acid" in mol_names


# ---------------------------------------------------------------------------
# Tests: IMPPAT 2.0 Claim Generation & Contract Check
# ---------------------------------------------------------------------------

def test_imppat_claims_generation_and_contract(repo_root: Path, sources, tmp_imppat_file: Path):
    from atlas.ingest.imppat import ImppatAdapter

    adapter = ImppatAdapter()
    claims = list(adapter.load(repo_root, tmp_imppat_file))
    assert len(claims) >= 8

    # Verify subjects use canonical species identifier
    for c in claims:
        assert c.subject == "org:zingiber-officinale"
        assert c.src == "SRC-IMPPAT-2.0"
        assert c.derivation == "literature"
        # Verify contract compliance: no gap returned
        gap = check(c, sources)
        assert gap is None, f"Claim {c} rejected by contract: {gap}"

    # Traditional use: Ayurvedic properties
    tu_claims = {c.field: c.v for c in claims if c.group == "traditional_use"}
    assert any(c.field == "ayurveda:rasa" and c.v == "Katu" for c in claims)
    assert any(c.field == "ayurveda:guna" and c.v == "Laghu" for c in claims)
    assert any(c.field == "ayurveda:virya" and c.v == "Ushna" for c in claims)
    assert any(c.field == "ayurveda:vipaka" and c.v == "Madhura" for c in claims)
    assert any(c.field == "ayurveda:dosha" and c.v == "Kapha-Vata hara" for c in claims)

    # Traditional use: Therapeutics
    assert any("abdominal-pain" in c.field and c.v == "Abdominal pain" for c in claims)
    assert any("anemia" in c.field and c.v == "Anemia" for c in claims)

    # Molecules: Phytochemicals
    mol_claims = [c for c in claims if c.group == "molecules"]
    assert len(mol_claims) == 2
    mol_names = {c.v for c in mol_claims}
    assert "Gingerglycolipid B" in mol_names
    assert "Gingerglycolipid A" in mol_names


# ---------------------------------------------------------------------------
# Tests: Fetch / Scraper helpers (Mocked)
# ---------------------------------------------------------------------------

def test_tcm_fetch_herb_mocked():
    from atlas.ingest.tcm import fetch_herb_detail

    mock_response = {
        "summary": [
            ["Herb id", "Herb pinyin name", "Herb Chinese name", "Herb English name", "Herb Latin name", "Properties", "Meridians", "Use part", "TCMID id", "TCM-ID id"],
            ["HERB001850", "GAO LI SHEN", "高丽参", "Korea ginseng", {"title": "Radix Ginseng Korea"}, "Minor Warm; Sweet; Slightly Bitter", "Lung; Spleen; Heart", "Panax ginseng CA.Mey", {}, {}]
        ],
        "herb_ingredient": [
            ["Ingredient id", "Ingredient name", "Ingredient alias"],
            [{"title": "HBIN015954"}, "amylum", "corn starch"]
        ]
    }

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value.read.return_value = json.dumps(mock_response).encode("utf-8")
        rec = fetch_herb_detail("HERB001850")
        assert rec is not None
        assert rec["herb_id"] == "HERB001850"
        assert rec["chinese_name"] == "高丽参"
        assert rec["species_name"] == "Panax ginseng"
        assert len(rec["ingredients"]) == 1


def test_imppat_fetch_plant_mocked():
    from atlas.ingest.imppat import parse_imppat_phytochemical_table, parse_imppat_therapeutics_table

    html_phy = """
    <table id="table_id">
    <tbody>
    <tr>
      <td><a href="/imppat/phytochemical/Zingiber officinale">Zingiber officinale</a></td>
      <td>rhizome</td>
      <td><a href="/imppat/phytochemical-detailedpage/IMPHY000448">IMPHY000448</a></td>
      <td>Gingerglycolipid B</td>
      <td>ISBN:9788171360536</td>
    </tr>
    </tbody>
    </table>
    """
    phys = parse_imppat_phytochemical_table(html_phy)
    assert len(phys) == 1
    assert phys[0]["name"] == "Gingerglycolipid B"
    assert phys[0]["phytochemical_id"] == "IMPHY000448"
    assert phys[0]["plant_part"] == "rhizome"

    html_tu = """
    <table id="table_id">
    <tbody>
    <tr>
      <td><a href="/imppat/therapeutics/Zingiber officinale">Zingiber officinale</a></td>
      <td>rhizome</td>
      <td>Abdominal pain</td>
      <td>MESH:D015746</td>
      <td>The Ayurvedic Pharmacopoeia of India Part-1 Volume-9</td>
    </tr>
    </tbody>
    </table>
    """
    tus = parse_imppat_therapeutics_table(html_tu)
    assert len(tus) == 1
    assert tus[0]["therapeutic_use"] == "Abdominal pain"
    assert tus[0]["mesh_id"] == "MESH:D015746"
    assert tus[0]["plant_part"] == "rhizome"
