"""Prompt/query builders derived from docs/sciverse-prompts.md.

The preamble and output contract are the traceability contract of
`product.md` §3 rendered for literature retrieval. The deterministic pipeline
does not run a model over them; it uses the same rules to *build* search
queries from atlas gaps and to grade what comes back. When a model session
does the reading (docs/sciverse-prompts.md), it should use PREAMBLE verbatim.
"""
from __future__ import annotations

PREAMBLE = """You are sourcing values for the Food Atlas, a traceable atlas of edible life.
The atlas publishes claims, not papers. A claim is only publishable if you can
report ALL of:

  value | unit | basis (fresh_weight | dry_weight | as_sold) | food_part |
  taxon or cultivar | analytical method | sample n | source DOI | license

Hard rules — violating any of them makes the finding useless:
1. PRIMARY EVIDENCE ONLY.
2. NO AMOUNT WITHOUT A BASIS — "basis not stated", never inferred.
3. NO FOOD PART BY ASSUMPTION.
4. BIOACTIVITY IS EVIDENCE, NEVER A HEALTH CLAIM.
5. NO NUMBER YOU CANNOT QUOTE — verbatim sentence or table caption, plus
   doc_id and location.
6. UNKNOWN IS A VALID ANSWER.
Report in the OUTPUT CONTRACT. If a field is unavailable, write "not reported"
— do not omit the field, do not fill it from background knowledge."""

OUTPUT_CONTRACT = """OUTPUT CONTRACT (one block per finding, YAML):
- compound: <name>
  food: <food + cultivar>
  food_part: <peel|flesh|seed|floret|leaf|sprout|juice|pomace|not reported>
  value: <number>
  unit: <as printed, e.g. mg/100 g>
  basis: <fresh_weight|dry_weight|as_sold|not stated>
  method: <HPLC-DAD, LC-MS/MS, FRAP, ...|not reported>
  n: <samples|not reported>
  year_of_sampling: <not reported>
  region: <not reported>
  quote: "<verbatim sentence or table caption>"
  doc_id: <sciverse doc_id>
  location: <page/section>
  doi: <doi>
  primary: <yes|no — if no, name the study it was taken from>
  open_access: <yes|no|unknown>
  license: <CC BY 4.0 | CC BY-NC | publisher terms | unknown>"""

BASIS_TERMS = (
    'concentration with a unit; the words "fresh weight", "dry weight", '
    '"dw", "fw", or "as consumed"; a named quantification method; and a '
    "sample count"
)


def rule6_query(compound: str, food: str, part: str | None = None) -> str:
    """§2.1: find the measuring passage for a value carried without basis."""
    target = f"{compound} in {food}" + (f", resolved to {part}" if part else "")
    return (
        f"Primary analytical measurement of {target}: I need the concentration "
        f"table, not a review's summary sentence. Prefer passages that contain: "
        f"{BASIS_TERMS}. Most quantitative first."
    )


def rule5_query(field_label: str, food: str, carried_value: str | None) -> str:
    """§4: independent analytical study for an unverified carried value."""
    value = f' (carried value: {carried_value})' if carried_value else ""
    return (
        f"Independent analytical studies that measured {field_label} in raw "
        f"{food} with their own measurement (not a compilation), resolving to "
        f"the edible part, with a named quantification method and sample "
        f"count{value}."
    )


def license_triage_fields() -> list[str]:
    """Rule 9 triage columns, all confirmed filterable in the live catalog
    (checked 2026-09-20): doi, title, venue, year, OA status, license."""
    return [
        "unique_id",
        "doc_id",
        "title",
        "doi",
        "publication_published_year",
        "publication_venue_name_unified",
        "access_is_oa",
        "access_oa_status",
        "access_license",
    ]
