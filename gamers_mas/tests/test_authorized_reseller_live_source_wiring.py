from app.agents.authorized_reseller_agent import build_authorized_reseller_search_result


class FakeSuccessfulRealSource:
    source_name = "fake_real_authorized_source"

    def search_deals(self, title: str, **filters):
        return [
            {
                "store": "Fake Real Store",
                "title": title,
                "price_eur": None,
                "price_usd": 49.99,
                "condition": "digital",
                "shipping_eur": 0.0,
                "availability": "available",
                "trust_score": 0.8,
                "source_type": "authorized_reseller",
                "source_adapter": self.source_name,
                "currency": "USD",
            }
        ]


class FakeFailingRealSource:
    source_name = "fake_failing_real_source"

    def search_deals(self, title: str, **filters):
        raise RuntimeError("fake source failure")


class FakeEmptyRealSource:
    source_name = "fake_empty_real_source"

    def search_deals(self, title: str, **filters):
        return []


def test_authorized_reseller_uses_real_source_when_enabled_and_successful():
    result = build_authorized_reseller_search_result(
        game_title="Crimson Desert",
        match_mode="exact",
        real_source=FakeSuccessfulRealSource(),
        real_source_enabled=True,
        mock_fallback_available=True,
    )

    assert result["source_adapter"] == "fake_real_authorized_source"
    assert result["match_status"] == "resolved"
    assert result["resolved_title"] == "Crimson Desert"
    assert result["deals"][0]["store"] == "Fake Real Store"
    assert result["bdi_trace"]["selected_plan"] == "query_real_source"
    assert result["bdi_trace"]["beliefs"]["real_source_available"] is True
    assert result["bdi_trace"]["beliefs"]["real_source_returned_deals"] is True


def test_authorized_reseller_falls_back_to_mock_when_real_source_fails():
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
    assert result["bdi_trace"]["beliefs"]["real_source_available"] is False


def test_authorized_reseller_falls_back_to_mock_when_real_source_returns_no_deals():
    result = build_authorized_reseller_search_result(
        game_title="Crimson Desert",
        match_mode="exact",
        real_source=FakeEmptyRealSource(),
        real_source_enabled=True,
        mock_fallback_available=True,
    )

    assert result["source_adapter"] == "mock_authorized_reseller"
    assert result["match_status"] == "resolved"
    assert len(result["deals"]) == 2
    assert result["bdi_trace"]["selected_plan"] == "fallback_to_mock_source"
    assert result["bdi_trace"]["beliefs"]["real_source_available"] is True
    assert result["bdi_trace"]["beliefs"]["real_source_returned_deals"] is False


def test_authorized_reseller_returns_no_results_when_real_source_fails_and_fallback_disabled():
    result = build_authorized_reseller_search_result(
        game_title="Crimson Desert",
        match_mode="exact",
        real_source=FakeFailingRealSource(),
        real_source_enabled=True,
        mock_fallback_available=False,
    )

    assert result["source_adapter"] == "none"
    assert result["match_status"] == "not_found"
    assert result["deals"] == []
    assert result["bdi_trace"]["selected_plan"] == "return_no_results"


def test_authorized_reseller_keeps_mock_behavior_when_real_source_disabled():
    result = build_authorized_reseller_search_result(
        game_title="Crimson Desert",
        match_mode="exact",
        real_source=FakeSuccessfulRealSource(),
        real_source_enabled=False,
        mock_fallback_available=True,
    )

    assert result["source_adapter"] == "mock_authorized_reseller"
    assert result["match_status"] == "resolved"
    assert len(result["deals"]) == 2
    assert result["bdi_trace"]["selected_plan"] == "use_mock_source"