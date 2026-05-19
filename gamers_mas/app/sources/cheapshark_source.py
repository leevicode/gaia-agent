import json
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.currency.converter import (
    apply_usd_to_eur_conversion_to_deals,
    resolve_usd_to_eur_rate,
)
from app.currency.ecb_rate_source import ECBRateSource
from app.matching import normalize_text
from app.sources.base import DealSource


CHEAPSHARK_BASE_URL = "https://www.cheapshark.com/api/1.0"


def parse_optional_float(value: Any) -> float | None:
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def default_http_get_json(url: str, timeout_seconds: float) -> Any:
    request = Request(
        url,
        headers={
            "User-Agent": "gamers-mas-spade-demo/0.1",
        },
    )

    with urlopen(request, timeout=timeout_seconds) as response:
        status_code = getattr(response, "status", 200)

        if status_code < 200 or status_code >= 300:
            raise RuntimeError(
                f"CheapShark request failed with HTTP status {status_code}."
            )

        body = response.read().decode("utf-8")

    return json.loads(body)


def is_exact_returned_title_match(requested_title: str, returned_title: Any) -> bool:
    if not isinstance(returned_title, str):
        return False

    return normalize_text(returned_title) == normalize_text(requested_title)


def filter_raw_deals_by_exact_title(
    raw_deals: list[Any],
    requested_title: str,
) -> list[dict[str, Any]]:
    exact_title_deals = []

    for raw_deal in raw_deals:
        if not isinstance(raw_deal, dict):
            continue

        if is_exact_returned_title_match(
            requested_title=requested_title,
            returned_title=raw_deal.get("title"),
        ):
            exact_title_deals.append(raw_deal)

    return exact_title_deals


def get_game_search_title(raw_game: dict[str, Any]) -> str | None:
    title = raw_game.get("external") or raw_game.get("title")

    if not isinstance(title, str) or not title.strip():
        return None

    return title.strip()


def get_game_search_id(raw_game: dict[str, Any]) -> str | None:
    game_id = raw_game.get("gameID")

    if game_id is None:
        return None

    game_id_text = str(game_id).strip()
    if not game_id_text:
        return None

    return game_id_text


def find_exact_game_match(
    raw_games: list[Any],
    requested_title: str,
) -> dict[str, Any] | None:
    for raw_game in raw_games:
        if not isinstance(raw_game, dict):
            continue

        game_title = get_game_search_title(raw_game)
        game_id = get_game_search_id(raw_game)

        if game_title is None or game_id is None:
            continue

        if is_exact_returned_title_match(requested_title, game_title):
            return raw_game

    return None


class CheapSharkSource(DealSource):
    """
    Real CheapShark source adapter.

    CheapShark prices are USD. This adapter first resolves the requested game
    title to an exact CheapShark gameID, then fetches deals only for that gameID.
    This prevents related products such as deluxe packs, DLC, or other editions
    from being ranked as the selected base game.
    """

    source_name = "cheapshark"

    def __init__(
        self,
        timeout_seconds: float = 8.0,
        page_size: int = 10,
        http_get_json=default_http_get_json,
        enable_currency_conversion: bool = False,
        currency_rate_provider: str = "ecb",
        currency_rate_timeout_seconds: float = 8.0,
        allow_currency_fallback_rate: bool = True,
        fallback_usd_to_eur_rate: float | None = None,
        fallback_usd_to_eur_rate_source: str = "manual_fallback_rate",
        fallback_usd_to_eur_rate_date: str = "not_specified",
        ecb_rate_source: ECBRateSource | None = None,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than 0.")

        if page_size <= 0:
            raise ValueError("page_size must be greater than 0.")

        if currency_rate_timeout_seconds <= 0:
            raise ValueError("currency_rate_timeout_seconds must be greater than 0.")

        self.timeout_seconds = timeout_seconds
        self.page_size = page_size
        self.http_get_json = http_get_json
        self.enable_currency_conversion = enable_currency_conversion
        self.currency_rate_provider = currency_rate_provider
        self.currency_rate_timeout_seconds = currency_rate_timeout_seconds
        self.allow_currency_fallback_rate = allow_currency_fallback_rate
        self.fallback_usd_to_eur_rate = fallback_usd_to_eur_rate
        self.fallback_usd_to_eur_rate_source = fallback_usd_to_eur_rate_source
        self.fallback_usd_to_eur_rate_date = fallback_usd_to_eur_rate_date
        self.ecb_rate_source = ecb_rate_source

    def build_url(self, endpoint: str, params: dict[str, Any] | None = None) -> str:
        clean_endpoint = endpoint.strip("/")

        url = f"{CHEAPSHARK_BASE_URL}/{clean_endpoint}"

        if not params:
            return url

        clean_params = {
            key: value
            for key, value in params.items()
            if value is not None
        }

        if not clean_params:
            return url

        return f"{url}?{urlencode(clean_params)}"

    def get_store_map(self) -> dict[str, str]:
        stores_url = self.build_url("stores")
        stores = self.http_get_json(stores_url, self.timeout_seconds)

        store_map = {}

        if not isinstance(stores, list):
            return store_map

        for store in stores:
            if not isinstance(store, dict):
                continue

            store_id = store.get("storeID")
            store_name = store.get("storeName")

            if store_id is None or store_name is None:
                continue

            store_map[str(store_id)] = str(store_name)

        return store_map

    def search_games(self, title: str) -> list[Any]:
        games_url = self.build_url(
            "games",
            {
                "title": title.strip(),
                "limit": self.page_size,
            },
        )
        raw_games = self.http_get_json(games_url, self.timeout_seconds)

        if not isinstance(raw_games, list):
            return []

        return raw_games

    def get_game_details(self, game_id: str) -> dict[str, Any]:
        game_url = self.build_url(
            "games",
            {
                "id": game_id,
            },
        )
        game_details = self.http_get_json(game_url, self.timeout_seconds)

        if not isinstance(game_details, dict):
            return {}

        return game_details

    def search_deals(self, title: str, **filters) -> list[dict]:
        if not title or not title.strip():
            return []

        requested_title = title.strip()

        raw_games = self.search_games(requested_title)
        exact_game = find_exact_game_match(
            raw_games=raw_games,
            requested_title=requested_title,
        )

        if exact_game is None:
            return []

        game_id = get_game_search_id(exact_game)
        if game_id is None:
            return []

        game_title = get_game_search_title(exact_game) or requested_title
        game_details = self.get_game_details(game_id)
        game_info = game_details.get("info", {})
        if not isinstance(game_info, dict):
            game_info = {}

        raw_deals = game_details.get("deals", [])
        if not isinstance(raw_deals, list):
            return []

        store_map = self.get_store_map()
        steam_app_id = (
            exact_game.get("steamAppID")
            or game_info.get("steamAppID")
        )
        thumb = exact_game.get("thumb") or game_info.get("thumb")

        mapped_deals = []

        for raw_deal in raw_deals:
            if not isinstance(raw_deal, dict):
                continue

            mapped_deal = self.map_deal(
                raw_deal=raw_deal,
                requested_title=game_title,
                store_map=store_map,
                game_id=game_id,
                steam_app_id=steam_app_id,
                thumb=thumb,
            )

            max_price = filters.get("max_price")
            if isinstance(max_price, (int, float)):
                price_usd = mapped_deal.get("price_usd")
                if price_usd is None or price_usd > float(max_price):
                    continue

            mapped_deals.append(mapped_deal)

        if self.enable_currency_conversion and mapped_deals:
            rate = resolve_usd_to_eur_rate(
                rate_provider=self.currency_rate_provider,
                timeout_seconds=self.currency_rate_timeout_seconds,
                allow_fallback_rate=self.allow_currency_fallback_rate,
                fallback_usd_to_eur_rate=self.fallback_usd_to_eur_rate,
                fallback_rate_source=self.fallback_usd_to_eur_rate_source,
                fallback_rate_date=self.fallback_usd_to_eur_rate_date,
                ecb_rate_source=self.ecb_rate_source,
            )
            mapped_deals = apply_usd_to_eur_conversion_to_deals(
                deals=mapped_deals,
                rate=rate,
            )

        return mapped_deals

    def map_deal(
        self,
        raw_deal: dict[str, Any],
        requested_title: str,
        store_map: dict[str, str],
        game_id: str | None = None,
        steam_app_id: Any = None,
        thumb: Any = None,
    ) -> dict:
        store_id = str(raw_deal.get("storeID", ""))
        store_name = store_map.get(store_id, f"CheapShark store {store_id}".strip())

        sale_price_usd = parse_optional_float(
            raw_deal.get("salePrice", raw_deal.get("price"))
        )
        normal_price_usd = parse_optional_float(
            raw_deal.get("normalPrice", raw_deal.get("retailPrice"))
        )
        savings_percent = parse_optional_float(raw_deal.get("savings"))
        deal_rating = parse_optional_float(raw_deal.get("dealRating"))

        return {
            "store": store_name,
            "title": requested_title,
            "price_eur": None,
            "price_usd": sale_price_usd,
            "normal_price_usd": normal_price_usd,
            "savings_percent": savings_percent,
            "deal_rating": deal_rating,
            "condition": "digital",
            "shipping_eur": 0.0,
            "availability": "available",
            "trust_score": 0.8,
            "source_type": "authorized_reseller",
            "source_adapter": self.source_name,
            "currency": "USD",
            "currency_conversion_applied": False,
            "currency_note": (
                "CheapShark prices are USD. No EUR conversion has been applied."
            ),
            "deal_id": raw_deal.get("dealID"),
            "store_id": store_id,
            "game_id": raw_deal.get("gameID") or game_id,
            "steam_app_id": raw_deal.get("steamAppID") or steam_app_id,
            "thumb": raw_deal.get("thumb") or thumb,
        }
