import pytest

from atlas.claims import Claim, tier_for


def test_tier_follows_derivation():
    assert tier_for("analytical") == 1
    assert tier_for("aggregated") == 2
    assert tier_for("registry") == 2
    assert tier_for("extracted") == 3
    assert tier_for("borrowed") == 4
    assert tier_for("editorial") == 4
    assert tier_for("unverified") == 5


def test_unknown_derivation_raises():
    with pytest.raises(ValueError):
        tier_for("guessed")


def test_amount_detection():
    base = dict(subject="food:apple", field="nutrient:fdc:1162", src="S", derivation="analytical")
    assert Claim(group="nutrition", v=4.6, **base).is_amount
    assert not Claim(group="nutrition", v="present", **base).is_amount
    assert not Claim(group="sensory", v=3.0, **base).is_amount
    assert not Claim(group="nutrition", v=True, **base).is_amount


def test_claim_tier_property():
    c = Claim(subject="food:apple", group="nutrition", field="x", v=1.0, src="S", derivation="literature")
    assert c.tier == 3
