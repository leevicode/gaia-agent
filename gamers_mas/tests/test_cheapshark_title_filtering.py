from urllib.parse import parse_qs, urlparse

from app.agents.authorized_reseller_agent import build_authorized_reseller_search_result
from app.currency.converter import build_configured_usd_to_eur_rate
from app.sources.cheapshark_source import (
    CheapSharkSource,
    filter_raw_deals_by_exact_title,
    find_exact_game_match,
    is_exact_returned_title_match,
)


class FakeEcbRateSource:
    def get_usd_to_eur_rate(self):
        return build_configured_usd_to_eur_rate(
            usd_to_eur_rate="0.90",
            source="fake_ecb_rate",
            rate_date="2026-05-08",
        )


def fake_cheapshark_with_exact_and_related_games(url: str, timeout_seconds: float):
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
                "storeName": "Epic Games Store",
            },
            {
                "storeID": "27",
                "storeName": "Gamesplanet",
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
                "gameID": "exact-game-1",
                "steamAppID": "3321460",
                "external": "Crimson Desert",
                "thumb": "https://example.test/exact.jpg",
            },
            {
                "gameID": "related-game-2",
                "steamAppID": "related-steam-2",
                "external": "Crimson Desert Digital Deluxe Edition",
                "thumb": "https://example.test/related2.jpg",
            },
        ]

    if parsed_url.path.endswith("/games") and query.get("id") == ["exact-game-1"]:
        return {
            "info": {
                "title": "Crimson Desert",
                "steamAppID": "3321460",
                "thumb": "https://example.test/exact.jpg",
            },
            "deals": [
                {
                    "storeID": "27",
                    "dealID": "exact-deal-1",
                    "price": "62.99",
                    "retailPrice": "69.99",
                    "savings": "10.001429",
                }
            ],
        }

    if parsed_url.path.endswith("/games") and query.get("id") == ["related-game-1"]:
        raise AssertionError("Related deluxe-pack gameID should not be queried.")

    if parsed_url.path.endswith("/games") and query.get("id") == ["related-game-2"]:
        raise AssertionError("Related digital-deluxe gameID should not be queried.")

    raise AssertionError(f"Unexpected URL: {url}")


def fake_cheapshark_with_only_related_games(url: str, timeout_seconds: float):
    parsed_url = urlparse(url)
    query = parse_qs(parsed_url.query)

    if parsed_url.path.endswith("/stores"):
        return [
            {
                "storeID": "25",
                "storeName": "Epic Games Store",
            }
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
                "gameID": "related-game-2",
                "steamAppID": "related-steam-2",
                "external": "Crimson Desert Digital Deluxe Edition",
                "thumb": "https://example.test/related2.jpg",
            },
        ]

    raise AssertionError(f"Unexpected URL: {url}")


def test_exact_returned_title_match_accepts_only_normalized_exact_title():
    assert is_exact_returned_title_match(
        requested_title="Crimson Desert",
        returned_title="Crimson Desert",
    ) is True
    assert is_exact_returned_title_match(
        requested_title="Crimson Desert",
        returned_title="crimson desert",
    ) is True
    assert is_exact_returned_title_match(
        requested_title="Crimson Desert",
        returned_title="Crimson Desert Deluxe Pack",
    ) is False
    assert is_exact_returned_title_match(
        requested_title="Crimson Desert",
        returned_title="Crimson Desert Digital Deluxe Edition",
    ) is False


def test_find_exact_game_match_rejects_related_games():
    raw_games = [
        {
            "gameID": "related-game-1",
            "external": "Crimson Desert Deluxe Pack",
        },
        {
            "gameID": "exact-game-1",
            "external": "Crimson Desert",
        },
        {
            "gameID": "related-game-2",
            "external": "Crimson Desert Digital Deluxe Edition",
        },
    ]

    match = find_exact_game_match(
        raw_games=raw_games,
        requested_title="Crimson Desert",
    )

    assert match == {
        "gameID": "exact-game-1",
        "external": "Crimson Desert",
    }


def test_filter_raw_deals_by_exact_title_rejects_related_titles():
    raw_deals = [
        {
            "title": "Crimson Desert Deluxe Pack",
        },
        {
            "title": "Crimson Desert",
        },
        {
            "title": "Crimson Desert Digital Deluxe Edition",
        },
    ]

    filtered_deals = filter_raw_deals_by_exact_title(
        raw_deals=raw_deals,
        requested_title="Crimson Desert",
    )

    assert filtered_deals == [
        {
            "title": "Crimson Desert",
        }
    ]


def test_cheapshark_source_queries_only_exact_gameid_before_currency_conversion():
    source = CheapSharkSource(
        timeout_seconds=8.0,
        http_get_json=fake_cheapshark_with_exact_and_related_games,
        enable_currency_conversion=True,
        ecb_rate_source=FakeEcbRateSource(),
    )

    deals = source.search_deals("Crimson Desert")

    assert len(deals) == 1
    assert deals[0]["title"] == "Crimson Desert"
    assert deals[0]["store"] == "Gamesplanet"
    assert deals[0]["price_usd"] == 62.99
    assert deals[0]["price_eur"] == 56.69
    assert deals[0]["deal_id"] == "exact-deal-1"
    assert deals[0]["game_id"] == "exact-game-1"


def test_cheapshark_source_returns_empty_list_when_only_related_games_exist():
    source = CheapSharkSource(
        timeout_seconds=8.0,
        http_get_json=fake_cheapshark_with_only_related_games,
        enable_currency_conversion=True,
        ecb_rate_source=FakeEcbRateSource(),
    )

    deals = source.search_deals("Crimson Desert")

    assert deals == []


def test_authorized_reseller_falls_back_to_mock_when_cheapshark_only_returns_related_games():
    real_source = CheapSharkSource(
        timeout_seconds=8.0,
        http_get_json=fake_cheapshark_with_only_related_games,
        enable_currency_conversion=True,
        ecb_rate_source=FakeEcbRateSource(),
    )

    result = build_authorized_reseller_search_result(
        game_title="Crimson Desert",
        match_mode="exact",
        real_source=real_source,
        real_source_enabled=True,
        mock_fallback_available=True,
    )

    assert result["source_adapter"] == "mock_authorized_reseller"
    assert result["match_status"] == "resolved"
    assert result["resolved_title"] == "Crimson Desert"
    assert len(result["deals"]) == 2
    assert result["bdi_trace"]["selected_plan"] == "fallback_to_mock_source"
    assert result["bdi_trace"]["beliefs"]["real_source_available"] is True
    assert result["bdi_trace"]["beliefs"]["real_source_returned_deals"] is False
