"""Tests for BHL API plate resolver and photos coverage collector."""
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from atlas.claims import Claim
from atlas.registry import Source
from atlas.unified.cells import Cell
from atlas.unified.collectors import COLLECTORS, Universe, photos
from atlas.unified.fields import FIELDS
from atlas.unified.identity import Edge
from atlas.unified.photos import (
    PlateResolver,
    lookup_photo_status,
    register_searched_empty,
    register_verified_plate,
    resolve_bhl_plate,
    resolve_plate,
)
from atlas.unified.store import Store

SRC_BHL = Source(
    id="SRC-BHL",
    title="Biodiversity Heritage Library",
    publisher="Smithsonian",
    url="https://www.biodiversitylibrary.org/",
    license="public_domain",
    license_class="ship",
    license_read=True,
    kind="registry",
    independence="independent",
    supports=("photos",),
    attribution="BHL",
)


def test_field_photos_has_photos_collector():
    photo_field = next(f for f in FIELDS if f.key == "photos")
    assert photo_field.collector == "photos"


def test_photos_in_collectors():
    assert "photos" in COLLECTORS
    assert COLLECTORS["photos"] is photos


def test_resolve_bhl_plate_success_mocked_session():
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "Status": "ok",
        "Result": [
            {
                "NameBankID": "12345",
                "NameConfirmed": "Malus domestica",
                "PageUrl": "https://www.biodiversitylibrary.org/page/12345",
            }
        ],
    }
    mock_session.get.return_value = mock_response

    url = resolve_bhl_plate("Malus domestica", api_key="test_api_key", session=mock_session)
    assert url == "https://www.biodiversitylibrary.org/page/12345"
    mock_session.get.assert_called_once()
    args, kwargs = mock_session.get.call_args
    assert kwargs.get("params", {}).get("name") == "Malus domestica"
    assert kwargs.get("params", {}).get("apikey") == "test_api_key"
    assert kwargs.get("params", {}).get("op") == "NameSearch"


def test_resolve_bhl_plate_with_illustration_page():
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "Status": "ok",
        "Result": [
            {
                "Pages": [
                    {
                        "PageID": 9876,
                        "Illustration": True,
                        "PageUrl": "https://www.biodiversitylibrary.org/page/9876",
                    }
                ]
            }
        ],
    }
    mock_session.get.return_value = mock_response

    url = resolve_bhl_plate("Brassica oleracea", api_key="k", session=mock_session)
    assert url == "https://www.biodiversitylibrary.org/page/9876"


def test_resolve_bhl_plate_empty_result_returns_none():
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "Status": "ok",
        "Result": [],
    }
    mock_session.get.return_value = mock_response

    assert resolve_bhl_plate("Unknown species", api_key="k", session=mock_session) is None


def test_resolve_bhl_plate_error_status_returns_none():
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "Status": "error",
        "ErrorMessage": "Invalid API Key",
    }
    mock_session.get.return_value = mock_response

    assert resolve_bhl_plate("Malus domestica", api_key="invalid", session=mock_session) is None


def test_resolve_bhl_plate_without_api_key_or_session_returns_none(monkeypatch):
    monkeypatch.delenv("BHL_API_KEY", raising=False)
    assert resolve_bhl_plate("Malus domestica", api_key=None, session=None) is None


def test_resolve_bhl_plate_network_exception_returns_none():
    mock_session = MagicMock()
    mock_session.get.side_effect = IOError("Network unreachable")

    assert resolve_bhl_plate("Malus domestica", api_key="k", session=mock_session) is None


def test_plate_resolver_and_photo_status_lookup():
    # Malus domestica and Brassica oleracea have verified historical plates
    assert lookup_photo_status("Malus domestica") is Cell.FILLED
    assert lookup_photo_status("brassica oleracea") is Cell.FILLED
    assert resolve_plate("Malus domestica") is not None

    # Unsearched species
    assert lookup_photo_status("zzz unknown plant") is Cell.UNSEARCHED

    # Searched empty species
    register_searched_empty("rare wild weed")
    assert lookup_photo_status("rare wild weed") is Cell.SEARCHED_EMPTY

    # PlateResolver wrapper
    resolver = PlateResolver()
    assert resolver.status("malus domestica") is Cell.FILLED
    assert resolver.status("rare wild weed") is Cell.SEARCHED_EMPTY
    assert resolver.status("zzz unknown plant") is Cell.UNSEARCHED


def test_photos_collector_filled_for_verified_plates():
    u = Universe(
        species={
            "malus domestica": {},
            "brassica oleracea": {},
            "unknown species": {},
        }
    )
    cells = photos(u)
    assert cells["malus domestica"] is Cell.FILLED
    assert cells["brassica oleracea"] is Cell.FILLED
    assert cells["unknown species"] is Cell.UNSEARCHED


def test_photos_collector_searched_empty_no_fake_photos():
    register_searched_empty("searched empty herb")
    u = Universe(
        species={
            "searched empty herb": {},
            "unsearched grass": {},
        }
    )
    cells = photos(u)
    # Honest empty: searched in BHL/image registry where no authentic plate was found
    assert cells["searched empty herb"] is Cell.SEARCHED_EMPTY
    assert cells["unsearched grass"] is Cell.UNSEARCHED


def test_photos_collector_ledger_and_store_priority(tmp_path):
    # 1. Ledger priority
    u_ledger = Universe(
        species={
            "vitis vinifera": {},
            "zzz nulla": {},
        },
        ledger={"photos": {"vitis vinifera"}},
    )
    cells_ledger = photos(u_ledger)
    assert cells_ledger["vitis vinifera"] is Cell.FILLED
    assert cells_ledger["zzz nulla"] is Cell.UNSEARCHED

    # 2. Store priority: accepted claim -> FILLED, rejected claim -> SEARCHED_EMPTY
    s = Store(tmp_path / "u.duckdb")
    accepted_claim = Claim(
        subject="prod:plate:1",
        group="photos",
        field="plate_url",
        v="https://www.biodiversitylibrary.org/page/555",
        src="SRC-BHL",
        derivation="analytical",
        food_part="product",
    )
    rejected_claim = Claim(
        subject="prod:plate:2",
        group="photos",
        field="plate_url",
        v="https://example.org/fake.jpg",
        src="SRC-BHL",
        derivation="unverified",  # unverified -> rejected by rule 5
    )
    s.replace_source("SRC-BHL", [accepted_claim, rejected_claim], {"SRC-BHL": SRC_BHL}, "b1")

    u_store = Universe(
        species={
            "solanum lycopersicum": {},
            "pisum sativum": {},
            "zzz nulla": {},
        },
        store=s,
    )
    edges = [
        Edge("prod:plate:1", "solanum lycopersicum", "manual", 1.0, "b", "a", "d"),
        Edge("prod:plate:2", "pisum sativum", "manual", 1.0, "b", "a", "d"),
    ]
    s.load_edges(edges)
    u_store.edges = edges

    cells_store = photos(u_store)
    # solanum lycopersicum has accepted claim in store -> Cell.FILLED
    assert cells_store["solanum lycopersicum"] is Cell.FILLED
    # pisum sativum has only rejected claim in store -> Cell.SEARCHED_EMPTY
    assert cells_store["pisum sativum"] is Cell.SEARCHED_EMPTY
    # zzz nulla has no claims -> Cell.UNSEARCHED
    assert cells_store["zzz nulla"] is Cell.UNSEARCHED
    s.close()


def test_bhl_plate_cache(tmp_path: Path):
    from atlas.unified.photos import BHLPlateCache, PlateResolver

    cache_file = tmp_path / "bhl_cache.json"
    cache = BHLPlateCache(cache_file)
    assert len(cache) == 0

    # Cache a found plate
    cache.put("fragaria ananassa", "https://www.biodiversitylibrary.org/page/99999", title="Strawberry")
    assert cache.get("fragaria ananassa") == "https://www.biodiversitylibrary.org/page/99999"
    assert cache.status("fragaria ananassa") is Cell.FILLED

    # Cache an empty search (honest empty)
    cache.put_empty("rare orchid")
    assert cache.get("rare orchid") is None
    assert cache.status("rare orchid") is Cell.SEARCHED_EMPTY
    assert cache.status("completely unknown") is Cell.UNSEARCHED

    # Verify persistence to file
    cache.save()
    cache2 = BHLPlateCache(cache_file)
    assert cache2.get("fragaria ananassa") == "https://www.biodiversitylibrary.org/page/99999"
    assert cache2.status("rare orchid") is Cell.SEARCHED_EMPTY

    # PlateResolver using cache avoids network
    mock_session = MagicMock()
    resolver = PlateResolver(session=mock_session, cache=cache2)
    res = resolver.resolve("fragaria ananassa")
    assert res == "https://www.biodiversitylibrary.org/page/99999"
    mock_session.get.assert_not_called()

