from app.catalogs import get_console_catalog_titles, get_software_catalog_titles
from app.matching import normalize_text, resolve_catalog_key
from app.mock_data import (
    AUTHORIZED_RESELLER_DEALS,
    GRAY_MARKET_DEALS,
    MARKETPLACE_DEALS,
    OFFICIAL_STORE_DEALS,
)


def test_normalize_text_basic():
    assert normalize_text("  PlayStation 5 Disc Edition  ") == "playstation 5 disc edition"
    assert normalize_text("Crimson-Desert: Deluxe Edition!") == "crimson desert deluxe edition"


def test_software_catalog_contains_expected_titles():
    titles = get_software_catalog_titles()
    assert "Crimson Desert" in titles
    assert "Crimson Desert Deluxe Edition" in titles
    assert "PlayStation 5 Disc Edition" not in titles
    assert "PlayStation 5 Digital Edition" not in titles


def test_console_catalog_contains_expected_titles():
    titles = get_console_catalog_titles()
    assert "PlayStation 5 Disc Edition" in titles
    assert "PlayStation 5 Digital Edition" in titles
    assert "Crimson Desert" not in titles


def test_fuzzy_software_query_is_ambiguous():
    result = resolve_catalog_key(
        "crimson",
        get_software_catalog_titles(),
        match_mode="fuzzy",
    )

    assert result["status"] == "ambiguous"
    assert result["resolved_key"] is None
    assert set(result["suggestions"]) == {
        "Crimson Desert",
        "Crimson Desert Deluxe Edition",
    }


def test_fuzzy_console_query_is_ambiguous():
    result = resolve_catalog_key(
        "playstation 5",
        get_console_catalog_titles(),
        match_mode="fuzzy",
    )

    assert result["status"] == "ambiguous"
    assert result["resolved_key"] is None
    assert set(result["suggestions"]) == {
        "PlayStation 5 Disc Edition",
        "PlayStation 5 Digital Edition",
    }


def test_fuzzy_unique_console_partial_match_resolves():
    result = resolve_catalog_key(
        "playstation 5 digital",
        get_console_catalog_titles(),
        match_mode="fuzzy",
    )

    assert result["status"] == "resolved"
    assert result["resolved_key"] == "PlayStation 5 Digital Edition"
    assert result["suggestions"] == []


def test_case_insensitive_exact_match_resolves():
    result = resolve_catalog_key(
        "crimson desert",
        get_software_catalog_titles(),
        match_mode="exact",
    )

    assert result["status"] == "resolved"
    assert result["resolved_key"] == "Crimson Desert"


def test_exact_mode_does_not_fallback_from_deluxe_to_base_in_official_catalog():
    result = resolve_catalog_key(
        "Crimson Desert Deluxe Edition",
        OFFICIAL_STORE_DEALS.keys(),
        match_mode="exact",
    )

    assert result["status"] == "not_found"
    assert result["resolved_key"] is None
    assert result["suggestions"] == []


def test_exact_mode_resolves_deluxe_only_in_authorized_reseller_catalog():
    result = resolve_catalog_key(
        "Crimson Desert Deluxe Edition",
        AUTHORIZED_RESELLER_DEALS.keys(),
        match_mode="exact",
    )

    assert result["status"] == "resolved"
    assert result["resolved_key"] == "Crimson Desert Deluxe Edition"


def test_exact_mode_does_not_fallback_from_deluxe_to_base_in_gray_market_catalog():
    result = resolve_catalog_key(
        "Crimson Desert Deluxe Edition",
        GRAY_MARKET_DEALS.keys(),
        match_mode="exact",
    )

    assert result["status"] == "not_found"
    assert result["resolved_key"] is None


def test_exact_mode_resolves_only_selected_console_edition_in_official_catalog():
    result = resolve_catalog_key(
        "PlayStation 5 Digital Edition",
        OFFICIAL_STORE_DEALS.keys(),
        match_mode="exact",
    )

    assert result["status"] == "resolved"
    assert result["resolved_key"] == "PlayStation 5 Digital Edition"


def test_exact_mode_resolves_only_selected_console_edition_in_marketplace_catalog():
    result = resolve_catalog_key(
        "PlayStation 5 Digital Edition",
        MARKETPLACE_DEALS.keys(),
        match_mode="exact",
    )

    assert result["status"] == "resolved"
    assert result["resolved_key"] == "PlayStation 5 Digital Edition"


def test_exact_mode_does_not_partially_match_console_title():
    result = resolve_catalog_key(
        "playstation 5",
        get_console_catalog_titles(),
        match_mode="exact",
    )

    assert result["status"] == "not_found"
    assert result["resolved_key"] is None
    assert result["suggestions"] == []
