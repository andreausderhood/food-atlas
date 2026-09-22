from atlas.site import catalog
from atlas.unified.identity import product_id


def test_ciqual_rows_from_real_raw_data():
    rows = catalog._ciqual_rows()
    assert len(rows) == 3484, "every ALIM record of Ciqual 2025 is a product record"
    assert rows[0]["source"] == "SRC-CIQUAL-2025"
    first = product_id(rows[0]["source"], rows[0]["id"])
    assert first.startswith("prod:ciq:") and first != "prod:ciq:"


def test_swiss_rows_skip_blank_spreadsheet_rows():
    rows = catalog._swiss_rows()
    # 1,416 non-empty spreadsheet lines, 200 of them fully blank (ID=None) -> 1,216 real foods
    assert len(rows) == 1216
    assert all(r["id"] not in ("", "None") for r in rows)
    assert rows[0]["source"] == "SRC-SWISS-FCDB-V7.1"
    first = product_id(rows[0]["source"], rows[0]["id"])
    assert first.startswith("prod:swiss:") and first != "prod:swiss:"


def test_new_sources_are_in_source_short():
    from atlas.unified.identity import SOURCE_SHORT
    assert SOURCE_SHORT["SRC-CIQUAL-2025"] == "ciq"          # matches the adapter prefix prod:ciq
    assert SOURCE_SHORT["SRC-SWISS-FCDB-V7.1"] == "swiss"    # matches the adapter prefix prod:swiss
    assert SOURCE_SHORT["SRC-COFID-2021"] == "cofid"         # matches the adapter prefix prod:cofid


def test_cofid_rows_from_real_raw_data():
    rows = catalog._cofid_rows()
    assert len(rows) > 0, "CoFID 2021 must have product records"
    assert rows[0]["source"] == "SRC-COFID-2021"
    first = product_id(rows[0]["source"], rows[0]["id"])
    assert first.startswith("prod:cofid:") and first != "prod:cofid:"
