"""TDD Red Phase: tests for FoodAtlas v4.11 molecules bulk adapter."""
import json
import duckdb
from pathlib import Path


def _make_foodatlas_dir(tmp_path):
    """Create a minimal FoodAtlas parquet dataset for testing."""
    d = tmp_path / "fa"
    d.mkdir()
    con = duckdb.connect()

    def write(name, select):
        con.execute(f"COPY ({select}) TO '{d / name}' (FORMAT PARQUET)")

    # Entities: 2 foods, 3 chemicals (some with chebi/pubchem, some with only flavor descriptors)
    write("entities.parquet", """
        select * from (values
            ('f1', 'food', 'apple', '', '[]', '{}', '{}'),
            ('f2', 'food', 'banana', '', '[]', '{}', '{}'),
            ('c1', 'chemical', 'l-ascorbic acid', '', '[]', '{"chebi": [29073], "pubchem_compound": [54670067]}', '{"flavor_descriptors": []}'),
            ('c2', 'chemical', 'quercetin', '', '[]', '{"chebi": [16243], "pubchem_compound": [5280343]}', '{"flavor_descriptors": ["bitter"]}'),
            ('c3', 'chemical', 'sulindac', '', '[]', '{"chebi": [9352]}', '{"flavor_descriptors": []}')
        ) t(foodatlas_id, entity_type, common_name, scientific_name, synonyms, external_ids, attributes)
    """)

    # Triplets: r1=contains (food→chemical), r2=is_a
    write("triplets.parquet", """
        select * from (values
            ('f1', 'r1', 'c1', '', '["a1"]'),
            ('f1', 'r1', 'c2', '', '["a2"]'),
            ('f2', 'r1', 'c3', '', '["a3"]'),
            ('c1', 'r2', 'c2', '', '["a4"]')
        ) t(head_id, relationship_id, tail_id, source, attestation_ids)
    """)

    # Attestations: a1 has numeric amount, a2 is non-numeric (presence), a3 has numeric, a4 is non-numeric
    write("attestations.parquet", """
        select * from (values
            ('a1', 'v1', 'fdc', 9.0, 'mg/100g'),
            ('a2', 'v2', 'lit2kg:claude-opus-4-8', null, null),
            ('a3', 'v3', 'fdc', 4.6, 'mg/100g'),
            ('a4', 'v4', 'lit2kg:claude-opus-4-8', null, null)
        ) t(attestation_id, evidence_id, source, conc_value, conc_unit)
    """)

    # Evidence
    write("evidence.parquet", """
        select * from (values
            ('v1', 'fdc', '{"source": "fdc"}'),
            ('v2', 'pubmed', '{"source": "pubmed"}'),
            ('v3', 'fdc', '{"source": "fdc"}'),
            ('v4', 'pubmed', '{"source": "pubmed"}')
        ) t(evidence_id, source_type, reference)
    """)

    # Relationships
    write("relationships.parquet", """
        select * from (values
            ('r1', 'contains'),
            ('r2', 'is_a')
        ) t(foodatlas_id, name)
    """)

    con.close()
    return d


class TestFoodAtlasBulkAdapterRegistered:
    """Adapter must be registered under SRC-FOODATLAS-V4.11."""

    def test_adapter_registered(self):
        from atlas.ingest.base import registered
        assert "SRC-FOODATLAS-V4.11" in registered()

    def test_source_short_identity(self):
        from atlas.unified.identity import SOURCE_SHORT
        assert SOURCE_SHORT["SRC-FOODATLAS-V4.11"] == "fa"


class TestFoodAtlasBulkMoleculesClaims:
    """Adapter produces molecules claims from FoodAtlas parquet data."""

    def test_claims_from_real_parquet(self, tmp_path):
        from atlas.ingest.bulk_foodatlas import BulkFoodAtlasAdapter
        from atlas.claims import Claim

        fa_dir = _make_foodatlas_dir(tmp_path)
        adapter = BulkFoodAtlasAdapter("SRC-FOODATLAS-V4.11")
        claims = list(adapter.load(fa_dir, fa_dir))

        # At least the numeric amount claims should be produced
        amount_claims = [c for c in claims if c.is_amount]
        assert len(amount_claims) >= 2, f"Expected at least 2 amount claims, got {len(amount_claims)}"

        # Check that molecule:chebi and molecule:pubchem fields are used
        fields = {c.field for c in claims}
        assert any(f.startswith("molecule:chebi:") for f in fields), f"No molecule:chebi fields found in {fields}"
        assert any(f.startswith("molecule:pubchem:") for f in fields), f"No molecule:pubchem fields found in {fields}"

    def test_claims_subject_prefix(self, tmp_path):
        from atlas.ingest.bulk_foodatlas import BulkFoodAtlasAdapter

        fa_dir = _make_foodatlas_dir(tmp_path)
        adapter = BulkFoodAtlasAdapter("SRC-FOODATLAS-V4.11")
        claims = list(adapter.load(fa_dir, fa_dir))

        # All subjects should use prod:fa: prefix
        for c in claims:
            assert c.subject.startswith("prod:fa:"), f"Subject {c.subject} does not start with prod:fa:"

    def test_amount_claims_have_required_fields(self, tmp_path):
        from atlas.ingest.bulk_foodatlas import BulkFoodAtlasAdapter

        fa_dir = _make_foodatlas_dir(tmp_path)
        adapter = BulkFoodAtlasAdapter("SRC-FOODATLAS-V4.11")
        claims = list(adapter.load(fa_dir, fa_dir))

        for c in claims:
            if c.is_amount:
                assert c.basis == "as_described", f"Amount claim {c.field} has basis={c.basis!r}, expected as_described"
                assert c.food_part == "product", f"Amount claim {c.field} has food_part={c.food_part!r}, expected product"
                assert c.unit is not None, f"Amount claim {c.field} has no unit"

    def test_non_numeric_presence_claims(self, tmp_path):
        from atlas.ingest.bulk_foodatlas import BulkFoodAtlasAdapter

        fa_dir = _make_foodatlas_dir(tmp_path)
        adapter = BulkFoodAtlasAdapter("SRC-FOODATLAS-V4.11")
        claims = list(adapter.load(fa_dir, fa_dir))

        # Non-numeric claims (v is a string like "present") should exist
        presence_claims = [c for c in claims if not c.is_amount and isinstance(c.v, str)]
        assert len(presence_claims) >= 1, f"Expected at least 1 presence claim, got {len(presence_claims)}"

        # Presence claims should NOT have unit/basis/food_part (not amount claims)
        for c in presence_claims:
            assert c.group == "molecules", f"Presence claim {c.field} has group={c.group!r}, expected molecules"

    def test_chebi_pubchem_unpacked_separately(self, tmp_path):
        from atlas.ingest.bulk_foodatlas import BulkFoodAtlasAdapter

        fa_dir = _make_foodatlas_dir(tmp_path)
        adapter = BulkFoodAtlasAdapter("SRC-FOODATLAS-V4.11")
        claims = list(adapter.load(fa_dir, fa_dir))

        # c1 has both chebi:29073 and pubchem:54670067 — should produce separate claims
        chebi_claims = [c for c in claims if c.field == "molecule:chebi:29073"]
        pubchem_claims = [c for c in claims if c.field == "molecule:pubchem:54670067"]
        assert len(chebi_claims) >= 1, "Expected at least one claim for chebi:29073"
        assert len(pubchem_claims) >= 1, "Expected at least one claim for pubchem:54670067"

    def test_flavor_descriptors_not_claims(self, tmp_path):
        from atlas.ingest.bulk_foodatlas import BulkFoodAtlasAdapter

        fa_dir = _make_foodatlas_dir(tmp_path)
        adapter = BulkFoodAtlasAdapter("SRC-FOODATLAS-V4.11")
        claims = list(adapter.load(fa_dir, fa_dir))

        # c2 (quercetin) has flavor_descriptors=["bitter"] — these should NOT become claims
        flavor_claims = [c for c in claims if "bitter" in str(c.v)]
        assert len(flavor_claims) == 0, f"Flavor descriptors should not be claims, found: {flavor_claims}"

    def test_group_is_molecules(self, tmp_path):
        from atlas.ingest.bulk_foodatlas import BulkFoodAtlasAdapter

        fa_dir = _make_foodatlas_dir(tmp_path)
        adapter = BulkFoodAtlasAdapter("SRC-FOODATLAS-V4.11")
        claims = list(adapter.load(fa_dir, fa_dir))

        for c in claims:
            assert c.group == "molecules", f"Claim {c.field} has group={c.group!r}, expected molecules"
