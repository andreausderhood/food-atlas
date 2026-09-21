from atlas.claims import Claim
from atlas.contract import validate
from atlas.registry import Source

SRC = Source(id="S", title="t", publisher="p", url="https://example.org", license="CC0-1.0", license_class="ship",
             license_read=True, kind="measurement", independence="independent", supports=("nutrition",),
             attribution="a")


def amount(**kw):
    base = dict(subject="prod:bls:B1", group="nutrition", field="nutrient:bls:VITC", v=4.6, unit="mg",
                basis="as_described", food_part="product", src="S", derivation="analytical")
    return Claim(**(base | kw))


def rules(*claims):
    return [g.rule for g in validate(list(claims), {"S": SRC}).gaps]


def test_product_record_amount_is_accepted_with_as_described():
    assert rules(amount()) == []


def test_product_record_may_not_borrow_a_curated_basis():
    assert rules(amount(basis="fresh_weight")) == [6]


def test_curated_food_may_not_use_as_described():
    assert rules(amount(subject="food:apple", food_part="whole")) == [6]


def test_product_record_must_declare_food_part_product():
    assert rules(amount(food_part="whole")) == [6]


def test_curated_food_with_fresh_weight_is_unchanged():
    assert rules(amount(subject="food:apple", basis="fresh_weight", food_part="whole")) == []


def test_presence_claims_on_products_need_no_basis():
    assert rules(Claim("prod:fdcf:1", "nutrition", "contains:CHEBI:1", "present", "S", "extracted")) == []
