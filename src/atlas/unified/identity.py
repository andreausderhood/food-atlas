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


# ---------------------------------------------------------------------------
# Proposal generation (Task 19)
# ---------------------------------------------------------------------------

import re

GENERIC_CATEGORY_WORDS = frozenset({
    "mushroom", "mushrooms",
    "pepper", "peppers",
    "bean", "beans",
    "berry", "berries",
})

_PROPOSALS_DIR = Path("data/research/proposals")


def _normalize_name(name: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace for matching."""
    return re.sub(r"[^a-z0-9\s]", "", name.lower()).strip()


def _normalize_compact(name: str) -> str:
    """Lowercase, strip punctuation, remove all whitespace for phrase matching."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _build_matcher_index(pool: dict) -> dict:
    """Pre-compute lookup structures for fast product-to-species matching.

    Returns dict with keys:
      - exact_binomial: {normalized_name: binomial}
      - exact_common: {normalized_common_name: binomial}
      - common_substring: {normalized_binomial: [binomial, ...]}  (for fuzzy)
      - binomial_set: set of all normalized binomials
    """
    exact_binomial: dict[str, str] = {}
    exact_common: dict[str, str] = {}
    common_substring: dict[str, list[str]] = {}
    binomial_set: set[str] = set()

    for binomial, entry in pool.items():
        norm_b = _normalize_name(binomial)
        exact_binomial[norm_b] = binomial
        binomial_set.add(norm_b)

        for cn in entry.get("common_names") or []:
            norm_cn = _normalize_name(cn)
            if not norm_cn:
                continue
            # Only keep the first common name per species for exact matching
            if norm_cn not in exact_common:
                exact_common[norm_cn] = binomial
            # Index for substring fuzzy matching
            common_substring.setdefault(norm_cn, []).append(binomial)

    return {
        "exact_binomial": exact_binomial,
        "exact_common": exact_common,
        "common_substring": common_substring,
        "binomial_set": binomial_set,
    }


def match_product_to_species(
    product_name: str,
    pool: dict,
    index: dict | None = None,
    min_confidence: float = 0.5,
) -> list[dict]:
    """Match a product name against the species pool using pre-built index.

    Returns proposal dicts with keys: source, record, name, species,
    match_class, confidence.
    """
    norm = _normalize_name(product_name)
    if not norm:
        return []
    if index is None:
        index = _build_matcher_index(pool)

    results: list[dict] = []
    seen: set[str] = set()
    norm_words = set(norm.split())

    # 1) Exact binomial match → exact_binomial, confidence 1.0
    if norm in index["exact_binomial"]:
        binomial = index["exact_binomial"][norm]
        results.append({"species": binomial, "match_class": "exact_binomial", "confidence": 1.0})
        seen.add(binomial)

    # 2) Exact common name match → common_exact, confidence 0.85
    #    Also try compact normalization (no spaces) so "black currant"
    #    matches the common name "Blackcurrant" for Ribes nigrum.
    if norm in index["exact_common"]:
        binomial = index["exact_common"][norm]
        if binomial not in seen:
            results.append({"species": binomial, "match_class": "common_exact", "confidence": 0.85})
            seen.add(binomial)
    compact = _normalize_compact(norm)
    if compact and compact != norm and compact in index["exact_common"]:
        binomial = index["exact_common"][compact]
        if binomial not in seen:
            results.append({"species": binomial, "match_class": "common_exact", "confidence": 0.85})
            seen.add(binomial)

    # 3) Any word in product name matches a common name exactly → common_exact
    #    Skip generic category words (mushroom, pepper, bean, berry) that
    #    cause false positives when they appear as qualifiers in product names.
    for w in norm_words:
        if w in GENERIC_CATEGORY_WORDS:
            continue
        if w in index["exact_common"]:
            binomial = index["exact_common"][w]
            if binomial not in seen:
                results.append({"species": binomial, "match_class": "common_exact", "confidence": 0.85})
                seen.add(binomial)
                break
        # Also check singular form (strip trailing 's')
        singular = w.rstrip('s')
        if singular and singular != w and singular not in GENERIC_CATEGORY_WORDS and singular in index["exact_common"]:
            binomial = index["exact_common"][singular]
            if binomial not in seen:
                results.append({"species": binomial, "match_class": "common_exact", "confidence": 0.85})
                seen.add(binomial)
                break

    # 4) Product name contains a common name as a whole word → fuzzy, confidence 0.6
    #    Skip generic category words.
    for cn, binomials in index["common_substring"].items():
        if len(cn) < 4:
            continue  # skip short names that cause false substring matches
        if cn in GENERIC_CATEGORY_WORDS:
            continue
        if cn in norm_words:
            for b in binomials:
                if b not in seen:
                    results.append({"species": b, "match_class": "fuzzy", "confidence": 0.6})
                    seen.add(b)
                    break
            if any(b in seen for b in binomials):
                break  # only one fuzzy per product

    # 5) Product name contains a binomial as substring → fuzzy, confidence 0.6
    for nb in index["binomial_set"]:
        if nb not in seen and nb != norm and nb in norm:
            results.append({"species": index["exact_binomial"][nb], "match_class": "fuzzy", "confidence": 0.6})
            seen.add(nb)
            break  # only one fuzzy per product

    return [r for r in results if r["confidence"] >= min_confidence]


def generate_proposals(
    products: list[dict],
    pool: dict | None = None,
    out_dir: Path | None = None,
) -> Path:
    """Generate identity proposals for all products and write to proposals dir.

    Each product dict must have keys: source, id, name.
    Returns the path to the written proposals JSONL file.
    """
    if pool is None:
        from atlas.unified.collectors import load_pool
        pool = load_pool(Path("."))
    out_dir = out_dir or _PROPOSALS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    index = _build_matcher_index(pool)
    proposals: list[dict] = []
    seen_pair: set[tuple] = set()
    for rec in products:
        candidates = [("name", rec["name"])]
        sci = rec.get("sci") if isinstance(rec, dict) else None
        if sci:
            candidates.append(("sci", sci))
        for field, text in candidates:
            matches = match_product_to_species(text, pool, index=index)
            for m in matches:
                key = (rec["source"], rec["id"], m["species"], m["match_class"])
                if key in seen_pair:
                    continue
                seen_pair.add(key)
                proposals.append({
                    "source": rec["source"],
                    "record": rec["id"],
                    "name": rec["name"],
                    "sci": sci or "",
                    "species": m["species"],
                    "match_class": m["match_class"],
                    "confidence": m["confidence"],
                })

    out_path = out_dir / "identity-proposals.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for p in proposals:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    return out_path


def apply_exact_matches(
    proposals: list[dict],
    edges_path: Path,
    batch: str = "t19",
    approver: str = "auto",
    today: str = "2026-09-22",
) -> list[dict]:
    """Auto-approve exact_binomial proposals with confidence >= AUTO_APPROVE threshold.

    Writes approved edges to edges_path (JSONL). Returns the list of approved
    proposal dicts (for parity checking, etc.).
    """
    threshold = AUTO_APPROVE.get("exact_binomial", 2.0)
    approved: list[dict] = []
    for p in proposals:
        if p["match_class"] == "exact_binomial" and p["confidence"] >= threshold:
            approved.append(p)

    edges = [
        Edge(
            product=product_id(p["source"], p["record"]),
            species=p["species"],
            method=p["match_class"],
            confidence=p["confidence"],
            batch=batch,
            approved_by=approver,
            approved_at=today,
            status="approved",
            relation="derives_from",
        )
        for p in approved
    ]

    # Append to existing edges if file exists
    existing = load_edges(edges_path) if edges_path.is_file() else []
    existing_keys = {(e.product, e.species) for e in existing}
    new_edges = [e for e in edges if (e.product, e.species) not in existing_keys]
    all_edges = existing + new_edges
    write_edges(edges_path, all_edges)
    return approved


def check_parity(proposals: list[dict], pilot_species: list[str]) -> bool:
    """Return True when every pilot species has at least one proposal.

    Parity means both pilot species are represented in the generated
    proposals, not necessarily auto-approved edges.
    """
    proposal_species = {p["species"] for p in proposals}
    return all(sp in proposal_species for sp in pilot_species)
