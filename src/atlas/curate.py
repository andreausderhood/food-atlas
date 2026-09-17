"""Search helpers for mapping raw source rows onto food nodes (used while editing foods.yaml)."""
from __future__ import annotations

from pathlib import Path

from atlas.ingest.fdc import find_csv_dir, read_csv_rows

FDC_DIRS = ("data/raw/fdc-foundation", "data/raw/fdc-srlegacy")


def search_fdc(root: Path, query: str) -> list[str]:
    q = query.lower()
    out = []
    for rel in FDC_DIRS:
        folder = find_csv_dir(root / rel)
        for r in read_csv_rows(folder / "food.csv"):
            if q in r["description"].lower():
                out.append(f"{Path(rel).name}\t{r['fdc_id']}\t{r['description']}")
    return out


def search_bls(root: Path, query: str) -> list[str]:
    from openpyxl import load_workbook
    from atlas.ingest.bls import find_workbook
    q = query.lower()
    wb = load_workbook(find_workbook(root / "data/raw/bls"), read_only=True)
    try:
        ws = wb.worksheets[0]
        return ["\t".join("" if x is None else str(x) for x in row)
                for row in ws.iter_rows(min_row=2, max_col=3, values_only=True)
                if any(x is not None and q in str(x).lower() for x in row)]
    finally:
        wb.close()

def search_foodatlas(root: Path, query: str) -> list[str]:
    import duckdb
    from atlas.ingest.foodatlas import sql_path
    bundle = root / "data/raw/foodatlas/foodatlas-v4.11"
    with duckdb.connect() as con:
        rows = con.execute(
            f"select foodatlas_id, common_name from read_parquet({sql_path(bundle / 'entities.parquet')}) "
            "where entity_type = 'food' and common_name ilike ? order by common_name",
            [f"%{query}%"],
        ).fetchall()
    return [f"{fa_id}\t{name}" for fa_id, name in rows]
