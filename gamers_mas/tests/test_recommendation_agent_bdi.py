from app.agents.recommendation_agent import build_recommendation_result


def test_recommendation_agent_selects_legitimate_deal_and_warns_about_gray_market():
    deals = [
        {
            "store": "Fanatical",
            "title": "Crimson Desert",
            "price_eur": 52.99,
            "trust_score": 0.8,
            "source_type": "authorized_reseller",
        },
        {
            "store": "Kinguin",
            "title": "Crimson Desert",
            "price_eur": 39.99,
            "trust_score": 0.3,
            "source_type": "gray_market",
        },
    ]

    result = build_recommendation_result(
        game_title="Crimson Desert",
        deals=deals,
    )

    assert result["best_legitimate_deal"]["store"] == "Fanatical"
    assert result["gray_market_warning_deal"]["store"] == "Kinguin"
    assert result["bdi_trace"]["selected_plan"] == "select_legitimate_and_warn"
    assert result["bdi_trace"]["beliefs"]["legitimate_deal_count"] == 1
    assert result["bdi_trace"]["beliefs"]["gray_market_deal_count"] == 1


def test_recommendation_agent_selects_legitimate_only_plan_when_no_gray_market_exists():
    deals = [
        {
            "store": "Steam",
            "title": "Crimson Desert",
            "price_eur": 69.99,
            "trust_score": 1.0,
            "source_type": "official",
        },
        {
            "store": "Fanatical",
            "title": "Crimson Desert",
            "price_eur": 52.99,
            "trust_score": 0.8,
            "source_type": "authorized_reseller",
        },
    ]

    result = build_recommendation_result(
        game_title="Crimson Desert",
        deals=deals,
    )

    assert result["best_legitimate_deal"]["store"] == "Fanatical"
    assert result["gray_market_warning_deal"] is None
    assert result["bdi_trace"]["selected_plan"] == "select_legitimate_only"


def test_recommendation_agent_reports_no_legitimate_deal_when_only_gray_market_exists():
    deals = [
        {
            "store": "Kinguin",
            "title": "Crimson Desert",
            "price_eur": 39.99,
            "trust_score": 0.3,
            "source_type": "gray_market",
        },
    ]

    result = build_recommendation_result(
        game_title="Crimson Desert",
        deals=deals,
    )

    assert result["best_legitimate_deal"] is None
    assert result["gray_market_warning_deal"]["store"] == "Kinguin"
    assert result["bdi_trace"]["selected_plan"] == "report_no_legitimate_deal"
    assert result["bdi_trace"]["beliefs"]["legitimate_deal_available"] is False
    assert result["bdi_trace"]["beliefs"]["gray_market_available"] is True


def test_recommendation_agent_bdi_trace_contains_goals_and_considered_plans():
    deals = [
        {
            "store": "Fanatical",
            "title": "Crimson Desert",
            "price_eur": 52.99,
            "trust_score": 0.8,
            "source_type": "authorized_reseller",
        },
        {
            "store": "Kinguin",
            "title": "Crimson Desert",
            "price_eur": 39.99,
            "trust_score": 0.3,
            "source_type": "gray_market",
        },
    ]

    result = build_recommendation_result(
        game_title="Crimson Desert",
        deals=deals,
    )

    trace = result["bdi_trace"]

    assert trace["agent_name"] == "RecommendationAgent"
    assert "recommend_best_legitimate_deal" in trace["goals"]
    assert "avoid_recommending_gray_market_as_main_choice" in trace["goals"]
    assert "warn_about_gray_market" in trace["goals"]
    assert "select_legitimate_and_warn" in trace["considered_plans"]
    assert "select_legitimate_only" in trace["considered_plans"]
    assert "report_no_legitimate_deal" in trace["considered_plans"]