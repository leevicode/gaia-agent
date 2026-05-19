from urllib.parse import parse_qs, urlparse

from app.currency.converter import build_configured_usd_to_eur_rate
from app.sources.cheapshark_source import CheapSharkSource


class FakeEcbRateSource:
    def get_usd_to_eur_rate(self):
        return build_configured_usd_to_eur_rate(
            usd_to_eur_rate="0.90",
            source="fake_ecb_rate",
            rate_date="2026-05-08",
        )


def fake_cheapshark_http_get_json(url: str, timeout_seconds: float):
    parsed_url = urlparse(url)
    query = parse_qs(parsed_url.query)

    if parsed_url.path.endswith("/stores"):
        return [
            {
                "storeID": "27",
                "storeName": "Gamesplanet",
            }
        ]

    if parsed_url.path.endswith("/games") and "title" in query:
        return [
            {
                "gameID": "game-456",
                "steamAppID": "3321460",
                "external": "Crimson Desert",
                "thumb": "https://example.test/thumb.jpg",
            }
        ]

    if parsed_url.path.endswith("/games") and query.get("id") == ["game-456"]:
        return {
            "info": {
                "title": "Crimson Desert",
                "steamAppID": "3321460",
                "thumb": "https://example.test/thumb.jpg",
            },
            "deals": [
                {
                    "storeID": "27",
                    "dealID": "deal-123",
                    "price": "62.99",
                    "retailPrice": "69.99",
                    "savings": "10.001429",
                }
            ],
        }

    raise AssertionError(f"Unexpected URL: {url}")


def test_cheapshark_source_converts_usd_to_eur_when_conversion_is_enabled():
    source = CheapSharkSource(
        timeout_seconds=8.0,
        http_get_json=fake_cheapshark_http_get_json,
        enable_currency_conversion=True,
        ecb_rate_source=FakeEcbRateSource(),
    )

    deals = source.search_deals("Crimson Desert")

    assert len(deals) == 1

    deal = deals[0]

    assert deal["store"] == "Gamesplanet"
    assert deal["price_usd"] == 62.99
    assert deal["price_eur"] == 56.69
    assert deal["original_price_usd"] == 62.99
    assert deal["original_currency"] == "USD"
    assert deal["converted_currency"] == "EUR"
    assert deal["currency_conversion_applied"] is True
    assert deal["conversion_rate"] == 0.9
    assert deal["conversion_rate_source"] == "fake_ecb_rate"
    assert deal["conversion_rate_date"] == "2026-05-08"
    assert "Converted from 62.99 USD" in deal["conversion_note"]


def test_cheapshark_source_keeps_usd_separate_when_conversion_is_disabled():
    source = CheapSharkSource(
        timeout_seconds=8.0,
        http_get_json=fake_cheapshark_http_get_json,
        enable_currency_conversion=False,
    )

    deals = source.search_deals("Crimson Desert")

    assert len(deals) == 1

    deal = deals[0]

    assert deal["price_usd"] == 62.99
    assert deal["price_eur"] is None
    assert deal["currency"] == "USD"
    assert deal["currency_conversion_applied"] is False
    assert "No EUR conversion" in deal["currency_note"]


def test_cheapshark_source_uses_configured_fallback_rate_when_ecb_fails():
    class FakeFailingEcbRateSource:
        def get_usd_to_eur_rate(self):
            raise RuntimeError("fake ECB failure")

    source = CheapSharkSource(
        timeout_seconds=8.0,
        http_get_json=fake_cheapshark_http_get_json,
        enable_currency_conversion=True,
        allow_currency_fallback_rate=True,
        fallback_usd_to_eur_rate=0.92,
        fallback_usd_to_eur_rate_source="manual_fallback_rate",
        fallback_usd_to_eur_rate_date="2026-05-08",
        ecb_rate_source=FakeFailingEcbRateSource(),
    )

    deals = source.search_deals("Crimson Desert")

    assert deals[0]["price_eur"] == 57.95
    assert deals[0]["conversion_rate"] == 0.92
    assert deals[0]["conversion_rate_source"] == "manual_fallback_rate"
