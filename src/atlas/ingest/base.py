"""Standard ingest adapter interface and registry: every bulk source enters the same door.

`atlas ingest <src_id> <path>` looks an adapter up by its source id, streams its
claims through the contract into data/build/unified.duckdb (rejects carry the
value, never a claim), and is idempotent per source like `Store.replace_source`.
"""
from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path

from atlas.claims import Claim
from atlas.unified.collectors import EDGES_PATH, STORE_PATH
from atlas.unified.identity import load_edges
from atlas.unified.store import Store


class BaseIngestAdapter:
    """One adapter per raw source: set `src_id`, implement `load()` as a lazy claim stream."""

    src_id: str = ""

    def load(self, root: Path, path: Path) -> Iterator[Claim]:
        """Yield the raw source's claims one at a time; raise on malformed input."""
        raise NotImplementedError


_REGISTRY: dict[str, BaseIngestAdapter] = {}


def register(adapter: BaseIngestAdapter) -> BaseIngestAdapter:
    """Add an adapter to the registry under its src_id; registering the same instance twice is fine."""
    if not adapter.src_id:
        raise ValueError("an ingest adapter needs a src_id")
    existing = _REGISTRY.get(adapter.src_id)
    if existing is not None and existing is not adapter:
        raise ValueError(f"src_id {adapter.src_id!r} is already registered")
    _REGISTRY[adapter.src_id] = adapter
    return adapter


def unregister(src_id: str) -> None:
    _REGISTRY.pop(src_id, None)


def get_adapter(src_id: str) -> BaseIngestAdapter:
    try:
        return _REGISTRY[src_id]
    except KeyError:
        raise KeyError(
            f"no ingest adapter registered for {src_id!r}; known: {registered() or 'none'}") from None


def registered() -> list[str]:
    return sorted(_REGISTRY)


def register_cli(sub) -> None:
    i = sub.add_parser("ingest", help="run a registered adapter and stream its claims into the unified store")
    i.add_argument("src_id", help="the source id the adapter is registered under")
    i.add_argument("path", type=Path, help="path to the raw source data (absolute, or relative to the root)")


def run(args, root: Path) -> int:
    try:
        adapter = get_adapter(args.src_id)
    except KeyError as e:
        print(str(e))
        return 2
    path = Path(args.path)
    if not path.is_absolute():
        path = root / path
    from atlas.registry import load_sources
    sources = load_sources(root / "data/registry/sources.yaml", root / "data/registry/link_status.yaml")
    store = Store(root / STORE_PATH)
    try:
        batch = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        stats = store.replace_source(args.src_id, adapter.load(root, path), sources, batch)
        edges = load_edges(root / EDGES_PATH)
        if edges:                      # load_edges cannot handle an empty batch
            store.load_edges(edges)
    finally:
        store.close()
    print(f"{args.src_id}: {stats.accepted} accepted · {stats.rejected} rejected")
    return 0


# Import bulk adapters so they self-register on module load.
from atlas.ingest import biofoodcomp  # noqa: E402, F401
from atlas.ingest import bls_bulk  # noqa: E402, F401
from atlas.ingest import cofid  # noqa: E402, F401
from atlas.ingest import bulk_fdc  # noqa: E402, F401
from atlas.ingest import bulk_foodatlas  # noqa: E402, F401
from atlas.ingest import ciqual  # noqa: E402, F401
from atlas.ingest import duke  # noqa: E402, F401
from atlas.ingest import flavonoids  # noqa: E402, F401
from atlas.ingest import imppat  # noqa: E402, F401
from atlas.ingest import swiss_fcdb  # noqa: E402, F401
from atlas.ingest import tcm  # noqa: E402, F401
from atlas.ingest import pomological  # noqa: E402, F401
