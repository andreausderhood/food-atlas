"""Gap-driven Sciverse harvest: turn open atlas gaps into candidate evidence.

Deterministic, model-free: per gap it builds the query from
docs/sciverse-prompts.md §2.1 (rule 6: amount without basis/part) or §4
(rule 5: unverified carried value), runs at most ``per_gap_calls`` Sciverse
calls (§12 batch budget), grades hits against the traceability rules and
writes findings as YAML next to a run manifest. Everything it emits is
CANDIDATE evidence for curation — nothing here publishes a claim.

Fail-closed by design (docs/research-workflow.md): a finding that cannot be
quoted verbatim from retrieved text is not recorded.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import time
from dataclasses import dataclass, field as dc_field
from pathlib import Path

from atlas.research.sciverse.client import SciverseClient
from atlas.research.sciverse.models import AgenticResult
from atlas.research.sciverse.prompts import rule5_query, rule6_query

UNIT_RE = re.compile(
    r"\d+(?:[.,]\d+)?\s*(?:µ|μ|u)?\s*(?:mg|µg|μg|mcg|ug|g|kg|IU|mmol|meq)\s*"
    r"(?:[A-Z][A-Za-z0-9-]{1,11}\s*)?(?:/\s*(?:100\s*)?(?:g|kg|ml|mL)\b|/\s*100\s*g\b)?")
PER_MASS_RE = re.compile(
    r"\d+(?:[.,]\d+)?\s*(?:µ|μ|u)?\s*(?:mg|µg|μg|mcg|ug|g|kg|IU|mmol|µmol|μmol)\s*"
    r"(?:[A-Z][A-Za-z0-9-]{1,11}\s*)?/\s*(?:100\s*)?(?:g|kg|ml|mL)")
# the corpus mangles numbers into LaTeX: "per $100\mathrm{g}$", "$0.97\mathrm{g}$ DW"
LATEX_VAL_RE = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*\\(?:mathrm|text)\{"
    r"(mg|µg|μg|ug|g|kg|mL|ml|mmol|µmol|μmol|µM|μM)\}")
BASIS_RE = re.compile(
    r"fresh\s+weight|\bfw\b|dry\s+(?:matter|weight)\b|\bdw\b|"
    r"as\s+(?:sold|consumed|purchased)\b|as\s+is\b|moisture\s+content", re.I)
# a figure quoted with a bracketed citation is second-hand (rule 10); a
# DW/FW value is a water-content ratio, not a nutrient concentration
CITED_RE = re.compile(r"\[\d{1,3}\]\s*\.?\s*$")
RATIO_RE = re.compile(r"\b(?:g|kg|mg)\s+(?:DW|FW)\s*/|\b(?:DW|FW)\s*/\s*(?:DW|FW|g)\b", re.I)
PART_RE = re.compile(
    r"\b(peel|peels|flesh|pulp|seed|seeds|floret|florets|leaf|leaves|sprout"
    r"|sprouts|juice|pomace|stalk|curd|head)\b", re.I)
MAX_QUOTE = 600
MAX_HITS_PER_RESULT = 12
DEFAULT_OUT_DIR = "data/research/sciverse"


def load_names(root: Path) -> dict[str, str]:
    """Human names for registry ids from the last build output."""
    atlas = root / "data/build/atlas.json"
    names: dict[str, str] = {}
    if atlas.is_file():
        data = json.loads(atlas.read_text(encoding="utf-8"))
        for group in ("foods", "nutrients", "molecules"):
            nodes = data.get(group) or {}
            if isinstance(nodes, list):
                nodes = {n.get("id") or n.get("key") or "": n for n in nodes}
            for key, node in nodes.items():
                name = node.get("name") if isinstance(node, dict) else None
                if name:
                    names[key] = name
    # Fallback for nutrients the build did not touch: the FDC codebooks.
    for path in sorted(root.glob("data/raw/fdc-*/**/nutrient.csv"),
                       reverse=True):  # foundation (newer) wins over srlegacy
        if not path.is_file():
            continue
        with path.open(encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                key = f"nutrient:fdc:{row.get('id')}"
                names.setdefault(key, row.get("name") or "")
        break
    return {k: v for k, v in names.items() if v}


def humanize(key: str) -> str:
    return key.rsplit(":", 1)[-1].replace("-", " ")


def describe(subject: str, field_id: str, names: dict[str, str]) -> tuple[str, str, str | None]:
    """-> (food_label, field_label, compound_label)"""
    food_label = names.get(subject, humanize(subject))
    nutrient_id = field_id[len("contains:"):] if field_id.startswith("contains:") else field_id
    field_label = names.get(nutrient_id, humanize(nutrient_id))
    compound_label = field_label if field_id.startswith("contains:") else None
    return food_label, field_label, compound_label


@dataclass(frozen=True)
class GapItem:
    subject: str
    field: str
    rule: str
    question: str
    carried_value: str | None = None
    src: str | None = None
    would_be_settled_by: str | None = None

    @classmethod
    def from_row(cls, row: dict) -> "GapItem":
        return cls(
            subject=row["subject"], field=row["field"], rule=row["rule"],
            question=row.get("question", ""),
            carried_value=row.get("carried_value") or None,
            src=row.get("src") or None,
            would_be_settled_by=row.get("would_be_settled_by") or None,
        )

    @property
    def is_composition(self) -> bool:
        return self.field.startswith("contains:") or self.field.startswith("nutrient:fdc:")

    @property
    def gap_id(self) -> str:
        digest = hashlib.sha1(f"{self.subject}|{self.field}|{self.rule}".encode()).hexdigest()[:10]
        return f"G{self.rule}-{digest}"


def build_query(gap: GapItem, names: dict[str, str]) -> str:
    food_label, field_label, compound_label = describe(gap.subject, gap.field, names)
    if gap.rule == "6":
        return rule6_query(compound_label or field_label, food_label)
    if gap.rule == "5" and gap.is_composition:
        carried = (carried_value := gap.carried_value) and f"{carried_value} (from {gap.src or 'unknown source'})"
        return rule5_query(field_label, food_label, carried)
    raise ValueError(f"gap {gap.gap_id}: no query builder for rule {gap.rule} / field {gap.field}")


@dataclass
class Hit:
    doc_id: str | None
    title: str | None
    doi: str | None
    score: float | None
    offset: int | None
    quote: str
    value: str | None
    basis: str | None
    part: str | None
    flags: tuple[str, ...] = ()


@dataclass
class Finding:
    gap_id: str
    subject: str
    field: str
    rule: str
    status: str  # closed_candidate | partial | unresolved
    missing: list[str]
    query: str
    calls_used: int
    hits: list[Hit] = dc_field(default_factory=list)


def _find_value(text: str) -> tuple[str | None, int, int, bool]:
    """First concentration in `text`. Returns (value, start, end, in_original).

    `in_original` False means the value was only found in the tag-stripped
    copy of an HTML row, so the verbatim quote must be the raw row itself."""
    def latex_ok(m: re.Match) -> bool:
        # a LaTeX unit directly after "per"/a unit is a denominator
        # ("mg vitamin C per $100\mathrm{g}$"), not a value
        before = text[max(0, m.start() - 15):m.start()]
        return not re.search(r"(?:per|/|in)\s*\$?\s*$|\b(?:mg|µg|μg|g|kg)\s*\$?\s*$", before)

    match = PER_MASS_RE.search(text)
    if match:
        return re.sub(r"\s+", " ", match.group(0)).strip(), match.start(), match.end(), True
    stripped = _strip_tags(text)
    if stripped is not text:
        match = PER_MASS_RE.search(stripped)
        if match:
            return re.sub(r"\s+", " ", match.group(0)).strip(), match.start(), match.end(), False
    for match in LATEX_VAL_RE.finditer(text):
        if latex_ok(match):
            return f"{match.group(1)} {match.group(2)}", match.start(), match.end(), True
    return None, -1, -1, True


def _extract_value(text: str) -> str | None:
    return _find_value(text)[0]


def _basis_of(text: str) -> str | None:
    match = BASIS_RE.search(text)
    return match.group(0).lower() if match else None


def _part_of(text: str) -> str | None:
    match = PART_RE.search(text)
    return match.group(1).lower() if match else None


def _sentence_around(text: str, needle: str, span: tuple[int, int] | None = None) -> str:
    if span is not None:
        index = span[0]
    else:
        index = text.find(needle)
    if index < 0:
        return text[:MAX_QUOTE]
    start = text.rfind(". ", 0, index)
    start = 0 if start < 0 else start + 2
    end = text.find(". ", span[1] if span else index)
    end = len(text) if end < 0 else end + 1
    return text[start:end].strip()


def _table_rows(text: str) -> list[str]:
    """Verbatim `<tr>` rows of HTML tables embedded in a chunk (sciverse
    renders quantitative tables as HTML inside the passage)."""
    rows: list[str] = []
    for match in re.finditer(r"<tr\b.*?</tr>", text, re.S | re.I):
        rows.append(match.group(0))
    return rows


def _strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html)


def _verify_quote(quote: str, text: str) -> str:
    """A quote that is not verbatim inside the retrieved text must never be
    recorded (traceability rule 5). Raises instead."""
    cleaned = " ".join(quote.split())
    haystack = " ".join(text.split())
    if cleaned and cleaned in haystack:
        return cleaned
    raise ValueError(f"quote not verbatim in retrieved text: {quote[:80]!r}...")


def grade_hit(hit, text: str, context: str | None = None) -> Hit:
    """Grade a passage. `text` carries the value; `context` (e.g. the whole
    chunk containing a table header) may state the basis/food part."""
    context = text if context is None else context
    value, start, end, in_original = _find_value(text)
    if value and in_original and LATEX_VAL_RE.match(text, start):
        # extend LaTeX values with a trailing per-mass tail: "75.8 mg GAE/100 g"
        tail = re.match(r"\s*(?:[A-Z]{2,5}\s*)?/\s*(?:100\s*)?(?:g|kg|mL)\b",
                        text[end:end + 20])
        if tail:
            value = value + tail.group(0).replace("\n", " ")
            end += tail.end()
    basis = _basis_of(context)
    part = _part_of(context)
    flags: tuple[str, ...] = ()
    if value:
        if in_original:
            quote = _verify_quote(_sentence_around(text, value, (start, end)), text)
        else:
            # value only visible in the stripped copy: the raw row is the quote
            quote = _verify_quote(text, text)
    else:
        quote = _verify_quote(text, text)
    if value:
        if CITED_RE.search(quote.rstrip()):
            flags += ("second_hand",)  # bracketed citation → rule 10
        if RATIO_RE.search(quote):
            flags += ("ratio",)  # DW/FW water content, not a concentration
    return Hit(doc_id=hit.doc_id, title=hit.title, doi=hit.doi, score=hit.score,
               offset=hit.offset, quote=quote[:MAX_QUOTE], value=value,
               basis=basis, part=part, flags=flags)


GENERIC_FOOD_WORDS = frozenset({
    "green", "red", "sweet", "wild", "baby", "black", "white", "raw", "the"})


def food_words_of(subject: str, name: str | None) -> frozenset[str]:
    tokens = set(re.split(r"[\s:-]+", (subject + " " + (name or "")).lower()))
    return frozenset(t for t in tokens if len(t) >= 3 and t not in GENERIC_FOOD_WORDS)


def grade(result: AgenticResult, food_words: frozenset[str] = frozenset()) -> list[Hit]:
    graded: list[Hit] = []
    for hit in result.hits:
        if food_words and not any(
                re.search(rf"\b{re.escape(w)}\b", (hit.title or "") + " " + hit.chunk, re.I)
                for w in food_words):
            continue  # not about this food (e.g. cell-biology noise)
        if "<tr" in hit.chunk.lower() and "<td" in hit.chunk.lower():
            # quantitative HTML table: grade each value-carrying row, but let
            # basis/food part come from the whole chunk (header may state it)
            for row in _table_rows(hit.chunk):
                if not _extract_value(_strip_tags(row)) and \
                        not PER_MASS_RE.search(row) and \
                        not LATEX_VAL_RE.search(row):
                    continue
                graded.append(grade_hit(hit, row, context=hit.chunk))
        else:
            graded.append(grade_hit(hit, hit.chunk))
    with_value = [h for h in graded if h.value]
    return sorted(with_value, key=lambda h: h.score or 0.0, reverse=True)[:MAX_HITS_PER_RESULT]


def harvest_gap(client: SciverseClient, gap: GapItem, names: dict[str, str],
                per_gap_calls: int = 2, top_k: int = 8) -> Finding:
    query = build_query(gap, names)
    finding = Finding(gap_id=gap.gap_id, subject=gap.subject, field=gap.field,
                      rule=gap.rule, status="unresolved", missing=["no primary measurement found"],
                      query=query, calls_used=0)
    search = client.agentic_search(query, top_k=top_k)
    finding.calls_used += 1
    hits = grade(search, food_words_of(gap.subject, names.get(gap.subject)))
    if not hits:
        finding.missing = ["no quantitative passage with a unit in the top results"]
        return finding
    finding.missing = []
    best = hits[0]
    if best.basis is None and gap.rule == "6" and best.doc_id \
            and finding.calls_used < per_gap_calls:
        page = client.content(doc_id=best.doc_id,
                              offset=best.offset if best.offset is not None else 0)
        finding.calls_used += 1
        confirmed = grade_hit(search.hits[0], page.text)
        if confirmed.basis:
            hits[0] = confirmed
    best = hits[0]
    if best.value and best.basis and best.part and not best.flags:
        finding.status = "closed_candidate"
    else:
        finding.status = "partial"
        flag_gaps = {"second_hand": "primary source not reached (cited figure)",
                     "ratio": "value is a DW/FW ratio, not a concentration"}
        finding.missing = [name for name, present in
                           (("basis", best.basis), ("food_part", best.part)) if not present]
        finding.missing += [flag_gaps.get(flag, flag) for flag in best.flags]
    finding.hits = hits
    return finding


class ResponseCache:
    """Content-addressed JSON cache so re-runs never re-spend API calls."""

    def __init__(self, directory: Path):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def key(self, method: str, path: str, payload: dict | None, params: dict | None) -> str:
        blob = json.dumps([method, path, payload, params], sort_keys=True,
                          ensure_ascii=False)
        return hashlib.sha256(blob.encode()).hexdigest()

    def get(self, key: str) -> dict | None:
        path = self.directory / f"{key}.json"
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
        return None

    def put(self, key: str, data: dict) -> None:
        path = self.directory / f"{key}.json"
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


class CachedClient(SciverseClient):
    """Client variant that consults ResponseCache before the network."""

    def __init__(self, cache: ResponseCache, refresh: bool = False, **kwargs):
        super().__init__(**kwargs)
        self._cache = cache
        self._refresh = refresh

    def _request_json(self, method: str, path: str, params: dict | None = None,
                      payload: dict | None = None) -> dict:
        key = self._cache.key(method, path, payload, params)
        if not self._refresh:
            cached = self._cache.get(key)
            if cached is not None:
                return cached
        data = super()._request_json(method, path, params=params, payload=payload)
        self._cache.put(key, data)
        return data


def read_gaps(root: Path, rule: int | None = None, subject_prefix: str | None = None,
              limit: int | None = None) -> list[GapItem]:
    path = root / "data/build/gaps.csv"
    seen: set[str] = set()
    gaps: list[GapItem] = []
    with path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if rule is not None and row["rule"] != str(rule):
                continue
            if subject_prefix and not row["subject"].startswith(subject_prefix):
                continue
            gap = GapItem.from_row(row)
            if not gap.is_composition:
                continue  # season/growing gaps need different query builders
            if gap.gap_id in seen:
                continue  # duplicate rows in gaps.csv share a subject+field
            seen.add(gap.gap_id)
            gaps.append(gap)
            if limit is not None and len(gaps) >= limit:
                break
    return gaps


def harvest(client: SciverseClient, gaps: list[GapItem], names: dict[str, str],
            out_dir: Path, run_id: str | None = None, per_gap_calls: int = 2,
            top_k: int = 8, pause: float = 0.5, sleep=time.sleep) -> dict:
    run_id = run_id or time.strftime("%Y%m%d-%H%M%S")
    run_dir = out_dir / run_id
    (run_dir / "cache").mkdir(parents=True, exist_ok=True)
    findings: list[Finding] = []
    for gap in gaps:
        findings.append(harvest_gap(client, gap, names,
                                    per_gap_calls=per_gap_calls, top_k=top_k))
        if pause and sleep is not None:
            sleep(pause)
    from collections import Counter
    from dataclasses import asdict
    import yaml
    payload = []
    for finding in findings:
        payload.append({
            "gap_id": finding.gap_id, "subject": finding.subject,
            "field": finding.field, "rule": finding.rule,
            "status": finding.status, "missing": finding.missing,
            "query": finding.query, "calls_used": finding.calls_used,
            "hits": [asdict(hit) for hit in finding.hits],
        })
    with (run_dir / "findings.yaml").open("w", encoding="utf-8") as stream:
        yaml.safe_dump(payload, stream, allow_unicode=True, sort_keys=False,
                       width=100)
    summary = {
        "run_id": run_id, "gaps": len(findings),
        "status": dict(Counter(f.status for f in findings)),
        "calls_used": sum(f.calls_used for f in findings),
        "client_calls": client.calls,
    }
    (run_dir / "run.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
