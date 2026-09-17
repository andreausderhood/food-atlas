"""Fail-closed write classification using the SAME contract as atlas build.

A genuine quotation proves occurrence, not that an asserted numeric value follows
from it. Until raw-row adapters verify the whole claim, local evidence is proposal
only. There is deliberately no model-controlled `verified=True` escape hatch.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from atlas.claims import Claim, Gap
from atlas.contract import check
from atlas.registry import Source
from atlas.research.evidence import Cache


@dataclass(frozen=True)
class Evidence:
    ref: str
    quote: str
    cache_key: str | None = None


@dataclass(frozen=True)
class Decision:
    action: str
    reason: str
    gap: Gap | None = None


def verify_evidence(e: Evidence, root: Path) -> None:
    if not isinstance(e.quote, str) or not e.quote.strip():
        raise ValueError("empty evidence quotation")
    if urlsplit(e.ref).scheme in ("https", "http"):
        text = Cache(root / "data/research/cache").read(e.cache_key or "", e.ref)
    else:
        path = Path(e.ref)
        raw = (root / "data/raw").resolve()
        if path.is_absolute() or not (root / path).resolve().is_relative_to(raw):
            raise ValueError("evidence must resolve under data/raw")
        text = (root / path).read_text(encoding="utf-8")
    if e.quote not in text:
        raise ValueError("evidence quotation does not occur in retrieved text")


def classify(claim: Claim, sources: dict[str, Source], evidence: list[Evidence], root: Path) -> Decision:
    gap = check(claim, sources)
    if gap:
        return Decision("reject", gap.question, gap)
    if not evidence or not claim.ref or not any(e.ref == claim.ref for e in evidence):
        return Decision("reject", "A matching evidence record is required for the claim reference.")
    try:
        for e in evidence:
            verify_evidence(e, root)
    except (OSError, ValueError, KeyError, UnicodeError) as error:
        return Decision("reject", str(error))
    return Decision("propose", "Evidence occurrence verified; semantic review required. No raw-row proof adapter yet.")
