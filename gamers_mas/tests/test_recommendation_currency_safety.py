from app.agents.recommendation_agent import build_recommendation_result


def test_recommendation_agent_does_not_compare_usd_deals_as_eur():
    deals = [
        {
            "store": "CheapShark Store",
            "title": "Crimson Desert",
            "price_eur": None,
            "price_usd": 39.99,
            "trust_score": 0.8,
            "source_type": "authorized_reseller",
            "currency": "USD",
        },
        {
            "store": "Steam",
            "title": "Crimson Desert",
            "price_eur": 69.99,
            "trust_score": 1.0,
            "source_type": "official",
            "currency": "EUR",
        },
    ]

    result = build_recommendation_result(
        game_title="Crimson Desert",
        deals=deals,
    )

    assert result["best_legitimate_deal"]["store"] == "Steam"
    assert result["foreign_currency_deals"][0]["store"] == "CheapShark Store"
    assert result["bdi_trace"]["beliefs"]["foreign_currency_deal_count"] == 1
    assert result["bdi_trace"]["beliefs"]["do_not_compare_usd_as_eur"] is True


def test_recommendation_agent_reports_no_legitimate_deal_when_only_usd_deals_exist():
    deals = [
        {
            "store": "CheapShark Store",
            "title": "Crimson Desert",
            "price_eur": None,
            "price_usd": 39.99,
            "trust_score": 0.8,
            "source_type": "authorized_reseller",
            "currency": "USD",
        }
    ]

    result = build_recommendation_result(
        game_title="Crimson Desert",
        deals=deals,
    )

    assert result["best_legitimate_deal"] is None
    assert result["foreign_currency_deals"][0]["store"] == "CheapShark Store"
    assert result["bdi_trace"]["selected_plan"] == "report_no_legitimate_deal"
    assert result["bdi_trace"]["beliefs"]["foreign_currency_deal_available"] is True