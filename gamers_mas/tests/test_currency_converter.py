import pytest

from app.currency.converter import (
    apply_usd_to_eur_conversion_to_deal,
    apply_usd_to_eur_conversion_to_deals,
    build_configured_usd_to_eur_rate,
    convert_usd_to_eur_amount,
    resolve_usd_to_eur_rate,
)


class FakeSuccessfulEcbRateSource:
    def get_usd_to_eur_rate(self):
        return build_configured_usd_to_eur_rate(
            usd_to_eur_rate="0.91",
            source="fake_ecb_rate",
            rate_date="2026-05-08",
        )


class FakeFailingEcbRateSource:
    def get_usd_to_eur_rate(self):
        raise RuntimeError("fake ECB failure")


def test_build_configured_usd_to_eur_rate_creates_rate_from_configuration():
    rate = build_configured_usd_to_eur_rate(
        usd_to_eur_rate="0.92",
        source="manual_demo_rate",
        rate_date="2026-05-08",
    )

    assert rate.from_currency == "USD"
    assert rate.to_currency == "EUR"
    assert rate.rate == 0.92
    assert rate.provider == "configured_fallback"
    assert rate.source == "manual_demo_rate"
    assert rate.rate_date == "2026-05-08"


def test_convert_usd_to_eur_amount_uses_rate_and_rounds_to_two_decimals():
    rate = build_configured_usd_to_eur_rate(
        usd_to_eur_rate="0.92",
        source="manual_demo_rate",
        rate_date="2026-05-08",
    )

    result = convert_usd_to_eur_amount(
        price_usd=62.99,
        rate=rate,
    )

    assert result.original_amount == 62.99
    assert result.original_currency == "USD"
    assert result.converted_amount == 57.95
    assert result.converted_currency == "EUR"
    assert result.conversion_rate == 0.92
    assert result.conversion_rate_source == "manual_demo_rate"
    assert result.conversion_rate_date == "2026-05-08"
    assert "Converted from 62.99 USD" in result.conversion_note


def test_apply_usd_to_eur_conversion_to_deal_preserves_original_usd_details():
    rate = build_configured_usd_to_eur_rate(
        usd_to_eur_rate="0.92",
        source="manual_demo_rate",
        rate_date="2026-05-08",
    )
    deal = {
        "store": "Gamesplanet",
        "title": "Crimson Desert",
        "price_eur": None,
        "price_usd": 62.99,
        "currency": "USD",
        "source_adapter": "cheapshark",
        "source_type": "authorized_reseller",
        "trust_score": 0.8,
    }

    converted_deal = apply_usd_to_eur_conversion_to_deal(
        deal=deal,
        rate=rate,
    )

    assert deal["price_eur"] is None
    assert converted_deal["price_eur"] == 57.95
    assert converted_deal["original_price_usd"] == 62.99
    assert converted_deal["original_currency"] == "USD"
    assert converted_deal["converted_currency"] == "EUR"
    assert converted_deal["currency_conversion_applied"] is True
    assert converted_deal["conversion_rate"] == 0.92
    assert converted_deal["conversion_rate_source"] == "manual_demo_rate"
    assert converted_deal["conversion_rate_date"] == "2026-05-08"
    assert "Converted from 62.99 USD" in converted_deal["conversion_note"]


def test_apply_usd_to_eur_conversion_to_deal_marks_non_usd_deal_without_conversion():
    rate = build_configured_usd_to_eur_rate(
        usd_to_eur_rate="0.92",
        source="manual_demo_rate",
        rate_date="2026-05-08",
    )
    deal = {
        "store": "GOG",
        "price_eur": 59.99,
        "currency": "EUR",
    }

    converted_deal = apply_usd_to_eur_conversion_to_deal(
        deal=deal,
        rate=rate,
    )

    assert converted_deal["price_eur"] == 59.99
    assert converted_deal["currency_conversion_applied"] is False


def test_apply_usd_to_eur_conversion_to_deals_converts_list():
    rate = build_configured_usd_to_eur_rate(
        usd_to_eur_rate="0.92",
        source="manual_demo_rate",
        rate_date="2026-05-08",
    )
    deals = [
        {
            "store": "Store One",
            "price_eur": None,
            "price_usd": 10.0,
            "currency": "USD",
        },
        {
            "store": "Store Two",
            "price_eur": None,
            "price_usd": 20.0,
            "currency": "USD",
        },
    ]

    converted_deals = apply_usd_to_eur_conversion_to_deals(
        deals=deals,
        rate=rate,
    )

    assert converted_deals[0]["price_eur"] == 9.2
    assert converted_deals[1]["price_eur"] == 18.4


def test_resolve_usd_to_eur_rate_uses_ecb_when_available():
    rate = resolve_usd_to_eur_rate(
        rate_provider="ecb",
        timeout_seconds=8.0,
        allow_fallback_rate=True,
        fallback_usd_to_eur_rate=0.92,
        fallback_rate_source="manual_fallback_rate",
        fallback_rate_date="2026-05-08",
        ecb_rate_source=FakeSuccessfulEcbRateSource(),
    )

    assert rate.rate == 0.91
    assert rate.source == "fake_ecb_rate"


def test_resolve_usd_to_eur_rate_uses_fallback_when_ecb_fails():
    rate = resolve_usd_to_eur_rate(
        rate_provider="ecb",
        timeout_seconds=8.0,
        allow_fallback_rate=True,
        fallback_usd_to_eur_rate=0.92,
        fallback_rate_source="manual_fallback_rate",
        fallback_rate_date="2026-05-08",
        ecb_rate_source=FakeFailingEcbRateSource(),
    )

    assert rate.rate == 0.92
    assert rate.source == "manual_fallback_rate"


def test_resolve_usd_to_eur_rate_rejects_invalid_provider():
    with pytest.raises(ValueError, match="Unsupported currency rate provider"):
        resolve_usd_to_eur_rate(
            rate_provider="unknown",
            timeout_seconds=8.0,
            allow_fallback_rate=True,
            fallback_usd_to_eur_rate=0.92,
            fallback_rate_source="manual_fallback_rate",
            fallback_rate_date="2026-05-08",
        )
