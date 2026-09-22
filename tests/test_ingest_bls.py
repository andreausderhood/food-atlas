"""TDD tests for BLS 4.0 streaming adapter (Task 23)."""
from __future__ import annotations

import pytest

from atlas.claims import UnmappedDerivation
from atlas.ingest.base import registered, get_adapter
from atlas.ingest.bls_bulk import BlsAdapter


def test_bls_adapter_is_registered():
    """BlsAdapter must self-register under SRC-BLS-4.0."""
    assert "SRC-BLS-4.0" in registered()


def test_bls_adapter_src_id():
    """src_id must be SRC-BLS-4.0."""
    adapter = BlsAdapter()
    assert adapter.src_id == "SRC-BLS-4.0"


def test_bls_adapter_load_is_lazy(project, bls_dir):
    """load() must return a lazy iterator, not a list."""
    adapter = BlsAdapter()
    claims = adapter.load(project, bls_dir)
    assert hasattr(claims, "__next__") or hasattr(claims, "__iter__")
    # Must not have consumed the iterator yet
    assert not isinstance(claims, list)


def test_bls_adapter_yields_claims(project, bls_dir):
    """load() must yield Claim objects with correct fields."""
    adapter = BlsAdapter()
    claims = list(adapter.load(project, bls_dir))
    # At least the apple energy claim should be present
    assert len(claims) >= 1
    c = claims[0]
    assert c.subject == "food:apple"
    assert c.field.startswith("nutrient:bls:")
    assert c.basis == "fresh_weight"
    assert c.food_part == "whole"
    assert c.src == "SRC-BLS-4.0"
    assert c.derivation == "aggregated"


def test_bls_adapter_rejects_unknown_origin(project, bls_dir):
    """Unmapped Datenherkunft must raise UnmappedDerivation."""
    from openpyxl import load_workbook
    path = next(bls_dir.rglob("BLS_4_0_Daten_*.xlsx"))
    wb = load_workbook(path)
    ws = wb.active
    ws.cell(row=2, column=5).value = "Bauchgefühl"
    wb.save(path)
    wb.close()
    adapter = BlsAdapter()
    with pytest.raises(UnmappedDerivation, match="Bauchgefühl"):
        list(adapter.load(project, bls_dir))


def test_bls_adapter_maps_german_names(project, bls_dir):
    """BLS apple code F110100 must appear in claim refs."""
    adapter = BlsAdapter()
    claims = list(adapter.load(project, bls_dir))
    apple_refs = [c.ref for c in claims if "F110100" in (c.ref or "")]
    assert len(apple_refs) >= 1, "BLS apple code F110100 should appear in refs"