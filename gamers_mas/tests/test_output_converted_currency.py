from app.agents.output_agent import format_recommended_legitimate_deal


def test_format_recommended_legitimate_deal_mentions_usd_conversion_source_and_date():
    summary = format_recommended_legitimate_deal(
        {
            "store": "Gamesplanet",
            "price_eur": 56.69,
            "price_usd": 62.99,
            "original_price_usd": 62.99,
            "currency_conversion_applied": True,
            "conversion_rate": 0.9,
            "conversion_rate_source": "European Central Bank euro foreign exchange reference rates",
            "conversion_rate_date": "2026-05-08",
            "trust_score": 0.8,
            "source_type": "authorized_reseller",
        }
    )

    assert "Recommended legitimate deal: Gamesplanet - €56.69" in summary
    assert "converted from 62.99 USD" in summary
    assert "1 USD = 0.900000 EUR" in summary
    assert "rate source=European Central Bank euro foreign exchange reference rates" in summary
    assert "rate date=2026-05-08" in summary
    assert "type=authorized_reseller" in summary


def test_format_recommended_legitimate_deal_keeps_normal_eur_output_for_unconverted_deal():
    summary = format_recommended_legitimate_deal(
        {
            "store": "GOG",
            "price_eur": 59.99,
            "trust_score": 1.0,
            "source_type": "official",
        }
    )

    assert summary == (
        "Recommended legitimate deal: GOG - €59.99 | "
        "trust=1.0 | type=official"
    )
