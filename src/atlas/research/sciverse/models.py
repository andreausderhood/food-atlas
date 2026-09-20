"""Typesafe models for the Sciverse API (https://api.sciverse.space).

Every model is a frozen dataclass with a strict parser: unknown shapes raise
``ModelParseError`` instead of slipping ``None`` into the pipeline. Extra keys
on hits and metadata records are preserved in ``raw`` for provenance; on all
other payloads they are discarded.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class ModelParseError(ValueError):
    """A Sciverse response did not match the documented shape."""


def _require(d: Any, key: str, types: type | tuple, where: str) -> Any:
    if not isinstance(d, dict):
        raise ModelParseError(f"{where}: expected object, got {type(d).__name__}")
    if key not in d or d[key] is None:
        raise ModelParseError(f"{where}: missing required field {key!r}")
    value = d[key]
    if not isinstance(value, types):
        raise ModelParseError(
            f"{where}: field {key!r} has type {type(value).__name__}, expected {types}")
    return value


def _optional(d: Any, key: str, types: type | tuple, where: str) -> Any | None:
    if not isinstance(d, dict):
        raise ModelParseError(f"{where}: expected object, got {type(d).__name__}")
    value = d.get(key)
    if value is None or isinstance(value, types):
        return value
    raise ModelParseError(
        f"{where}: field {key!r} has type {type(value).__name__}, expected {types}")


def _int_or_str_int(value: Any, where: str) -> int:
    """Large int64 totals may arrive as strings; the API also ships integral
    numerics as floats (publication_published_year=2018.0)."""
    if isinstance(value, bool):
        raise ModelParseError(f"{where}: boolean where int expected")
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            raise ModelParseError(f"{where}: non-numeric total {value!r}") from None
    raise ModelParseError(f"{where}: total has type {type(value).__name__}")


@dataclass(frozen=True)
class AgenticHit:
    """One evidence chunk from ``POST /agentic-search``."""
    chunk: str
    doc_id: str | None
    title: str | None
    doi: str | None
    chunk_id: str | None
    score: float | None
    source_type: str | None
    offset: int | None
    page_no: int | None
    raw: dict = field(repr=False, hash=False, compare=False)

    @classmethod
    def parse(cls, d: dict) -> "AgenticHit":
        where = "agentic-search hit"
        chunk = _require(d, "chunk", str, where)
        return cls(
            chunk=chunk,
            doc_id=_optional(d, "doc_id", str, where),
            title=_optional(d, "title", str, where),
            doi=_optional(d, "doi", str, where),
            chunk_id=_optional(d, "chunk_id", str, where),
            score=_optional(d, "score", (int, float), where),
            source_type=_optional(d, "source_type", str, where),
            offset=_optional(d, "offset", int, where),
            page_no=_optional(d, "page_no", int, where),
            raw=dict(d),
        )


@dataclass(frozen=True)
class AgenticResult:
    hits: tuple[AgenticHit, ...]
    raw: dict = field(repr=False, hash=False, compare=False)

    @classmethod
    def parse(cls, d: dict) -> "AgenticResult":
        where = "agentic-search response"
        hits = _require(d, "hits", (list, tuple), where)
        return cls(
            hits=tuple(AgenticHit.parse(h) for h in hits),
            raw=dict(d),
        )


RELATIONS = ("CITATIONS", "REFERENCES", "RELATED_WORKS")
FRESHNESS = ("NONE", "MILD", "STRONG")
SOURCE_TYPES = ("web", "pdf")


@dataclass(frozen=True)
class MetaFilter:
    field: str
    operator: str
    value: Any

    def to_payload(self) -> dict:
        return {"field": self.field, "operator": self.operator, "value": self.value}


@dataclass(frozen=True)
class MetaSort:
    field: str
    order: str = "SORT_ORDER_DESC"  # SORT_ORDER_DESC | SORT_ORDER_ASC

    def to_payload(self) -> dict:
        return {"field": self.field, "order": self.order}


@dataclass(frozen=True)
class MetaRecord:
    unique_id: str
    doc_id: str | None
    title: str | None
    doi: str | None
    year: int | None
    venue: str | None
    raw: dict = field(repr=False, hash=False, compare=False)

    @classmethod
    def parse(cls, d: dict) -> "MetaRecord":
        where = "meta-search record"
        unique_id = _require(d, "unique_id", str, where)
        year = _optional(d, "publication_published_year", (int, float), where)
        if isinstance(year, float):
            year = _int_or_str_int(year, f"{where} publication_published_year")
        return cls(
            unique_id=unique_id,
            doc_id=_optional(d, "doc_id", str, where),
            title=_optional(d, "title", str, where),
            doi=_optional(d, "doi", str, where),
            year=year,
            venue=_optional(d, "publication_venue_name_unified", str, where),
            raw=dict(d),
        )


@dataclass(frozen=True)
class MetaResult:
    results: tuple[MetaRecord, ...]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    next_cursor: str | None
    raw: dict = field(repr=False, hash=False, compare=False)

    @classmethod
    def parse(cls, d: dict) -> "MetaResult":
        where = "meta-search response"
        results = _require(d, "results", (list, tuple), where)
        total_count = _int_or_str_int(_require(d, "total_count", (int, str), where), f"{where} total_count")
        return cls(
            results=tuple(MetaRecord.parse(r) for r in results),
            total_count=total_count,
            page=_int_or_str_int(_require(d, "page", (int, str), where), f"{where} page"),
            page_size=_int_or_str_int(_require(d, "page_size", (int, str), where), f"{where} page_size"),
            total_pages=_int_or_str_int(_require(d, "total_pages", (int, str), where), f"{where} total_pages"),
            next_cursor=_optional(d, "next_cursor", str, where) or None,
            raw=dict(d),
        )


@dataclass(frozen=True)
class CatalogField:
    name: str
    type: str | None
    filterable: bool | None
    sortable: bool | None
    searchable: bool | None
    description: str | None
    operators: tuple[str, ...]
    sample_values: tuple[Any, ...] | None

    @classmethod
    def parse(cls, d: dict) -> "CatalogField":
        where = "meta-catalog field"
        name = _require(d, "name", str, where)
        ops = _optional(d, "operators", (list, tuple), where) or ()
        samples = _optional(d, "sample_values", (list, tuple), where)
        return cls(
            name=name,
            type=_optional(d, "type", str, where),
            filterable=_optional(d, "filterable", bool, where),
            sortable=_optional(d, "sortable", bool, where),
            searchable=_optional(d, "searchable", bool, where),
            description=_optional(d, "description", str, where),
            operators=tuple(str(o) for o in ops),
            sample_values=tuple(samples) if samples is not None else None,
        )


@dataclass(frozen=True)
class Catalog:
    fields: tuple[CatalogField, ...]
    default_fields: tuple[str, ...]
    filter_operators: tuple[str, ...]

    @classmethod
    def parse(cls, d: dict) -> "Catalog":
        where = "meta-catalog response"
        fields = _require(d, "fields", (list, tuple), where)
        default = _optional(d, "default_fields", (list, tuple), where) or ()
        ops = _optional(d, "filter_operators", (list, tuple), where) or ()
        return cls(
            fields=tuple(CatalogField.parse(f) for f in fields),
            default_fields=tuple(str(f) for f in default),
            filter_operators=tuple(str(o) for o in ops),
        )

    def filterable_names(self) -> frozenset[str]:
        return frozenset(f.name for f in self.fields if f.filterable)

    def sortable_names(self) -> frozenset[str]:
        return frozenset(f.name for f in self.fields if f.sortable)


@dataclass(frozen=True)
class RelationEntry:
    id: str
    id_type: str | None
    title: str | None

    @classmethod
    def parse(cls, d: dict) -> "RelationEntry":
        where = "meta-paper-relations entry"
        return cls(
            id=_require(d, "id", str, where),
            id_type=_optional(d, "id_type", str, where),
            title=_optional(d, "title", str, where),
        )


@dataclass(frozen=True)
class RelationPage:
    items: tuple[RelationEntry, ...]
    total_count: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def parse(cls, d: dict) -> "RelationPage":
        where = "meta-paper-relations response"
        items = _require(d, "items", (list, tuple), where)
        return cls(
            items=tuple(RelationEntry.parse(i) for i in items),
            total_count=_int_or_str_int(_require(d, "total_count", (int, str), where), f"{where} total_count"),
            page=_int_or_str_int(_require(d, "page", (int, str), where), f"{where} page"),
            page_size=_int_or_str_int(_require(d, "page_size", (int, str), where), f"{where} page_size"),
            total_pages=_int_or_str_int(_require(d, "total_pages", (int, str), where), f"{where} total_pages"),
        )


@dataclass(frozen=True)
class ContentPage:
    text: str
    bytes_returned: int | None
    text_length: int | None
    next_offset: int | None
    more: bool

    @classmethod
    def parse(cls, d: dict) -> "ContentPage":
        where = "content response"
        more = _optional(d, "more", bool, where)
        return cls(
            text=_require(d, "text", str, where),
            bytes_returned=_optional(d, "bytes_returned", int, where),
            text_length=_optional(d, "text_length", int, where),
            next_offset=_optional(d, "next_offset", int, where),
            more=bool(more),
        )
