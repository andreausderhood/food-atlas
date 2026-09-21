"""Task 16: standard ingest adapter interface, registry and the `atlas ingest` CLI."""
from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from atlas.claims import Claim
from atlas.cli import main
from atlas.ingest.base import BaseIngestAdapter


class JsonlAdapter(BaseIngestAdapter):
    """Minimal example adapter: one JSON line per product record.

    Contract shape used by the bulk store (rule 6'): prod: subject, as_described
    basis, food_part product. Bad lines stay in the file; the store routes them.
    """

    src_id = "SRC-TEST"

    def load(self, root: Path, path: Path) -> Iterator[Claim]:
        with path.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                d = json.loads(line)
                yield Claim(
                    subject=d["subject"], group="nutrition", field=d["field"], v=d["v"],
                    src=self.src_id, derivation="analytical", unit="mg",
                    basis=d.get("basis"), food_part=d.get("food_part", "product"), ref=d["ref"],
                )


SOURCES_YAML = """
SRC-TEST:
  title: Test source
  publisher: Test publisher
  url: https://example.com/test
  license: CC0-1.0
  license_class: ship
  license_read: true
  kind: measurement
  independence: independent
  supports: [nutrition]
  attribution: "Test publisher."
"""

CLAIMS = [
    {"subject": "prod:test:1", "field": "nutrient:test:c", "v": 4.6, "ref": "test:1",
     "basis": "as_described"},
    {"subject": "prod:test:2", "field": "nutrient:test:c", "v": 3.1, "ref": "test:2"},   # no basis
]


@pytest.fixture
def clean_registry():
    from atlas.ingest import base
    before = set(base.registered())
    yield base
    for src_id in set(base.registered()) - before:
        base.unregister(src_id)


@pytest.fixture
def ingest_root(tmp_path):
    root = tmp_path / "proj"
    reg = root / "data/registry"
    reg.mkdir(parents=True)
    (reg / "sources.yaml").write_text(SOURCES_YAML, encoding="utf-8")
    claims = root / "claims.jsonl"
    claims.write_text("\n".join(json.dumps(c) for c in CLAIMS) + "\n", encoding="utf-8")
    return root, claims


def test_adapter_interface_load_is_abstract():
    from atlas.ingest.base import BaseIngestAdapter
    with pytest.raises(NotImplementedError):
        BaseIngestAdapter().load(Path("."), Path("."))


def test_registry_registers_and_discovers_by_src_id(clean_registry):
    adapter = JsonlAdapter()
    clean_registry.register(adapter)
    assert clean_registry.get_adapter("SRC-TEST") is adapter
    assert "SRC-TEST" in clean_registry.registered()


def test_registry_rejects_duplicate_src_id(clean_registry):
    clean_registry.register(JsonlAdapter())
    with pytest.raises(ValueError, match="SRC-TEST"):
        clean_registry.register(JsonlAdapter())


def test_registry_requires_a_src_id(clean_registry):
    class NoId(BaseIngestAdapter):
        pass
    with pytest.raises(ValueError, match="src_id"):
        clean_registry.register(NoId())


def test_registry_unknown_src_id_raises_with_known_ids(clean_registry):
    with pytest.raises(KeyError):
        clean_registry.get_adapter("SRC-NOPE")


def test_adapter_streams_claims(ingest_root):
    from atlas.ingest.base import BaseIngestAdapter
    root, claims = ingest_root
    class Reader(BaseIngestAdapter):
        src_id = "SRC-TEST"
        def load(self, root, path):
            yield from (json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    assert not isinstance(Reader().load(root, claims), list)   # lazy stream, not a materialized list


def test_atlas_ingest_runs_adapter_and_writes_store(clean_registry, ingest_root, capsys):
    from atlas.unified.store import Store
    clean_registry.register(JsonlAdapter())
    root, claims = ingest_root
    code = main(["--root", str(root), "ingest", "SRC-TEST", "claims.jsonl"])   # relative to the root
    assert code == 0
    assert "accepted" in capsys.readouterr().out
    s = Store(root / "data/build/unified.duckdb")
    # claim 2 has no basis on a prod: subject -> rule 6, carried as a reject, never a claim
    assert s.con.execute("SELECT COUNT(*) FROM datapoints").fetchone()[0] == 1
    assert s.con.execute("SELECT subject, rule, carried FROM rejects").fetchall() == [("prod:test:2", 6, "3.1")]
    s.close()


def test_atlas_ingest_unknown_src_id_fails_cleanly(clean_registry, ingest_root, capsys):
    root, _ = ingest_root
    assert main(["--root", str(root), "ingest", "SRC-NOPE", "claims.jsonl"]) == 2
    assert "SRC-NOPE" in capsys.readouterr().out
