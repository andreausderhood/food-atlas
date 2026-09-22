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


def test_bls_bulk_product_claims_for_every_row(project, bls_dir):
    """Rule 6': every BLS row yields prod:bls:<code> claims with as_described/product, even unmapped rows."""
    adapter = BlsAdapter()
    claims = list(adapter.load(project, bls_dir))
    bulk = [c for c in claims if c.subject == "prod:bls:F999999"]
    assert len(bulk) >= 2                       # unmapped row still gets product claims
    for c in bulk:
        assert c.basis == "as_described" and c.food_part == "product"


def test_bls_dash_cells_are_skipped(project, bls_dir):
    """'-' means 'ohne Angabe' — no claim, no reject; it is not a measurement."""
    adapter = BlsAdapter()
    claims = list(adapter.load(project, bls_dir))
    assert all(c.v != "-" for c in claims)


def test_bls_trace_cells_carry_TR_as_rejectables(project, bls_dir):
    """'TR' (Spuren) is yielded honestly; the contract rejects it as non-numeric."""
    from openpyxl import load_workbook
    path = next(bls_dir.rglob("BLS_4_0_Daten_*.xlsx"))
    wb = load_workbook(path)
    ws = wb.active
    ws.append(["G000000", "Spinat roh", "Spinach raw", 21, "Analyse", "R4", "TR", "Spuren", "R5"])
    wb.save(path)
    wb.close()
    claims = list(BlsAdapter().load(project, bls_dir))
    tr = [c for c in claims if c.v == "TR"]
    assert len(tr) == 1                          # only the VITC cell carries TR
    c = tr[0]
    assert c.subject == "prod:bls:G000000"
    assert c.derivation == "trace"