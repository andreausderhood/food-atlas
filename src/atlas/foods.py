"""Organisms, processes and the four typed food levels (product.md §4 Food levels)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

RANKS = ("species", "subspecies", "convar", "var")
LEVELS = ("taxon_food", "cultivar", "part", "form")
PARTS = (
    "whole", "head", "leaf", "inflorescence", "stem", "axillary_bud",
    "exocarp", "mesocarp", "seed", "seedling",
)


class FoodModelError(ValueError):
    pass


@dataclass(frozen=True)
class Organism:
    id: str
    name: str
    rank: str
    parent: str | None
    ncbi_taxon: int | None


@dataclass(frozen=True)
class FoodNode:
    id: str
    level: str
    name: str
    name_de: str | None = None
    derives_from: str | None = None
    is_a: str | None = None
    part_of: str | None = None
    part: str | None = None
    process: str | None = None
    default_part: str = "whole"
    foodon: str | None = None
    foodatlas_ids: tuple[str, ...] = ()
    fdc_match: tuple[str, ...] = ()
    bls_codes: tuple[str, ...] = ()


def _read(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _reject_cycles(parents: dict[str, str | None]) -> None:
    done: set[str] = set()
    for start in parents:
        chain: set[str] = set()
        current = start
        while current in parents and current not in done:
            if current in chain:
                raise FoodModelError(f"cycle at {current}")
            chain.add(current)
            current = parents[current]
        done.update(chain)


def load_organisms(path: Path) -> dict[str, Organism]:
    out: dict[str, Organism] = {}
    for oid, d in _read(path).items():
        if not oid.startswith("org:"):
            raise FoodModelError(f"{oid}: organism ids start with 'org:'")
        if d["rank"] not in RANKS:
            raise FoodModelError(f"{oid}: rank {d['rank']!r} not in {RANKS}")
        out[oid] = Organism(oid, d["name"], d["rank"], d.get("parent"), d.get("ncbi_taxon"))
    for o in out.values():
        if o.rank == "species" and o.parent is not None:
            raise FoodModelError(f"{o.id}: a species has no parent in this register")
        if o.rank != "species" and o.parent is None:
            raise FoodModelError(f"{o.id}: an infraspecific taxon needs a parent")
        if o.parent is not None and o.parent not in out:
            raise FoodModelError(f"{o.id}: parent {o.parent!r} is not registered")
    _reject_cycles({o.id: o.parent for o in out.values()})
    return out


def load_processes(path: Path) -> dict[str, str]:
    return {pid: d["name"] for pid, d in _read(path).items()}


def load_foods(
    path: Path, organisms: dict[str, Organism], processes: dict[str, str]
) -> tuple[dict[str, FoodNode], dict[str, str]]:
    raw = _read(path)
    excluded = {fa: d["reason"] for fa, d in (raw.pop("excluded_foodatlas", None) or {}).items()}
    nodes: dict[str, FoodNode] = {}
    for fid, d in raw.items():
        d = dict(d)
        for key in ("foodatlas_ids", "fdc_match", "bls_codes"):
            d[key] = tuple(d.get(key) or ())
        nodes[fid] = FoodNode(id=fid, **d)
    errors = [e for n in nodes.values() for e in _node_errors(n, nodes, organisms, processes)]
    seen: dict[str, str] = {}
    bls: dict[str, str] = {}
    for n in nodes.values():
        for fa in n.foodatlas_ids:
            if fa in excluded:
                errors.append(f"{n.id}: FoodAtlas {fa} is excluded ({excluded[fa]})")
            if fa in seen:
                errors.append(f"FoodAtlas {fa} mapped to both {seen[fa]} and {n.id}")
            seen[fa] = n.id
        for code in n.bls_codes:
            if code in bls:
                errors.append(f"bls code {code!r} mapped to both {bls[code]} and {n.id}")
            bls[code] = n.id
    if errors:
        raise FoodModelError("\n".join(errors))
    _reject_cycles({n.id: _food_parent(n) for n in nodes.values()})
    return nodes, excluded


def _node_errors(n: FoodNode, nodes, organisms, processes) -> list[str]:
    e: list[str] = []
    if not n.id.startswith("food:"):
        e.append(f"{n.id}: food ids start with 'food:'")
    if n.level not in LEVELS:
        return e + [f"{n.id}: level {n.level!r} not in {LEVELS}"]
    if n.default_part not in PARTS:
        e.append(f"{n.id}: default_part {n.default_part!r} not in {PARTS}")
    if n.level == "taxon_food" and n.derives_from not in organisms:
        e.append(f"{n.id}: taxon_food must derive from a registered organism")
    if n.level == "cultivar" and (n.is_a not in nodes or nodes[n.is_a].level != "taxon_food"):
        e.append(f"{n.id}: cultivar must be is_a a taxon_food")
    if n.level == "part":
        if n.part not in PARTS:
            e.append(f"{n.id}: part {n.part!r} not in {PARTS}")
        if n.part_of not in nodes or nodes[n.part_of].level not in ("taxon_food", "cultivar"):
            e.append(f"{n.id}: part must be part_of a taxon_food or cultivar")
    if n.level == "form":
        if n.derives_from not in nodes:
            e.append(f"{n.id}: form must derive from a registered food")
        if n.process not in processes:
            e.append(f"{n.id}: form needs a registered process")
    return e


def food_part(node: FoodNode) -> str:
    return node.part if node.level == "part" else node.default_part


def basis(node: FoodNode) -> str:
    """Raw foods are reported per 100 g fresh edible portion; processed forms as sold."""
    return "as_sold" if node.level == "form" else "fresh_weight"


def _food_parent(node: FoodNode) -> str | None:
    if node.level == "cultivar":
        return node.is_a
    if node.level == "part":
        return node.part_of
    if node.level == "form":
        return node.derives_from
    return None


def taxon_of(node: FoodNode, nodes: dict[str, FoodNode]) -> str:
    seen: set[str] = set()
    cur = node
    while cur.level != "taxon_food":
        if cur.id in seen:
            raise FoodModelError(f"cycle at {cur.id}")
        seen.add(cur.id)
        parent = _food_parent(cur)
        if parent is None or parent not in nodes:
            raise FoodModelError(f"{cur.id}: no taxon_food ancestor found")
        cur = nodes[parent]
    return cur.derives_from
