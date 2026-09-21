import pytest

from atlas.unified.identity import (
    Edge,
    IdentityError,
    apply_review,
    cluster_proposals,
    load_edges,
    product_id,
    resolver,
    species_id,
    validate_edges,
    write_edges,
    write_review_sheet,
)

BLS = "SRC-BLS-4.0"
POOL = {"malus domestica": {}, "beta vulgaris": {}}
PROPOSALS = [
    {"source": BLS, "record": "B1", "name": "Apfel roh", "species": "malus domestica", "match_class": "common_exact", "confidence": 0.8},
    {"source": BLS, "record": "B2", "name": "Apfel gedünstet", "species": "malus domestica", "match_class": "common_exact", "confidence": 0.8},
    {"source": BLS, "record": "B3", "name": "Beta vulgaris", "species": "beta vulgaris", "match_class": "exact_binomial", "confidence": 0.95},
]


def test_node_ids():
    assert product_id(BLS, "B1") == "prod:bls:B1"
    assert species_id("malus domestica") == "org:malus-domestica"


def test_cluster_is_species_source_matchclass_and_autofills(tmp_path):
    clusters = cluster_proposals(PROPOSALS)
    assert [len(c.products) for c in clusters] == [2, 1]           # biggest decision first
    sheet = tmp_path / "review.csv"
    write_review_sheet(sheet, clusters)
    rows = sheet.read_text().splitlines()
    assert rows[1].startswith(",malus domestica") and rows[2].startswith("approve,beta vulgaris")


def test_review_roundtrip_and_stable_edges(tmp_path):
    clusters = cluster_proposals(PROPOSALS)
    sheet = tmp_path / "review.csv"
    write_review_sheet(sheet, clusters)
    sheet.write_text(sheet.read_text().replace(",malus domestica", "approve,malus domestica", 1))
    edges = apply_review(sheet, clusters, "tranche-1", "andre", "2026-09-21")
    assert {e.product for e in edges} == {"prod:bls:B1", "prod:bls:B2", "prod:bls:B3"}
    validate_edges(edges, POOL)
    out = tmp_path / "edges.jsonl"
    write_edges(out, edges)
    assert load_edges(out) == sorted(edges, key=lambda e: (e.product, e.species))
    assert cluster_proposals(PROPOSALS, decided={e.product for e in edges}) == []   # decided = not proposed again
    assert resolver(edges)("prod:bls:B1") == "malus domestica"


def test_undecided_and_rejected_rows(tmp_path):
    clusters = cluster_proposals(PROPOSALS)
    sheet = tmp_path / "review.csv"
    write_review_sheet(sheet, clusters)
    sheet.write_text(sheet.read_text().replace(",malus domestica", "reject,malus domestica", 1))
    edges = apply_review(sheet, clusters, "t", "andre", "2026-09-21")
    assert {(e.product, e.status) for e in edges} == {
        ("prod:bls:B1", "rejected"), ("prod:bls:B2", "rejected"), ("prod:bls:B3", "approved")}
    assert resolver(edges)("prod:bls:B1") is None                    # a rejected edge attaches nothing


def test_edges_reject_unknown_species_and_conflicts():
    e = Edge("prod:bls:B1", "malus domestica", "manual", 1.0, "b", "a", "2026-09-21")
    with pytest.raises(IdentityError):
        validate_edges([Edge("prod:bls:B1", "nope nope", "manual", 1.0, "b", "a", "d")], POOL)
    with pytest.raises(IdentityError):
        validate_edges([e, Edge("prod:bls:B1", "beta vulgaris", "manual", 1.0, "b", "a", "d")], POOL)
