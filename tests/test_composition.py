"""The composition model: a whole is 100% of a declared basis (spec §5)."""


def claim(label, value, src="SRC-A", tier=1, unit="g"):
    return dict(group="nutrition", label=label, v=value, unit=unit, src=src,
                tier=tier, derivation="analytical")


def test_single_source_reads_as_one_value():
    from atlas.site.composition import reading
    r = reading([claim("Protein", 2.92)], "Protein")
    assert r["text"] == "2.92"
    assert r["is_range"] is False
    assert r["unit"] == "g"
    assert r["sources"] == 1


def test_disagreeing_sources_read_as_a_range():
    from atlas.site.composition import reading
    claims = [claim("Carotene, beta", 2870.0, src="SRC-A", unit="ug"),
              claim("Carotene, beta", 2873.0, src="SRC-B", unit="ug")]
    r = reading(claims, "Carotene, beta")
    assert r["text"] == "2870–2873"
    assert r["is_range"] is True
    assert (r["low"], r["high"]) == (2870.0, 2873.0)
    assert r["sources"] == 2


def test_agreeing_sources_do_not_produce_a_range():
    from atlas.site.composition import reading
    claims = [claim("Calcium, Ca", 254.0, src="SRC-A", unit="mg"),
              claim("Calcium, Ca", 254.0, src="SRC-B", unit="mg")]
    r = reading(claims, "Calcium, Ca")
    assert r["is_range"] is False
    assert r["text"] == "254"
    assert r["sources"] == 2


def test_absent_nutrient_is_none_never_zero():
    from atlas.site.composition import reading
    assert reading([claim("Protein", 2.92)], "Water") is None


def test_non_numeric_and_boolean_values_are_ignored():
    from atlas.site.composition import reading
    assert reading([claim("Protein", "present")], "Protein") is None
    assert reading([claim("Protein", True)], "Protein") is None


def test_unit_and_tier_come_from_the_best_evidenced_claim():
    from atlas.site.composition import reading
    claims = [claim("Protein", 4.16, src="SRC-BLS", tier=3),
              claim("Protein", 2.92, src="SRC-FDC", tier=1)]
    r = reading(claims, "Protein")
    assert r["tier"] == 1
    assert r["text"] == "2.92–4.16"
