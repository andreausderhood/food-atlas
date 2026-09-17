from atlas.claims import Claim
from atlas.coverage import missing_coverage
from atlas.foods import FoodNode, Organism


def test_missing_fields_are_named_not_invented():
    org = Organism('org:malus-domestica', 'Malus domestica', 'species', None, 3750)
    node = FoodNode('food:apple', 'taxon_food', 'Apple', derives_from=org.id)
    claims = [Claim(node.id, 'sensory', 'taste', 'Tart', 'SRC-EDITORIAL', 'editorial')]
    gaps = missing_coverage(claims, {org.id: org}, {node.id: node})
    keys = {(g.subject, g.field) for g in gaps}
    assert (node.id, 'season:DE') in keys
    assert (org.id, 'primary_region_of_diversity') in keys
    assert (node.id, 'taste') not in keys
    assert all(g.carried_value is None and g.would_be_settled_by for g in gaps)


def test_growing_accepts_any_sourced_growing_field():
    org = Organism('org:malus-domestica', 'Malus domestica', 'species', None, 3750)
    claims = [Claim(org.id, 'growing', 'temperature_optimal_c', 'Read from source', 'S', 'registry')]
    assert not any(g.field == 'growing' for g in missing_coverage(claims, {org.id: org}, {}))
