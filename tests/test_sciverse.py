"""Offline Sciverse client/pipeline tests; a fake transport, no network."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas.research.sciverse.client import (
    BASE_URL,
    SciverseClient,
    SciverseError,
    SciverseHTTPError,
    load_token,
)
from atlas.research.sciverse.models import (
    AgenticResult,
    Catalog,
    ContentPage,
    MetaFilter,
    MetaResult,
    MetaSort,
    ModelParseError,
    RelationPage,
)
from atlas.research.sciverse.pipeline import (
    CachedClient,
    GapItem,
    ResponseCache,
    build_query,
    describe,
    grade,
    grade_hit,
    harvest,
    load_names,
    read_gaps,
    _verify_quote,
)
from atlas.research.sciverse.prompts import license_triage_fields, rule5_query, rule6_query

TOKEN = "sv-test-token-000000000000000000000000000"


class FakeTransport:
    """Scripted transport: maps (method, path) -> list of responses."""

    def __init__(self, script: dict):
        self.script = script
        self.calls: list[dict] = []

    def __call__(self, method, url, headers, body, timeout):
        path = url[len(BASE_URL):].split("?")[0]
        self.calls.append({"method": method, "path": path, "url": url,
                           "headers": headers, "body": body})
        seq = self.script.setdefault(path, [])
        if not seq:
            raise AssertionError(f"unexpected call to {path}: {url}")
        item = seq.pop(0)
        if isinstance(item, tuple) and item[0] == "status":
            status, payload = item[1], item[2]
            headers_out = {"Retry-After": "0.01"} if status == 429 else {}
            return status, headers_out, json.dumps(payload).encode()
        return 200, {}, json.dumps(item).encode()


@pytest.fixture
def transport():
    return FakeTransport({})


@pytest.fixture
def client(transport):
    return SciverseClient(token=TOKEN, transport=transport, attempts=3,
                          sleep=lambda s: None)


# --- token ---------------------------------------------------------------

def test_load_token_reads_env_vars():
    env = {"SCIVERSE_TOKEN": " tok "}
    assert load_token(env) == "tok"
    assert load_token({"SCIVERSE_API_TOKEN": "tok2"}) == "tok2"
    with pytest.raises(SciverseError):
        load_token({})


def test_client_requires_token_without_env(monkeypatch):
    monkeypatch.delenv("SCIVERSE_TOKEN", raising=False)
    monkeypatch.delenv("SCIVERSE_API_TOKEN", raising=False)
    with pytest.raises(SciverseError):
        SciverseClient(transport=FakeTransport({}))


# --- models --------------------------------------------------------------

def test_agentic_hit_requires_chunk():
    with pytest.raises(ModelParseError):
        AgenticResult.parse({"hits": [{"title": "no chunk"}]})


def test_agentic_hit_keeps_raw_and_tolerant_fields():
    result = AgenticResult.parse({"hits": [{
        "chunk": "quercetin 12.3 mg/100 g fw", "doc_id": "DOC1",
        "doi": "10.1/x", "score": 0.9, "venue": "unknown-field"}]})
    assert result.hits[0].doc_id == "DOC1"
    assert result.hits[0].raw["venue"] == "unknown-field"


def test_meta_record_parses_and_keeps_raw():
    result = MetaResult.parse({"results": [{"unique_id": "doi:10.1/x",
        "doc_id": "DOC1", "title": "T", "doi": "10.1/x",
        "publication_published_year": 2019}], "total_count": 1, "page": 1,
        "page_size": 25, "total_pages": 1})
    assert result.results[0].year == 2019
    assert result.total_count == 1


def test_meta_record_string_totals_are_ints():
    result = MetaResult.parse({"results": [], "total_count": "12", "page": "1",
        "page_size": "25", "total_pages": "1"})
    assert (result.total_count, result.total_pages) == (12, 1)
    with pytest.raises(ModelParseError):
        MetaResult.parse({"results": [], "total_count": "many", "page": 1,
            "page_size": 25, "total_pages": 1})


def test_content_page_defaults_more_false():
    page = ContentPage.parse({"text": "hello", "more": True,
                              "next_offset": 5, "text_length": 5})
    assert page.more and page.next_offset == 5
    page2 = ContentPage.parse({"text": "hello"})
    assert page2.more is False


def test_catalog_and_relations_shape():
    catalog = Catalog.parse({"fields": [{"name": "doi", "filterable": True,
        "operators": ["FILTER_OP_EQ"]}], "default_fields": ["doi"],
        "filter_operators": ["FILTER_OP_EQ"]})
    assert "doi" in catalog.filterable_names()
    relations = RelationPage.parse({"items": [{"id": "doi:10.1/x",
        "title": "T"}], "total_count": 1, "page": 1, "page_size": 25,
        "total_pages": 1})
    assert relations.items[0].id == "doi:10.1/x"


# --- client behaviour -----------------------------------------------------

AGENTIC = {"hits": [{"chunk": "Ascorbic acid 4.6 mg/100 g fresh weight in "
                     "apple flesh (n=6, HPLC-DAD).",
                     "doc_id": "DOC1", "score": 0.8}]}
CATALOG = {"fields": [{"name": "doi", "filterable": True, "sortable": False}],
           "default_fields": ["doi"], "filter_operators": ["FILTER_OP_EQ"]}


def test_agentic_search_payload_and_headers(client, transport):
    transport.script["/agentic-search"] = [AGENTIC]
    result = client.agentic_search("quercetin in apple", top_k=5)
    assert result.hits[0].doc_id == "DOC1"
    sent = json.loads(transport.calls[0]["body"])
    assert sent == {"query": "quercetin in apple", "top_k": 5,
                    "retrieval": "hybrid", "sub_queries": 0}
    headers = transport.calls[0]["headers"]
    assert headers["Authorization"] == f"Bearer {TOKEN}"
    assert headers["Content-Type"] == "application/json"


def test_agentic_search_validates_inputs(client):
    for kwargs in ({"query": "", "top_k": 5}, {"query": "x", "top_k": 0},
                   {"query": "x", "top_k": 101},
                   {"query": "x", "retrieval": "bogus"},
                   {"query": "x", "source_types": ("book",)}):
        with pytest.raises(SciverseError):
            client.agentic_search(**kwargs)


def test_retry_on_429_then_success(client, transport):
    transport.script["/agentic-search"] = [
        ("status", 429, {"error": "rate limited"}), AGENTIC]
    result = client.agentic_search("q")
    assert result.hits[0].doc_id == "DOC1"
    assert len(transport.calls) == 2


def test_retry_exhausts_on_500(client, transport):
    transport.script["/agentic-search"] = [
        ("status", 500, {"error": "boom"})] * 5
    with pytest.raises(SciverseHTTPError) as excinfo:
        client.agentic_search("q")
    assert excinfo.value.status == 500
    assert len(transport.calls) == client.attempts


def test_http_error_passes_body(client, transport):
    transport.script["/agentic-search"] = [
        ("status", 401, {"error": "bad token"})]
    with pytest.raises(SciverseHTTPError) as excinfo:
        client.agentic_search("q")
    assert excinfo.value.status == 401
    assert "bad token" in excinfo.value.body


def test_error_envelope_raises(client, transport):
    transport.script["/agentic-search"] = [
        ("status", 200, {"code": "E2", "message": "bad query"})]
    with pytest.raises(SciverseError, match="error envelope"):
        client.agentic_search("q")


def test_success_envelope_is_unwrapped(client, transport):
    transport.script["/meta-paper-relations"] = [
        {"code": 0, "data": {"items": [{"id": "doi:10.1/x"}],
                             "total_count": 1, "page": 1, "page_size": 25,
                             "total_pages": 1}}]
    page = client.relations("doi:10.1/a", "REFERENCES")
    assert page.items[0].id == "doi:10.1/x"


def test_relations_validates_relation_name(client):
    with pytest.raises(SciverseError, match="relation"):
        client.relations("doi:10.1/a", "FRIENDS")


def test_identity_safety(client):
    with pytest.raises(SciverseError, match="doc_id"):
        client.content(doc_id="../etc/passwd")
    with pytest.raises(SciverseError, match="file_name"):
        client.resource("/etc/passwd")
    with pytest.raises(SciverseError, match="file_name"):
        client.resource("a\\b.png")
    with pytest.raises(SciverseError, match="doc_id or source"):
        client.content()


def test_content_params_serialized(client, transport):
    transport.script["/content"] = [{"text": "body", "more": False}]
    page = client.content(doc_id="DOC1", offset=40, limit=100)
    assert page.text == "body"
    url = transport.calls[0]["url"]
    assert "doc_id=DOC1" in url and "offset=40" in url and "limit=100" in url


def test_meta_search_validates(client):
    with pytest.raises(SciverseError):
        client.meta_search(page_size=500)
    with pytest.raises(SciverseError):
        client.meta_search(query="x", sort=[MetaSort("citation_count")])
    with pytest.raises(SciverseError):
        client.meta_search(filters=[MetaFilter("doi", "FILTER_OP_EQ", "x")],
                           facets=[{}] * 6)


def test_read_all_follows_more(client, transport):
    transport.script["/content"] = [
        {"text": "part1", "more": True, "next_offset": 5},
        {"text": "part2", "more": False}]
    assert client.read_all("DOC1") == "part1part2"


def test_find_by_doi_returns_none_when_absent(client, transport):
    transport.script["/meta-search"] = [
        {"results": [], "total_count": 0, "page": 1, "page_size": 1,
         "total_pages": 0}]
    assert client.find_by_doi("10.1/none") is None


# --- prompts / query builders ---------------------------------------------

def test_rule6_and_rule5_queries_carry_the_contract():
    q6 = rule6_query("quercetin", "Apple")
    assert "quercetin in Apple" in q6 and "concentration table" in q6
    assert "fresh weight" in q6 and "dry weight" in q6
    q5 = rule5_query("Vitamin C", "Cabbage", "59.4 (from SRC-FDC)")
    assert "Independent analytical studies" in q5
    assert "59.4 (from SRC-FDC)" in q5 and "compilation" in q5


def test_license_triage_fields_are_the_live_catalog_ones():
    assert set(license_triage_fields()) <= {
        "unique_id", "doc_id", "title", "doi", "publication_published_year",
        "publication_venue_name_unified", "access_is_oa", "access_oa_status",
        "access_license"}


# --- pipeline ---------------------------------------------------------------

NAMES = {"food:cabbage.green": "Green cabbage (cultivar group)",
         "nutrient:fdc:1185": "Vitamin K (phylloquinone)",
         "food:apple": "Apple", "nutrient:fdc:1162": "Vitamin C"}


def test_describe_uses_build_names():
    food, field_label, compound = describe("food:cabbage.green",
                                           "contains:nutrient:fdc:1185", NAMES)
    assert food == "Green cabbage (cultivar group)"
    assert field_label == "Vitamin K (phylloquinone)"
    assert compound == "Vitamin K (phylloquinone)"


def test_gap_item_ids_and_filters():
    gap = GapItem.from_row({"subject": "food:cabbage.green",
                            "field": "contains:nutrient:fdc:1185",
                            "rule": "6", "question": "q", "carried_value": "",
                            "src": "S", "would_be_settled_by": "w"})
    assert gap.is_composition and gap.gap_id.startswith("G6-")
    season_gap = GapItem.from_row({"subject": "food:apple",
                                   "field": "season:DE", "rule": "5",
                                   "question": "q"})
    assert not season_gap.is_composition


def test_build_query_resolves_names():
    gap = GapItem.from_row({"subject": "food:cabbage.green",
                            "field": "contains:nutrient:fdc:1185",
                            "rule": "6", "question": "q"})
    query = build_query(gap, NAMES)
    assert "Green cabbage (cultivar group)" in query
    assert "Vitamin K (phylloquinone)" in query


CHUNK_WITH_BASIS = ("Quercetin content was 12.3 mg/100 g fresh weight in "
                    "apple peel (n=6, HPLC-DAD).")
CHUNK_NO_BASIS = "Quercetin was 12.3 mg/100 g in apple peel by HPLC-DAD."


def _agentic(chunks):
    return AgenticResult.parse({"hits": [
        c if isinstance(c, dict) else {"chunk": c, "doc_id": f"DOC{i}",
                                       "score": 1 - i * 0.1,
                                       "doi": f"10.1/{i}", "title": f"T{i}"}
        for i, c in enumerate(chunks)]})


def test_grade_hit_extracts_value_basis_part():
    hit = _agentic([CHUNK_WITH_BASIS]).hits[0]
    graded = grade_hit(hit, hit.chunk)
    assert graded.value == "12.3 mg/100 g"
    assert graded.basis == "fresh weight"
    assert graded.part == "peel"
    assert graded.quote.startswith("Quercetin")


def test_find_value_reads_latex_mangled_numbers():
    from atlas.research.sciverse.pipeline import _find_value
    text = ("Analyte concentrations were reported on a per fresh weight basis, "
            "e.g., mg vitamin C per $100\\mathrm{g}$ fresh kale.")
    value, start, end, _ = _find_value(text)
    assert value is None  # "per $100\mathrm{g}$" is a denominator, not a value
    text2 = "Dry weight decreased from $0.97\\mathrm{g}$ DW/g fresh weight within 24 h."
    value2, s, e, _ = _find_value(text2)
    assert value2 == "0.97 g"
    assert text2[s:e] == "0.97\\mathrm{g}"


def test_grade_flags_second_hand_and_ratio_values():
    cited = _agentic([{"chunk": "Total phenolics reached 75.8 mg GAE/100 g of "
                               "fresh weight (FW) [21].",
                       "doc_id": "DOC7", "score": 0.9,
                       "title": "kale phenolics review"}])
    hits = grade(cited, frozenset({"kale"}))
    assert hits[0].value == "75.8 mg GAE/100 g"
    assert "second_hand" in hits[0].flags
    ratio = _agentic([{"chunk": "DW decreased from 0.97 g DW/g fresh weight "
                                "during imbibition.",
                       "doc_id": "DOC6", "score": 0.9, "title": "kale seeds"}])
    hits = grade(ratio, frozenset({"kale"}))
    assert "ratio" in hits[0].flags


def test_grade_drops_hits_without_food_context():
    food = frozenset({"kale"})
    cell_noise = _agentic([{"chunk": "Table 3. Lysine 10.2 mg/100 g in fed cell extracts.",
                            "doc_id": "DOC9", "score": 0.9,
                            "title": "role of uncharged trna in polyp"}])
    assert grade(cell_noise, food) == []
    on_food = _agentic([{"chunk": "Kale leaves contained 12.5 mg/100 g quercetin.",
                         "doc_id": "DOC8", "score": 0.9,
                         "title": "kale composition study"}])
    assert len(grade(on_food, food)) == 1


def test_grade_extracts_html_table_rows_with_header_context():
    chunk = ('<p>Table 1. Glucosinolates in broccoli florets, fresh weight '
             '(µmol/100 g).</p>'
             '<table><tr><td>Compound</td><td>Amount</td></tr>'
             '<tr><td>Glucoraphanin</td><td>29.4 μmol/100 g</td></tr>'
             '<tr><td>Glucobrassicin</td><td>3.86 μmol/100 g</td></tr></table>')
    hits = grade(_agentic([chunk]))
    assert [h.value for h in hits] == ["29.4 μmol/100 g", "3.86 μmol/100 g"]
    assert all(h.basis == "fresh weight" for h in hits)
    assert all(h.part in ("floret", "florets") for h in hits)
    assert "Glucoraphanin" in hits[0].quote and "<td>" in hits[0].quote


def test_grade_hit_flags_missing_basis():
    hit = _agentic([CHUNK_NO_BASIS]).hits[0]
    graded = grade_hit(hit, hit.chunk)
    assert graded.value == "12.3 mg/100 g"
    assert graded.basis is None


def test_verify_quote_rejects_unquotable_text():
    with pytest.raises(ValueError, match="verbatim"):
        _verify_quote("not in this text at all 4.6 mg", "different words")


def test_harvest_budget_and_outputs(tmp_path, transport, monkeypatch):
    gaps = [
        # rule 6, hit carries value + basis + part → closed, 1 call.
        GapItem.from_row({"subject": "food:apple",
                          "field": "contains:nutrient:fdc:1162",
                          "rule": "6", "question": "q"}),
        # rule 6, hit carries a value but no basis → content confirmation call.
        GapItem.from_row({"subject": "food:apple",
                          "field": "contains:nutrient:fdc:1185",
                          "rule": "6", "question": "q"}),
        # rule 5, carried value, hit states no basis → no second call allowed.
        GapItem.from_row({"subject": "food:apple",
                          "field": "nutrient:fdc:1185", "rule": "5",
                          "question": "q", "carried_value": "59.4",
                          "src": "SRC-FDC-FOUNDATION-2026-04"}),
    ]
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data/build").mkdir(parents=True)
    (tmp_path / "data/build/atlas.json").write_text(json.dumps({
        "foods": {"food:apple": {"name": "Apple"}},
        "nutrients": {"nutrient:fdc:1162": {"name": "Vitamin C"},
                      "nutrient:fdc:1185": {"name": "Vitamin K"}}}))
    transport.script["/agentic-search"] = [
        AGENTIC,
        {"hits": [{"chunk": CHUNK_NO_BASIS, "doc_id": "DOC2", "score": 0.9,
                   "doi": "10.1/2", "title": "T2"}]},
        {"hits": [{"chunk": CHUNK_NO_BASIS, "doc_id": "DOC3", "score": 0.8,
                   "doi": "10.1/3", "title": "T3"}]},
    ]
    transport.script["/content"] = [
        {"text": "The values are expressed on a fresh weight basis. "
                 + CHUNK_NO_BASIS, "more": False}]
    out_dir = tmp_path / "data/research/sciverse"
    summary = harvest(SciverseClient(token=TOKEN, transport=transport,
                                     sleep=None), gaps, NAMES, out_dir,
                      run_id="test-run", pause=0)
    assert summary["status"] == {"closed_candidate": 2, "partial": 1}
    assert summary["calls_used"] == 4  # 3 searches + 1 confirmation read
    run = json.loads((out_dir / "test-run/run.json").read_text())
    assert run == summary
    text = (out_dir / "test-run/findings.yaml").read_text()
    assert "closed_candidate" in text and "fresh weight" in text
    assert "DOC1" in text and "DOC2" in text and "DOC3" in text


def test_cached_client_skips_network(tmp_path, transport):
    cache = ResponseCache(tmp_path / "cache")
    first = CachedClient(cache, token=TOKEN, transport=transport, sleep=None)
    transport.script["/agentic-search"] = [AGENTIC, AGENTIC]
    first.agentic_search("q")
    first.agentic_search("q", top_k=5)  # different payload → second call
    assert len(transport.calls) == 2
    second = CachedClient(cache, token=TOKEN, transport=transport, sleep=None)
    second.agentic_search("q")  # cache hit, no transport call
    second.agentic_search("q", top_k=5)
    assert len(transport.calls) == 2


def test_read_gaps_filters_by_rule_and_subject(tmp_path):
    build = tmp_path / "data/build"
    build.mkdir(parents=True)
    (build / "gaps.csv").write_text(
        "subject,field,rule,question,would_be_settled_by,carried_value,src\n"
        "food:apple,contains:nutrient:fdc:1162,6,q,w,,S\n"
        "food:apple,season:DE,5,q,w,,S\n"
        "food:cabbage.green,nutrient:fdc:1185,5,q,w,59.4,S\n")
    gaps = read_gaps(tmp_path, rule=5)
    assert [g.subject for g in gaps] == ["food:cabbage.green"]
    assert read_gaps(tmp_path, rule=6, limit=10)[0].field == \
        "contains:nutrient:fdc:1162"
    assert read_gaps(tmp_path, subject_prefix="food:cabbage")[0].subject == \
        "food:cabbage.green"


def test_load_names_from_build(tmp_path):
    build = tmp_path / "data/build"
    build.mkdir(parents=True)
    (build / "atlas.json").write_text(json.dumps(
        {"foods": {"food:apple": {"name": "Apple"}}, "nutrients": {}}))
    names = load_names(tmp_path)
    assert names == {"food:apple": "Apple"}
