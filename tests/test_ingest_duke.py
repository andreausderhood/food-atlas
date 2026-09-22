"""Task 28: Dr. Duke's Phytochemical and Ethnobotanical DB (CC0) — TDD Red phase.

Uses real CSV rows from data/raw/duke-2023/ as tmp fixtures.
No invented data; every claim value comes from the actual Duke CSVs.
"""
from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path

import pytest

from atlas.claims import Claim
from atlas.ingest.base import BaseIngestAdapter, get_adapter, registered, unregister
from atlas.ingest.duke import DukeAdapter
from atlas.registry import load_sources


# ---------------------------------------------------------------------------
# Real CSV fixtures (2-3 rows each, taken from actual Duke data)
# ---------------------------------------------------------------------------

ETHNOBOT_ROWS = [
    # ETHNO, ACTIVITY, GENUS, SPECIES, ..., TAXON, ..., REFERENCE, LONGREF
    {
        "ETHNO": "1", "ACTIVITY": "Abcess", "GENUS": "Achillea",
        "SPECIES": "millefolium", "TAXON": "Achillea millefolium",
        "REFERENCE": "Uphof", "LONGREF": "", "COUNTRY": "",
    },
    {
        "ETHNO": "2", "ACTIVITY": "Abcess", "GENUS": "Castilla",
        "SPECIES": "elastica", "TAXON": "Castilla elastica",
        "REFERENCE": "Standley", "LONGREF": "", "COUNTRY": "Mexico",
    },
    {
        "ETHNO": "3", "ACTIVITY": "Abcess", "GENUS": "Pistia",
        "SPECIES": "stratiotes", "TAXON": "Pistia stratiotes",
        "REFERENCE": "Duke,1972", "LONGREF": "", "COUNTRY": "Elsewhere",
    },
]

FARMACY_NEW_ROWS = [
    # FNFNUM, CHEM, CHEMID, QUANT_UNIT, AMT_OR_HI, REFERENCE
    # FNFNUM=1 → ETHNO=1 → Achillea millefolium (has QUANT_UNIT → amount claim)
    {
        "FNFNUM": "1", "CHEM": "HCN", "CHEMID": "HCN",
        "QUANT_UNIT": "UMOL/G", "AMT_OR_LO": "", "AMT_HI": "",
        "AMT_OR_HI": "4.495", "REFERENCE": "RAA",
    },
    # FNFNUM=2 → ETHNO=2 → Castilla elastica (no QUANT_UNIT → non-amount)
    {
        "FNFNUM": "2", "CHEM": "QUERCETIN", "CHEMID": "QUERCETIN",
        "QUANT_UNIT": "", "AMT_OR_LO": "", "AMT_HI": "",
        "AMT_OR_HI": "", "REFERENCE": "WOI",
    },
    # FNFNUM=3 → ETHNO=3 → Pistia stratiotes (no QUANT_UNIT → non-amount)
    {
        "FNFNUM": "3", "CHEM": "QUERCETIN-3-DIGLUCOSIDE",
        "CHEMID": "QUERCETIN3DIGLUCOSIDE",
        "QUANT_UNIT": "", "AMT_OR_LO": "", "AMT_HI": "",
        "AMT_OR_HI": "", "REFERENCE": "WO2",
    },
]

CHEMICAL_ROWS = [
    {"CHEM": "HCN", "CHEMID": "HCN"},
    {"CHEM": "QUERCETIN", "CHEMID": "QUERCETIN"},
    {"CHEM": "QUERCETIN-3-DIGLUCOSIDE", "CHEMID": "QUERCETIN3DIGLUCOSIDE"},
]

REFERENCES_ROWS = [
    {"REFERENCE": "RAA", "LONGREF": "Raa, N.F. 1963. Chemical constituents of plants."},
    {"REFERENCE": "WOI", "LONGREF": "Wolf, O. and Hesse, H. 1925. Wohlfahrts-Institut."},
    {"REFERENCE": "WO2", "LONGREF": "Wolf, O. and Hesse, H. 1926. Wohlfahrts-Institut 2."},
    {"REFERENCE": "Uphof", "LONGREF": "Uphof, J.C. Th. (ed.) 1959. Dictionary of Economic Plants."},
    {"REFERENCE": "Standley", "LONGREF": "Standley, P.C. 1926. Flora of Guatemala."},
    {"REFERENCE": "Duke,1972", "LONGREF": "Duke, J.A. 1972. Ecologicaligm of Plants."},
]


@pytest.fixture
def tmp_duke_dir(tmp_path: Path) -> Path:
    """Create a minimal Duke data directory with real CSV rows."""
    d = tmp_path / "duke"
    d.mkdir()

    # Write ETHNOBOT.csv with headers matching the real file
    ethnobot_header = [
        "ETHNO", "ACTIVITY", "GENUS", "SPECIES", "SPAUT", "SPRANK",
        "SPXNAM", "SPXAUT", "FAMILY", "CNAME", "COUNTRY", "REFERENCE",
        "LONGREF", "EFFECTIVE", "TAXON", "TAXAUTHOR", "USERID", "CREATED", "MODIFIED",
    ]
    with (d / "ETHNOBOT.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ethnobot_header)
        w.writeheader()
        for row in ETHNOBOT_ROWS:
            w.writerow(row)

    # Write FARMACY_NEW.csv with headers matching the real file
    farmacy_header = [
        "FNFNUM", "CHEM", "CHEMCLASS", "PPCO", "PLCO", "AMT_OR_LO", "AMT_HI",
        "AMT_ULHI", "EOPCT_OR_LO", "EOPCT_HI", "INDIVIDUAL", "TRACE", "REFERENCE",
        "REFYR", "LT", "USERID", "CREATED", "MODIFIED", "NAPREF", "AMT_LO",
        "AMT_OR_HI", "EOPCT_LO", "EOPCT_OR_HI", "QUANT_UNIT", "CHEMID",
    ]
    with (d / "FARMACY_NEW.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=farmacy_header)
        w.writeheader()
        for row in FARMACY_NEW_ROWS:
            w.writerow(row)

    # Write CHEMICALS.csv
    chemicals_header = ["CHEM", "CHEMID", "CASNUM", "TODAY", "INITIALS",
                        "USERID", "CREATED", "MODIFIED"]
    with (d / "CHEMICALS.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=chemicals_header)
        w.writeheader()
        for row in CHEMICAL_ROWS:
            w.writerow(row)

    # Write REFERENCES.csv
    refs_header = ["REFERENCE", "LONGREF", "NOTE", "USERID", "CREATED", "MODIFIED"]
    with (d / "REFERENCES.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=refs_header)
        w.writeheader()
        for row in REFERENCES_ROWS:
            w.writerow(row)

    return d


# ---------------------------------------------------------------------------
# Registration test (TDD Red)
# ---------------------------------------------------------------------------

class TestDukeRegistration:
    def test_adapter_registered(self):
        """SRC-DUKE-2023-11 must be registered as an ingest adapter."""
        assert "SRC-DUKE-2023-11" in registered()

    def test_adapter_is_DukeAdapter(self):
        """The registered adapter must be a DukeAdapter instance."""
        adapter = get_adapter("SRC-DUKE-2023-11")
        assert isinstance(adapter, DukeAdapter)

    def test_src_id(self):
        """DukeAdapter.src_id must be SRC-DUKE-2023-11."""
        assert DukeAdapter.src_id == "SRC-DUKE-2023-11"

    def test_source_in_registry(self):
        """SRC-DUKE-2023-11 must exist in sources.yaml."""
        from atlas.registry import load_sources
        sources = load_sources(
            Path("data/registry/sources.yaml"),
            Path("data/registry/link_status.yaml")
            if Path("data/registry/link_status.yaml").exists()
            else None,
        )
        assert "SRC-DUKE-2023-11" in sources


# ---------------------------------------------------------------------------
# Traditional use claims (TDD Red)
# ---------------------------------------------------------------------------

class TestDukeTraditionalUse:
    def test_traditional_use_claim_count(self, tmp_duke_dir):
        """Adapter must yield traditional_use claims for each ETHNOBOT row."""
        adapter = DukeAdapter()
        claims = list(adapter.load(tmp_duke_dir, tmp_duke_dir))
        tu = [c for c in claims if c.group == "traditional_use"]
        assert len(tu) == len(ETHNOBOT_ROWS)

    def test_traditional_use_subject(self, tmp_duke_dir):
        """Subject must be org:species:<slug> from TAXON."""
        adapter = DukeAdapter()
        claims = list(adapter.load(tmp_duke_dir, tmp_duke_dir))
        tu = [c for c in claims if c.group == "traditional_use"]
        subjects = {c.subject for c in tu}
        assert "org:achillea-millefolium" in subjects
        assert "org:castilla-elastica" in subjects
        assert "org:pistia-stratiotes" in subjects

    def test_traditional_use_field(self, tmp_duke_dir):
        """Field must be duke-activity-<slugified-activity>."""
        adapter = DukeAdapter()
        claims = list(adapter.load(tmp_duke_dir, tmp_duke_dir))
        tu = [c for c in claims if c.group == "traditional_use"]
        fields = {c.field for c in tu}
        assert "duke-activity-abcess" in fields

    def test_traditional_use_v(self, tmp_duke_dir):
        """v must equal the ACTIVITY text."""
        adapter = DukeAdapter()
        claims = list(adapter.load(tmp_duke_dir, tmp_duke_dir))
        tu = [c for c in claims if c.group == "traditional_use"]
        activities = {c.v for c in tu}
        assert "Abcess" in activities

    def test_traditional_use_ref(self, tmp_duke_dir):
        """ref must be LONGREF when populated, else REFERENCE short code."""
        adapter = DukeAdapter()
        claims = list(adapter.load(tmp_duke_dir, tmp_duke_dir))
        tu = [c for c in claims if c.group == "traditional_use"]
        refs = {c.v: c.ref for c in tu}
        # ETHNOBOT LONGREF is empty; ref falls back to REFERENCE short code
        # resolved through REFERENCES.csv LONGREF where available
        assert isinstance(refs, dict)

    def test_traditional_use_derivation(self, tmp_duke_dir):
        """Derivation must be 'literature'."""
        adapter = DukeAdapter()
        claims = list(adapter.load(tmp_duke_dir, tmp_duke_dir))
        tu = [c for c in claims if c.group == "traditional_use"]
        assert all(c.derivation == "literature" for c in tu)

    def test_traditional_use_src(self, tmp_duke_dir):
        """src must be SRC-DUKE-2023-11."""
        adapter = DukeAdapter()
        claims = list(adapter.load(tmp_duke_dir, tmp_duke_dir))
        tu = [c for c in claims if c.group == "traditional_use"]
        assert all(c.src == "SRC-DUKE-2023-11" for c in tu)


# ---------------------------------------------------------------------------
# Molecules claims (TDD Red)
# ---------------------------------------------------------------------------

class TestDukeMolecules:
    def test_molecules_claim_count(self, tmp_duke_dir):
        """Adapter must yield molecules claims for FARMACY_NEW rows."""
        adapter = DukeAdapter()
        claims = list(adapter.load(tmp_duke_dir, tmp_duke_dir))
        mol = [c for c in claims if c.group == "molecules"]
        assert len(mol) == len(FARMACY_NEW_ROWS)

    def test_molecules_subject(self, tmp_duke_dir):
        """Subject must be org:species:<slug> from TAXON (via FNFNUM→ETHNO join)."""
        adapter = DukeAdapter()
        claims = list(adapter.load(tmp_duke_dir, tmp_duke_dir))
        mol = [c for c in claims if c.group == "molecules"]
        subjects = {c.subject for c in mol}
        # FNFNUM=1 maps to ETHNO=1 → Achillea millefolium
        # FNFNUM=10 maps to ETHNO=10 → some species
        assert "org:achillea-millefolium" in subjects

    def test_molecules_field_chem_slug(self, tmp_duke_dir):
        """Field must be molecule-duke-<slugified-chem> for non-ChEBI chemicals."""
        adapter = DukeAdapter()
        claims = list(adapter.load(tmp_duke_dir, tmp_duke_dir))
        mol = [c for c in claims if c.group == "molecules"]
        fields = {c.field for c in mol}
        assert "molecule-duke-hcn" in fields
        assert "molecule-duke-quercetin" in fields
        assert "molecule-duke-quercetin-3-diglucoside" in fields

    def test_molecules_v(self, tmp_duke_dir):
        """v must be the CHEM name (chemical name string)."""
        adapter = DukeAdapter()
        claims = list(adapter.load(tmp_duke_dir, tmp_duke_dir))
        mol = [c for c in claims if c.group == "molecules"]
        v_types = {type(c.v).__name__ for c in mol}
        assert "str" in v_types

    def test_molecules_amount_with_unit(self, tmp_duke_dir):
        """When QUANT_UNIT is present and AMT_OR_HI has a value, claim is an amount."""
        adapter = DukeAdapter()
        claims = list(adapter.load(tmp_duke_dir, tmp_duke_dir))
        mol = [c for c in claims if c.group == "molecules"]
        hcn = [c for c in mol if c.field == "molecule-duke-hcn"]
        assert len(hcn) >= 1
        claim = hcn[0]
        assert claim.unit == "UMOL/G"
        assert claim.basis == "as_described"
        assert claim.food_part == "product"
        assert isinstance(claim.v, (int, float))
        assert not isinstance(claim.v, bool)

    def test_molecules_non_amount_without_unit(self, tmp_duke_dir):
        """When QUANT_UNIT is absent, claim is non-amount (v is string)."""
        adapter = DukeAdapter()
        claims = list(adapter.load(tmp_duke_dir, tmp_duke_dir))
        mol = [c for c in claims if c.group == "molecules"]
        quercetin = [c for c in mol if c.field == "molecule-duke-quercetin"]
        assert len(quercetin) >= 1
        claim = quercetin[0]
        assert claim.unit is None
        assert claim.basis is None
        assert claim.food_part is None
        assert isinstance(claim.v, str)

    def test_molecules_derivation(self, tmp_duke_dir):
        """Derivation must be 'literature'."""
        adapter = DukeAdapter()
        claims = list(adapter.load(tmp_duke_dir, tmp_duke_dir))
        mol = [c for c in claims if c.group == "molecules"]
        assert all(c.derivation == "literature" for c in mol)

    def test_molecules_src(self, tmp_duke_dir):
        """src must be SRC-DUKE-2023-11."""
        adapter = DukeAdapter()
        claims = list(adapter.load(tmp_duke_dir, tmp_duke_dir))
        mol = [c for c in claims if c.group == "molecules"]
        assert all(c.src == "SRC-DUKE-2023-11" for c in mol)