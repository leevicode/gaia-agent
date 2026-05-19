from copy import deepcopy

from app.mock_data import (
    AUTHORIZED_RESELLER_DEALS,
    GRAY_MARKET_DEALS,
    MARKETPLACE_DEALS,
    OFFICIAL_STORE_DEALS,
)
from app.sources.base import DealSource


class MockDictionaryDealSource(DealSource):
    """Generic mock source backed by an in-memory dictionary."""

    def __init__(self, source_name: str, deal_catalog: dict[str, list[dict]]) -> None:
        self.source_name = source_name
        self.deal_catalog = deal_catalog

    def search_deals(self, title: str, **filters) -> list[dict]:
        deals = deepcopy(self.deal_catalog.get(title, []))

        max_price = filters.get("max_price")
        if isinstance(max_price, (int, float)):
            deals = [
                deal for deal in deals
                if deal.get("price_eur", float("inf")) <= float(max_price)
            ]

        radius_km = filters.get("radius_km")
        if isinstance(radius_km, (int, float)):
            deals = [
                deal for deal in deals
                if deal.get("distance_km", 0.0) <= float(radius_km)
                or "distance_km" not in deal
            ]

        return deals


class MockOfficialStoreSource(MockDictionaryDealSource):
    def __init__(self) -> None:
        super().__init__(
            source_name="mock_official_store",
            deal_catalog=OFFICIAL_STORE_DEALS,
        )


class MockAuthorizedResellerSource(MockDictionaryDealSource):
    def __init__(self) -> None:
        super().__init__(
            source_name="mock_authorized_reseller",
            deal_catalog=AUTHORIZED_RESELLER_DEALS,
        )


class MockGrayMarketSource(MockDictionaryDealSource):
    def __init__(self) -> None:
        super().__init__(
            source_name="mock_gray_market",
            deal_catalog=GRAY_MARKET_DEALS,
        )


class MockMarketplaceSource(MockDictionaryDealSource):
    def __init__(self) -> None:
        super().__init__(
            source_name="mock_marketplace",
            deal_catalog=MARKETPLACE_DEALS,
        )