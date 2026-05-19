from app.agents.software_coordinator_agent import build_software_resolution_result


def test_software_coordinator_bdi_handles_ambiguous_title_before_querying_sources():
    result = build_software_resolution_result(
        game_title="crimson",
        match_mode="fuzzy",
    )

    assert result["match_status"] == "ambiguous"
    assert result["resolved_game_title"] is None
    assert set(result["suggestions"]) == {
        "Crimson Desert",
        "Crimson Desert Deluxe Edition",
    }
    assert result["bdi_trace"]["selected_plan"] == "handle_ambiguity"
    assert result["bdi_trace"]["beliefs"]["title_is_ambiguous"] is True
    assert result["bdi_trace"]["beliefs"]["exact_match_required_before_source_query"] is True


def test_software_coordinator_bdi_queries_sources_after_exact_resolution():
    result = build_software_resolution_result(
        game_title="Crimson Desert",
        match_mode="exact",
    )

    assert result["match_status"] == "resolved"
    assert result["resolved_game_title"] == "Crimson Desert"
    assert result["suggestions"] == []
    assert result["bdi_trace"]["selected_plan"] == "query_software_sources"
    assert result["bdi_trace"]["beliefs"]["title_is_resolved"] is True


def test_software_coordinator_bdi_does_not_fallback_in_exact_mode():
    result = build_software_resolution_result(
        game_title="crimson",
        match_mode="exact",
    )

    assert result["match_status"] == "not_found"
    assert result["resolved_game_title"] is None
    assert result["suggestions"] == []
    assert result["bdi_trace"]["selected_plan"] == "handle_not_found"
    assert result["bdi_trace"]["beliefs"]["title_not_found"] is True


def test_software_coordinator_bdi_adds_matching_notice_for_fuzzy_unique_match():
    result = build_software_resolution_result(
        game_title="deluxe",
        match_mode="fuzzy",
    )

    assert result["match_status"] == "resolved"
    assert result["resolved_game_title"] == "Crimson Desert Deluxe Edition"
    assert result["search_notices"] == [
        "Matched 'deluxe' to 'Crimson Desert Deluxe Edition'."
    ]
    assert result["bdi_trace"]["selected_plan"] == "query_software_sources"


def test_software_coordinator_bdi_trace_contains_goals_and_considered_plans():
    result = build_software_resolution_result(
        game_title="Crimson Desert",
        match_mode="exact",
    )

    trace = result["bdi_trace"]

    assert trace["agent_name"] == "SoftwareCoordinatorAgent"
    assert "resolve_software_title" in trace["goals"]
    assert "avoid_edition_mixups" in trace["goals"]
    assert "query_sources_only_after_resolution" in trace["goals"]
    assert "handle_ambiguity" in trace["considered_plans"]
    assert "query_software_sources" in trace["considered_plans"]
    assert "handle_not_found" in trace["considered_plans"]