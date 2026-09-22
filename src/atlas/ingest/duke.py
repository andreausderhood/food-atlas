"""Dr. Duke's Phytochemical and Ethnobotanical DB (CC0) — streaming ingest adapter.

Produces ``traditional_use`` claims from ETHNOBOT.csv (species-native,
no identity edges needed) and ``molecules`` claims from FARMACY_NEW.csv
(joined with ETHNOBOT for TAXON and CHEMICALS for CHEMID).

Amount claims are only emitted when the source carries QUANT_UNIT and
a numeric amount value; otherwise non-amount presence claims are emitted.
This avoids Rule 6 rejections (amount without unit/basis/food_part).
"""
from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

import duckdb

from atlas.claims import Claim
from atlas.ingest.base import BaseIngestAdapter, register
from atlas.unified.identity import species_id


SRC_ID = "SRC-DUKE-2023-11"


def _slugify(text: str) -> str:
    """Lowercase, replace non-alphanumeric with hyphens, strip edges."""
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s


def _resolve_references(root: Path) -> dict[str, str]:
    """Load REFERENCES.csv → {short_code: longref} mapping."""
    ref_path = root / "REFERENCES.csv"
    if not ref_path.is_file():
        return {}
    con = duckdb.connect()
    try:
        rows = con.execute(
            f"SELECT REFERENCE, LONGREF FROM read_csv('{ref_path}')"
        ).fetchall()
    finally:
        con.close()
    return {r[0]: r[1] for r in rows if r[0] and r[1]}


def _resolve_ref(short_ref: str, ref_map: dict[str, str]) -> str | None:
    """Resolve a short REFERENCE code to LONGREF via the lookup dict."""
    if not short_ref:
        return None
    return ref_map.get(short_ref) or short_ref


def _stream_traditional_use(con: duckdb.DuckDBPyConnection,
                            root: Path) -> Iterator[Claim]:
    """Yield traditional_use claims from ETHNOBOT.csv."""
    ref_map = _resolve_references(root)
    ethnobot_path = root / "ETHNOBOT.csv"
    if not ethnobot_path.is_file():
        return

    query = (
        f"SELECT TAXON, ACTIVITY, REFERENCE, LONGREF "
        f"FROM read_csv('{ethnobot_path}')"
    )
    for row in con.execute(query).fetchall():
        taxon, activity, ref_short, longref = row
        if not taxon or not activity:
            continue

        subject = species_id(taxon)
        ref = longref if longref else _resolve_ref(ref_short, ref_map)

        yield Claim(
            subject=subject,
            group="traditional_use",
            field=f"duke-activity-{_slugify(activity)}",
            v=activity,
            src=SRC_ID,
            derivation="literature",
            ref=ref,
        )


def _stream_molecules(con: duckdb.DuckDBPyConnection,
                      root: Path) -> Iterator[Claim]:
    """Yield molecules claims from FARMACY_NEW.csv joined with ETHNOBOT.

    FARMACY_NEW.FNFNUM maps to ETHNOBOT.ETHNO (same plant record).
    Amount claims are only emitted when QUANT_UNIT is present and a
    numeric amount value exists; otherwise non-amount presence claims.
    """
    ref_map = _resolve_references(root)
    farmacy_path = root / "FARMACY_NEW.csv"
    ethnobot_path = root / "ETHNOBOT.csv"
    chemicals_path = root / "CHEMICALS.csv"

    if not farmacy_path.is_file() or not ethnobot_path.is_file():
        return

    query = (
        f"SELECT "
        f"  fn.FNFNUM, fn.CHEM, fn.CHEMID, fn.QUANT_UNIT, "
        f"  fn.AMT_OR_LO, fn.AMT_HI, fn.AMT_OR_HI, "
        f"  fn.REFERENCE, "
        f"  eb.TAXON "
        f"FROM read_csv('{farmacy_path}') fn "
        f"LEFT JOIN read_csv('{ethnobot_path}') eb "
        f"  ON fn.FNFNUM = eb.ETHNO "
        f"LEFT JOIN read_csv('{chemicals_path}') ch "
        f"  ON fn.CHEM = ch.CHEM "
        f"  AND fn.CHEMID = ch.CHEMID "
    )

    for row in con.execute(query).fetchall():
        (fnfnum, chem, chemid, quant_unit,
         amt_or_lo, amt_hi, amt_or_hi,
         ref_short, taxon) = row

        if not chem or not taxon:
            continue

        subject = species_id(taxon)

        # Resolve reference
        ref = _resolve_ref(ref_short, ref_map)

        # Determine field name
        if chemid and chemid.startswith("CHEBI:"):
            field = f"chebi:{chemid[5:]}"
        else:
            field = f"molecule-duke-{_slugify(chem)}"

        # Determine if this is an amount claim
        has_unit = bool(quant_unit and str(quant_unit).strip())
        amt_or_lo_s = str(amt_or_lo).strip() if amt_or_lo is not None else ""
        amt_hi_s = str(amt_hi).strip() if amt_hi is not None else ""
        amt_or_hi_s = str(amt_or_hi).strip() if amt_or_hi is not None else ""
        has_amount = bool(amt_or_lo_s or amt_hi_s or amt_or_hi_s)

        if has_unit and has_amount:
            # Amount claim with unit, basis, food_part (Rule 6 compliant)
            v_str = amt_or_lo_s or amt_hi_s or amt_or_hi_s
            try:
                v = float(v_str)
            except (ValueError, TypeError):
                yield Claim(
                    subject=subject,
                    group="molecules",
                    field=field,
                    v=chem,
                    src=SRC_ID,
                    derivation="literature",
                    ref=ref,
                )
                continue

            yield Claim(
                subject=subject,
                group="molecules",
                field=field,
                v=v,
                src=SRC_ID,
                derivation="literature",
                unit=str(quant_unit).strip(),
                basis="as_described",
                food_part="product",
                ref=ref,
            )
        else:
            # Non-amount presence claim
            yield Claim(
                subject=subject,
                group="molecules",
                field=field,
                v=chem,
                src=SRC_ID,
                derivation="literature",
                ref=ref,
            )


class DukeAdapter(BaseIngestAdapter):
    """Streaming adapter for Dr. Duke's Phytochemical and Ethnobotanical DB.

    Produces species-native ``traditional_use`` and ``molecules`` claims
    directly on ``org:species:<slug>`` subjects without identity edges.
    """

    src_id = SRC_ID

    def load(self, root: Path, path: Path) -> Iterator[Claim]:
        """Stream claims from Duke CSV files under ``path``."""
        source_dir = path if path.name == "ETHNOBOT.csv" else path
        con = duckdb.connect()
        try:
            yield from _stream_traditional_use(con, source_dir)
            yield from _stream_molecules(con, source_dir)
        finally:
            con.close()


register(DukeAdapter())