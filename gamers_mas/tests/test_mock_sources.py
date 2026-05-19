from app.sources.mock_sources import (
    MockAuthorizedResellerSource,
    MockGrayMarketSource,
    MockMarketplaceSource,
    MockOfficialStoreSource,
)


def test_mock_official_source_returns_official_deals():
    source = MockOfficialStoreSource()

    deals = source.search_deals("Crimson Desert")

    assert source.source_name == "mock_official_store"
    assert len(deals) == 3
    assert all(deal["source_type"] == "official" for deal in deals)


def test_mock_authorized_reseller_source_returns_authorized_deals():
    source = MockAuthorizedResellerSource()

    deals = source.search_deals("Crimson Desert")

    assert source.source_name == "mock_authorized_reseller"
    assert len(deals) == 2
    assert all(deal["source_type"] == "authorized_reseller" for deal in deals)


def test_mock_gray_market_source_returns_gray_market_deals():
    source = MockGrayMarketSource()

    deals = source.search_deals("Crimson Desert")

    assert source.source_name == "mock_gray_market"
    assert len(deals) == 2
    assert all(deal["source_type"] == "gray_market" for deal in deals)


def test_mock_marketplace_source_applies_price_and_radius_filters():
    source = MockMarketplaceSource()

    deals = source.search_deals(
        "PlayStation 5 Disc Edition",
        max_price=400.0,
        radius_km=15.0,
    )

    stores = {deal["store"] for deal in deals}

    assert "Facebook Marketplace" in stores
    assert "OfferUp" in stores
    assert "eBay Local" not in stores


def test_mock_source_returns_copy_not_original_reference():
    source = MockAuthorizedResellerSource()

    first_result = source.search_deals("Crimson Desert")
    first_result[0]["store"] = "Modified Store"

    second_result = source.search_deals("Crimson Desert")

    assert second_result[0]["store"] != "Modified Store"