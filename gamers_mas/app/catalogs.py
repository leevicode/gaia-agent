from app.mock_data import (
    AUTHORIZED_RESELLER_DEALS,
    GRAY_MARKET_DEALS,
    MARKETPLACE_DEALS,
    OFFICIAL_STORE_DEALS,
)


def get_console_catalog_titles() -> list[str]:
    marketplace_titles = set(MARKETPLACE_DEALS.keys())
    official_titles = set(OFFICIAL_STORE_DEALS.keys())
    console_titles = marketplace_titles | (official_titles & marketplace_titles)
    return sorted(console_titles)


def get_software_catalog_titles() -> list[str]:
    all_titles = (
        set(OFFICIAL_STORE_DEALS.keys())
        | set(AUTHORIZED_RESELLER_DEALS.keys())
        | set(GRAY_MARKET_DEALS.keys())
    )
    console_titles = set(get_console_catalog_titles())
    software_titles = all_titles - console_titles
    return sorted(software_titles)
