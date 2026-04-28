import launcher


def test_resolve_ambiguity_updates_software_request_to_exact(monkeypatch):
    request_data = {
        "request_id": "req-1",
        "scenario": "software_deal",
        "match_mode": "fuzzy",
        "game_title": "crimson",
    }
    response_data = {
        "status": "ambiguous",
        "request_id": "req-1",
        "scenario": "software_deal",
        "query": "crimson",
        "suggestions": [
            "Crimson Desert",
            "Crimson Desert Deluxe Edition",
        ],
    }

    monkeypatch.setattr(
        launcher,
        "ask_choice_from_suggestions",
        lambda suggestions: "Crimson Desert Deluxe Edition",
    )
    monkeypatch.setattr(
        launcher,
        "new_request_id",
        lambda: "req-2",
    )

    updated_request = launcher.resolve_ambiguity(request_data, response_data)

    assert updated_request["scenario"] == "software_deal"
    assert updated_request["match_mode"] == "exact"
    assert updated_request["game_title"] == "Crimson Desert Deluxe Edition"
    assert updated_request["request_id"] == "req-2"


def test_resolve_ambiguity_updates_console_request_to_exact(monkeypatch):
    request_data = {
        "request_id": "req-10",
        "scenario": "local_console_search",
        "match_mode": "fuzzy",
        "product_name": "playstation 5",
        "max_price": 500.0,
        "radius_km": 15.0,
    }
    response_data = {
        "status": "ambiguous",
        "request_id": "req-10",
        "scenario": "local_console_search",
        "query": "playstation 5",
        "suggestions": [
            "PlayStation 5 Disc Edition",
            "PlayStation 5 Digital Edition",
        ],
    }

    monkeypatch.setattr(
        launcher,
        "ask_choice_from_suggestions",
        lambda suggestions: "PlayStation 5 Digital Edition",
    )
    monkeypatch.setattr(
        launcher,
        "new_request_id",
        lambda: "req-11",
    )

    updated_request = launcher.resolve_ambiguity(request_data, response_data)

    assert updated_request["scenario"] == "local_console_search"
    assert updated_request["match_mode"] == "exact"
    assert updated_request["product_name"] == "PlayStation 5 Digital Edition"
    assert updated_request["max_price"] == 500.0
    assert updated_request["radius_km"] == 15.0
    assert updated_request["request_id"] == "req-11"


def test_resolve_ambiguity_requires_suggestions():
    request_data = {
        "request_id": "req-x",
        "scenario": "software_deal",
        "match_mode": "fuzzy",
        "game_title": "crimson",
    }
    response_data = {
        "status": "ambiguous",
        "request_id": "req-x",
        "scenario": "software_deal",
        "query": "crimson",
        "suggestions": [],
    }

    try:
        launcher.resolve_ambiguity(request_data, response_data)
    except RuntimeError as exc:
        assert "without suggestions" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError for ambiguous response without suggestions.")
