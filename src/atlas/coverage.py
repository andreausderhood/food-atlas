"""Required pilot fields become named questions, never fabricated facts."""
from atlas.claims import Gap


def missing_coverage(claims, organisms, nodes):
    have = {(c.subject, c.group, c.field) for c in claims}
    groups = {(c.subject, c.group) for c in claims}
    gaps = []

    def need(subject, group, field, source, any_field=False):
        present = (subject, group) in groups if any_field else (subject, group, field) in have
        if not present:
            gaps.append(Gap(subject, field, 5,
                f"Required pilot {group} field has not yet been verified.",
                f"Read the primary {source} entry and record the exact reference and permitted use.",
                src=source))

    for org in organisms.values():
        if org.rank == 'species':
            need(org.id, 'identity', 'ncbi_taxon', 'SRC-NCBI-TAXONOMY')
            need(org.id, 'origin', 'primary_region_of_diversity', 'SRC-KHOURY-2016')
            need(org.id, 'growing', 'growing', 'SRC-ECOCROP', any_field=True)
        else:
            need(org.id, 'identity', 'rank', 'SRC-MANSFELD')
    for node in nodes.values():
        if node.level != 'taxon_food':
            continue
        need(node.id, 'season', 'season:DE', 'SRC-BZFE-SAISONKALENDER')
        for group, fields in [('sensory', ('colour', 'texture', 'taste')), ('narrative', ('eli5', 'story'))]:
            for field in fields:
                need(node.id, group, field, 'SRC-EDITORIAL')
    return gaps
