import pytest

from app.bdi import BDIState, Goal, Plan


def test_bdi_state_stores_beliefs_goals_and_plans():
    state = BDIState(agent_name="RecommendationAgent")

    state.set_belief("legitimate_deal_count", 2)
    state.set_belief("gray_market_deal_count", 1)

    state.add_goal(
        Goal(
            name="recommend_best_legitimate_deal",
            priority=10,
            description="Prefer legitimate sources over risky gray-market sources.",
        )
    )

    state.add_plan(
        Plan(
            name="select_legitimate_and_warn",
            trigger="deals_available",
            priority=10,
            description="Select a legitimate deal and warn about gray-market risk.",
        )
    )

    assert state.get_belief("legitimate_deal_count") == 2
    assert state.get_belief("gray_market_deal_count") == 1
    assert state.goal_names() == ["recommend_best_legitimate_deal"]
    assert state.plan_names() == ["select_legitimate_and_warn"]


def test_bdi_decision_creates_traceable_output():
    state = BDIState(agent_name="RecommendationAgent")

    state.set_belief("legitimate_deal_count", 2)
    state.set_belief("gray_market_is_risky", True)

    state.add_goal(Goal(name="recommend_best_legitimate_deal", priority=10))
    state.add_goal(Goal(name="warn_about_gray_market", priority=8))

    state.add_plan(
        Plan(
            name="select_legitimate_and_warn",
            trigger="deals_available",
            priority=10,
        )
    )

    decision = state.decide(
        selected_plan_name="select_legitimate_and_warn",
        reason="A legitimate deal exists, so gray-market offers are shown only as warnings.",
    )

    trace = decision.to_dict()

    assert trace["agent_name"] == "RecommendationAgent"
    assert trace["selected_plan"] == "select_legitimate_and_warn"
    assert trace["beliefs"]["legitimate_deal_count"] == 2
    assert trace["beliefs"]["gray_market_is_risky"] is True
    assert trace["goals"] == [
        "recommend_best_legitimate_deal",
        "warn_about_gray_market",
    ]
    assert trace["considered_plans"] == ["select_legitimate_and_warn"]


def test_bdi_goals_are_sorted_by_priority_then_name():
    state = BDIState(agent_name="ValueRankerAgent")

    state.add_goal(Goal(name="avoid_risky_offer", priority=8))
    state.add_goal(Goal(name="rank_by_value", priority=10))
    state.add_goal(Goal(name="explain_warnings", priority=8))

    assert state.goal_names() == [
        "rank_by_value",
        "avoid_risky_offer",
        "explain_warnings",
    ]


def test_bdi_plans_are_sorted_by_priority_then_name():
    state = BDIState(agent_name="LocalCoordinatorAgent")

    state.add_plan(Plan(name="query_sources", trigger="resolved", priority=10))
    state.add_plan(Plan(name="handle_not_found", trigger="not_found", priority=8))
    state.add_plan(Plan(name="handle_ambiguity", trigger="ambiguous", priority=9))

    assert state.plan_names() == [
        "query_sources",
        "handle_ambiguity",
        "handle_not_found",
    ]


def test_select_highest_priority_plan_for_trigger():
    state = BDIState(agent_name="SoftwareCoordinatorAgent")

    state.add_goal(Goal(name="resolve_title", priority=10))

    state.add_plan(
        Plan(
            name="query_sources",
            trigger="resolved",
            priority=10,
        )
    )
    state.add_plan(
        Plan(
            name="query_sources_backup",
            trigger="resolved",
            priority=5,
        )
    )

    decision = state.select_highest_priority_plan(
        trigger="resolved",
        reason="The title was resolved exactly, so source agents can be queried.",
    )

    assert decision.selected_plan == "query_sources"
    assert decision.reason == "The title was resolved exactly, so source agents can be queried."


def test_decide_rejects_unknown_plan():
    state = BDIState(agent_name="RecommendationAgent")

    state.add_plan(
        Plan(
            name="select_legitimate_and_warn",
            trigger="deals_available",
            priority=10,
        )
    )

    with pytest.raises(ValueError, match="Unknown plan"):
        state.decide(
            selected_plan_name="non_existing_plan",
            reason="This should fail.",
        )


def test_select_highest_priority_plan_rejects_unknown_trigger():
    state = BDIState(agent_name="SoftwareCoordinatorAgent")

    state.add_plan(
        Plan(
            name="query_sources",
            trigger="resolved",
            priority=10,
        )
    )

    with pytest.raises(ValueError, match="No plan found"):
        state.select_highest_priority_plan(
            trigger="ambiguous",
            reason="This should fail.",
        )