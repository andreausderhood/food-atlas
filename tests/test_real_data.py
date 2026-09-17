from pathlib import Path

import pytest

from atlas.foods import load_foods, load_organisms, load_processes

REPO = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.data
FDC = {"data/raw/fdc-foundation": "SRC-FDC-FOUNDATION-2026-04", "data/raw/fdc-srlegacy": "SRC-FDC-SRLEGACY-2018-04"}


def need(rel: str) -> Path:
    path = REPO / rel
    if not path.exists():
        pytest.skip(f"{rel} not downloaded")
    return path


@pytest.fixture(scope="module")
def nodes():
    reg = REPO / "data/registry"
    orgs, procs = load_organisms(reg / "organisms.yaml"), load_processes(reg / "processes.yaml")
    return load_foods(reg / "foods.yaml", orgs, procs)[0]


def test_fdc_maps_pilot_foods_and_classifies_every_used_derivation(nodes):
    from atlas.ingest.fdc import load_fdc
    subjects = set()
    for rel, src in FDC.items():
        claims, _ = load_fdc(need(rel), src, nodes)  # raises on unmapped derivations or bad mappings
        subjects |= {c.subject for c in claims}
    expected = {n.id for n in nodes.values() if n.fdc_match}
    assert expected <= subjects, f"no FDC rows for {sorted(expected - subjects)}"


def test_foundation_shared_codebook_and_gaps_are_explicit(nodes):
    from atlas.claims import DERIVATION_TIER
    from atlas.ingest.fdc import load_fdc
    folder = need("data/raw/fdc-foundation")
    assert not list(folder.rglob("food_nutrient_derivation.csv"))  # precondition of this regression
    claims, _ = load_fdc(folder, FDC["data/raw/fdc-foundation"], nodes)
    derivations = {c.derivation for c in claims}
    assert derivations <= {"analytical", "calculated", "unverified"}
    assert {"analytical", "calculated", "unverified"} <= derivations  # all three documented ID classes occur
    unverified = [c for c in claims if c.derivation == "unverified"]
    assert all(DERIVATION_TIER[c.derivation] == 5 for c in unverified)  # gaps, never promoted
    assert all("missing_derivation" in c.flags and "missing_derivation_table" in c.flags for c in unverified)
    assert all(c.method and "FDC derivation ID" in c.method for c in unverified)
    mapped = [c for c in claims if c.derivation != "unverified"]
    assert all(c.method and "SR Legacy 2018-04 lookup" in c.method for c in mapped)
    assert all(c.ref and c.ref.startswith("fdc:") for c in claims)


def test_foundation_publishes_only_foundation_food_rows(nodes):
    from atlas.ingest.fdc import load_fdc
    claims, _ = load_fdc(need("data/raw/fdc-foundation"), FDC["data/raw/fdc-foundation"], nodes)
    assert claims  # sample/acquisition rows (75k+) must not leak in as duplicate subjects
    from atlas.ingest.fdc import find_csv_dir, read_csv_rows
    published = {f"fdc:{r['fdc_id']}" for r in read_csv_rows(
        find_csv_dir(need("data/raw/fdc-foundation")) / "food.csv")
        if r["data_type"] == "foundation_food"}
    assert {c.ref for c in claims} <= published


def test_honeycrisp_real_sucrose_spread_and_vitamin_c_gap(nodes):
    from atlas.ingest.fdc import load_fdc
    claims, _ = load_fdc(need("data/raw/fdc-foundation"), FDC["data/raw/fdc-foundation"], nodes)
    apple = [c for c in claims if c.subject == "food:apple.honeycrisp"]
    assert apple
    assert not any(c.field == "nutrient:fdc:1162" for c in apple)  # no Vitamin C measurement
    sucrose = next(c for c in apple if c.field == "nutrient:fdc:1010")
    assert sucrose.derivation == "analytical"
    assert (sucrose.v, sucrose.unit, sucrose.n, sucrose.v_min, sucrose.v_max) == (1.06, "g", 2, 0.99, 1.13)


def test_bls_layout_and_pilot_codes(nodes):
    from openpyxl import load_workbook
    from atlas.ingest.bls import find_workbook, load_bls, nutrient_columns, parse_value_header
    root = need("data/raw/bls")
    ws = load_workbook(find_workbook(root), read_only=True).worksheets[0]
    headers = ["" if h is None else str(h) for h in next(ws.iter_rows(max_row=1, values_only=True))]
    triples = nutrient_columns(headers)
    assert len(triples) == 138
    assert sum(parse_value_header(headers[v])[2] is not None for v, _, _ in triples) >= 130
    claims, _, names_de = load_bls(root, "SRC-BLS-4.0", nodes)
    mapped = {n.id for n in nodes.values() if n.bls_codes}
    assert mapped and mapped <= set(names_de)

def test_foodatlas_real_claims_preserve_contract(nodes):
    from atlas.ingest.foodatlas import load_aliases, load_foodatlas
    bundle = need("data/raw/foodatlas/foodatlas-v4.11")
    claims, molecules = load_foodatlas(bundle, "SRC-FOODATLAS-V4.11", nodes, load_aliases(REPO / "data/registry/molecule_aliases.yaml"))
    presence = [c for c in claims if c.v == "present"]
    amounts = [c for c in claims if c.v != "present"]
    assert presence and amounts and molecules
    assert len({(c.subject, c.field) for c in presence}) == len(presence)
    assert all(c.basis is None and c.derivation == "extracted" for c in amounts)
    assert all(c.flags == ("llm_extracted",) for c in claims)
    assert all(not c.ref or all(ref.startswith("PMC") for ref in c.ref.split(", ")) for c in claims)


def test_foodatlas_pilot_is_ctd_free_and_deduplicated(nodes):
    from atlas.ingest.foodatlas import load_aliases, load_foodatlas
    bundle = need("data/raw/foodatlas/foodatlas-v4.11")
    claims, molecules = load_foodatlas(bundle, "SRC-FOODATLAS-V4.11", nodes, load_aliases(REPO / "data/registry/molecule_aliases.yaml"))
    apple = {c.field for c in claims if c.subject == "food:apple" and c.v == "present"}
    assert len(apple) > 100
    plain_vitamin_c = {"vitamin c", "l-ascorbic acid", "l-ascorbate", "ascorbic acid", "ascorbate"}
    keys = {k for k, m in molecules.items() if m["name"].lower() in plain_vitamin_c}
    assert keys <= {"nutrient:fdc:1162"}, keys
    assert all(c.flags == ("llm_extracted",) for c in claims)
