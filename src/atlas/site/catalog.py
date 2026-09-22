"""Catalog helper: list source records from raw FDC and BLS datasets."""
from __future__ import annotations

import csv
from pathlib import Path

FDC_SOURCES = {
    "data/raw/fdc-foundation": "SRC-FDC-FOUNDATION-2026-04",
    "data/raw/fdc-srlegacy": "SRC-FDC-SRLEGACY-2018-04",
}
BLS_SOURCE = "SRC-BLS-4.0"


def _fdc_rows(root: Path = Path(".")) -> list[dict]:
    rows = []
    for rel, src in FDC_SOURCES.items():
        folder = root / rel
        if not folder.is_dir():
            continue
        hits = sorted(folder.rglob("food.csv"))
        if not hits:
            continue
        with hits[0].open(encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rows.append({"source": src, "id": r["fdc_id"], "name": r.get("description", "")})
    return rows


def _bls_rows(root: Path = Path(".")) -> list[dict]:
    folder = root / "data/raw/bls"
    if not folder.is_dir():
        return []
    # BLS 4.0 xlsx: BLS Code, Lebensmittelbezeichnung, Food name, then nutrient triplets
    xlsx_hits = sorted(folder.rglob("BLS_4_0_Daten_*.xlsx"))
    if xlsx_hits:
        import openpyxl
        wb = openpyxl.load_workbook(xlsx_hits[0], read_only=True, data_only=True)
        try:
            ws = wb.worksheets[0]
            rows = []
            for r in ws.iter_rows(min_row=2, values_only=True):
                code = r[0] if r[0] is not None else ""
                if not str(code).strip():
                    continue
                de_name = r[1] if r[1] is not None else ""
                en_name = r[2] if r[2] is not None else ""
                rows.append({"source": BLS_SOURCE, "id": str(code).strip(),
                             "name": str(en_name), "name_de": str(de_name)})
            return rows
        finally:
            wb.close()
    # Fallback: CSV food list (legacy BLS format)
    csv_hits = sorted(folder.rglob("*food*.csv")) or sorted(folder.rglob("*.csv"))
    rows = []
    if csv_hits:
        with csv_hits[0].open(encoding="utf-8", errors="replace") as f:
            for r in csv.DictReader(f):
                rec_id = r.get("BLS_Code") or r.get("code") or r.get("id")
                if rec_id:
                    rows.append({"source": BLS_SOURCE, "id": rec_id,
                                 "name": r.get("Food name", r.get("name", ""))})
    return rows


CIQUAL_SOURCE = "SRC-CIQUAL-2025"
SWISS_SOURCE = "SRC-SWISS-FCDB-V7.1"


def _ciqual_rows(root: Path = Path(".")) -> list[dict]:
    """Product records from the Ciqual 2025 ALIM table (raw XML)."""
    folder = root / "data/raw/ciqual-2025"
    hits = sorted(folder.rglob("alim_*.xml"))
    if not hits:
        return []
    from xml.etree.ElementTree import iterparse
    rows = []
    for _, el in iterparse(hits[0], events=("end",)):
        if el.tag != "ALIM":
            continue
        code = (el.findtext("alim_code") or "").strip()
        if code:
            sci_el = el.find("alim_nom_sci")
            sci = "" if sci_el is None or sci_el.get("missing") is not None else (sci_el.text or "").strip()
            rows.append({"source": CIQUAL_SOURCE, "id": code, "sci": sci,
                         "name": (el.findtext("alim_nom_eng") or el.findtext("alim_nom_fr") or "").strip()})
        el.clear()
    return rows


def _swiss_rows(root: Path = Path(".")) -> list[dict]:
    """Product records from Swiss FCDB v7.1 'Generic Foods' (raw xlsx); blank spreadsheet rows are skipped."""
    folder = root / "data/raw/swiss-fcdb"
    hits = sorted(folder.rglob("*.xlsx"))
    if not hits:
        return []
    import openpyxl
    wb = openpyxl.load_workbook(hits[0], read_only=True, data_only=True)
    try:
        ws = wb["Generic Foods"]
        rows = []
        for r in ws.iter_rows(min_row=4, values_only=True):   # header is row 3
            rec_id = r[0]
            if rec_id is None:
                continue                                      # trailing blank rows, not real foods
            rows.append({"source": SWISS_SOURCE, "id": str(rec_id), "name": str(r[3] or "")})
        return rows
    finally:
        wb.close()


COFID_SOURCE = "SRC-COFID-2021"


def _cofid_rows(root: Path = Path(".")) -> list[dict]:
    """Product records from CoFID 2021 (raw xlsx); blank spreadsheet rows are skipped."""
    folder = root / "data/raw/cofid-2021"
    hits = sorted(folder.rglob("*.xlsx"))
    hits = [h for h in hits if "oldFoods" not in h.name]
    if not hits:
        return []
    import openpyxl
    wb = openpyxl.load_workbook(hits[0], read_only=True, data_only=True)
    try:
        ws = wb["1.3 Proximates"]
        rows = []
        for r in ws.iter_rows(min_row=4, values_only=True):
            code = r[0]
            if code is None:
                continue
            rows.append({"source": COFID_SOURCE, "id": str(code), "name": str(r[1] or "")})
        return rows
    finally:
        wb.close()


BFC_SOURCE = "SRC-BFOODCOMP-4.0"


def _bfc_rows(root: Path = Path(".")) -> list[dict]:
    """Product records from BioFoodComp 4.0 (raw xlsx); blank spreadsheet rows are skipped.

    Streams all 12 category sheets (01 Cereals through 12 Miscellaneous),
    skipping the per-100gFA fatty-acid sheet and metadata sheets.
    Scientific name (col 7) and variety (col 8) are included for identity traceability.
    """
    folder = root / "data/raw/biofoodcomp-4.0"
    hits = sorted(folder.rglob("*.xlsx"))
    if not hits:
        return []
    import openpyxl
    wb = openpyxl.load_workbook(hits[0], read_only=True, data_only=True)
    try:
        rows = []
        for sheet_name in wb.sheetnames:
            if sheet_name in ("Copyright", "Codes", "Components", "Bibliography"):
                continue
            if sheet_name == "09 Fish & Shellfish_Fatty acids":
                continue
            if not sheet_name.startswith(("01 ", "02 ", "03 ", "04 ", "05 ", "06 ",
                                          "07 ", "08 ", "09 ", "10_", "11 ", "12 ")):
                continue
            ws = wb[sheet_name]
            for r in ws.iter_rows(min_row=2, values_only=True):
                rec_id = r[0]
                if rec_id is None:
                    continue
                rec_id = str(rec_id).strip()
                if not rec_id:
                    continue
                sci_name = r[7] if len(r) > 7 and r[7] is not None else ""
                variety = r[8] if len(r) > 8 and r[8] is not None else ""
                rows.append({
                    "source": BFC_SOURCE,
                    "id": rec_id,
                    "name": str(r[5] or r[4] or ""),
                    "sci": str(sci_name) if sci_name else "",
                    "variety": str(variety) if variety else "",
                })
        return rows
    finally:
        wb.close()


FA_SOURCE = "SRC-FOODATLAS-V4.11"


def _foodatlas_rows(root: Path = Path(".")) -> list[dict]:
    """Product records from FoodAtlas v4.11 food entities (raw parquet, duckdb)."""
    folder = root / "data/raw/foodatlas/foodatlas-v4.11"
    hits = sorted(folder.rglob("entities.parquet"))
    if not hits:
        return []
    import duckdb
    con = duckdb.connect()
    try:
        rows = con.execute(
            f"SELECT foodatlas_id, common_name FROM read_parquet('{hits[0]}') "
            "WHERE entity_type = 'food' ORDER BY foodatlas_id"
        ).fetchall()
        return [{"source": FA_SOURCE, "id": str(i), "name": str(n or "")}
                for i, n in rows if i is not None]
    finally:
        con.close()


FLAV_SOURCE = "SRC-USDA-FLAVONOID-EXP-1.1"


def _flavonoid_rows(root: Path = Path(".")) -> list[dict]:
    """Product records from the USDA Expanded Flavonoid Database R1.1."""
    folder = root / "data/raw/flavonoid-exp-1.1"
    if not folder.is_dir():
        return []
    rows: list[dict] = []
    with (folder / "FOOD_DES.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({"source": FLAV_SOURCE, "id": r["NDB_No"], "name": r["Long_Desc"]})
    return rows
