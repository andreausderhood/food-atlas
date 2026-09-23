"""The traceability contract (product.md §3): each claim passes rules 1–10 or becomes a gap."""
from __future__ import annotations

import re
import math
from dataclasses import dataclass, field

from atlas.claims import BASES, DERIVATION_TIER, PRODUCT_PREFIX, Claim, Gap
from atlas.registry import Source

UNVERIFIED = "SRC-UNVERIFIED"
PREDICTED_METHOD = re.compile(r"^model:[^\@\s]+@[^\@\s]+$")
HEALTH_CLAIM = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\banti-?(inflammatory|cancer|diabetic|oxidant|viral|bacterial|aging)\s+(foods?|fruits?|vegetables?)\b",
        r"\b(cures?|treats?|prevents?|heals?)\s+(cancer|diabetes|disease|inflammation|infections?)\b",
        r"\bsuper-?foods?\b",
    )
]
TEXT_GROUPS = ("bioactivity", "narrative", "sensory")
SETTLED_BY = {
    1: "A claim with a subject, a field and a known derivation.",
    2: "Register the source in data/registry/sources.yaml.",
    3: "A source whose scope covers this claim group.",
    4: "A working link to the source, or a replacement source.",
    5: "A named, traceable source for this value.",
    6: "Unit, basis (fresh weight, dry weight or as sold) and food part from the original study.",
    7: "The model name and version, written as model:<name>@<version>.",
    8: "Evidence wording without a health claim, flagged evidence_only.",
    9: "A read license that allows open redistribution, or a curated citation of a single fact.",
    10: "The primary study that measured this value.",
}


@dataclass(frozen=True)
class CheckResult:
    """Return value of contract.check(): ok=True means the claim passes all rules."""
    ok: bool
    reason: str | None = None
    rule: int | None = None
    gap: Gap | None = None

    def __bool__(self) -> bool:
        """Truthy when there IS a problem, falsy when ok."""
        return not self.ok

    @classmethod
    def passed(cls) -> "CheckResult":
        return cls(ok=True)

    @classmethod
    def failed(cls, gap: Gap) -> "CheckResult":
        return cls(ok=False, reason=gap.question, rule=gap.rule, gap=gap)


@dataclass
class ValidationResult:
    accepted: list[Claim] = field(default_factory=list)
    gaps: list[Gap] = field(default_factory=list)


def _gap(claim: Claim, rule: int, question: str) -> Gap:
    return Gap(
        subject=claim.subject, field=claim.field, rule=rule, question=question,
        would_be_settled_by=SETTLED_BY[rule], carried_value=None if rule in (1, 2, 9) else claim.v, src=claim.src,
    )


def check(claim: Claim, sources: dict[str, Source]) -> CheckResult:
    source = sources.get(claim.src)
    if source is None:
        return CheckResult.failed(_gap(claim, 2, f"Source {claim.src!r} is not registered."))
    if not claim.subject or not claim.field or claim.derivation not in DERIVATION_TIER:
        return CheckResult.failed(_gap(claim, 1, f"Incomplete claim or unknown derivation {claim.derivation!r}."))
    if any(isinstance(v, float) and not math.isfinite(v) for v in (claim.v, claim.v_min, claim.v_max)):
        return CheckResult.failed(_gap(claim, 1, "Non-finite numeric value."))
    if claim.derivation == "unverified" or claim.src == UNVERIFIED:
        return CheckResult.failed(_gap(claim, 5, "Unverified value: the source does not state how it was obtained."))
    if not source.license_read:
        return CheckResult.failed(_gap(claim, 9, f"The license of {source.id} has not been read yet."))
    if source.license_class == "cite" and not claim.curated:
        return CheckResult.failed(_gap(claim, 9, f"{source.id} may only be cited fact by fact, not imported in bulk."))
    if source.license_class == "cite" and not claim.ref:
        return CheckResult.failed(_gap(claim, 9, "A cited fact needs a specific reference."))
    ALLOWED_SHIP = ("ship", "public_domain", "open_license", "open_content")
    if source.license_class not in ALLOWED_SHIP and source.license_class != "cite":
        return CheckResult.failed(_gap(claim, 9, f"{source.id} is {source.license_class}-only and cannot ship under open terms."))
    if claim.group not in source.supports:
        return CheckResult.failed(_gap(claim, 3, f"{source.id} does not support claim group {claim.group!r}."))
    if claim.is_amount and (not claim.unit or claim.basis not in BASES or not claim.food_part):
        return CheckResult.failed(_gap(claim, 6, "Amount without unit, basis or food part."))
    if claim.is_amount and claim.subject.startswith(PRODUCT_PREFIX) != (claim.basis == "as_described"):
        return CheckResult.failed(_gap(claim, 6, "Basis as_described belongs to product records only, and a product record may use no other basis."))
    if claim.is_amount and claim.subject.startswith(PRODUCT_PREFIX) and claim.food_part != "product":
        return CheckResult.failed(_gap(claim, 6, "A product record describes its own sample: food_part must be 'product'."))
    if claim.is_amount and claim.derivation == "extracted":
        return CheckResult.failed(_gap(claim, 10, "Machine-extracted amount; the primary measurement is not confirmed."))
    if "secondhand" in claim.flags:
        return CheckResult.failed(_gap(claim, 10, "Value quoted second-hand from another study."))
    if claim.derivation == "predicted" and not (claim.method and PREDICTED_METHOD.match(claim.method)):
        return CheckResult.failed(_gap(claim, 7, "Prediction without model name and version."))
    if claim.group == "bioactivity" and "evidence_only" not in claim.flags:
        return CheckResult.failed(_gap(claim, 8, "Bioactivity claim not marked as evidence."))
    if claim.group in TEXT_GROUPS and isinstance(claim.v, str) and any(p.search(claim.v) for p in HEALTH_CLAIM):
        return CheckResult.failed(_gap(claim, 8, "The wording reads as a health claim."))
    if claim.tier <= 3 and source.link_status == "broken":
        return CheckResult.failed(_gap(claim, 4, f"The link to {source.id} is broken."))
    return CheckResult.passed()


def validate(claims: list[Claim], sources: dict[str, Source]) -> ValidationResult:
    result = ValidationResult()
    for claim in claims:
        cr = check(claim, sources)
        if cr.ok:
            result.accepted.append(claim)
        else:
            result.gaps.append(cr.gap)  # type: ignore[arg-type]
    return result
