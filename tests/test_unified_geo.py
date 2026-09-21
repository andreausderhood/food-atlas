from atlas.claims import Claim
from atlas.registry import Source
from atlas.unified.cells import Cell
from atlas.unified.collectors import COLLECTORS, Universe, distribution
from atlas.unified.geo import normalize_distribution, parse_countries
from atlas.unified.identity import Edge
from atlas.unified.store import Store

SRC_GEO = Source(
    id="SRC-GEO",
    title="Geography Dataset",
    publisher="Kew",
    url="http://kew.org/wcvp",
    license="CC0",
    license_class="ship",
    license_read=True,
    kind="measurement",
    independence="independent",
    supports=("geography", "origin"),
    attribution="Kew WCVP",
)


def test_parse_countries_basic():
    assert parse_countries("Germany, France and United States") == {"DE", "FR", "US"}
    assert parse_countries("Germany; France; Italy") == {"DE", "FR", "IT"}
    assert parse_countries("Spain and Portugal") == {"ES", "PT"}
    assert parse_countries("DE, FR, US") == {"DE", "FR", "US"}


def test_normalize_distribution_sorted_tuple():
    assert normalize_distribution("Germany, France and United States") == ("DE", "FR", "US")
    assert normalize_distribution("United States, Germany, France") == ("DE", "FR", "US")
    assert normalize_distribution("") == ()
    assert normalize_distribution(None) == ()
    assert normalize_distribution("   ") == ()


def test_common_aliases():
    # Prompt explicitly lists:
    # "USA", "United States of America", "UK", "United Kingdom", "Russia", "Russian Federation",
    # "Cote d'Ivoire", "South Korea", "Vietnam", "Tanzania", "DR Congo", "Bolivia", "Syria",
    # "Iran", "Laos", "Venezuela"
    aliases = {
        "USA": "US",
        "United States of America": "US",
        "UK": "GB",
        "United Kingdom": "GB",
        "Russia": "RU",
        "Russian Federation": "RU",
        "Cote d'Ivoire": "CI",
        "Côte d'Ivoire": "CI",
        "South Korea": "KR",
        "Vietnam": "VN",
        "Viet Nam": "VN",
        "Tanzania": "TZ",
        "DR Congo": "CD",
        "Democratic Republic of the Congo": "CD",
        "Congo (DRC)": "CD",
        "Congo (Republic)": "CG",
        "Bolivia": "BO",
        "Syria": "SY",
        "Iran": "IR",
        "Laos": "LA",
        "Venezuela": "VE",
    }
    for name, code in aliases.items():
        assert parse_countries(name) == {code}, f"Failed for alias: {name}"


def test_countries_with_and_in_name():
    # Should not be split by "and" or "&"
    assert parse_countries("Bosnia and Herzegovina") == {"BA"}
    assert parse_countries("Bosnia & Herzegovina") == {"BA"}
    assert parse_countries("Trinidad and Tobago") == {"TT"}
    assert parse_countries("Antigua and Barbuda") == {"AG"}
    assert parse_countries("Saint Kitts and Nevis") == {"KN"}
    assert parse_countries("Saint Vincent and the Grenadines") == {"VC"}
    assert parse_countries("Sao Tome and Principe") == {"ST"}
    assert parse_countries("São Tomé and Príncipe") == {"ST"}
    assert parse_countries("Trinidad and Tobago, Canada and France") == {"TT", "CA", "FR"}


def test_ignores_non_country_regional_descriptors():
    assert parse_countries("Mediterranean") == set()
    assert parse_countries("Tropics") == set()
    assert parse_countries("Worldwide") == set()
    assert parse_countries("Cultivated") == set()
    assert normalize_distribution("Mediterranean, Tropics, Worldwide, Cultivated") == ()
    # Mixed with valid countries
    assert parse_countries("Mediterranean, Spain, Tropics, France") == {"ES", "FR"}
    assert normalize_distribution("Mediterranean, Spain, Tropics, France") == ("ES", "FR")


def test_complex_epd_distribution_string():
    s1 = (
        "It is a Mediterranean climate plant. Kuwait, Mediterranean, Middle East, "
        "Qatar, Saudi Arabia, Countries: United Arab Emirates , Albania , Bosnia &amp; Herzegovina"
    )
    assert parse_countries(s1) == {"KW", "QA", "SA", "AE", "AL", "BA"}

    s2 = (
        "Africa*, Botswana, East Africa, Uganda, Countries: Angola , Burkina Faso , "
        "Burundi , Benin , Botswana , Congo (DRC) , Central African Republic , "
        "Congo (Republic) , Cote d'Ivoire , Cameroon"
    )
    assert parse_countries(s2) == {
        "BW", "UG", "AO", "BF", "BI", "BJ", "CD", "CF", "CG", "CI", "CM"
    }


def test_distribution_in_collectors():
    assert "distribution" in COLLECTORS
    assert COLLECTORS["distribution"] is distribution


def test_distribution_context_when_iso_codes_exist():
    u = Universe(
        species={
            "malus domestica": {
                "epd": {
                    "path": "plants/malus",
                    "distribution": "Germany, France and United States",
                }
            },
            "abelmoschus angulosus": {
                "epd": {
                    "distribution": "India, Sri Lanka",
                }
            },
        }
    )
    cells = distribution(u)
    assert cells["malus domestica"] is Cell.CONTEXT
    assert cells["abelmoschus angulosus"] is Cell.CONTEXT


def test_distribution_searched_empty_when_empty_or_no_valid_iso():
    u = Universe(
        species={
            "beta vulgaris": {
                "epd": {
                    "path": "plants/beta",
                    "distribution": "",
                }
            },
            "aaronsohnia factorovskyi": {
                "epd": {
                    "path": "plants/aaronsohnia",
                    "distribution": "Mediterranean, Tropics",  # Non-country descriptors only
                }
            },
            "brassica oleracea": {
                "epd": {},
            },
        }
    )
    cells = distribution(u)
    assert cells["beta vulgaris"] is Cell.SEARCHED_EMPTY
    assert cells["aaronsohnia factorovskyi"] is Cell.SEARCHED_EMPTY
    assert cells["brassica oleracea"] is Cell.SEARCHED_EMPTY


def test_distribution_unsearched_for_non_epd_species():
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
    cells = distribution(u)
    assert cells["zzz nulla"] is Cell.UNSEARCHED
    assert cells["unknown plant"] is Cell.UNSEARCHED


def test_distribution_overlays_ledger_and_store(tmp_path):
    # 1. Ledger priority for geography and origin
    u_ledger = Universe(
        species={
            "malus domestica": {"epd": {"distribution": "Germany"}},
            "beta vulgaris": {"epd": {"distribution": "Tropics"}},
            "zzz nulla": {},
        },
        ledger={
            "geography": {"malus domestica"},
            "origin": {"zzz nulla"},
        },
    )
    cells_ledger = distribution(u_ledger)
    assert cells_ledger["malus domestica"] is Cell.FILLED
    assert cells_ledger["beta vulgaris"] is Cell.SEARCHED_EMPTY
    assert cells_ledger["zzz nulla"] is Cell.FILLED

    # 2. Store priority: accepted -> FILLED, rejected -> SEARCHED_EMPTY
    s = Store(tmp_path / "u.duckdb")
    accepted_claim = Claim(
        subject="prod:kew:1",
        group="geography",
        field="country_iso",
        v="DE",
        src="SRC-GEO",
        derivation="analytical",
        food_part="product",
    )
    origin_claim = Claim(
        subject="prod:kew:2",
        group="origin",
        field="country_iso",
        v="FR",
        src="SRC-GEO",
        derivation="analytical",
        food_part="product",
    )
    rejected_claim = Claim(
        subject="prod:kew:3",
        group="geography",
        field="country_iso",
        v="IT",
        src="SRC-GEO",
        derivation="unverified",
    )
    s.replace_source(
        "SRC-GEO",
        [accepted_claim, origin_claim, rejected_claim],
        {"SRC-GEO": SRC_GEO},
        "b1",
    )

    u_store = Universe(
        species={
            "malus domestica": {"epd": {"distribution": "France"}},
            "vitis vinifera": {"epd": {"distribution": "Worldwide"}},
            "beta vulgaris": {"epd": {"distribution": "Germany"}},
            "zzz nulla": {},
        },
        store=s,
    )
    edges = [
        Edge("prod:kew:1", "malus domestica", "manual", 1.0, "b", "a", "d"),
        Edge("prod:kew:2", "vitis vinifera", "manual", 1.0, "b", "a", "d"),
        Edge("prod:kew:3", "beta vulgaris", "manual", 1.0, "b", "a", "d"),
    ]
    s.load_edges(edges)
    u_store.edges = edges

    cells_store = distribution(u_store)
    # malus domestica has accepted geography claim -> FILLED
    assert cells_store["malus domestica"] is Cell.FILLED
    # vitis vinifera has accepted origin claim -> FILLED
    assert cells_store["vitis vinifera"] is Cell.FILLED
    # beta vulgaris has only rejected claim -> SEARCHED_EMPTY (overrides EPD CONTEXT)
    assert cells_store["beta vulgaris"] is Cell.SEARCHED_EMPTY
    # zzz nulla has no claims and no epd -> UNSEARCHED
    assert cells_store["zzz nulla"] is Cell.UNSEARCHED
    s.close()
