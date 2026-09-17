import pytest

from atlas.claims import Claim
from atlas.contract import validate
from atlas.registry import Source


def src(sid="S", **kw):
    base = dict(
        id=sid, title="t", publisher="p", url="https://example.org", license="CC0-1.0",
        license_class="ship", license_read=True, kind="measurement", independence="independent",
        supports=("nutrition", "molecules", "bioactivity", "narrative", "season"), attribution="a",
    )
    base.update(kw)
    return Source(**base)


def amount(**kw):
    base = dict(
        subject="food:apple", group="nutrition", field="nutrient:fdc:1162", v=4.6,
        unit="mg", basis="fresh_weight", food_part="whole", src="S", derivation="analytical",
    )
    base.update(kw)
    return Claim(**base)


def rules(claims, sources):
    return [g.rule for g in validate(claims, sources).gaps]


def test_clean_amount_is_accepted():
    r = validate([amount()], {"S": src()})
    assert len(r.accepted) == 1 and r.gaps == []


def test_rule2_unregistered_source():
    assert rules([amount(src="NOPE")], {"S": src()}) == [2]


def test_rule1_unknown_derivation():
    assert rules([amount(derivation="guessed")], {"S": src()}) == [1]


def test_rule5_unverified_is_quarantined():
    assert rules([amount(derivation="unverified")], {"S": src()}) == [5]


def test_rule9_unread_license():
    assert rules([amount()], {"S": src(license_read=False)}) == [9]


def test_rule9_adapter_source_cannot_ship():
    assert rules([amount()], {"S": src(license_class="adapter")}) == [9]


def test_rule9_cite_source_only_for_curated_facts():
    s = {"S": src(license_class="cite", supports=("season",))}
    kw = dict(subject="food:apple", group="season", field="season:DE", v="Aug–Oct", src="S", derivation="registry", ref="Table 1, test row")
    assert rules([Claim(**kw), Claim(curated=True, **kw)], s) == [9]


def test_rule3_scope():
    assert rules([amount()], {"S": src(supports=("season",))}) == [3]


@pytest.mark.parametrize("change", [dict(basis=None), dict(basis="per_serving"), dict(food_part=None), dict(unit=None)])
def test_rule6_amount_needs_unit_basis_part(change):
    assert rules([amount(**change)], {"S": src()}) == [6]


def test_rule10_extracted_amount_becomes_gap():
    assert rules([amount(derivation="extracted")], {"S": src()}) == [10]


def test_rule10_extracted_presence_is_accepted():
    c = Claim(subject="food:apple", group="molecules", field="contains:CHEBI:16243", v="present",
              src="S", derivation="extracted", flags=("llm_extracted",))
    assert rules([c], {"S": src()}) == []


def test_rule10_secondhand_flag():
    assert rules([amount(flags=("secondhand",))], {"S": src()}) == [10]


def test_rule7_prediction_needs_model_and_version():
    kw = dict(group="bioactivity", v=0.8, derivation="predicted", flags=("evidence_only",))
    bad = amount(method="random forest", **kw)
    good = amount(method="model:frap-rf@2026.1", **kw)
    assert rules([bad, good], {"S": src()}) == [7]


def test_rule8_bioactivity_needs_evidence_flag():
    c = Claim(subject="food:apple", group="bioactivity", field="evidence:antioxidant",
              v="compound-level assay evidence", src="S", derivation="literature")
    assert rules([c], {"S": src()}) == [8]


def test_rule8_health_claim_wording():
    c = Claim(subject="food:apple", group="narrative", field="story",
              v="An anti-inflammatory food that prevents cancer.", src="S", derivation="editorial")
    assert rules([c], {"S": src()}) == [8]


def test_rule8_ordinary_wording_passes():
    c = Claim(subject="food:apple", group="narrative", field="story",
              v="The wax on the peel prevents water loss.", src="S", derivation="editorial")
    assert rules([c], {"S": src()}) == []


def test_rule4_broken_link_blocks_tiers_1_to_3_only():
    broken = {"S": src(link_status="broken")}
    assert rules([amount()], broken) == [4]
    assert rules([amount(derivation="borrowed")], broken) == []
