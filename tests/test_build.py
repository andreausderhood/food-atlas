import json

import duckdb
import pytest

from atlas.build import build


def test_build_end_to_end(project):
    result = build(project)
    v = result.validation
    # FDC: 2 accepted per file (×2 files); BLS: 1; FoodAtlas presence: 2; curated: 1
    assert len(v.accepted) == 8
    # FDC dried apple has no derivation (×2) → 5; FoodAtlas amount → 6; health wording → 8
    assert sorted(g.rule for g in v.gaps if g.carried_value is not None) == [5, 5, 6, 8]
    assert any(g.field == "season:DE" and g.carried_value is None for g in v.gaps)

    out = project / "data/build"
    payload = json.loads((out / "atlas.json").read_text(encoding="utf-8"))
    foods = {f["id"]: f for f in payload["foods"]}
    hc = foods["food:apple.honeycrisp"]
    assert hc["taxon"] == "org:malus-domestica"
    assert {c["src"] for c in hc["claims"] if c["field"] == "nutrient:fdc:1162"} == {
        "SRC-FDC-FOUNDATION-2026-04", "SRC-FDC-SRLEGACY-2018-04"}
    assert foods["food:apple"]["name_de"] == "Apfel roh"
    assert any(g["rule"] == 6 for g in foods["food:apple"]["gaps"])
    assert "e1671" in payload["excluded_foodatlas"]
    assert payload["molecules"]["nutrient:fdc:1162"]["foodatlas_ids"] == ["c1", "c2", "c3"]

    con = duckdb.connect(str(out / "atlas.duckdb"), read_only=True)
    assert con.execute("select count(*) from claims").fetchone()[0] == 8
    assert con.execute("select count(*) from gaps").fetchone()[0] == len(v.gaps)

    notice = (project / "NOTICE.md").read_text(encoding="utf-8")
    assert "USDA ARS. FoodData Central." in notice and "Max Rubner-Institut" in notice
    assert "SRC-UNVERIFIED" not in notice


def test_build_requires_raw_data(project):
    import shutil
    shutil.rmtree(project / "data/raw/bls")
    with pytest.raises(FileNotFoundError, match="bls"):
        build(project)
    assert build(project, require_raw=False).validation.accepted
