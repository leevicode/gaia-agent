from app.agents.output_agent import (
    build_foreign_currency_summary,
    format_foreign_currency_deal,
)
from app.agents.software_coordinator_agent import build_software_presentation_payload


def test_software_coordinator_passes_foreign_currency_deals_to_output_payload():
    foreign_currency_deals = [
        {
            "store": "CheapShark Store",
            "title": "Crimson Desert",
            "price_eur": None,
            "price_usd": 39.99,
            "currency": "USD",
            "source_adapter": "cheapshark",
        }
    ]

    payload = build_software_presentation_payload(
        request_id="req-1",
        recommendation_payload={
            "game_title": "Crimson Desert",
            "best_legitimate_deal": {
                "store": "Steam",
                "price_eur": 69.99,
                "trust_score": 1.0,
                "source_type": "official",
            },
            "gray_market_warning_deal": None,
            "foreign_currency_deals": foreign_currency_deals,
            "bdi_trace": {
                "agent_name": "RecommendationAgent",
                "selected_plan": "select_legitimate_only",
            },
        },
        search_notices=[],
        coordinator_bdi_trace={
            "agent_name": "SoftwareCoordinatorAgent",
            "selected_plan": "query_software_sources",
        },
    )

    assert payload["foreign_currency_deals"] == foreign_currency_deals
    assert payload["recommendation_bdi_trace"]["agent_name"] == "RecommendationAgent"


def test_format_foreign_currency_deal_makes_currency_safety_clear():
    summary = format_foreign_currency_deal(
        {
            "store": "CheapShark Store",
            "price_usd": 39.99,
            "currency": "USD",
            "source_adapter": "cheapshark",
        }
    )

    assert "CheapShark Store" in summary
    assert "39.99 USD" in summary
    assert "source=cheapshark" in summary
    assert "not compared with EUR results" in summary


def test_build_foreign_currency_summary_formats_multiple_deals():
    summaries = build_foreign_currency_summary(
        [
            {
                "store": "Store One",
                "price_usd": 10.0,
                "currency": "USD",
                "source_adapter": "cheapshark",
            },
            {
                "store": "Store Two",
                "price_usd": 20.5,
                "currency": "USD",
                "source_adapter": "cheapshark",
            },
        ]
    )

    assert summaries == [
        "Store One - 10.00 USD | source=cheapshark | not compared with EUR results",
        "Store Two - 20.50 USD | source=cheapshark | not compared with EUR results",
    ]