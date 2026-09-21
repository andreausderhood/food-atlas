"""Identity edges: which source product is which species — decided by a person, stored in Git.

Claims stay keyed to the product (its source record); a species only attaches
through an approved edge, joined at read time. Approving a tranche therefore
raises species coverage without re-ingesting anything.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

def species_slug(binomial: str) -> str:
    return "-".join(binomial.lower().split())

SOURCE_SHORT = {
    "SRC-FDC-FOUNDATION-2026-04": "fdcf",
    "SRC-FDC-SRLEGACY-2018-04": "fdcs",
    "SRC-BLS-4.0": "bls",
    "SRC-CIQUAL-2025": "ciq",
    "SRC-SWISS-FCDB-V7.1": "swiss",
}
STATUSES = ("approved", "rejected")
AUTO_APPROVE = {"exact_binomial": 0.95}   # pre-filled "approve" in the review sheet, still reviewable


class IdentityError(ValueError):
    pass


def product_id(src: str, record: str) -> str:
    return f"prod:{SOURCE_SHORT[src]}:{record}"


def species_id(binomial: str) -> str:
    return "org:" + species_slug(binomial)


@dataclass(frozen=True)
class Edge:
    product: str
    species: str        # pool binomial, lower-case
    method: str         # match_class of the proposal, or "manual"
    confidence: float
    batch: str
    approved_by: str
    approved_at: str    # ISO date
    status: str = "approved"
    relation: str = "derives_from"


def write_edges(path: Path, edges: list[Edge]) -> None:
    """Sorted, one JSON object per line, so Git diffs show exactly the changed decisions."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(asdict(e), sort_keys=True, ensure_ascii=False)
             for e in sorted(edges, key=lambda e: (e.product, e.species))]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def load_edges(path: Path) -> list[Edge]:
    if not path.is_file():
        return []
    return [Edge(**json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def validate_edges(edges: list[Edge], pool: dict) -> None:
    """Every species must exist in the pool; one product may not be approved for two species."""
    approved: dict[str, str] = {}
    for e in edges:
        if e.status not in STATUSES:
            raise IdentityError(f"{e.product}: unknown status {e.status!r}")
        if e.species not in pool:
            raise IdentityError(f"{e.product}: species {e.species!r} is not in the pool")
        if e.status != "approved":
            continue
        if approved.setdefault(e.product, e.species) != e.species:
            raise IdentityError(f"{e.product}: approved for both {approved[e.product]!r} and {e.species!r}")


@dataclass(frozen=True)
class Cluster:
    """The review unit: one species, one source, one match class — decided once for all its products."""
    species: str
    source: str
    match_class: str
    confidence: float
    products: tuple[str, ...]
    sample_names: tuple[str, ...]

    @property
    def key(self) -> str:
        return f"{self.source}|{self.species}|{self.match_class}"

    @property
    def auto(self) -> bool:
        return self.confidence >= AUTO_APPROVE.get(self.match_class, 2.0)


def cluster_proposals(rows: list[dict], decided: set[str] | None = None) -> list[Cluster]:
    """Group matcher proposals; products with an existing decision are not proposed again."""
    decided = decided or set()
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        pid = product_id(r["source"], r["record"])
        if pid not in decided:
            groups[(r["species"], r["source"], r["match_class"])].append(r)
    clusters = [
        Cluster(species, source, match_class, min(r["confidence"] for r in rs),
                tuple(sorted(product_id(r["source"], r["record"]) for r in rs)),
                tuple(r["name"] for r in rs[:5]))
        for (species, source, match_class), rs in groups.items()
    ]
    return sorted(clusters, key=lambda c: (-len(c.products), c.species, c.source))


REVIEW_COLUMNS = ["decision", "species", "source", "match_class", "confidence", "n_products", "sample_names", "cluster_key"]


def write_review_sheet(path: Path, clusters: list[Cluster]) -> None:
    """Sheet for the reviewer: fill `decision` with approve, reject, or other:<binomial>."""
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(REVIEW_COLUMNS)
        for c in clusters:
            w.writerow(["approve" if c.auto else "", c.species, c.source, c.match_class, c.confidence,
                        len(c.products), " | ".join(c.sample_names), c.key])


def apply_review(path: Path, clusters: list[Cluster], batch: str, approver: str, today: str) -> list[Edge]:
    """Turn the filled sheet into edges; blank decisions stay undecided (and are proposed again)."""
    by_key = {c.key: c for c in clusters}
    edges: list[Edge] = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            decision = (row["decision"] or "").strip().lower()
            cluster = by_key.get(row["cluster_key"])
            if not decision or cluster is None:
                continue
            if decision == "approve":
                status, species, method = "approved", cluster.species, cluster.match_class
            elif decision == "reject":
                status, species, method = "rejected", cluster.species, cluster.match_class
            elif decision.startswith("other:"):
                status, species, method = "approved", decision.split(":", 1)[1].strip(), "manual"
            else:
                raise IdentityError(f"{row['cluster_key']}: unknown decision {decision!r}")
            edges.extend(Edge(p, species, method, cluster.confidence, batch, approver, today, status)
                         for p in cluster.products)
    return edges


def resolver(edges: list[Edge]) -> Callable[[str], str | None]:
    """product id -> binomial for approved edges, None otherwise."""
    table = {e.product: e.species for e in edges if e.status == "approved"}
    return table.get
