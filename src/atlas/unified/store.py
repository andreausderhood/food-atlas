"""Bulk datapoint store: DuckDB, rebuilt per source, never hand-edited.

The Git ledger holds curated claims and identity decisions. Bulk claims are a
pure function of hash-pinned raw files + parser + identity edges, so they live
in data/build/ and are regenerated, not versioned.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import duckdb

from atlas.build import claim_dict
from atlas.claims import Claim
from atlas.contract import check
from atlas.registry import Source
from atlas.unified.identity import Edge

CHUNK = 50_000
SCHEMA = """
CREATE TABLE IF NOT EXISTS datapoints (
    subject VARCHAR, "group" VARCHAR, field VARCHAR, v VARCHAR, v_num DOUBLE, unit VARCHAR,
    basis VARCHAR, food_part VARCHAR, src VARCHAR, derivation VARCHAR, tier INTEGER,
    method VARCHAR, ref VARCHAR, v_min DOUBLE, v_max DOUBLE, n INTEGER, flags VARCHAR, batch VARCHAR);
CREATE TABLE IF NOT EXISTS rejects (
    subject VARCHAR, "group" VARCHAR, field VARCHAR, rule INTEGER, src VARCHAR, batch VARCHAR,
    carried VARCHAR);   -- the rejected value, kept so a later source can settle the gap; never counted as a claim
CREATE TABLE IF NOT EXISTS product_species (
    product VARCHAR PRIMARY KEY, species VARCHAR, method VARCHAR, confidence DOUBLE, batch VARCHAR);
"""


@dataclass(frozen=True)
class IngestStats:
    accepted: int
    rejected: int


def _num(v) -> float | None:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _row(c: Claim, batch: str) -> tuple:
    d = claim_dict(c)
    v = d["v"]
    return (d["subject"], d["group"], d["field"], json.dumps(v) if isinstance(v, (dict, list)) else str(v),
            _num(v), d["unit"], d["basis"], d["food_part"], d["src"], d["derivation"], d["tier"],
            d["method"], d["ref"], d["v_min"], d["v_max"], d["n"], ";".join(d["flags"]), batch)


class Store:
    def __init__(self, path: Path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.con = duckdb.connect(str(path))
        self.con.execute(SCHEMA)

    def close(self) -> None:
        self.con.close()

    def replace_source(self, src: str, claims: Iterable[Claim], sources: dict[str, Source], batch: str) -> IngestStats:
        """Idempotent: drop this source's rows, stream its claims through the contract, insert the result."""
        self.con.execute("DELETE FROM datapoints WHERE src = ?", [src])
        self.con.execute("DELETE FROM rejects WHERE src = ?", [src])
        ok: list[tuple] = []
        bad: list[tuple] = []
        accepted = rejected = 0

        def flush() -> None:
            if ok:
                self.con.executemany("INSERT INTO datapoints VALUES (" + ",".join("?" * 18) + ")", ok)
                ok.clear()
            if bad:
                self.con.executemany("INSERT INTO rejects VALUES (?,?,?,?,?,?,?)", bad)
                bad.clear()

        for claim in claims:
            cr = check(claim, sources)
            if cr.ok:
                ok.append(_row(claim, batch))
                accepted += 1
            else:
                gap = cr.gap
                bad.append((claim.subject, claim.group, claim.field, gap.rule, claim.src, batch,
                            None if gap.carried_value is None else str(gap.carried_value)))
                rejected += 1
            if len(ok) + len(bad) >= CHUNK:
                flush()
        flush()
        return IngestStats(accepted, rejected)

    def load_edges(self, edges: list[Edge]) -> None:
        self.con.execute("DELETE FROM product_species")
        rows = [(e.product, e.species, e.method, e.confidence, e.batch) for e in edges if e.status == "approved"]
        if rows:  # duckdb executemany raises on an empty parameter list
            self.con.executemany(
                "INSERT INTO product_species VALUES (?,?,?,?,?)", rows)

    def species_with_claims(self, group: str) -> set[str]:
        """Species that own at least one accepted datapoint in `group`, through an approved edge."""
        rows = self.con.execute(
            'SELECT DISTINCT p.species FROM datapoints d JOIN product_species p ON p.product = d.subject '
            'WHERE d."group" = ?', [group]).fetchall()
        return {r[0] for r in rows}

    def species_native_with_claims(self, group: str) -> set[str]:
        """Subject slugs (org:<slug>) that directly own accepted datapoints in `group`.

        Species-native sources (e.g. Dr. Duke's ethnobotany) claim at the species
        itself, not through a product edge; callers map the slug back to a pool binomial.
        """
        rows = self.con.execute(
            'SELECT DISTINCT subject FROM datapoints WHERE "group" = ? AND subject LIKE ?',
            [group, "org:%"]).fetchall()
        return {r[0][4:] for r in rows}   # strip the 'org:' prefix

    def species_searched_empty(self, group: str) -> set[str]:
        """Species with a linked product whose source was read for `group`, but nothing was accepted."""
        rows = self.con.execute(
            'SELECT DISTINCT p.species FROM rejects r JOIN product_species p ON p.product = r.subject '
            'WHERE r."group" = ?', [group]).fetchall()
        return {r[0] for r in rows} - self.species_with_claims(group)

    def count(self, table: str) -> int:
        return self.con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
