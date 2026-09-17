from atlas.ingest.foodatlas import load_aliases, load_foodatlas, molecule_key


def test_molecule_key_preference():
    assert molecule_key("x", {"fdc_nutrient": [1162], "chebi": [29073]}, {}) == "nutrient:fdc:1162"
    assert molecule_key("x", {"chebi": [16243], "pubchem_compound": [5280343]}, {}) == "CHEBI:16243"
    assert molecule_key("x", {"pubchem_compound": [1]}, {}) == "PUBCHEM:1"
    assert molecule_key("x", {}, {}) == "FA:x"
    assert molecule_key("x", {"chebi": [1]}, {"x": "nutrient:fdc:9"}) == "nutrient:fdc:9"


def rewrite_parquet(path, select):
    import duckdb
    from atlas.ingest.foodatlas import sql_path
    with duckdb.connect() as con:
        con.execute(f"create table original as select * from read_parquet({sql_path(path)})")
        con.execute(f"copy ({select}) to {sql_path(path)} (format parquet)")


def test_ctd_evidence_is_excluded_even_when_attestation_says_literature(foodatlas_dir, mini_nodes):
    rewrite_parquet(foodatlas_dir / "evidence.parquet", """
        select evidence_id, case when evidence_id='v4' then 'ctd' else source_type end as source_type,
        reference from original
    """)
    claims, molecules = load_foodatlas(foodatlas_dir, "SRC-FA", mini_nodes, {})
    assert not any(c.subject == "food:apple.honeycrisp" for c in claims)
    assert "CHEBI:16243" not in molecules


def test_pmc_prefix_is_normalized_and_evidence_text_never_published(foodatlas_dir, mini_nodes):
    from dataclasses import asdict
    import json
    rewrite_parquet(foodatlas_dir / "evidence.parquet", """
        select evidence_id, source_type,
        case when evidence_id='v1' then '{"pmcid":"PMC111", "text":"PRIVATE_EVIDENCE_SENTENCE"}'
        else reference end as reference from original
    """)
    claims, molecules = load_foodatlas(foodatlas_dir, "SRC-FA", mini_nodes, load_aliases(foodatlas_dir / "aliases.yaml"))
    c = next(c for c in claims if c.subject == "food:apple" and c.v == "present")
    assert c.ref == "PMC111, PMC222, PMC333"
    assert "PRIVATE_EVIDENCE_SENTENCE" not in json.dumps([list(map(asdict, claims)), molecules])


def test_search_foodatlas(project):
    from atlas.curate import search_foodatlas
    assert set(search_foodatlas(project, "APPLE")) == {"e897\tapple", "e1536\tHoneycrisp apple"}
    assert search_foodatlas(project, "' OR true --") == []


def test_load_foodatlas(foodatlas_dir, mini_nodes):
    aliases = load_aliases(foodatlas_dir / "aliases.yaml")
    claims, molecules = load_foodatlas(foodatlas_dir, "SRC-FA", mini_nodes, aliases)
    presence = {(c.subject, c.field): c for c in claims if c.v == "present"}
    amounts = [c for c in claims if c.v != "present"]

    vitc = presence[("food:apple", "contains:nutrient:fdc:1162")]
    assert vitc.ref == "PMC111, PMC222, PMC333" and vitc.n == 3  # fdc row a5 not read
    assert vitc.flags == ("llm_extracted",) and vitc.derivation == "extracted"
    assert ("food:apple.honeycrisp", "contains:CHEBI:16243") in presence
    assert len(presence) == 2  # the r3 (CTD) row is never read

    assert len(amounts) == 1
    assert (amounts[0].v, amounts[0].basis, amounts[0].unit) == (9.0, None, "mg/100g")

    assert set(molecules) == {"nutrient:fdc:1162", "CHEBI:16243"}
    assert molecules["nutrient:fdc:1162"]["foodatlas_ids"] == ["c1", "c2", "c3"]
    assert molecules["CHEBI:16243"]["flavor"] == ["bitter"]
