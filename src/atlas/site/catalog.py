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
