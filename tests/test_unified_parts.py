from atlas.claims import Claim
from atlas.foods import PARTS
from atlas.registry import Source
from atlas.unified.cells import Cell
from atlas.unified.collectors import COLLECTORS, Universe, edible_parts
from atlas.unified.identity import Edge
from atlas.unified.parts import normalize_edible_parts, normalize_part
from atlas.unified.store import Store

SRC_PARTS = Source(
    id="SRC-PARTS",
    title="Edible Plants Database",
    publisher="EPD",
    url="http://example.org/epd",
    license="CC0",
    license_class="ship",
    license_read=True,
    kind="measurement",
    independence="independent",
    supports=("edible_parts", "parts"),
    attribution="EPD",
)


def test_normalize_part_prompt_tokens():
    # Specific tokens required by the task prompt:
    # "Roots,", "Pods,", "Leaves,", "Fruit", "Seeds,", "Flowers,", "Shoots,", "Whole plant"
    assert normalize_part("Roots,") == "stem"
    assert normalize_part("Pods,") == "mesocarp"
    assert normalize_part("Leaves,") == "leaf"
    assert normalize_part("Fruit") == "mesocarp"
    assert normalize_part("Seeds,") == "seed"
    assert normalize_part("Flowers,") == "inflorescence"
    assert normalize_part("Shoots,") == "stem"
    assert normalize_part("Whole plant") == "whole"


def test_normalize_part_canonical_vocabulary():
    # Every canonical part in foods.PARTS maps to itself
    for part in PARTS:
        assert normalize_part(part) == part
        assert normalize_part(part.upper()) == part
        assert normalize_part(f"{part},") == part


def test_normalize_part_botanical_synonyms():
    # Fruit / mesocarp
    assert normalize_part("fruits") == "mesocarp"
    assert normalize_part("fruit,") == "mesocarp"
    assert normalize_part("berries") == "mesocarp"
    assert normalize_part("berry,") == "mesocarp"
    assert normalize_part("pod") == "mesocarp"
    assert normalize_part("pods") == "mesocarp"
    assert normalize_part("pulp") == "mesocarp"
    assert normalize_part("aril") == "mesocarp"
    assert normalize_part("aril,") == "mesocarp"

    # Leaf
    assert normalize_part("leaf") == "leaf"
    assert normalize_part("leaves") == "leaf"
    assert normalize_part("fronds,") == "leaf"
    assert normalize_part("frond") == "leaf"
    assert normalize_part("greens") == "leaf"

    # Seed
    assert normalize_part("seed") == "seed"
    assert normalize_part("seeds") == "seed"
    assert normalize_part("nut") == "seed"
    assert normalize_part("nuts,") == "seed"
    assert normalize_part("kernel") == "seed"
    assert normalize_part("kernels,") == "seed"
    assert normalize_part("grain") == "seed"
    assert normalize_part("beans") == "seed"

    # Inflorescence / flower
    assert normalize_part("flower") == "inflorescence"
    assert normalize_part("flowers") == "inflorescence"
    assert normalize_part("blossom") == "inflorescence"
    assert normalize_part("floret") == "inflorescence"

    # Stem / root / tuber / shoot
    assert normalize_part("stem") == "stem"
    assert normalize_part("stems,") == "stem"
    assert normalize_part("stalk") == "stem"
    assert normalize_part("stalks") == "stem"
    assert normalize_part("shoot") == "stem"
    assert normalize_part("shoots") == "stem"
    assert normalize_part("root") == "stem"
    assert normalize_part("roots") == "stem"
    assert normalize_part("tuber") == "stem"
    assert normalize_part("tubers,") == "stem"
    assert normalize_part("rhizome") == "stem"
    assert normalize_part("rhizomes,") == "stem"
    assert normalize_part("corm") == "stem"
    assert normalize_part("corms,") == "stem"
    assert normalize_part("bulb") == "stem"
    assert normalize_part("bulbs,") == "stem"

    # Exocarp / bark / peel
    assert normalize_part("bark") == "exocarp"
    assert normalize_part("bark,") == "exocarp"
    assert normalize_part("inner bark") == "exocarp"
    assert normalize_part("peel") == "exocarp"
    assert normalize_part("rind") == "exocarp"

    # Head / cabbage
    assert normalize_part("head") == "head"
    assert normalize_part("cabbage") == "head"
    assert normalize_part("cabbage,") == "head"

    # Axillary bud
    assert normalize_part("bud") == "axillary_bud"
    assert normalize_part("buds") == "axillary_bud"
    assert normalize_part("buds,") == "axillary_bud"
    assert normalize_part("axillary bud") == "axillary_bud"

    # Seedling / sprouts
    assert normalize_part("seedling") == "seedling"
    assert normalize_part("seedlings,") == "seedling"
    assert normalize_part("sprouts") == "seedling"
    assert normalize_part("sprout") == "seedling"

    # Whole
    assert normalize_part("plant") == "whole"
    assert normalize_part("plant,") == "whole"
    assert normalize_part("whole") == "whole"
    assert normalize_part("mushroom") == "whole"
    assert normalize_part("mushroom,") == "whole"
    assert normalize_part("fungus,") == "whole"
    assert normalize_part("seaweed,") == "whole"
    assert normalize_part("algae,") == "whole"
    assert normalize_part("lichen") == "whole"
    assert normalize_part("truffle,") == "whole"


def test_normalize_part_unrecognized_returns_none():
    assert normalize_part("") is None
    assert normalize_part("   ") is None
    assert normalize_part("-") is None
    assert normalize_part("?") is None
    assert normalize_part("?,") is None
    assert normalize_part("tea") is None
    assert normalize_part("tea,") is None
    assert normalize_part("spice") is None
    assert normalize_part("flavouring") is None
    assert normalize_part("drink") is None
    assert normalize_part("oil") is None
    assert normalize_part("gum") is None
    assert normalize_part("sap") is None
    assert normalize_part("medicine") is None
    assert normalize_part("starch") is None
    assert normalize_part("salt") is None
    assert normalize_part("wood") is None
    assert normalize_part("caution") is None
    assert normalize_part("(POISONOUS)") is None


def test_normalize_edible_parts_empty_and_none():
    assert normalize_edible_parts(None) == ()
    assert normalize_edible_parts([]) == ()
    assert normalize_edible_parts("") == ()
    assert normalize_edible_parts("   ") == ()
    assert normalize_edible_parts(["-", "?", "tea", "spice"]) == ()


def test_normalize_edible_parts_list():
    assert normalize_edible_parts(["Roots,", "Pods,", "Leaves,"]) == ("leaf", "mesocarp", "stem")
    assert normalize_edible_parts([
        "Fruit", "Seeds,", "Flowers,", "Shoots,", "Whole plant"
    ]) == ("inflorescence", "mesocarp", "seed", "stem", "whole")
    assert normalize_edible_parts(["Leaves", "-", "tea,"]) == ("leaf",)
    assert normalize_edible_parts(["Seeds", "(POISONOUS)", ","]) == ("seed",)
    assert normalize_edible_parts(["Fruit", "Fruit,", "mesocarp"]) == ("mesocarp",)
    assert normalize_edible_parts(["Inner", "bark,"]) == ("exocarp",)


def test_normalize_edible_parts_string():
    assert normalize_edible_parts("Roots, Pods, Leaves") == ("leaf", "mesocarp", "stem")
    assert normalize_edible_parts("Leaves - tea") == ("leaf",)
    assert normalize_edible_parts("Fruit; Seeds") == ("mesocarp", "seed")
    assert normalize_edible_parts("Whole plant") == ("whole",)


def test_edible_parts_in_collectors():
    assert "edible_parts" in COLLECTORS
    assert COLLECTORS["edible_parts"] is edible_parts


def test_edible_parts_context_when_valid_parts_exist():
    u = Universe(
        species={
            "malus domestica": {
                "epd": {
                    "path": "plants/malus",
                    "edible_parts": ["Fruit", "Leaves"],
                }
            },
            "abelmoschus esculentus": {
                "epd": {
                    "edible_parts": ["Pods,"],
                }
            },
            "beta vulgaris": {
                "epd": {
                    "edible_parts": "Roots, Leaves",
                }
            },
        }
    )
    cells = edible_parts(u)
    assert cells["malus domestica"] is Cell.CONTEXT
    assert cells["abelmoschus esculentus"] is Cell.CONTEXT
    assert cells["beta vulgaris"] is Cell.CONTEXT


def test_edible_parts_searched_empty_when_empty_or_unrecognizable():
    u = Universe(
        species={
            "plant empty list": {
                "epd": {
                    "path": "plants/empty",
                    "edible_parts": [],
                }
            },
            "plant empty str": {
                "epd": {
                    "path": "plants/empty2",
                    "edible_parts": "",
                }
            },
            "plant only tea": {
                "epd": {
                    "path": "plants/tea",
                    "edible_parts": ["tea", "flavouring", "-"],
                }
            },
            "plant no parts key": {
                "epd": {
                    "path": "plants/noparts",
                }
            },
        }
    )
    cells = edible_parts(u)
    assert cells["plant empty list"] is Cell.SEARCHED_EMPTY
    assert cells["plant empty str"] is Cell.SEARCHED_EMPTY
    assert cells["plant only tea"] is Cell.SEARCHED_EMPTY
    assert cells["plant no parts key"] is Cell.SEARCHED_EMPTY


def test_edible_parts_unsearched_for_non_epd_species():
    u = Universe(
        species={
            "zzz nulla": {
                "sources": ["wiki:something"],
                "epd": None,
            },
            "unknown plant": {
                "common_names": [],
            },
        }
    )
    cells = edible_parts(u)
    assert cells["zzz nulla"] is Cell.UNSEARCHED
    assert cells["unknown plant"] is Cell.UNSEARCHED


def test_edible_parts_overlays_ledger_and_store(tmp_path):
    # 1. Ledger priority
    u_ledger = Universe(
        species={
            "malus domestica": {"epd": {"edible_parts": ["Fruit"]}},
            "beta vulgaris": {"epd": {"edible_parts": ["tea"]}},
            "zzz nulla": {},
        },
        ledger={
            "edible_parts": {"malus domestica"},
            "parts": {"zzz nulla"},
        },
    )
    cells_ledger = edible_parts(u_ledger)
    assert cells_ledger["malus domestica"] is Cell.FILLED
    assert cells_ledger["beta vulgaris"] is Cell.SEARCHED_EMPTY
    assert cells_ledger["zzz nulla"] is Cell.FILLED

    # 2. Store priority: accepted -> FILLED, rejected -> SEARCHED_EMPTY
    s = Store(tmp_path / "u.duckdb")
    accepted_claim = Claim(
        subject="prod:epd:1",
        group="edible_parts",
        field="part",
        v="fruit",
        src="SRC-PARTS",
        derivation="analytical",
        food_part="product",
    )
    parts_claim = Claim(
        subject="prod:epd:2",
        group="parts",
        field="part",
        v="seed",
        src="SRC-PARTS",
        derivation="analytical",
        food_part="product",
    )
    rejected_claim = Claim(
        subject="prod:epd:3",
        group="edible_parts",
        field="part",
        v="leaf",
        src="SRC-PARTS",
        derivation="unverified",
    )
    s.replace_source(
        "SRC-PARTS",
        [accepted_claim, parts_claim, rejected_claim],
        {"SRC-PARTS": SRC_PARTS},
        "b1",
    )

    u_store = Universe(
        species={
            "malus domestica": {"epd": {"edible_parts": ["Fruit"]}},
            "vitis vinifera": {"epd": {"edible_parts": ["tea"]}},
            "beta vulgaris": {"epd": {"edible_parts": ["Fruit"]}},
            "zzz nulla": {},
        },
        store=s,
    )
    edges = [
        Edge("prod:epd:1", "malus domestica", "manual", 1.0, "b", "a", "d"),
        Edge("prod:epd:2", "vitis vinifera", "manual", 1.0, "b", "a", "d"),
        Edge("prod:epd:3", "beta vulgaris", "manual", 1.0, "b", "a", "d"),
    ]
    s.load_edges(edges)
    u_store.edges = edges

    cells_store = edible_parts(u_store)
    # malus domestica has accepted edible_parts claim -> FILLED
    assert cells_store["malus domestica"] is Cell.FILLED
    # vitis vinifera has accepted parts claim -> FILLED
    assert cells_store["vitis vinifera"] is Cell.FILLED
    # beta vulgaris has only rejected claim -> SEARCHED_EMPTY (overrides EPD CONTEXT)
    assert cells_store["beta vulgaris"] is Cell.SEARCHED_EMPTY
    # zzz nulla has no claims and no epd -> UNSEARCHED
    assert cells_store["zzz nulla"] is Cell.UNSEARCHED
    s.close()
