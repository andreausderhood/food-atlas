"""Streaming FoodAtlas v4.11 molecules adapter: yields product claims from parquet bundle.

Produces ``prod:fa:<id>`` claims for foods containing molecules, with group
``molecules`` (rule 6-prime: unit + basis=as_described + food_part=product).

Uses DuckDB SQL joins for performance, streaming result rows without loading
the full dataset into Python RAM.  Only r1 (``contains``) triplets are
processed; r2 (``is_a``) and other relationships are skipped.  Flavor
descriptors in chemical attributes are documented as a skip and never
produced as claims.

For each food→chemical r1-triplet the adapter reads the attestation's
``conc_value`` and ``conc_unit``.  Numeric values become amount claims;
``None`` conc_value produces a non-amount presence claim (documented as
such).  The chemical's ``external_ids`` JSON is unpacked so that each
``chebi`` and ``pubchem_compound`` ID yields a separate claim (field
``molecule:chebi:<id>`` or ``molecule:pubchem:<id>``).
"""
from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

from atlas.claims import Claim
from atlas.ingest.base import BaseIngestAdapter, register


SRC_ID = "SRC-FOODATLAS-V4.11"
REQUIRED_FILES = (
    "entities.parquet",
    "triplets.parquet",
    "attestations.parquet",
    "evidence.parquet",
)


def _find_parquet_dir(path: Path) -> Path:
    """Find the FoodAtlas parquet directory under ``path`` (recursive)."""
    hits = sorted(path.rglob("entities.parquet"))
    if len(hits) != 1:
        raise FileNotFoundError(
            f"expected one entities.parquet under {path}, found {len(hits)}"
        )
    folder = hits[0].parent
    missing = [f for f in REQUIRED_FILES if not (folder / f).exists()]
    if missing:
        raise FileNotFoundError(f"{folder}: missing {missing}")
    return folder


# DuckDB cannot easily unnest JSON arrays in parquet columns, so we
# load the small lookup tables (attestations, evidence, entities) into
# Python dicts and stream triplets row-by-row.  This keeps RAM usage
# bounded while still being fast enough for the ~108 K r1 triplets.


class BulkFoodAtlasAdapter(BaseIngestAdapter):
    """Streaming FoodAtlas v4.11 molecules adapter."""

    def __init__(self, src_id: str = SRC_ID) -> None:
        self.src_id = src_id

    def load(self, root: Path, path: Path) -> Iterator[Claim]:
        folder = _find_parquet_dir(path)

        import duckdb

        con = duckdb.connect()
        entities_path = str(folder / "entities.parquet")
        triplets_path = str(folder / "triplets.parquet")
        attestations_path = str(folder / "attestations.parquet")
        evidence_path = str(folder / "evidence.parquet")

        # Load attestations into a dict keyed by attestation_id.
        attestations: dict[str, tuple] = {}
        for r in con.execute(
            f"SELECT attestation_id, evidence_id, conc_value, conc_unit "
            f"FROM read_parquet('{attestations_path}')"
        ).fetchall():
            attestations[r[0]] = r

        # Load evidence into a dict keyed by evidence_id.
        evidence: dict[str, str | None] = {}
        for r in con.execute(
            f"SELECT evidence_id, reference "
            f"FROM read_parquet('{evidence_path}')"
        ).fetchall():
            evidence[r[0]] = r[1]

        # Load chemical entities into a dict keyed by foodatlas_id.
        entities: dict[str, tuple] = {}
        for r in con.execute(
            f"SELECT foodatlas_id, external_ids, attributes "
            f"FROM read_parquet('{entities_path}') "
            "WHERE entity_type = 'chemical'"
        ).fetchall():
            entities[r[0]] = r

        # Stream triplets row by row — only r1 (contains) food→chemical edges.
        for t in con.execute(
            f"SELECT head_id, tail_id, attestation_ids "
            f"FROM read_parquet('{triplets_path}') "
            "WHERE relationship_id = 'r1'"
        ).fetchall():
            head_id, tail_id, attestation_ids_json = t

            chem = entities.get(tail_id)
            if chem is None:
                continue

            ext_ids = json.loads(chem[1]) if chem[1] else {}
            attrs = json.loads(chem[2]) if chem[2] else {}

            # Skip flavor descriptors — they are documented as a skip, not claims.
            _flavor_descriptors = attrs.get("flavor_descriptors", [])

            chebi_ids = ext_ids.get("chebi", [])
            pubchem_ids = ext_ids.get("pubchem_compound", [])

            if not chebi_ids and not pubchem_ids:
                continue

            attestation_ids = json.loads(attestation_ids_json) if attestation_ids_json else []
            if not attestation_ids:
                continue

            for att_id in attestation_ids:
                att = attestations.get(att_id)
                if att is None:
                    continue
                _aid, ev_id, conc_value, conc_unit = att
                ref = evidence.get(ev_id)

                if conc_value is not None:
                    # Amount claim — rule 6-prime: unit + basis=as_described + food_part=product.
                    for chebi_id in chebi_ids:
                        yield Claim(
                            subject=f"prod:fa:{head_id}",
                            group="molecules",
                            field=f"molecule:chebi:{chebi_id}",
                            v=float(conc_value),
                            src=self.src_id,
                            derivation="registry",
                            unit=conc_unit or "",
                            basis="as_described",
                            food_part="product",
                            ref=ref,
                        )
                    for pubchem_id in pubchem_ids:
                        yield Claim(
                            subject=f"prod:fa:{head_id}",
                            group="molecules",
                            field=f"molecule:pubchem:{pubchem_id}",
                            v=float(conc_value),
                            src=self.src_id,
                            derivation="registry",
                            unit=conc_unit or "",
                            basis="as_described",
                            food_part="product",
                            ref=ref,
                        )
                else:
                    # Non-numeric presence claim — documented as non-amount.
                    for chebi_id in chebi_ids:
                        yield Claim(
                            subject=f"prod:fa:{head_id}",
                            group="molecules",
                            field=f"molecule:chebi:{chebi_id}",
                            v="present",
                            src=self.src_id,
                            derivation="registry",
                            ref=ref,
                        )
                    for pubchem_id in pubchem_ids:
                        yield Claim(
                            subject=f"prod:fa:{head_id}",
                            group="molecules",
                            field=f"molecule:pubchem:{pubchem_id}",
                            v="present",
                            src=self.src_id,
                            derivation="registry",
                            ref=ref,
                        )

        con.close()


# Register at import time so ``atlas ingest`` can find it.
register(BulkFoodAtlasAdapter())