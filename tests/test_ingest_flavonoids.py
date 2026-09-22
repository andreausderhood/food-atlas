"""Task 29: USDA Expanded Flavonoid Database R1.1 — streaming adapter tests (TDD red)."""
from __future__ import annotations

import csv
from collections.abc import Iterator
from pathlib import Path

import pytest

from atlas.claims import Claim
from atlas.ingest.base import get_adapter, registered, unregister
from atlas.ingest.flavonoids import FlavonoidAdapter

SOURCE_ID = "SRC-USDA-FLAVONOID-EXP-1.1"

# Real rows from the actual flavonoid database (never invented values).
# Row 1: non-zero, borrowed derivation (BFSN)
REAL_NONZERO_ROW = {
    "NDB_No": "01102",
    "Nutr_No": "749",
    "Flav_Val": "0.81",
    "Src_Cd": "4",
    "Deriv_Cd": "BFSN",
    "Ref_NDB_No": "09266",
}
# Row 2: zero value, assumed-zero derivation (Z)
REAL_ZERO_ROW = {
    "NDB_No": "01001",
    "Nutr_No": "710",
    "Flav_Val": "0",
    "Src_Cd": "7",
    "Deriv_Cd": "Z",
    "Ref_NDB_No": "",
}
# Row 3: analytical derivation (A)
REAL_ANALYTICAL_ROW = {
    "NDB_No": "01103",
    "Nutr_No": "770",
    "Flav_Val": "0.01",
    "Src_Cd": "1",
    "Deriv_Cd": "A",
    "Ref_NDB_No": "",
}

FOOD_DES_ROWS = [
    {"NDB_No": "01001", "FdGrp_Cd": "0100", "Long_Desc": "Butter, salted"},
    {"NDB_No": "01102", "FdGrp_Cd": "0100", "Long_Desc": "Milk, chocolate, fluid, commercial, whole, with added vitamin A and vitamin D"},
    {"NDB_No": "01103", "FdGrp_Cd": "0100", "Long_Desc": "Milk, chocolate, fluid, commercial, reduced fat, with added vitamin A and vitamin D"},
]

NUTR_DEF_ROWS = [
    {"Nutr_No": "710", "Flav_Class": "Isoflavones", "Nutrient name": "Daidzein", "Tagname": "DDZEIN", "Unit": "mg", "Decimal": "2"},
    {"Nutr_No": "749", "Flav_Class": "Flavan-3-ols", "Nutrient name": "(+)-Catechin", "Tagname": "", "Unit": "mg", "Decimal": "2"},
    {"Nutr_No": "770", "Flav_Class": "Flavones", "Nutrient name": "Apigenin", "Tagname": "APIGEN", "Unit": "mg", "Decimal": "2"},
]


def _write_csv(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def _make_flavonoid_dir(root: Path) -> Path:
    d = root / "flavonoid-exp-1.1"
    d.mkdir(parents=True)
    _write_csv(d / "FOOD_DES.csv",
               ["NDB_No", "FdGrp_Cd", "Long_Desc"],
               FOOD_DES_ROWS)
    _write_csv(d / "NUTR_DEF.csv",
               ["Nutr_No", "Flav_Class", "Nutrient name", "Tagname", "Unit", "Decimal"],
               NUTR_DEF_ROWS)
    _write_csv(d / "FLAV_DAT.csv",
               ["NDB_No", "Nutr_No", "Flav_Val", "Src_Cd", "Deriv_Cd", "Ref_NDB_No"],
               [REAL_NONZERO_ROW, REAL_ZERO_ROW, REAL_ANALYTICAL_ROW])
    _write_csv(d / "DERIV_CD.csv",
               ["Deriv_CD", "Deriv_Desc"],
               [{"Deriv_CD": "A", "Deriv_Desc": "Analytical data"},
                {"Deriv_CD": "BFSN", "Deriv_Desc": "Based on another form"},
                {"Deriv_CD": "Z", "Deriv_Desc": "Assumed zero"}])
    _write_csv(d / "SRC_CD.csv",
               ["Src_Cd", "SrcCd_Desc"],
               [{"Src_Cd": "1", "SrcCd_Desc": "Analytical"},
                {"Src_Cd": "4", "SrcCd_Desc": "Calculated or imputed"},
                {"Src_Cd": "7", "SrcCd_Desc": "Assumed zero"}])
    _write_csv(d / "FD_GROUP.csv",
               ["FdGrp_Cd", "FdGrp_Desc"],
               [{"FdGrp_Cd": "0100", "FdGrp_Desc": "Dairy and egg products"}])
    return d


@pytest.fixture
def clean_registry():
    before = set(registered())
    yield
    for sid in set(registered()) - before:
        unregister(sid)


@pytest.fixture
def flavonoid_root(tmp_path):
    return _make_flavonoid_dir(tmp_path)


class TestFlavonoidAdapterRegistration:
    def test_adapter_is_registered(self, clean_registry):
        adapter = FlavonoidAdapter()
        assert adapter.src_id == SOURCE_ID
        assert SOURCE_ID in registered()

    def test_adapter_prefix(self, clean_registry):
        adapter = FlavonoidAdapter()
        assert adapter.prefix == "prod:flav:"


class TestFlavonoidClaimShape:
    def test_nonzero_claim_has_correct_shape(self, flavonoid_root):
        adapter = FlavonoidAdapter()
        claims = list(adapter.load(flavonoid_root, flavonoid_root))
        nonzero = [c for c in claims if c.field == "molecule:flav:749"]
        assert len(nonzero) >= 1
        c = nonzero[0]
        assert c.subject == "prod:flav:01102"
        assert c.group == "molecules"
        assert c.field == "molecule:flav:749"
        assert c.v == 0.81
        assert c.unit == "mg"
        assert c.basis == "as_described"
        assert c.food_part == "product"
        assert c.derivation == "borrowed"
        assert c.src == SOURCE_ID

    def test_zero_claim_included_honestly(self, flavonoid_root):
        adapter = FlavonoidAdapter()
        claims = list(adapter.load(flavonoid_root, flavonoid_root))
        zero = [c for c in claims if c.field == "molecule:flav:710" and c.v == 0.0]
        assert len(zero) >= 1, "Flav_Val=0 must be included as an honest claim, not skipped"
        c = zero[0]
        assert c.derivation == "assumed_zero"
        assert c.subject == "prod:flav:01001"
        assert c.unit == "mg"
        assert c.basis == "as_described"
        assert c.food_part == "product"

    def test_analytical_claim_derivation(self, flavonoid_root):
        adapter = FlavonoidAdapter()
        claims = list(adapter.load(flavonoid_root, flavonoid_root))
        analytical = [c for c in claims if c.field == "molecule:flav:770"]
        assert len(analytical) >= 1
        c = analytical[0]
        assert c.derivation == "analytical"
        assert c.v == 0.01
        assert c.subject == "prod:flav:01103"

    def test_claims_are_amount_claims(self, flavonoid_root):
        adapter = FlavonoidAdapter()
        claims = list(adapter.load(flavonoid_root, flavonoid_root))
        assert len(claims) == 3
        assert all(c.is_amount for c in claims)

    def test_deriv_cd_bfsn_maps_to_borrowed(self, flavonoid_root):
        adapter = FlavonoidAdapter()
        claims = list(adapter.load(flavonoid_root, flavonoid_root))
        bfsn = [c for c in claims if c.derivation == "borrowed"]
        assert len(bfsn) >= 1

    def test_deriv_cd_z_maps_to_assumed_zero(self, flavonoid_root):
        adapter = FlavonoidAdapter()
        claims = list(adapter.load(flavonoid_root, flavonoid_root))
        assumed = [c for c in claims if c.derivation == "assumed_zero"]
        assert len(assumed) >= 1

    def test_deriv_cd_a_maps_to_analytical(self, flavonoid_root):
        adapter = FlavonoidAdapter()
        claims = list(adapter.load(flavonoid_root, flavonoid_root))
        analytical = [c for c in claims if c.derivation == "analytical"]
        assert len(analytical) >= 1

    def test_subject_uses_plus_ndb_no(self, flavonoid_root):
        adapter = FlavonoidAdapter()
        claims = list(adapter.load(flavonoid_root, flavonoid_root))
        assert all(c.subject.startswith("prod:flav:") for c in claims)

    def test_field_uses_plus_nutr_no(self, flavonoid_root):
        adapter = FlavonoidAdapter()
        claims = list(adapter.load(flavonoid_root, flavonoid_root))
        assert all(c.field.startswith("molecule:flav:") for c in claims)

    def test_v_num_from_flav_val(self, flavonoid_root):
        adapter = FlavonoidAdapter()
        claims = list(adapter.load(flavonoid_root, flavonoid_root))
        v081 = [c for c in claims if c.v == 0.81]
        assert len(v081) >= 1
        assert isinstance(v081[0].v, float)

    def test_unit_from_nutr_def(self, flavonoid_root):
        adapter = FlavonoidAdapter()
        claims = list(adapter.load(flavonoid_root, flavonoid_root))
        assert all(c.unit == "mg" for c in claims)

    def test_claims_are_lazy(self, flavonoid_root):
        adapter = FlavonoidAdapter()
        claims_iter = adapter.load(flavonoid_root, flavonoid_root)
        assert isinstance(claims_iter, Iterator)