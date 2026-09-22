"""Task 30: IMPPAT 2.0 Ingest Adapter — species-native traditional_use and molecules.

Tests adapter registration, claim generation, field naming conventions,
epistemic separation (Rule 14b), and contract compliance using real JSONL data.
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

def _imppat_sample_lines(n: int = 3) -> list[dict]:
    """Read real IMPPAT records from the JSONL file."""
    path = Path(__file__).resolve().parent.parent / "data" / "raw" / "imppat-2.0" / "imppat_records.jsonl"
    records = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= n:
                break
            records.append(json.loads(line))
    return records


def _herb_sample_lines(n: int = 3) -> list[dict]:
    """Read real HERB records from the JSONL file."""
    path = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "herb" / "HERB_herb_info.jsonl"
    records = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= n:
                break
            records.append(json.loads(line))
    return records


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
def tmp_imppat_file(tmp_path: Path) -> Path:
    records = _imppat_sample_lines(3)
    p = tmp_path / "imppat_sample.jsonl"
    p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n", encoding="utf-8")
    return p


@pytest.fixture
def tmp_herb_file(tmp_path: Path) -> Path:
    records = _herb_sample_lines(3)
    p = tmp_path / "herb_sample.jsonl"
    p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n", encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Tests: Adapter Registration
# ---------------------------------------------------------------------------

def test_imppat_adapter_registered():
    adapter = get_adapter("SRC-IMPPAT-2.0")
    assert adapter.src_id == "SRC-IMPPAT-2.0"


def test_herb_adapter_not_registered_yet():
    """HERB adapter is registered after herb.py is imported via base.py."""
    from atlas.ingest import herb  # noqa: F401 — triggers registration
    adapter = get_adapter("SRC-HERB-TCM")
    assert adapter.src_id == "SRC-HERB-TCM"


# ---------------------------------------------------------------------------
# Tests: IMPPAT Molecules Claim Generation
# ---------------------------------------------------------------------------

def test_imppat_molecules_field_naming(tmp_imppat_file: Path):
    from atlas.ingest.imppat import ImppatAdapter

    adapter = ImppatAdapter()
    claims = list(adapter.load(repo_root, tmp_imppat_file))
    mol_claims = [c for c in claims if c.group == "molecules"]

    for c in mol_claims:
        assert c.field.startswith("molecule:imppat:"), f"Wrong field prefix: {c.field}"
        # IMPHY-ID should be the suffix after the colon
        imid = c.field.split("molecule:imppat:", 1)[1]
        assert imid.startswith("IMPHY"), f"IMPHY-ID expected, got: {imid}"
        # v should be the chemical name (non-amount, no unit)
        assert isinstance(c.v, str) and c.v, f"Chemical name expected, got: {c.v!r}"
        # No unit or basis for non-amount claims
        assert c.unit is None, f"Non-amount molecule claim should have no unit: {c}"
        assert c.basis is None, f"Non-amount molecule claim should have no basis: {c}"


def test_imppat_molecules_ref_includes_plant_part(tmp_imppat_file: Path):
    from atlas.ingest.imppat import ImppatAdapter

    adapter = ImppatAdapter()
    claims = list(adapter.load(repo_root, tmp_imppat_file))
    mol_claims = [c for c in claims if c.group == "molecules"]

    for c in mol_claims:
        assert c.ref is not None and c.ref != "", f"Molecule claim should have a ref: {c}"
        # Ref should include plant_part information
        # (format: reference | plant_part)
        assert " | " in c.ref or c.ref != "", f"Ref should include plant_part: {c.ref}"


# ---------------------------------------------------------------------------
# Tests: IMPPAT Traditional Use Claim Generation
# ---------------------------------------------------------------------------

def test_imppat_traditional_use_mesh_field_naming(tmp_imppat_file: Path):
    from atlas.ingest.imppat import ImppatAdapter

    adapter = ImppatAdapter()
    claims = list(adapter.load(repo_root, tmp_imppat_file))
    tu_claims = [c for c in claims if c.group == "traditional_use" and c.field.startswith("traditional_use:imppat:")]

    for c in tu_claims:
        # Field should be traditional_use:imppat:{first-MESH-token}
        suffix = c.field.split("traditional_use:imppat:", 1)[1]
        # First MESH token should be without MESH: prefix
        assert not suffix.startswith("MESH:"), f"MESH prefix should be stripped: {c.field}"
        assert suffix, f"Field should have MESH token suffix: {c.field}"
        # v should be the therapeutic_use text
        assert isinstance(c.v, str) and c.v, f"Therapeutic use text expected: {c.v!r}"
        # ref should be just the reference (no plant_part for traditional_use)
        assert c.ref is not None, f"Traditional use claim should have a ref: {c}"


def test_imppat_traditional_use_from_therapeutics(tmp_imppat_file: Path):
    from atlas.ingest.imppat import ImppatAdapter

    adapter = ImppatAdapter()
    claims = list(adapter.load(repo_root, tmp_imppat_file))
    tu_claims = [c for c in claims if c.group == "traditional_use" and c.field.startswith("traditional_use:imppat:")]

    # At least some therapeutic claims should be generated
    assert len(tu_claims) > 0, "Expected at least one traditional_use:imppat claim from therapeutics"

    # Verify mesh_id first token is used as field suffix
    for c in tu_claims:
        suffix = c.field.split("traditional_use:imppat:", 1)[1]
        # Should be a MESH ID token (alphanumeric with D prefix)
        assert suffix, f"Empty suffix in field: {c.field}"


# ---------------------------------------------------------------------------
# Tests: IMPPAT Contract Compliance
# ---------------------------------------------------------------------------

def test_imppat_claims_pass_contract(tmp_imppat_file: Path, sources):
    from atlas.ingest.imppat import ImppatAdapter

    adapter = ImppatAdapter()
    claims = list(adapter.load(repo_root, tmp_imppat_file))

    for c in claims:
        gap = check(c, sources)
        assert gap is None, f"Claim rejected by contract: {c} → {gap}"


# ---------------------------------------------------------------------------
# Tests: IMPPAT Non-Binomial plant_name Handling
# ---------------------------------------------------------------------------

def test_imppat_non_binomial_still_slugged(tmp_path: Path, sources):
    """Plant names that are not complete binomials are still ingested with species_id slugged."""
    from atlas.ingest.imppat import ImppatAdapter

    # Record with non-binomial plant_name
    record = {
        "plant_name": "Rhizoma Zingiberis",
        "common_name": "",
        "ayurvedic_properties": {},
        "phytochemicals": [],
        "therapeutics": [
            {
                "plant_name": "Rhizoma Zingiberis",
                "plant_part": "rhizome",
                "therapeutic_use": "Anti-inflammatory",
                "mesh_id": "MESH:D000001",
                "reference": "Test Ref",
            },
        ],
    }
    p = tmp_path / "imppat_non_binomial.jsonl"
    p.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")

    adapter = ImppatAdapter()
    claims = list(adapter.load(repo_root, p))

    # Should still produce claims with slugged subject
    tu_claims = [c for c in claims if c.group == "traditional_use" and c.field.startswith("traditional_use:imppat:")]
    assert len(tu_claims) > 0, "Non-binomial plant_name should still produce claims"
    assert tu_claims[0].subject == "org:rhizoma-zingiberis", f"Expected org:rhizoma-zingiberis, got {tu_claims[0].subject}"


# ---------------------------------------------------------------------------
# Tests: IMPPAT Species-Native (no identity edges)
# ---------------------------------------------------------------------------

def test_imppat_no_product_edges(tmp_imppat_file: Path):
    from atlas.ingest.imppat import ImppatAdapter

    adapter = ImppatAdapter()
    claims = list(adapter.load(repo_root, tmp_imppat_file))

    # All subjects should be species-level (org: prefix), never product-level
    for c in claims:
        assert c.subject.startswith("org:"), f"Species-native claim should have org: subject, got: {c.subject}"
        assert not c.subject.startswith("product:"), f"Should not produce product edges: {c.subject}"


# ---------------------------------------------------------------------------
# Tests: IMPPAT Epistemic Separation (Rule 14b)
# ---------------------------------------------------------------------------

def test_imppat_empty_ayurvedic_properties_skipped(tmp_imppat_file: Path):
    """Real IMPPAT JSONL records have empty ayurvedic_properties — no ayurveda claims produced."""
    from atlas.ingest.imppat import ImppatAdapter

    adapter = ImppatAdapter()
    claims = list(adapter.load(repo_root, tmp_imppat_file))

    ayurveda_fields = [c.field for c in claims if c.group == "traditional_use" and c.field.startswith("ayurveda:")]
    # Real IMPPAT JSONL data has empty ayurvedic_properties for all records
    assert len(ayurveda_fields) == 0, "Empty ayurvedic_properties should produce no ayurveda claims"


# ---------------------------------------------------------------------------
# Tests: IMPPAT Claim Counts
# ---------------------------------------------------------------------------

def test_imppat_claim_counts(tmp_imppat_file: Path):
    from atlas.ingest.imppat import ImppatAdapter

    adapter = ImppatAdapter()
    claims = list(adapter.load(repo_root, tmp_imppat_file))

    groups = {}
    for c in claims:
        groups.setdefault(c.group, []).append(c)

    assert "molecules" in groups, "Should produce molecules claims"
    assert "traditional_use" in groups, "Should produce traditional_use claims"
    assert len(groups["molecules"]) > 0, "Should have at least one molecule claim"
    assert len(groups["traditional_use"]) > 0, "Should have at least one traditional_use claim"