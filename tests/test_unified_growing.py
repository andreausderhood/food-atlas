from atlas.claims import Claim
from atlas.registry import Source
from atlas.unified.cells import Cell
from atlas.unified.collectors import COLLECTORS, Universe, growing
from atlas.unified.identity import Edge
from atlas.unified.store import Store

SRC_GROW = Source(
    id="SRC-GROW",
    title="Growing Guide",
    publisher="FAO",
    url="http://fao.org/ecocrop",
    license="CC0",
    license_class="ship",
    license_read=True,
    kind="measurement",
    independence="independent",
    supports=("growing",),
    attribution="FAO ECOCROP",
)


def test_growing_is_in_collectors():
    assert "growing" in COLLECTORS
    assert COLLECTORS["growing"] is growing


def test_growing_context_for_species_with_epd_grow():
    u = Universe(
        species={
            "malus domestica": {
                "epd": {
                    "path": "plants/malus",
                    "grow": "Temperate climates, well-drained loamy soil, full sun.",
                }
            },
            "abelmoschus angulosus": {
                "epd": {
                    "grow": "It is used as a hedge.",
                }
            },
        }
    )
    cells = growing(u)
    assert cells["malus domestica"] is Cell.CONTEXT
    assert cells["abelmoschus angulosus"] is Cell.CONTEXT


def test_growing_searched_empty_for_epd_species_without_epd_grow():
    u = Universe(
        species={
            "beta vulgaris": {
                "epd": {
                    "path": "plants/beta",
                    "grow": "",
                }
            },
            "aaronsohnia factorovskyi": {
                "epd": {
                    "path": "plants/aaronsohnia",
                    "distribution": "Kuwait, Mediterranean",
                }
            },
            "brassica oleracea": {
                "epd": {},
            },
        }
    )
    cells = growing(u)
    assert cells["beta vulgaris"] is Cell.SEARCHED_EMPTY
    assert cells["aaronsohnia factorovskyi"] is Cell.SEARCHED_EMPTY
    assert cells["brassica oleracea"] is Cell.SEARCHED_EMPTY


def test_growing_unsearched_for_nonepd_species_without_grow_data():
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
    cells = growing(u)
    assert cells["zzz nulla"] is Cell.UNSEARCHED
    assert cells["unknown plant"] is Cell.UNSEARCHED


def test_growing_prioritizes_claims_in_store_and_ledger(tmp_path):
    # 1. Ledger priority
    u_ledger = Universe(
        species={
            "malus domestica": {"epd": {"grow": "Temperate climate"}},
            "zzz nulla": {},
        },
        ledger={"growing": {"malus domestica", "zzz nulla"}},
    )
    cells_ledger = growing(u_ledger)
    assert cells_ledger["malus domestica"] is Cell.FILLED
    assert cells_ledger["zzz nulla"] is Cell.FILLED

    # 2. Store priority: accepted -> FILLED, rejected -> SEARCHED_EMPTY
    s = Store(tmp_path / "u.duckdb")
    accepted_claim = Claim(
        subject="prod:crop:1",
        group="growing",
        field="temp_max",
        v=35.0,
        src="SRC-GROW",
        derivation="analytical",
        unit="degC",
        basis="as_described",
        food_part="product",
    )
    rejected_claim = Claim(
        subject="prod:crop:2",
        group="growing",
        field="temp_max",
        v=35.0,
        src="SRC-GROW",
        derivation="unverified",  # unverified -> rejected by rule 5
    )
    s.replace_source("SRC-GROW", [accepted_claim, rejected_claim], {"SRC-GROW": SRC_GROW}, "b1")

    u_store = Universe(
        species={
            "malus domestica": {"epd": {"grow": "Full sun"}},
            "beta vulgaris": {"epd": {"grow": "Full sun"}},
            "zzz nulla": {},
        },
        store=s,
    )
    edges = [
        Edge("prod:crop:1", "malus domestica", "manual", 1.0, "b", "a", "d"),
        Edge("prod:crop:2", "beta vulgaris", "manual", 1.0, "b", "a", "d"),
    ]
    s.load_edges(edges)
    u_store.edges = edges

    cells_store = growing(u_store)
    # malus domestica has an accepted claim in store -> Cell.FILLED
    assert cells_store["malus domestica"] is Cell.FILLED
    # beta vulgaris has only a rejected claim in store -> Cell.SEARCHED_EMPTY (overrides epd.grow CONTEXT)
    assert cells_store["beta vulgaris"] is Cell.SEARCHED_EMPTY
    # zzz nulla has no claims in store/ledger and no epd -> Cell.UNSEARCHED
    assert cells_store["zzz nulla"] is Cell.UNSEARCHED
    s.close()
