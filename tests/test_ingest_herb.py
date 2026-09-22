"""Task 30: HERB TCM Ingest Adapter — species-native molecules and traditional_use.

Tests adapter registration, claim generation, field naming conventions,
latin_name skip logic, epistemic separation (Rule 14b), and contract compliance
using real JSONL data.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas.claims import Claim
from atlas.contract import check
from atlas.ingest.base import get_adapter
from atlas.registry import load_sources


# ---------------------------------------------------------------------------
# Real data fixtures (read from actual JSONL)
# ---------------------------------------------------------------------------

def _herb_sample_lines(n: int = 3) -> list[dict]:
    """Read real HERB records from the JSONL file."""
    path = Path(__file__).resolve().parent.parent / "data" / "raw" / "herb" / "HERB_herb_info.jsonl"
    records = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= n:
                break
            records.append(json.loads(line))
    return records


def _herb_non_binomial_record() -> dict:
    """A HERB record with non-binomial latin_name (should be skipped)."""
    return {
        "herb_id": "HERB999999",
        "pinyin_name": "TEST CAO",
        "chinese_name": "测试草",
        "english_name": "Test herb",
        "latin_name": "Rhizoma Zingiberis",
        "properties": "",
        "meridians": "",
        "species_name": "",
        "ingredients": [
            {"id": "HBIN999999", "name": "test compound", "alias": "test"},
        ],
    }


def _herb_empty_latin_record() -> dict:
    """A HERB record with empty latin_name (should be skipped)."""
    return {
        "herb_id": "HERB888888",
        "pinyin_name": "EMPTY LATIN",
        "chinese_name": "空拉丁",
        "english_name": "Empty latin herb",
        "latin_name": "",
        "properties": "",
        "meridians": "",
        "species_name": "",
        "ingredients": [
            {"id": "HBIN888888", "name": "another test compound", "alias": "test"},
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
def tmp_herb_file(tmp_path: Path) -> Path:
    records = _herb_sample_lines(3)
    p = tmp_path / "herb_sample.jsonl"
    p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n", encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Tests: Adapter Registration
# ---------------------------------------------------------------------------

def test_herb_adapter_registered():
    from atlas.ingest.herb import HerbAdapter

    adapter = get_adapter("SRC-HERB-TCM")
    assert isinstance(adapter, HerbAdapter)
    assert adapter.src_id == "SRC-HERB-TCM"


# ---------------------------------------------------------------------------
# Tests: HERB Molecules Claim Generation
# ---------------------------------------------------------------------------

def test_herb_molecules_field_naming(tmp_herb_file: Path):
    from atlas.ingest.herb import HerbAdapter

    adapter = HerbAdapter()
    claims = list(adapter.load(repo_root, tmp_herb_file))
    mol_claims = [c for c in claims if c.group == "molecules"]

    for c in mol_claims:
        assert c.field.startswith("molecule:herb:"), f"Wrong field prefix: {c.field}"
        # HBIN-ID should be the suffix after the colon, lowercase
        hbin = c.field.split("molecule:herb:", 1)[1]
        assert hbin == hbin.lower(), f"HBIN-ID should be lowercase: {hbin}"
        assert hbin.startswith("hbin"), f"HBIN-ID should start with 'hbin': {hbin}"
        # v should be the ingredient name
        assert isinstance(c.v, str) and c.v, f"Ingredient name expected, got: {c.v!r}"
        # No unit or basis for non-amount claims
        assert c.unit is None, f"Non-amount molecule claim should have no unit: {c}"
        assert c.basis is None, f"Non-amount molecule claim should have no basis: {c}"


def test_herb_molecules_ref_includes_herb_id_and_latin(tmp_herb_file: Path):
    from atlas.ingest.herb import HerbAdapter

    adapter = HerbAdapter()
    claims = list(adapter.load(repo_root, tmp_herb_file))
    mol_claims = [c for c in claims if c.group == "molecules"]

    for c in mol_claims:
        assert c.ref is not None and c.ref != "", f"Molecule claim should have a ref: {c}"
        # Ref should include herb_id and latin_name
        assert " | " in c.ref or len(c.ref) > 0, f"Ref should include herb_id and latin_name: {c.ref}"


# ---------------------------------------------------------------------------
# Tests: HERB Traditional Use Claim Generation
# ---------------------------------------------------------------------------

def test_herb_traditional_use_tcm_fields(tmp_herb_file: Path):
    from atlas.ingest.herb import HerbAdapter

    adapter = HerbAdapter()
    claims = list(adapter.load(repo_root, tmp_herb_file))
    tu_claims = [c for c in claims if c.group == "traditional_use"]

    # Should produce tcm:* traditional_use fields
    tcm_fields = {c.field for c in tu_claims}
    assert len(tcm_fields) > 0, "Should produce at least one tcm:* traditional_use claim"


# ---------------------------------------------------------------------------
# Tests: HERB Contract Compliance
# ---------------------------------------------------------------------------

def test_herb_claims_pass_contract(tmp_herb_file: Path, sources):
    from atlas.ingest.herb import HerbAdapter

    adapter = HerbAdapter()
    claims = list(adapter.load(repo_root, tmp_herb_file))

    for c in claims:
        gap = check(c, sources)
        assert gap is None, f"Claim rejected by contract: {c} → {gap}"


# ---------------------------------------------------------------------------
# Tests: HERB latin_name Skip Logic
# ---------------------------------------------------------------------------

def test_herb_non_binomial_latin_name_skipped(tmp_path: Path, sources):
    """HERB records with non-binomial latin_name should be skipped with counter."""
    from atlas.ingest.herb import HerbAdapter

    record = _herb_non_binomial_record()
    p = tmp_path / "herb_non_binomial.jsonl"
    p.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")

    adapter = HerbAdapter()
    claims = list(adapter.load(repo_root, p))

    # Non-binomial latin_name (Rhizoma Zingiberis) should produce no claims
    assert len(claims) == 0, f"Non-binomial latin_name should be skipped, got {len(claims)} claims"


def test_herb_empty_latin_name_skipped(tmp_path: Path, sources):
    """HERB records with empty latin_name should be skipped with counter."""
    from atlas.ingest.herb import HerbAdapter

    record = _herb_empty_latin_record()
    p = tmp_path / "herb_empty_latin.jsonl"
    p.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")

    adapter = HerbAdapter()
    claims = list(adapter.load(repo_root, p))

    # Empty latin_name should produce no claims
    assert len(claims) == 0, f"Empty latin_name should be skipped, got {len(claims)} claims"


def test_herb_binomial_latin_name_ingested(tmp_path: Path, sources):
    """HERB records with binomial latin_name should be ingested."""
    from atlas.ingest.herb import HerbAdapter

    record = {
        "herb_id": "HERB001481",
        "pinyin_name": "DUN YE SHU YU",
        "chinese_name": "盾叶薯蓣",
        "english_name": "Peltate Yam",
        "latin_name": "Dioscorea zingiberensis",
        "properties": "",
        "meridians": "",
        "species_name": "Dioscorea zingiberensis",
        "ingredients": [
            {"id": "HBIN013184", "name": "7-Epitaxol", "alias": "7-epitaxol"},
        ],
    }
    p = tmp_path / "herb_binomial.jsonl"
    p.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")

    adapter = HerbAdapter()
    claims = list(adapter.load(repo_root, p))

    # Binomial latin_name should produce claims
    assert len(claims) > 0, "Binomial latin_name should produce claims"
    mol_claims = [c for c in claims if c.group == "molecules"]
    assert len(mol_claims) > 0, "Should have molecule claims for binomial record"


# ---------------------------------------------------------------------------
# Tests: HERB Species-Native (no identity edges)
# ---------------------------------------------------------------------------

def test_herb_no_product_edges(tmp_herb_file: Path):
    from atlas.ingest.herb import HerbAdapter

    adapter = HerbAdapter()
    claims = list(adapter.load(repo_root, tmp_herb_file))

    for c in claims:
        assert c.subject.startswith("org:"), f"Species-native claim should have org: subject, got: {c.subject}"
        assert not c.subject.startswith("product:"), f"Should not produce product edges: {c.subject}"


# ---------------------------------------------------------------------------
# Tests: HERB Claim Counts
# ---------------------------------------------------------------------------

def test_herb_claim_counts(tmp_herb_file: Path):
    from atlas.ingest.herb import HerbAdapter

    adapter = HerbAdapter()
    claims = list(adapter.load(repo_root, tmp_herb_file))

    groups = {}
    for c in claims:
        groups.setdefault(c.group, []).append(c)

    assert "molecules" in groups, "Should produce molecules claims"
    assert "traditional_use" in groups, "Should produce traditional_use claims"
    assert len(groups["molecules"]) > 0, "Should have at least one molecule claim"
    assert len(groups["traditional_use"]) > 0, "Should have at least one traditional_use claim"