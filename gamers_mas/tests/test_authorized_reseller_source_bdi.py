from app.agents.authorized_reseller_agent import (
    build_authorized_reseller_search_result,
    build_authorized_source_bdi_state,
    select_authorized_source_plan,
)


class FakeFailingRealSource:
    source_name = "fake_failing_real_source"

    def search_deals(self, title: str, **filters):
        raise RuntimeError("fake source failure")


def test_authorized_reseller_agent_uses_mock_source_when_real_source_is_disabled():
    result = build_authorized_reseller_search_result(
        game_title="Crimson Desert",
        match_mode="exact",
        real_source_enabled=False,
    )

    assert result["source_adapter"] == "mock_authorized_reseller"
    assert result["match_status"] == "resolved"
    assert result["resolved_title"] == "Crimson Desert"
    assert len(result["deals"]) == 2
    assert result["bdi_trace"]["selected_plan"] == "use_mock_source"
    assert result["bdi_trace"]["beliefs"]["real_source_enabled"] is False


def test_authorized_reseller_agent_falls_back_to_mock_when_real_source_fails():
    result = build_authorized_reseller_search_result(
        game_title="Crimson Desert",
        match_mode="exact",
        real_source=FakeFailingRealSource(),
        real_source_enabled=True,
        mock_fallback_available=True,
    )

    assert result["source_adapter"] == "mock_authorized_reseller"
    assert result["match_status"] == "resolved"
    assert len(result["deals"]) == 2
    assert result["real_source_error"] == "fake source failure"
    assert result["bdi_trace"]["selected_plan"] == "fallback_to_mock_source"
    assert result["bdi_trace"]["beliefs"]["real_source_enabled"] is True
    assert result["bdi_trace"]["beliefs"]["real_source_available"] is False
    assert result["bdi_trace"]["beliefs"]["mock_fallback_available"] is True


def test_authorized_reseller_agent_selects_real_source_plan_when_enabled_available_and_useful():
    state = build_authorized_source_bdi_state(
        agent_name="AuthorizedResellerAgent",
        game_title="Crimson Desert",
        match_mode="exact",
        real_source_enabled=True,
        real_source_available=True,
        real_source_returned_deals=True,
        mock_fallback_available=True,
    )

    decision = select_authorized_source_plan(state)

    assert decision.selected_plan == "query_real_source"
    assert decision.to_dict()["beliefs"]["real_source_enabled"] is True
    assert decision.to_dict()["beliefs"]["real_source_available"] is True
    assert decision.to_dict()["beliefs"]["real_source_returned_deals"] is True


def test_authorized_reseller_bdi_trace_contains_goals_and_considered_plans():
    result = build_authorized_reseller_search_result(
        game_title="Crimson Desert",
        match_mode="exact",
        real_source_enabled=False,
    )

    trace = result["bdi_trace"]

    assert trace["agent_name"] == "AuthorizedResellerAgent"
    assert "find_authorized_reseller_deals" in trace["goals"]
    assert "preserve_demo_stability" in trace["goals"]
    assert "prepare_for_real_source_integration" in trace["goals"]
    assert "query_real_source" in trace["considered_plans"]
    assert "fallback_to_mock_source" in trace["considered_plans"]
    assert "use_mock_source" in trace["considered_plans"]
    assert "return_no_results" in trace["considered_plans"]


def test_authorized_reseller_agent_keeps_exact_mode_no_fallback_behavior():
    result = build_authorized_reseller_search_result(
        game_title="crimson",
        match_mode="exact",
        real_source_enabled=False,
    )

    assert result["source_adapter"] == "mock_authorized_reseller"
    assert result["match_status"] == "not_found"
    assert result["resolved_title"] is None
    assert result["deals"] == []
    assert result["bdi_trace"]["selected_plan"] == "use_mock_source"