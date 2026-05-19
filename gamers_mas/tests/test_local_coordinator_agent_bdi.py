from app.agents.local_coordinator_agent import build_local_resolution_result


def test_local_coordinator_bdi_handles_ambiguous_product_before_querying_sources():
    result = build_local_resolution_result(
        product_name="playstation 5",
        max_price=500.0,
        radius_km=15.0,
        match_mode="fuzzy",
    )

    assert result["match_status"] == "ambiguous"
    assert result["resolved_product_name"] is None
    assert set(result["suggestions"]) == {
        "PlayStation 5 Disc Edition",
        "PlayStation 5 Digital Edition",
    }
    assert result["bdi_trace"]["selected_plan"] == "handle_ambiguity"
    assert result["bdi_trace"]["beliefs"]["product_is_ambiguous"] is True
    assert result["bdi_trace"]["beliefs"]["exact_match_required_before_source_query"] is True


def test_local_coordinator_bdi_queries_sources_after_exact_resolution():
    result = build_local_resolution_result(
        product_name="PlayStation 5 Digital Edition",
        max_price=500.0,
        radius_km=15.0,
        match_mode="exact",
    )

    assert result["match_status"] == "resolved"
    assert result["resolved_product_name"] == "PlayStation 5 Digital Edition"
    assert result["suggestions"] == []
    assert result["bdi_trace"]["selected_plan"] == "query_console_sources"
    assert result["bdi_trace"]["beliefs"]["product_is_resolved"] is True
    assert result["bdi_trace"]["beliefs"]["price_constraint_present"] is True
    assert result["bdi_trace"]["beliefs"]["radius_constraint_present"] is True


def test_local_coordinator_bdi_does_not_fallback_in_exact_mode():
    result = build_local_resolution_result(
        product_name="playstation 5",
        max_price=500.0,
        radius_km=15.0,
        match_mode="exact",
    )

    assert result["match_status"] == "not_found"
    assert result["resolved_product_name"] is None
    assert result["suggestions"] == []
    assert result["bdi_trace"]["selected_plan"] == "handle_not_found"
    assert result["bdi_trace"]["beliefs"]["product_not_found"] is True


def test_local_coordinator_bdi_adds_matching_notice_for_fuzzy_unique_match():
    result = build_local_resolution_result(
        product_name="digital",
        max_price=500.0,
        radius_km=15.0,
        match_mode="fuzzy",
    )

    assert result["match_status"] == "resolved"
    assert result["resolved_product_name"] == "PlayStation 5 Digital Edition"
    assert result["search_notices"] == [
        "Matched 'digital' to 'PlayStation 5 Digital Edition'."
    ]
    assert result["bdi_trace"]["selected_plan"] == "query_console_sources"


def test_local_coordinator_bdi_trace_contains_goals_and_considered_plans():
    result = build_local_resolution_result(
        product_name="PlayStation 5 Digital Edition",
        max_price=500.0,
        radius_km=15.0,
        match_mode="exact",
    )

    trace = result["bdi_trace"]

    assert trace["agent_name"] == "LocalCoordinatorAgent"
    assert "resolve_console_product" in trace["goals"]
    assert "avoid_console_edition_mixups" in trace["goals"]
    assert "respect_user_price_and_radius_constraints" in trace["goals"]
    assert "query_sources_only_after_resolution" in trace["goals"]
    assert "handle_ambiguity" in trace["considered_plans"]
    assert "query_console_sources" in trace["considered_plans"]
    assert "handle_not_found" in trace["considered_plans"]