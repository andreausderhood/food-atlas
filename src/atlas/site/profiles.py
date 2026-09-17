"""Interview views over accepted claims, without evidence or season inference."""
import re

RESEARCH_KINDS = {
    "human": "Human studies", "in_vitro": "Laboratory studies",
    "in_vivo": "Animal studies", "tradition": "Traditional use",
    "model": "Predictions", "unknown": "Evidence not classified",
}


def season_records(claims: list[dict]) -> list[dict]:
    """Only explicit season:<ISO region>:fresh|stored month lists are filterable.

    Existing unstructured season claims remain readable but do not imply a
    harvest calendar. An empty month list is unknown, never twelve absent months.
    """
    records = []
    for c in claims:
        if c.get("group") != "season":
            continue
        match = re.fullmatch(r"season:([A-Z]{2}(?:-[A-Z0-9]+)?):(fresh|stored)", c.get("field", ""))
        months = c.get("v")
        if (match and isinstance(months, list) and months and c.get("src")
                and all(type(m) is int and 1 <= m <= 12 for m in months)):
            records.append(dict(region=match[1], kind=match[2], months=sorted(set(months)), src=c["src"]))
    return records


def research_profile(claims: list[dict]) -> list[dict]:
    """Study setting is explicit method metadata, not the source's tier.

    Unclassified bioactivity stays unclassified; molecular occurrence does not
    establish activity or efficacy in people. No scores or radar areas inferred.
    """
    groups = {kind: [] for kind in RESEARCH_KINDS}
    for c in claims:
        if c.get("group") != "bioactivity":
            continue
        kind = (c.get("method") or "").split(":", 1)[0]
        groups[kind if kind in groups else "unknown"].append(c)
    return [dict(kind=kind, label=RESEARCH_KINDS[kind], claims=values)
            for kind, values in groups.items() if values]
