"""One entry point: registries + raw sources + curated files → validated claims → data/build."""
from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import duckdb

from atlas.claims import Claim, Gap
from atlas.coverage import missing_coverage
from atlas.contract import ValidationResult, validate
from atlas.curated import load_curated
from atlas.foods import load_foods, load_organisms, load_processes, taxon_of
from atlas.ingest.bls import load_bls
from atlas.ingest.fdc import load_fdc
from atlas.ingest.foodatlas import load_aliases, load_foodatlas, sql_path
from atlas.registry import Source, load_sources

RAW = {
    "fdc_foundation": ("data/raw/fdc-foundation", "SRC-FDC-FOUNDATION-2026-04"),
    "fdc_srlegacy": ("data/raw/fdc-srlegacy", "SRC-FDC-SRLEGACY-2018-04"),
    "bls": ("data/raw/bls", "SRC-BLS-4.0"),
    "foodatlas": ("data/raw/foodatlas/foodatlas-v4.11", "SRC-FOODATLAS-V4.11"),
}
CLAIM_COLUMNS = ["subject", "group", "field", "v", "unit", "basis", "food_part", "src", "tier",
                 "derivation", "method", "ref", "v_min", "v_max", "n", "flags", "curated"]
GAP_COLUMNS = ["subject", "field", "rule", "question", "would_be_settled_by", "carried_value", "src"]


@dataclass
class BuildResult:
    validation: ValidationResult
    payload: dict


def claim_dict(c: Claim) -> dict:
    d = asdict(c)
    d["tier"] = c.tier
    d["flags"] = list(c.flags)
    return d


def build(root: Path, require_raw: bool = True) -> BuildResult:
    reg = root / "data/registry"
    sources = load_sources(reg / "sources.yaml", reg / "link_status.yaml")
    organisms = load_organisms(reg / "organisms.yaml")
    processes = load_processes(reg / "processes.yaml")
    nodes, excluded = load_foods(reg / "foods.yaml", organisms, processes)
    claims: list[Claim] = []
    nutrients: dict[str, dict] = {}
    molecules: dict[str, dict] = {}
    names_de: dict[str, str] = {}
    missing_raw = []
    for name, (rel, src_id) in RAW.items():
        path = root / rel
        if not path.exists():
            if require_raw:
                raise FileNotFoundError(f"{name}: {path} is missing — run `atlas fetch`")
            missing_raw.append((name, src_id))
            continue
        if name.startswith("fdc"):
            found, used = load_fdc(path, src_id, nodes)
            nutrients.update(used)
        elif name == "bls":
            found, used, de = load_bls(path, src_id, nodes)
            nutrients.update(used)
            names_de.update(de)
        else:
            found, molecules = load_foodatlas(path, src_id, nodes, load_aliases(reg / "molecule_aliases.yaml"))
        claims.extend(found)
    claims.extend(load_curated(root / "data/curated"))
    known_subjects = set(organisms) | set(nodes)
    unknown = sorted({c.subject for c in claims} - known_subjects)
    if unknown:
        raise ValueError(f"Unregistered claim subjects: {unknown}")
    result = validate(claims, sources)
    result.gaps.extend(missing_coverage(result.accepted, organisms, nodes))
    for name, src_id in missing_raw:
        result.gaps.append(Gap("dataset:" + name, "raw_source", 5,
            "Dataset not downloaded; this build has incomplete coverage.",
            "Approve and fetch the source dataset, then rebuild.", src=src_id))
    allowed_fields = {c.field for c in result.accepted}
    nutrients = {k: v for k, v in nutrients.items() if k in allowed_fields}
    molecules = {k: v for k, v in molecules.items() if "contains:" + k in allowed_fields}
    payload = make_payload(result, sources, organisms, nodes, processes, nutrients, molecules, names_de, excluded)
    payload["stats"]["missing_raw"] = [name for name, _ in missing_raw]
    payload["stats"]["partial"] = bool(missing_raw)
    write_outputs(root / "data/build", result, payload)
    write_notice(root / "NOTICE.md", result, sources)
    return BuildResult(result, payload)


def make_payload(result, sources, organisms, nodes, processes, nutrients, molecules, names_de, excluded) -> dict:
    by_subject: dict[str, list[dict]] = {}
    for c in result.accepted:
        by_subject.setdefault(c.subject, []).append(claim_dict(c))
    gaps_by_subject: dict[str, list[dict]] = {}
    for g in result.gaps:
        gaps_by_subject.setdefault(g.subject, []).append(asdict(g))
    counts: dict[str, int] = {}
    for c in result.accepted:
        counts[c.src] = counts.get(c.src, 0) + 1
    return {
        "sources": [asdict(s) | {"claims": counts.get(s.id, 0)} for s in sources.values()],
        "organisms": [asdict(o) | {"claims": by_subject.get(o.id, [])} for o in organisms.values()],
        "foods": [
            asdict(n) | {
                "taxon": taxon_of(n, nodes),
                "name_de": n.name_de or names_de.get(n.id),
                "claims": by_subject.get(n.id, []),
                "gaps": gaps_by_subject.get(n.id, []),
            }
            for n in nodes.values()
        ],
        "processes": processes,
        "nutrients": nutrients,
        "molecules": molecules,
        "gaps": [asdict(g) for g in result.gaps],
        "excluded_foodatlas": excluded,
        "stats": {"accepted": len(result.accepted), "gaps": len(result.gaps), "sources_used": sorted(counts)},
    }


def _write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: (";".join(v) if isinstance(v, list) else v) for k, v in r.items()})


def write_outputs(out: Path, result: ValidationResult, payload: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "atlas.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str, allow_nan=False), encoding="utf-8")
    _write_csv(out / "claims.csv", CLAIM_COLUMNS, [claim_dict(c) for c in result.accepted])
    _write_csv(out / "gaps.csv", GAP_COLUMNS, [asdict(g) for g in result.gaps])
    db = out / "atlas.duckdb"
    db.unlink(missing_ok=True)
    con = duckdb.connect(str(db))
    for table in ("claims", "gaps"):
        con.execute(f"create table {table} as select * from read_csv({sql_path(out / f'{table}.csv')}, "
                    "header = true, all_varchar = true)")
    # Keep CSV-compatible values while exposing typed analytical columns.
    for column, dtype in (("tier", "INTEGER"), ("n", "INTEGER"),
                          ("v_min", "DOUBLE"), ("v_max", "DOUBLE"), ("curated", "BOOLEAN")):
        con.execute(f'ALTER TABLE claims ALTER COLUMN "{column}" TYPE {dtype} USING TRY_CAST("{column}" AS {dtype})')
    con.execute('ALTER TABLE claims ADD COLUMN value_numeric DOUBLE')
    con.execute('UPDATE claims SET value_numeric = TRY_CAST(v AS DOUBLE)')
    con.execute('ALTER TABLE gaps ALTER COLUMN rule TYPE INTEGER USING TRY_CAST(rule AS INTEGER)')
    # Identity and display fields are queryable; full objects remain lossless JSON.
    for table in ("foods", "organisms", "sources", "molecules", "nutrients", "processes"):
        con.execute(f'CREATE TABLE {table} (id VARCHAR PRIMARY KEY, name VARCHAR, data JSON)')
        data = payload[table]
        if isinstance(data, dict):
            rows = [(key, value.get("name", key) if isinstance(value, dict) else value,
                     json.dumps(value, ensure_ascii=False, allow_nan=False)) for key, value in data.items()]
        else:
            rows = [(value["id"], value.get("name", value.get("title", value["id"])),
                     json.dumps(value, ensure_ascii=False, allow_nan=False)) for value in data]
        if rows:
            con.executemany(f'INSERT INTO {table} VALUES (?, ?, ?)', rows)
    con.close()


def write_notice(path: Path, result: ValidationResult, sources: dict[str, Source]) -> None:
    used = sorted({c.src for c in result.accepted} | {g.src for g in result.gaps if g.carried_value is not None and g.src in sources})
    lines = [
        "# NOTICE",
        "",
        "Generated by `atlas build`. Do not hand-edit.",
        "",
        "- Code: MIT (`LICENSE`).",
        "- Curated data in `data/registry/` and `data/curated/`: CC BY 4.0 (`LICENSE-DATA`).",
        "- Imported data keeps its upstream license:",
        "",
        "| Source | License | Attribution | URL |",
        "| :--- | :--- | :--- | :--- |",
    ]
    for sid in used:
        s = sources[sid]
        lines.append(f"| {s.title} (`{sid}`) | {s.license} | {s.attribution} | {s.url} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
