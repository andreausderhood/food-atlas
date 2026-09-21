"""Task 19: Identity cluster proposals and parity verification (TDD)."""
import json
import tempfile
from pathlib import Path

import pytest

from atlas.unified.identity import (
    Edge,
    AUTO_APPROVE,
    apply_exact_matches,
    check_parity,
    cluster_proposals,
    generate_proposals,
    load_edges,
    product_id,
    write_edges,
)
from atlas.unified.collectors import load_pool

BLS = "SRC-BLS-4.0"
FDC = "SRC-FDC-FOUNDATION-2026-04"
CIQ = "SRC-CIQUAL-2025"
SWISS = "SRC-SWISS-FCDB-V7.1"

PILOT_SPECIES = ["malus domestica", "brassica oleracea"]

SAMPLE_PRODUCTS = [
    {"source": FDC, "id": "F1", "name": "Apples, raw"},
    {"source": FDC, "id": "F2", "name": "Apple juice"},
    {"source": FDC, "id": "F3", "name": "Broccoli, raw"},
    {"source": FDC, "id": "F4", "name": "Cauliflower, raw"},
    {"source": CIQ, "id": "1000", "name": "Apple"},
    {"source": CIQ, "id": "1001", "name": "Broccoli"},
    {"source": SWISS, "id": "10533", "name": "Apple"},
    {"source": SWISS, "id": "10534", "name": "Broccoli"},
    {"source": FDC, "id": "F5", "name": "Random processed food 12345"},
    # Exact binomial matches for auto-approve and parity
    {"source": FDC, "id": "F6", "name": "Malus domestica"},
    {"source": FDC, "id": "F7", "name": "Brassica oleracea"},
]


def _load_proposals(path: Path) -> list[dict]:
    """Read proposals JSONL file back as list of dicts."""
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


@pytest.fixture(autouse=True)
def _proposals_tmp_dir(monkeypatch, tmp_path):
    """Fixture data must never overwrite the real proposals file in the repo."""
    import atlas.unified.identity as identity_mod
    monkeypatch.setattr(identity_mod, "_PROPOSALS_DIR", tmp_path / "proposals")


def _pool():
    return load_pool(Path("."))


def test_exact_binomial_match_generates_proposal():
    """A product whose name exactly matches a species binomial gets exact_binomial."""
    pool = _pool()
    proposals_path = generate_proposals(SAMPLE_PRODUCTS, pool)
    proposals = _load_proposals(proposals_path)
    # "Apple" (CIQ id 1000) should match malus domestica via common name
    apple_proposals = [p for p in proposals if p["source"] == CIQ and p["record"] == "1000"]
    assert len(apple_proposals) >= 1
    match_classes = {p["match_class"] for p in apple_proposals}
    assert "common_exact" in match_classes or "exact_binomial" in match_classes


def test_exact_match_confidence_is_one():
    """exact_binomial matches always have confidence 1.0."""
    pool = _pool()
    proposals_path = generate_proposals(SAMPLE_PRODUCTS, pool)
    proposals = _load_proposals(proposals_path)
    exact_binomial = [p for p in proposals if p["match_class"] == "exact_binomial"]
    for p in exact_binomial:
        assert p["confidence"] == 1.0, f"exact_binomial proposal {p} should have confidence 1.0"


def test_auto_approve_only_exact_binomial_above_threshold():
    """AUTO_APPROVE only applies to exact_binomial with confidence >= 0.95."""
    assert AUTO_APPROVE == {"exact_binomial": 0.95}
    # exact_binomial at 1.0 should auto-approve
    row = {"source": FDC, "record": "F1", "name": "Apples", "species": "malus domestica",
           "match_class": "exact_binomial", "confidence": 1.0}
    cluster = cluster_proposals([row])[0]
    assert cluster.auto is True

    # common_exact at 0.85 should NOT auto-approve
    row2 = {"source": FDC, "record": "F1", "name": "Apples", "species": "malus domestica",
            "match_class": "common_exact", "confidence": 0.85}
    cluster2 = cluster_proposals([row2])[0]
    assert cluster2.auto is False


def test_apply_exact_matches_writes_edges():
    """apply_exact_matches takes proposals with exact_binomial >= 0.95 and writes edges."""
    pool = _pool()
    proposals_path = generate_proposals(SAMPLE_PRODUCTS, pool)
    proposals = _load_proposals(proposals_path)
    with tempfile.TemporaryDirectory() as tmp:
        edges_path = Path(tmp) / "edges.jsonl"
        apply_exact_matches(proposals, edges_path, batch="t19", approver="test")
        edges = load_edges(edges_path)
        # All edges from apply_exact_matches should be approved
        for e in edges:
            assert e.status == "approved"
            assert e.method == "exact_binomial"
            assert e.confidence >= 0.95


def test_pilot_species_parity():
    """Malus domestica and Brassica oleracea must both have proposals generated."""
    pool = _pool()
    proposals_path = generate_proposals(SAMPLE_PRODUCTS, pool)
    proposals = _load_proposals(proposals_path)
    proposal_species = {p["species"] for p in proposals}
    for sp in PILOT_SPECIES:
        assert sp in proposal_species, f"Pilot species {sp} has no proposals — parity broken"


def test_parity_check_passes_for_pilot_species():
    """check_parity returns True when both pilot species have proposals."""
    pool = _pool()
    proposals_path = generate_proposals(SAMPLE_PRODUCTS, pool)
    proposals = _load_proposals(proposals_path)
    result = check_parity(proposals, PILOT_SPECIES)
    assert result is True, f"Parity check failed for pilot species with {len(proposals)} proposals"


def test_proposals_file_written():
    """generate_proposals writes a proposals file to data/research/proposals/."""
    pool = _pool()
    with tempfile.TemporaryDirectory() as tmp:
        proposals_dir = Path(tmp) / "proposals"
        proposals_path = generate_proposals(SAMPLE_PRODUCTS, pool, out_dir=proposals_dir)
        assert proposals_path.is_file()
        content = _load_proposals(proposals_path)
        assert len(content) > 0
        # Every proposal has required fields
        for p in content:
            assert "source" in p
            assert "record" in p
            assert "name" in p
            assert "species" in p
            assert "match_class" in p
            assert "confidence" in p


def test_no_open_candidates_for_exact_binomial_above_threshold():
    """exact_binomial proposals with confidence >= 0.95 must be auto-approved."""
    pool = _pool()
    proposals_path = generate_proposals(SAMPLE_PRODUCTS, pool)
    proposals = _load_proposals(proposals_path)
    exact_high = [p for p in proposals
                  if p["match_class"] == "exact_binomial" and p["confidence"] >= 0.95]
    with tempfile.TemporaryDirectory() as tmp:
        edges_path = Path(tmp) / "edges.jsonl"
        apply_exact_matches(proposals, edges_path, batch="t19", approver="test")
        approved_ids = {e.product + "|" + e.species for e in load_edges(edges_path)}
        for p in exact_high:
            pid = product_id(p["source"], p["record"])
            assert pid + "|" + p["species"] in approved_ids, \
                f"exact_binomial proposal {p} should be auto-approved"


def test_open_candidates_have_lower_confidence():
    """Proposals that remain as open candidates should have confidence < 0.95
    or match_class != exact_binomial."""
    pool = _pool()
    proposals_path = generate_proposals(SAMPLE_PRODUCTS, pool)
    proposals = _load_proposals(proposals_path)
    # common_exact proposals (confidence 0.85) should remain as open candidates
    common_exact = [p for p in proposals if p["match_class"] == "common_exact"]
    assert len(common_exact) > 0, "There should be common_exact proposals as open candidates"
    for p in common_exact:
        assert p["confidence"] < 0.95