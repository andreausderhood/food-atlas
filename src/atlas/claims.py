"""Claims are the atoms of the atlas: one value, one source, one derivation."""
from __future__ import annotations

from dataclasses import dataclass

BASES = ("fresh_weight", "dry_weight", "as_sold", "as_described")
PRODUCT_PREFIX = "prod:"   # a claim about one source record; the record itself says what was measured
AMOUNT_GROUPS = ("nutrition", "molecules")
DERIVATION_TIER: dict[str, int] = {
    "analytical": 1,
    "aggregated": 2,
    "registry": 2,
    "literature": 3,
    "extracted": 3,
    "calculated": 4,
    "imputed": 4,
    "borrowed": 4,
    "label": 4,
    "assumed_zero": 4,
    "trace": 4,
    "predicted": 4,
    "declared": 4,
    "editorial": 4,
    "unverified": 5,
}


class UnmappedDerivation(ValueError):
    """A source uses a derivation label the atlas has not classified yet."""


def tier_for(derivation: str) -> int:
    try:
        return DERIVATION_TIER[derivation]
    except KeyError:
        raise ValueError(f"unknown derivation: {derivation!r}") from None


@dataclass(frozen=True)
class Claim:
    subject: str
    group: str
    field: str
    v: object
    src: str
    derivation: str
    unit: str | None = None
    basis: str | None = None
    food_part: str | None = None
    method: str | None = None
    ref: str | None = None
    v_min: float | None = None
    v_max: float | None = None
    n: int | None = None
    flags: tuple[str, ...] = ()
    curated: bool = False

    @property
    def tier(self) -> int:
        return tier_for(self.derivation)

    @property
    def is_amount(self) -> bool:
        return (
            self.group in AMOUNT_GROUPS
            and isinstance(self.v, (int, float))
            and not isinstance(self.v, bool)
        )


@dataclass(frozen=True)
class Gap:
    subject: str
    field: str
    rule: int
    question: str
    would_be_settled_by: str
    carried_value: object = None
    src: str | None = None
