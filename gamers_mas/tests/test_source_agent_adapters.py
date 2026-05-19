from app.agents.authorized_reseller_agent import build_authorized_reseller_search_result
from app.agents.gray_market_agent import build_gray_market_search_result
from app.agents.marketplace_agent import build_marketplace_search_result
from app.agents.official_store_agent import build_official_store_search_result


def test_official_store_agent_uses_mock_source_adapter_with_price_filter():
    result = build_official_store_search_result(
        search_title="PlayStation 5 Disc Edition",
        match_mode="exact",
        max_price=500.0,
    )

    stores = {deal["store"] for deal in result["deals"]}

    assert result["source_adapter"] == "mock_official_store"
    assert result["match_status"] == "resolved"
    assert stores == {"GameStop"}


def test_authorized_reseller_agent_uses_mock_source_adapter_for_deluxe_exact_match():
    result = build_authorized_reseller_search_result(
        game_title="Crimson Desert Deluxe Edition",
        match_mode="exact",
    )

    assert result["source_adapter"] == "mock_authorized_reseller"
    assert result["match_status"] == "resolved"
    assert result["resolved_title"] == "Crimson Desert Deluxe Edition"
    assert result["deals"][0]["store"] == "Fanatical"


def test_gray_market_agent_does_not_fallback_from_deluxe_to_base_in_exact_mode():
    result = build_gray_market_search_result(
        game_title="Crimson Desert Deluxe Edition",
        match_mode="exact",
    )

    assert result["source_adapter"] == "mock_gray_market"
    assert result["match_status"] == "not_found"
    assert result["resolved_title"] is None
    assert result["deals"] == []


def test_marketplace_agent_uses_mock_source_adapter_with_price_and_radius_filters():
    result = build_marketplace_search_result(
        product_name="PlayStation 5 Disc Edition",
        max_price=400.0,
        radius_km=15.0,
        match_mode="exact",
    )

    stores = {deal["store"] for deal in result["deals"]}

    assert result["source_adapter"] == "mock_marketplace"
    assert result["match_status"] == "resolved"
    assert "Facebook Marketplace" in stores
    assert "OfferUp" in stores
    assert "eBay Local" not in stores


def test_official_store_agent_reports_ambiguity_in_fuzzy_mode():
    result = build_official_store_search_result(
        search_title="playstation 5",
        match_mode="fuzzy",
    )

    assert result["source_adapter"] == "mock_official_store"
    assert result["match_status"] == "ambiguous"
    assert result["resolved_title"] is None
    assert set(result["suggestions"]) == {
        "PlayStation 5 Disc Edition",
        "PlayStation 5 Digital Edition",
    }