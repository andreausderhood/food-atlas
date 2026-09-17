"""Source registry: who backs a claim, under which license, for which claim groups."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

CLAIM_GROUPS = (
    "identity", "nutrition", "molecules", "bioactivity", "sensory", "origin",
    "geography", "growing", "season", "process", "regulatory", "narrative",
)
LICENSE_CLASSES = ("ship", "cite", "adapter", "separate")
KINDS = (
    "measurement", "compilation", "registry", "research",
    "literature_extraction", "brand_claim", "library_editorial", "unverified",
)
INDEPENDENCE = ("independent", "declared_by_maker", "library_editorial")
LINK_STATUSES = ("unchecked", "ok", "redirected", "broken")
REQUIRED = (
    "title", "publisher", "url", "license", "license_class", "license_read",
    "kind", "independence", "supports", "attribution",
)


class RegistryError(ValueError):
    pass


@dataclass(frozen=True)
class Source:
    id: str
    title: str
    publisher: str
    url: str
    license: str
    license_class: str
    license_read: bool
    kind: str
    independence: str
    supports: tuple[str, ...]
    attribution: str
    identifier: str | None = None
    license_url: str | None = None
    link_status: str = "unchecked"


def _read(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_sources(path: Path, link_status_path: Path | None = None) -> dict[str, Source]:
    status = _read(link_status_path) if link_status_path and link_status_path.exists() else {}
    sources: dict[str, Source] = {}
    for sid, d in _read(path).items():
        missing = [k for k in REQUIRED if k not in d]
        if missing:
            raise RegistryError(f"{sid}: missing fields {missing}")
        for key, allowed in (("license_class", LICENSE_CLASSES), ("kind", KINDS), ("independence", INDEPENDENCE)):
            if d[key] not in allowed:
                raise RegistryError(f"{sid}: {key} {d[key]!r} not in {allowed}")
        if type(d["license_read"]) is not bool:
            raise RegistryError(f"{sid}: license_read must be an explicit boolean")
        unknown = sorted(set(d["supports"]) - set(CLAIM_GROUPS))
        if unknown:
            raise RegistryError(f"{sid}: unknown claim groups {unknown}")
        link = (status.get(sid) or {}).get("status", "unchecked")
        if link not in LINK_STATUSES:
            raise RegistryError(f"{sid}: link status {link!r} not in {LINK_STATUSES}")
        sources[sid] = Source(
            id=sid, title=d["title"], publisher=d["publisher"], url=d["url"],
            license=d["license"], license_class=d["license_class"],
            license_read=d["license_read"], kind=d["kind"],
            independence=d["independence"], supports=tuple(d["supports"]),
            attribution=d["attribution"], identifier=d.get("identifier"),
            license_url=d.get("license_url"), link_status=link,
        )
    return sources
