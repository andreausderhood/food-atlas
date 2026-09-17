"""FoodAtlas v4.11 (Apache-2.0) → presence claims for pilot foods.

Only `contains` links backed by LLM literature extraction are read. CTD rows (commercial
reuse prohibited) and FDC rows (imported directly from USDA) are never used. Amounts carry
no basis, so the contract turns them into gaps. Evidence sentences are not shipped, only
PMC IDs.
"""
from __future__ import annotations

import json
from pathlib import Path

import duckdb
import yaml

from atlas.claims import Claim
from atlas.foods import FoodNode, food_part


def sql_path(path: Path) -> str:
    return "'" + str(path).replace("'", "''") + "'"


def load_aliases(path: Path) -> dict[str, str]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {fa_id: d["key"] for fa_id, d in raw.items()}


def molecule_key(fa_id: str, external_ids: dict, aliases: dict[str, str]) -> str:
    if fa_id in aliases:
        return aliases[fa_id]
    if external_ids.get("fdc_nutrient"):
        return f"nutrient:fdc:{external_ids['fdc_nutrient'][0]}"
    if external_ids.get("chebi"):
        return f"CHEBI:{external_ids['chebi'][0]}"
    if external_ids.get("pubchem_compound"):
        return f"PUBCHEM:{external_ids['pubchem_compound'][0]}"
    return f"FA:{fa_id}"


def load_foodatlas(
    bundle: Path, src_id: str, nodes: dict[str, FoodNode], aliases: dict[str, str]
) -> tuple[list[Claim], dict[str, dict]]:
    fa_to_node = {fa: n.id for n in nodes.values() for fa in n.foodatlas_ids}
    if not fa_to_node:
        return [], {}
    with duckdb.connect() as con:
        rows = con.execute(f"""
            with ta as (
                select head_id, tail_id, unnest(cast(json(attestation_ids) as varchar[])) as aid
                from read_parquet({sql_path(bundle / 'triplets.parquet')})
                where relationship_id = 'r1' and list_contains(?::varchar[], head_id)
            )
            select ta.head_id, ta.tail_id, a.conc_value, a.conc_unit, e.reference
            from ta
            join read_parquet({sql_path(bundle / 'attestations.parquet')}) a on a.attestation_id = ta.aid
            join read_parquet({sql_path(bundle / 'evidence.parquet')}) e on e.evidence_id = a.evidence_id
            where a.source like 'lit2kg:%' and e.source_type = 'pubmed'
            order by ta.head_id, ta.tail_id, a.attestation_id
        """, [sorted(fa_to_node)]).fetchall()
        tails = sorted({r[1] for r in rows})
        chemicals = {}
        if tails:
            for fa_id, name, ext, attrs in con.execute(f"""
                select foodatlas_id, common_name, external_ids, attributes
                from read_parquet({sql_path(bundle / 'entities.parquet')})
                where list_contains(?::varchar[], foodatlas_id)
            """, [tails]).fetchall():
                ext_d, attr_d = json.loads(ext or "{}"), json.loads(attrs or "{}")
                chemicals[fa_id] = (molecule_key(fa_id, ext_d, aliases), name, ext_d, attr_d)

    molecules: dict[str, dict] = {}
    refs: dict[tuple[str, str], set[str]] = {}
    claims: list[Claim] = []
    for head, tail, conc_value, conc_unit, reference in rows:
        key, name, ext_d, attr_d = chemicals[tail]
        m = molecules.setdefault(key, {"name": name, "chebi": [], "pubchem": [], "flavor": set(), "foodatlas_ids": set()})
        m["chebi"] = sorted(set(m["chebi"]) | set(ext_d.get("chebi", [])))
        m["pubchem"] = sorted(set(m["pubchem"]) | set(ext_d.get("pubchem_compound", [])))
        m["flavor"].update(attr_d.get("flavor_descriptors", []))
        m["foodatlas_ids"].add(tail)
        node = nodes[fa_to_node[head]]
        pmcid = json.loads(reference or "{}").get("pmcid")
        pmcid = str(pmcid).strip() if pmcid else ""
        ref = ("PMC" + pmcid[3:] if pmcid.upper().startswith("PMC") else f"PMC{pmcid}") if pmcid else None
        refs.setdefault((node.id, key), set()).update([ref] if ref else [])
        if conc_value is not None:
            claims.append(Claim(
                subject=node.id, group="molecules", field=f"contains:{key}", v=float(conc_value),
                unit=conc_unit, basis=None, food_part=food_part(node), src=src_id,
                derivation="extracted", ref=ref, flags=("llm_extracted",),
            ))
    for (subject, key), ids in sorted(refs.items()):
        claims.append(Claim(
            subject=subject, group="molecules", field=f"contains:{key}", v="present",
            food_part=food_part(nodes[subject]), src=src_id, derivation="extracted",
            ref=", ".join(sorted(ids)), n=len(ids), flags=("llm_extracted",),
        ))
    for m in molecules.values():
        m["flavor"] = sorted(m["flavor"])
        m["foodatlas_ids"] = sorted(m["foodatlas_ids"])
    return claims, molecules
