"""BLS 4.0 (Max Rubner-Institut, CC BY 4.0) → nutrition claims."""
from __future__ import annotations

import re
from pathlib import Path

from openpyxl import load_workbook

from atlas.claims import Claim, UnmappedDerivation
from atlas.foods import FoodNode, basis, food_part

# BLS FAQ 6: the 13 categories of Datenherkunft.
HERKUNFT = {
    "Analyse": "analytical",
    "Literatur": "literature",
    "Aggregation": "aggregated",
    "Rezeptberechnung": "calculated",
    "Musterberechnung": "calculated",
    "Formelberechnung": "calculated",
    "Reskalierung": "calculated",
    "Nährstoffdatenbank": "borrowed",
    "Übernommener Wert": "borrowed",
    "Labelangabe": "label",
    "Logische Null": "assumed_zero",
    "Logische Annahme": "imputed",
    "Spuren": "trace",   # cells carry the literal value 'TR'
}
ORIGIN_HEADER = re.compile(r"herkunft", re.IGNORECASE)
UNIT = re.compile(r"\[\s*([^\]/]+?)\s*(?:/\s*100\s*g)?\s*\]")


def find_workbook(root: Path) -> Path:
    hits = sorted(root.rglob("BLS_4_0_Daten_*.xlsx"))
    if len(hits) != 1:
        raise FileNotFoundError(f"expected one BLS_4_0_Daten_*.xlsx under {root}, found {len(hits)}")
    return hits[0]


def nutrient_columns(headers: list[str]) -> list[tuple[int, int, int]]:
    """(value, origin, reference) column indexes, located by the 'Datenherkunft' header."""
    return [(i - 1, i, i + 1) for i, h in enumerate(headers) if i >= 4 and ORIGIN_HEADER.search(h)]


def parse_value_header(header: str) -> tuple[str, str, str | None]:
    tag, _, rest = header.strip().partition(" ")
    match = UNIT.search(rest)
    return tag, UNIT.sub("", rest).strip(), (match.group(1).strip() if match else None)


def load_bls(root: Path, src_id: str, nodes: dict[str, FoodNode]) -> tuple[list[Claim], dict[str, dict], dict[str, str]]:
    wb = load_workbook(find_workbook(root), read_only=True, data_only=True)
    try:
        rows = wb.worksheets[0].iter_rows(values_only=True)
        headers = ["" if h is None else str(h) for h in next(rows)]
        triples = nutrient_columns(headers)
        if not triples:
            raise ValueError("no 'Datenherkunft' columns found in the BLS workbook")
        wanted = {code: node for node in nodes.values() for code in node.bls_codes}
        claims: list[Claim] = []
        used: dict[str, dict] = {}
        names_de: dict[str, str] = {}
        for row in rows:
            node = wanted.get("" if row[0] is None else str(row[0]).strip())
            if node is None:
                continue
            names_de[node.id] = str(row[1])
            for vi, oi, ri in triples:
                value = row[vi] if vi < len(row) else None
                if value is None or value == "":
                    continue  # missing, not zero (BLS FAQ 11)
                origin = "" if row[oi] is None else str(row[oi]).strip()
                if origin == "-":
                    origin = ""  # BLS: no origin given for this value; stays honest as unverified
                if origin and origin not in HERKUNFT:
                    raise UnmappedDerivation(f"BLS Datenherkunft {origin!r} in column {headers[oi]!r}")
                tag, name, unit = parse_value_header(headers[vi])
                key = f"nutrient:bls:{tag}"
                used[key] = {"name": name, "unit": unit}
                reference = row[ri] if ri < len(row) else None
                claims.append(Claim(
                    subject=node.id, group="nutrition", field=key,
                    v=float(value) if isinstance(value, (int, float)) else str(value),
                    unit=unit, basis=basis(node), food_part=food_part(node), src=src_id,
                    derivation=HERKUNFT.get(origin, "unverified"),
                    ref=f"bls:{row[0]}" + (f"; {reference}" if reference else ""),
                ))
        return claims, used, names_de
    finally:
        wb.close()
