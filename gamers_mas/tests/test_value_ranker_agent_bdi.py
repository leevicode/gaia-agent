from app.agents.value_ranker_agent import build_ranking_result


def test_value_ranker_agent_ranks_available_deals_by_value():
    deals = [
        {
            "store": "Expensive Trusted Store",
            "title": "PlayStation 5 Digital Edition",
            "price_eur": 450.00,
            "shipping_eur": 0.0,
            "trust_score": 1.0,
            "condition": "new",
            "source_type": "official",
            "distance_km": 999999.0,
        },
        {
            "store": "Nearby Marketplace Seller",
            "title": "PlayStation 5 Digital Edition",
            "price_eur": 330.00,
            "shipping_eur": 0.0,
            "trust_score": 0.8,
            "condition": "used - very good",
            "source_type": "marketplace",
            "distance_km": 6.0,
        },
        {
            "store": "Far Marketplace Seller",
            "title": "PlayStation 5 Digital Edition",
            "price_eur": 345.00,
            "shipping_eur": 0.0,
            "trust_score": 0.74,
            "condition": "used - good",
            "source_type": "marketplace",
            "distance_km": 10.0,
        },
    ]

    result = build_ranking_result(
        product_name="PlayStation 5 Digital Edition",
        deals=deals,
    )

    ranked_deals = result["ranked_deals"]

    assert ranked_deals[0]["store"] == "Nearby Marketplace Seller"
    assert ranked_deals[1]["store"] == "Far Marketplace Seller"
    assert ranked_deals[2]["store"] == "Expensive Trusted Store"
    assert result["bdi_trace"]["selected_plan"] == "rank_available_deals"


def test_value_ranker_agent_reports_no_deals_when_list_is_empty():
    result = build_ranking_result(
        product_name="PlayStation 5 Digital Edition",
        deals=[],
    )

    assert result["ranked_deals"] == []
    assert result["bdi_trace"]["selected_plan"] == "report_no_deals"
    assert result["bdi_trace"]["beliefs"]["deals_available"] is False
    assert result["bdi_trace"]["beliefs"]["total_deal_count"] == 0


def test_value_ranker_agent_bdi_beliefs_count_risky_conditions():
    deals = [
        {
            "store": "Facebook Marketplace",
            "title": "PlayStation 5 Disc Edition",
            "price_eur": 380.00,
            "shipping_eur": 0.0,
            "trust_score": 0.8,
            "condition": "used - like new",
            "source_type": "marketplace",
            "distance_km": 5.0,
        },
        {
            "store": "GameStop",
            "title": "PlayStation 5 Disc Edition",
            "price_eur": 499.99,
            "shipping_eur": 14.99,
            "trust_score": 1.0,
            "condition": "refurbished",
            "source_type": "official",
            "distance_km": 999999.0,
        },
        {
            "store": "OfferUp",
            "title": "PlayStation 5 Disc Edition",
            "price_eur": 395.00,
            "shipping_eur": 0.0,
            "trust_score": 0.75,
            "condition": "used - very good",
            "source_type": "marketplace",
            "distance_km": 12.0,
        },
    ]

    result = build_ranking_result(
        product_name="PlayStation 5 Disc Edition",
        deals=deals,
    )

    beliefs = result["bdi_trace"]["beliefs"]

    assert beliefs["total_deal_count"] == 3
    assert beliefs["deals_available"] is True
    assert beliefs["used_or_refurbished_deal_count"] == 3
    assert beliefs["lower_trust_deal_count"] == 1
    assert beliefs["ranking_uses_price_shipping_trust_and_distance"] is True


def test_value_ranker_agent_bdi_trace_contains_goals_and_considered_plans():
    deals = [
        {
            "store": "Facebook Marketplace",
            "title": "PlayStation 5 Disc Edition",
            "price_eur": 380.00,
            "shipping_eur": 0.0,
            "trust_score": 0.8,
            "condition": "used - like new",
            "source_type": "marketplace",
            "distance_km": 5.0,
        }
    ]

    result = build_ranking_result(
        product_name="PlayStation 5 Disc Edition",
        deals=deals,
    )

    trace = result["bdi_trace"]

    assert trace["agent_name"] == "ValueRankerAgent"
    assert "rank_local_console_deals_by_value" in trace["goals"]
    assert "avoid_blindly_selecting_cheapest_offer" in trace["goals"]
    assert "support_warning_generation" in trace["goals"]
    assert "rank_available_deals" in trace["considered_plans"]
    assert "report_no_deals" in trace["considered_plans"]