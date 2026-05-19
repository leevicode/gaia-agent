from urllib.parse import parse_qs, urlparse

import pytest

from app.sources.cheapshark_source import (
    CheapSharkSource,
    parse_optional_float,
)


def fake_cheapshark_http_get_json(url: str, timeout_seconds: float):
    parsed_url = urlparse(url)
    query = parse_qs(parsed_url.query)

    if parsed_url.path.endswith("/stores"):
        return [
            {
                "storeID": "1",
                "storeName": "Steam",
            },
            {
                "storeID": "25",
                "storeName": "Fanatical",
            },
        ]

    if parsed_url.path.endswith("/games") and "title" in query:
        return [
            {
                "gameID": "related-game-1",
                "steamAppID": "related-steam-1",
                "external": "Crimson Desert Deluxe Pack",
                "thumb": "https://example.test/related.jpg",
            },
            {
                "gameID": "game-456",
                "steamAppID": "steam-789",
                "external": "Crimson Desert",
                "thumb": "https://example.test/thumb.jpg",
            },
        ]

    if parsed_url.path.endswith("/games") and query.get("id") == ["game-456"]:
        return {
            "info": {
                "title": "Crimson Desert",
                "steamAppID": "steam-789",
                "thumb": "https://example.test/thumb.jpg",
            },
            "deals": [
                {
                    "storeID": "25",
                    "dealID": "deal-123",
                    "price": "49.99",
                    "retailPrice": "69.99",
                    "savings": "28.575511",
                }
            ],
        }

    raise AssertionError(f"Unexpected URL: {url}")


def test_parse_optional_float_parses_valid_number():
    assert parse_optional_float("49.99") == 49.99
    assert parse_optional_float(12) == 12.0


def test_parse_optional_float_returns_none_for_invalid_value():
    assert parse_optional_float(None) is None
    assert parse_optional_float("not-a-number") is None


def test_cheapshark_source_maps_exact_gameid_deals_to_internal_schema():
    source = CheapSharkSource(
        timeout_seconds=8.0,
        http_get_json=fake_cheapshark_http_get_json,
    )

    deals = source.search_deals("Crimson Desert")

    assert len(deals) == 1

    deal = deals[0]

    assert deal["store"] == "Fanatical"
    assert deal["title"] == "Crimson Desert"
    assert deal["price_eur"] is None
    assert deal["price_usd"] == 49.99
    assert deal["normal_price_usd"] == 69.99
    assert deal["savings_percent"] == 28.575511
    assert deal["condition"] == "digital"
    assert deal["shipping_eur"] == 0.0
    assert deal["availability"] == "available"
    assert deal["trust_score"] == 0.8
    assert deal["source_type"] == "authorized_reseller"
    assert deal["source_adapter"] == "cheapshark"
    assert deal["currency"] == "USD"
    assert "No EUR conversion" in deal["currency_note"]
    assert deal["deal_id"] == "deal-123"
    assert deal["store_id"] == "25"
    assert deal["game_id"] == "game-456"
    assert deal["steam_app_id"] == "steam-789"


def test_cheapshark_source_uses_games_title_lookup_before_gameid_lookup():
    requested_urls = []

    def fake_http_get_json(url: str, timeout_seconds: float):
        requested_urls.append(url)
        return fake_cheapshark_http_get_json(url, timeout_seconds)

    source = CheapSharkSource(
        timeout_seconds=8.0,
        http_get_json=fake_http_get_json,
    )

    source.search_deals("Crimson Desert")

    first_url = requested_urls[0]
    second_url = requested_urls[1]

    first_query = parse_qs(urlparse(first_url).query)
    second_query = parse_qs(urlparse(second_url).query)

    assert urlparse(first_url).path.endswith("/games")
    assert first_query["title"] == ["Crimson Desert"]
    assert first_query["limit"] == ["10"]
    assert urlparse(second_url).path.endswith("/games")
    assert second_query["id"] == ["game-456"]


def test_cheapshark_source_applies_max_price_after_gameid_deal_lookup():
    source = CheapSharkSource(
        timeout_seconds=8.0,
        http_get_json=fake_cheapshark_http_get_json,
    )

    deals = source.search_deals(
        "Crimson Desert",
        max_price=40.0,
    )

    assert deals == []


def test_cheapshark_source_returns_empty_list_for_empty_title():
    source = CheapSharkSource(
        timeout_seconds=8.0,
        http_get_json=fake_cheapshark_http_get_json,
    )

    assert source.search_deals("") == []
    assert source.search_deals("   ") == []


def test_cheapshark_source_rejects_invalid_timeout():
    with pytest.raises(ValueError, match="timeout_seconds"):
        CheapSharkSource(timeout_seconds=0)


def test_cheapshark_source_rejects_invalid_page_size():
    with pytest.raises(ValueError, match="page_size"):
        CheapSharkSource(page_size=0)
