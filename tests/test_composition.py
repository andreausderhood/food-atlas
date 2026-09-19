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


KALE = [  # real values, data/build/atlas.json, per 100 g
    claim("Water", 89.6), claim("Water", 89.63, src="SRC-B"),
    claim("Carbohydrate, by difference", 4.42, tier=4),
    claim("Protein", 2.92), claim("Ash", 1.54), claim("Total lipid (fat)", 1.49),
]


def test_macro_split_separates_water_from_everything_else():
    from atlas.site.composition import macro_split
    split = macro_split(KALE)
    assert split["water"]["text"] == "89.6–89.63"
    assert split["dry_total"] == 10.37
    assert split["total"] == 100.0


def test_macro_split_orders_dry_matter_largest_first_with_display_names():
    from atlas.site.composition import macro_split
    split = macro_split(KALE)
    assert [(d["display"], d["text"]) for d in split["dry"]] == [
        ("Carbohydrate", "4.42"), ("Protein", "2.92"),
        ("Minerals (ash)", "1.54"), ("Fat", "1.49")]


def test_macro_split_is_none_without_water():
    from atlas.site.composition import macro_split
    assert macro_split([claim("Protein", 2.92)]) is None


def test_macro_split_is_none_without_any_dry_component():
    from atlas.site.composition import macro_split
    assert macro_split([claim("Water", 89.6)]) is None


def test_macro_split_tolerates_partial_dry_matter():
    from atlas.site.composition import macro_split
    split = macro_split([claim("Water", 89.6), claim("Protein", 2.92)])
    assert split["dry_total"] == 2.92
    assert [d["display"] for d in split["dry"]] == ["Protein"]
    assert split["total"] == 92.52


def test_micro_readings_keep_declared_order_and_skip_absent():
    from atlas.site.composition import micro_readings
    claims = [claim("Vitamin C, total ascorbic acid", 93.4, unit="mg"),
              claim("Calcium, Ca", 254.0, unit="mg"),
              claim("Vitamin K (phylloquinone)", 389.6, unit="ug"),
              claim("Vitamin K (phylloquinone)", 390.0, src="SRC-B", unit="ug")]
    rows = micro_readings(claims)
    assert [r["label"] for r in rows] == [
        "Vitamin K (phylloquinone)", "Vitamin C, total ascorbic acid", "Calcium, Ca"]
    assert rows[0]["text"] == "389.6–390"
    assert rows[0]["unit"] == "ug"


def test_micro_readings_respect_the_limit():
    from atlas.site.composition import micro_readings
    claims = [claim("Vitamin C, total ascorbic acid", 1.0, unit="mg"),
              claim("Calcium, Ca", 2.0, unit="mg"),
              claim("Iron, Fe", 3.0, unit="mg")]
    assert len(micro_readings(claims, limit=2)) == 2


def test_micro_readings_empty_when_nothing_present():
    from atlas.site.composition import micro_readings
    assert micro_readings([claim("Protein", 2.92)]) == []


def test_labelled_claims_resolve_nutrient_and_molecule_names():
    from atlas.site.build import labelled_claims
    payload = dict(nutrients={"nutrient:fdc:1003": {"name": "Protein"}},
                   molecules={"quercetin": {"name": "Quercetin"}})
    food = dict(claims=[
        dict(group="nutrition", field="nutrient:fdc:1003", v=2.92, src="SRC-A", tier=1),
        dict(group="molecules", field="contains:quercetin", v="present", src="SRC-B", tier=3),
        dict(group="nutrition", field="nutrient:fdc:9999", v=1.0, src="SRC-A", tier=1),
    ])
    rows = labelled_claims(food, payload)
    assert [r["label"] for r in rows] == ["Protein", "Quercetin", "nutrient:fdc:9999"]
