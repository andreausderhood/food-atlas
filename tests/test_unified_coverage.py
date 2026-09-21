import argparse
import json
from pathlib import Path

import pytest
import yaml

from atlas.claims import Claim
from atlas.registry import Source
from atlas.unified import cli as ucli
from atlas.unified.cells import Cell, aggregate
from atlas.unified.collectors import (
    Universe,
    common_names,
    food_hierarchy,
    load_universe,
    nutrients,
    species_identity,
)
from atlas.unified.fields import FIELDS
from atlas.unified.identity import Edge, write_edges
from atlas.unified.store import Store
from atlas.unified.table import build_table, regressions, render_text, write_json

POOL = {
    "malus domestica": {"common_names": ["apple"], "in_atlas": True,
                        "epd": {"path": "p/1", "distribution": "Asia", "edible_parts": ["fruit"]}},
    "beta vulgaris": {"common_names": [], "in_atlas": False,
                      "epd": {"path": "p/2", "distribution": "", "edible_parts": []}},
    "zzz nulla": {"common_names": [], "in_atlas": False},
}
SRC = Source(id="SRC-X", title="t", publisher="p", url="u", license="CC0", license_class="ship",
             license_read=True, kind="measurement", independence="independent",
             supports=("nutrition",), attribution="a")


def test_missing_subjects_are_unsearched():
    r = aggregate("k", "K", "species", {"a": Cell.FILLED, "b": Cell.NOT_APPLICABLE}, ["a", "b", "c"], None)
    assert r.counts["filled"] == 1 and r.counts["unsearched"] == 1 and not r.closed


def test_closed_means_nothing_unsearched():
    r = aggregate("k", "K", "species", {"a": Cell.SEARCHED_EMPTY, "b": Cell.FILLED}, ["a", "b"], None)
    assert r.closed and r.pct(Cell.FILLED) == 50.0


def test_table_roundtrip_and_ratchet(tmp_path):
    rows = build_table(Universe(species=POOL))
    base = tmp_path / "b.json"
    write_json(base, rows)
    assert regressions(rows, base) == []
    shrunk = build_table(Universe(species={"zzz nulla": POOL["zzz nulla"]}))
    assert any("species_identity" in p for p in regressions(shrunk, base))   # losing species loses cells
    assert "Species identity" in render_text(rows)


def test_nutrients_and_hierarchy_follow_the_edges(tmp_path):
    s = Store(tmp_path / "u.duckdb")
    claims = [Claim("prod:bls:B1", "nutrition", "nutrient:bls:VITC", 4.6, "SRC-X", "analytical",
                    unit="mg", basis="as_described", food_part="product"),
              Claim("prod:bls:B2", "nutrition", "nutrient:bls:VITC", 4.6, "SRC-X", "analytical", unit="mg")]
    s.replace_source("SRC-X", claims, {"SRC-X": SRC}, "b1")
    u = Universe(species=POOL, products=["prod:bls:B1", "prod:bls:B2", "prod:bls:B3"], store=s)
    assert nutrients(u) == {}                                          # no identity yet -> nothing on the species axis
    u.edges = [Edge("prod:bls:B1", "malus domestica", "manual", 1.0, "b", "a", "d"),
               Edge("prod:bls:B2", "beta vulgaris", "manual", 1.0, "b", "a", "d")]
    s.load_edges(u.edges)
    cells = nutrients(u)
    assert cells["malus domestica"] is Cell.FILLED
    assert cells["beta vulgaris"] is Cell.SEARCHED_EMPTY               # read, but rejected (rule 6: no basis)
    assert set(food_hierarchy(u)) == {"prod:bls:B1", "prod:bls:B2"}    # B3 is still undecided
    s.close()


def _tmp_root(tmp_path, pool):
    scope = tmp_path / "data/research/scope"
    scope.mkdir(parents=True, exist_ok=True)
    (scope / "species-pool.yaml").write_text(yaml.safe_dump({"pool": pool}), encoding="utf-8")
    return tmp_path


def test_load_universe_overlays_ledger_and_reads_edges(tmp_path):
    root = _tmp_root(tmp_path, {"malus domestica": {"in_atlas": False, "common_names": ["apple"]}})
    (root / "data/build").mkdir(parents=True)
    (root / "data/build/atlas.json").write_text(json.dumps({
        "organisms": [{"id": "org:apple", "name": "Malus domestica"},
                      {"id": "org:apple-fuji", "name": "Malus domestica 'Fuji'", "parent": "org:apple"}],
        "foods": [{"id": "food:apple", "level": "taxon_food", "taxon": "org:apple"},
                  {"id": "food:fuji", "level": "cultivar", "taxon": "org:apple-fuji",
                   "claims": [{"group": "nutrition"}]}]}), encoding="utf-8")
    write_edges(root / "data/registry/identity/edges.jsonl",
                [Edge("prod:bls:B1", "malus domestica", "manual", 1.0, "b", "a", "d")])
    u = load_universe(root, with_products=False)
    assert u.species["malus domestica"]["in_atlas"] is True           # overlay from the ledger, not the stale flag
    assert [e.product for e in u.edges] == ["prod:bls:B1"] and u.store is None
    assert u.ledger == {"nutrition": {"malus domestica"}}             # the cultivar's claim counts for its species
    assert nutrients(u) == {"malus domestica": Cell.FILLED}


def test_cli_coverage_check_gate(tmp_path, capsys, monkeypatch):
    from atlas.site import catalog
    monkeypatch.setattr(catalog, "_fdc_rows", lambda: [])              # a temp root has no raw files
    monkeypatch.setattr(catalog, "_bls_rows", lambda: [])
    root = _tmp_root(tmp_path, POOL)
    parser = argparse.ArgumentParser()
    ucli.register(parser.add_subparsers(dest="cmd"))
    assert ucli.run(parser.parse_args(["coverage", "--write-baseline"]), root) == 0
    assert (root / "docs/coverage/baseline.json").is_file() and (root / "data/build/coverage.json").is_file()
    assert ucli.run(parser.parse_args(["coverage", "--check"]), root) == 0
    _tmp_root(tmp_path, {"zzz nulla": POOL["zzz nulla"]})              # pool shrinks -> regression
    assert ucli.run(parser.parse_args(["coverage", "--check"]), root) == 1
    assert "REGRESSION" in capsys.readouterr().out


def test_common_names_collector(tmp_path):
    s = Store(tmp_path / "u.duckdb")
    src_id = Source(
        id="SRC-ID", title="t", publisher="p", url="u", license="CC0", license_class="ship",
        license_read=True, kind="measurement", independence="independent",
        supports=("identity",), attribution="a",
    )
    claims = [
        Claim("prod:fdc:100", "identity", "name", "Apple", "SRC-ID", "analytical"),
    ]
    s.replace_source("SRC-ID", claims, {"SRC-ID": src_id}, "b1")
    s.load_edges([Edge("prod:fdc:100", "store species", "manual", 1.0, "b", "a", "d")])

    species = {
        "malus domestica": {
            "common_names": ["apple"],
            "epd": {"path": "p/1"},
        },
        "beta vulgaris": {
            "common_names": [],
            "epd": {"path": "p/2"},
        },
        "wiki species": {
            "common_names": [],
            "sources": ["wiki:culinary-fruits"],
        },
        "unsearched species": {
            "common_names": [],
        },
        "ledger species": {
            "common_names": ["ledger name"],
        },
        "store species": {
            "common_names": [],
            "sources": ["wiki:fruits"],
        },
    }
    u = Universe(
        species=species,
        store=s,
        ledger={"identity": {"ledger species"}},
    )
    cells = common_names(u)
    assert cells["malus domestica"] is Cell.CONTEXT
    assert cells["beta vulgaris"] is Cell.SEARCHED_EMPTY
    assert cells["wiki species"] is Cell.SEARCHED_EMPTY
    assert cells["unsearched species"] is Cell.UNSEARCHED
    assert cells["ledger species"] is Cell.FILLED
    assert cells["store species"] is Cell.FILLED
    s.close()


def test_common_names_full_pool_closes_unsearched():
    root = Path(__file__).resolve().parent.parent
    u = load_universe(root, with_products=False)
    cells = common_names(u)
    r = aggregate("common_names", "Common names", "species", cells, u.species, "common_names")
    assert r.denominator == 26591
    assert r.counts[Cell.UNSEARCHED.value] == 0
    assert r.closed is True

