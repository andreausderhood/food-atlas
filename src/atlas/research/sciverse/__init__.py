"""Sciverse integration: typesafe API client + gap-driven harvest pipeline."""
from atlas.research.sciverse.client import (
    BASE_URL,
    ENV_TOKEN_VARS,
    SciverseClient,
    SciverseError,
    SciverseHTTPError,
    load_token,
)
from atlas.research.sciverse.models import (
    AgenticHit,
    AgenticResult,
    Catalog,
    CatalogField,
    ContentPage,
    MetaFilter,
    MetaRecord,
    MetaResult,
    MetaSort,
    ModelParseError,
    RelationEntry,
    RelationPage,
)
from atlas.research.sciverse.pipeline import (
    CachedClient,
    Finding,
    GapItem,
    Hit,
    ResponseCache,
    build_query,
    harvest,
    harvest_gap,
    load_names,
    read_gaps,
)

__all__ = [
    "BASE_URL", "ENV_TOKEN_VARS", "SciverseClient", "SciverseError",
    "SciverseHTTPError", "load_token",
    "AgenticHit", "AgenticResult", "Catalog", "CatalogField", "ContentPage",
    "MetaFilter", "MetaRecord", "MetaResult", "MetaSort", "ModelParseError",
    "RelationEntry", "RelationPage",
    "CachedClient", "Finding", "GapItem", "Hit", "ResponseCache",
    "build_query", "harvest", "harvest_gap", "load_names", "read_gaps",
]
