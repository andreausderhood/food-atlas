"""REST client for the Sciverse API — six documented endpoints, nothing more.

API base: https://api.sciverse.space (docs: https://sciverse.space/docs).
The token never enters source or git: it is read from SCIVERSE_TOKEN or
SCIVERSE_API_TOKEN, or passed explicitly by the caller.

Retries: 429 and 5xx are retried with exponential backoff, honouring
Retry-After. Any other non-200 raises SciverseHTTPError with the body.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable, Mapping

from atlas.research.sciverse.models import (
    RELATIONS,
    FRESHNESS,
    SOURCE_TYPES,
    AgenticResult,
    Catalog,
    ContentPage,
    MetaFilter,
    MetaRecord,
    MetaResult,
    MetaSort,
    ModelParseError,
    RelationPage,
)

BASE_URL = "https://api.sciverse.space"
ENV_TOKEN_VARS = ("SCIVERSE_TOKEN", "SCIVERSE_API_TOKEN")
DEFAULT_TIMEOUT = 60.0
DEFAULT_ATTEMPTS = 4

Transport = Callable[[str, str, dict, bytes | None, float], tuple[int, dict, bytes]]


def _retry_delay(retry_after: str | None, attempt: int) -> float:
    if retry_after:
        try:
            return float(retry_after)
        except ValueError:
            pass
    return min(60.0, 1.5 ** attempt)


class SciverseError(RuntimeError):
    """A Sciverse request failed after retries, or the payload was invalid."""


class SciverseHTTPError(SciverseError):
    def __init__(self, status: int, path: str, body: str):
        self.status = status
        self.path = path
        self.body = body[:2000]
        super().__init__(f"sciverse {path} returned HTTP {status}: {self.body}")


def load_token(env: Mapping[str, str] | None = None) -> str:
    env = os.environ if env is None else env
    for name in ENV_TOKEN_VARS:
        value: str | None = env.get(name)
        if value:
            return value.strip()
    raise SciverseError(
        "no Sciverse token: set SCIVERSE_TOKEN (or SCIVERSE_API_TOKEN) in the environment")


def _urllib_transport(method, url, headers, body, timeout):
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers), error.read()


class SciverseClient:
    def __init__(
        self,
        token: str | None = None,
        base_url: str = BASE_URL,
        transport: Transport | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        attempts: int = DEFAULT_ATTEMPTS,
        clock=time.time,
        sleep=time.sleep,
        max_top_k: int = 100,
        max_page_size: int = 200,
    ):
        self.token = token if token is not None else load_token()
        self.base_url = base_url.rstrip("/")
        self.transport = transport or _urllib_transport
        self.timeout = timeout
        self.attempts = max(1, attempts)
        self.clock = clock
        self.sleep = sleep
        self.max_top_k = max_top_k
        self.max_page_size = max_page_size
        self._calls = 0

    # -- plumbing ---------------------------------------------------------

    @property
    def calls(self) -> int:
        return self._calls

    def _headers(self, json_body: bool) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/json"}
        if json_body:
            headers["Content-Type"] = "application/json"
        return headers

    def _request_json(self, method: str, path: str, params: dict | None = None,
                      payload: dict | None = None) -> dict:
        url = self.base_url + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        body = None
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        last_error: Exception | None = None
        for attempt in range(self.attempts):
            status, headers, raw = self.transport(
                method, url, self._headers(body is not None), body, self.timeout)
            if status in (429,) or status >= 500:
                retry_after = headers.get("Retry-After") or headers.get("retry-after")
                delay = _retry_delay(retry_after, attempt)
                last_error = SciverseHTTPError(status, path, raw.decode("utf-8", "replace"))
                if attempt + 1 < self.attempts:
                    self.sleep(delay)
                    continue
                raise last_error
            text = raw.decode("utf-8", "replace")
            if status != 200:
                raise SciverseHTTPError(status, path, text)
            try:
                data = json.loads(text)
            except json.JSONDecodeError as error:
                raise SciverseError(f"sciverse {path}: non-JSON response: {text[:200]}") from error
            if not isinstance(data, dict):
                raise SciverseError(f"sciverse {path}: expected object response")
            # Some endpoints wrap payloads in a success envelope.
            if "data" in data and isinstance(data["data"], dict) and (
                    "code" in data or "biz_code" in data):
                return data["data"]
            if "code" in data and "data" not in data and str(data.get("code", "")) not in (
                    "0", "200", "SUCCESS", "success", "OK"):
                raise SciverseError(f"sciverse {path}: error envelope: {text[:400]}")
            return data
        raise last_error or SciverseError(f"sciverse {path}: exhausted retries")

    def _decode(self, model_class, data: dict, path: str):
        try:
            return model_class.parse(data)
        except ModelParseError as error:
            raise SciverseError(f"sciverse {path}: {error}") from error

    @staticmethod
    def _safe_identity(value: str, kind: str) -> str:
        if not value or not isinstance(value, str):
            raise SciverseError(f"{kind} must be a non-empty string")
        if ".." in value or "\\" in value:
            raise SciverseError(f"{kind} must not contain '..' or backslashes: {value!r}")
        if kind == "file_name" and value.startswith("/"):
            raise SciverseError(f"file_name must be relative, not absolute: {value!r}")
        return value

    # -- endpoints --------------------------------------------------------

    def agentic_search(
        self,
        query: str,
        top_k: int = 10,
        retrieval: str = "hybrid",
        sub_queries: int = 0,
        filters: dict | None = None,
        source_types: tuple[str, ...] | list[str] | None = None,
    ) -> AgenticResult:
        if not 1 <= len(query.strip()) <= 4096:
            raise SciverseError("agentic_search: query must be 1..4096 characters")
        if not 1 <= top_k <= self.max_top_k:
            raise SciverseError(f"agentic_search: top_k must be 1..{self.max_top_k}")
        if not 0 <= sub_queries <= 4:
            raise SciverseError("agentic_search: sub_queries must be 0..4")
        if retrieval not in ("hybrid", "milvus", "es"):
            raise SciverseError(f"agentic_search: unknown retrieval {retrieval!r}")
        if source_types is not None:
            bad = set(source_types) - set(SOURCE_TYPES)
            if bad:
                raise SciverseError(f"agentic_search: unknown source_types {sorted(bad)}")
        payload: dict = {"query": query, "top_k": top_k, "retrieval": retrieval,
                         "sub_queries": sub_queries}
        if filters:
            payload["filters"] = filters
        if source_types:
            payload["source_types"] = list(source_types)
        self._calls += 1
        return self._decode(AgenticResult,
                            self._request_json("POST", "/agentic-search", payload=payload),
                            "/agentic-search")

    def meta_search(
        self,
        filters: list[MetaFilter] | None = None,
        query: str | None = None,
        fields: list[str] | None = None,
        sort: list[MetaSort] | None = None,
        page: int = 1,
        page_size: int = 25,
        facets: list[dict] | None = None,
        freshness_boost: str = "NONE",
        cursor: str | None = None,
    ) -> MetaResult:
        if not 1 <= page:
            raise SciverseError("meta_search: page must be >= 1")
        if not 1 <= page_size <= self.max_page_size:
            raise SciverseError(f"meta_search: page_size must be 1..{self.max_page_size}")
        if freshness_boost not in FRESHNESS:
            raise SciverseError(f"meta_search: freshness_boost must be one of {FRESHNESS}")
        if query and sort:
            raise SciverseError("meta_search: sort cannot be combined with a non-empty query")
        if cursor and page > 1:
            raise SciverseError("meta_search: cursor cannot be combined with page > 1")
        payload: dict = {"page": page, "page_size": page_size,
                         "freshness_boost": freshness_boost}
        if query:
            payload["query"] = query
        if filters:
            payload["filters"] = [f.to_payload() for f in filters]
        if sort:
            payload["sort"] = [s.to_payload() for s in sort]
        if fields:
            payload["fields"] = list(fields)
        if facets:
            if len(facets) > 5:
                raise SciverseError("meta_search: at most 5 facets")
            payload["facets"] = facets
        if cursor:
            payload["cursor"] = cursor
        self._calls += 1
        return self._decode(MetaResult,
                            self._request_json("POST", "/meta-search", payload=payload),
                            "/meta-search")

    def meta_catalog(self, include_sample_values: bool = False,
                     include_field_stats: bool = False) -> Catalog:
        params = {
            "include_sample_values": str(include_sample_values).lower(),
            "include_field_stats": str(include_field_stats).lower(),
        }
        self._calls += 1
        return self._decode(Catalog,
                            self._request_json("GET", "/meta-catalog", params=params),
                            "/meta-catalog")

    def relations(self, unique_id: str, relation: str, page: int = 1,
                  page_size: int = 25) -> RelationPage:
        if relation not in RELATIONS:
            raise SciverseError(f"relations: relation must be one of {RELATIONS}")
        if not 1 <= page_size <= self.max_page_size:
            raise SciverseError(f"relations: page_size must be 1..{self.max_page_size}")
        self._safe_identity(unique_id, "unique_id")
        payload = {"unique_id": unique_id, "relation": relation,
                   "page": page, "page_size": page_size}
        self._calls += 1
        return self._decode(RelationPage,
                            self._request_json("POST", "/meta-paper-relations", payload=payload),
                            "/meta-paper-relations")

    def content(self, doc_id: str | None = None, source: str | None = None,
                offset: int | None = None, limit: int | None = None) -> ContentPage:
        if doc_id is None and source is None:
            raise SciverseError("content: doc_id or source is required")
        params: dict[str, str] = {}
        if doc_id is not None:
            params["doc_id"] = self._safe_identity(doc_id, "doc_id")
        if source is not None:
            params["source"] = self._safe_identity(source, "source")
        if offset is not None:
            if offset < 0:
                raise SciverseError("content: offset must be >= 0")
            params["offset"] = str(offset)
        if limit is not None:
            if limit <= 0:
                raise SciverseError("content: limit must be positive")
            params["limit"] = str(limit)
        self._calls += 1
        return self._decode(ContentPage,
                            self._request_json("GET", "/content", params=params),
                            "/content")

    def read_all(self, doc_id: str, max_chunks: int = 200, chunk_limit: int = 4000) -> str:
        """Page through a document's full text. Stops when ``more`` is false."""
        self._safe_identity(doc_id, "doc_id")
        parts: list[str] = []
        offset: int | None = 0
        for _ in range(max_chunks):
            page = self.content(doc_id=doc_id, offset=offset, limit=chunk_limit)
            parts.append(page.text)
            if not page.more or page.next_offset is None:
                return "".join(parts)
            offset = page.next_offset
        raise SciverseError(f"content {doc_id}: exceeded max_chunks={max_chunks}")

    def resource(self, file_name: str) -> tuple[str, bytes]:
        """Download a document resource. Returns (content_type, bytes)."""
        self._safe_identity(file_name, "file_name")
        url = self.base_url + "/resource?" + urllib.parse.urlencode({"file_name": file_name})
        last_error: Exception | None = None
        for attempt in range(self.attempts):
            status, headers, raw = self.transport(
                "GET", url, self._headers(json_body=False), None, self.timeout)
            if status in (429,) or status >= 500:
                retry_after = headers.get("Retry-After") or headers.get("retry-after")
                delay = _retry_delay(retry_after, attempt)
                last_error = SciverseHTTPError(status, "/resource", raw.decode("utf-8", "replace"))
                if attempt + 1 < self.attempts:
                    self.sleep(delay)
                    continue
                raise last_error
            if status != 200:
                raise SciverseHTTPError(status, "/resource", raw.decode("utf-8", "replace"))
            return headers.get("Content-Type", "application/octet-stream"), raw
        raise last_error or SciverseError("/resource: exhausted retries")

    def find_by_doi(self, doi: str) -> MetaRecord | None:
        """Structured DOI lookup via meta-search. Returns None when absent."""
        result = self.meta_search(filters=[MetaFilter("doi", "FILTER_OP_EQ", doi)],
                                  page_size=1)
        return result.results[0] if result.results else None
