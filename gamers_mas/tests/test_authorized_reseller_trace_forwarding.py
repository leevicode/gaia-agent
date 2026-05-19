from app.agents.output_agent import build_software_bdi_trace_list
from app.agents.software_coordinator_agent import build_software_presentation_payload


def test_software_coordinator_forwards_authorized_reseller_bdi_trace():
    authorized_trace = {
        "agent_name": "AuthorizedResellerAgent",
        "selected_plan": "query_real_source",
    }

    payload = build_software_presentation_payload(
        request_id="req-1",
        recommendation_payload={
            "game_title": "Crimson Desert",
            "best_legitimate_deal": {
                "store": "GOG",
                "price_eur": 59.99,
                "trust_score": 1.0,
                "source_type": "official",
            },
            "gray_market_warning_deal": None,
            "foreign_currency_deals": [],
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
        authorized_reseller_bdi_trace=authorized_trace,
    )

    assert payload["authorized_reseller_bdi_trace"] == authorized_trace


def test_output_agent_builds_software_trace_list_with_authorized_reseller_trace():
    coordinator_trace = {
        "agent_name": "SoftwareCoordinatorAgent",
        "selected_plan": "query_software_sources",
    }
    authorized_trace = {
        "agent_name": "AuthorizedResellerAgent",
        "selected_plan": "query_real_source",
    }
    recommendation_trace = {
        "agent_name": "RecommendationAgent",
        "selected_plan": "select_legitimate_and_warn",
    }

    traces = build_software_bdi_trace_list(
        coordinator_bdi_trace=coordinator_trace,
        authorized_reseller_bdi_trace=authorized_trace,
        recommendation_bdi_trace=recommendation_trace,
    )

    assert traces == [
        coordinator_trace,
        authorized_trace,
        recommendation_trace,
    ]
