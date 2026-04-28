import json
from pathlib import Path


REQUEST_FILE = Path("request.json")


def validate_request_data(data: dict) -> dict:
    request_id = data.get("request_id")
    scenario = data.get("scenario")
    match_mode = data.get("match_mode", "fuzzy")

    if not isinstance(request_id, str) or not request_id.strip():
        raise RuntimeError("request.json must contain a non-empty request_id string.")

    if match_mode not in {"fuzzy", "exact"}:
        raise RuntimeError("request.json must contain match_mode='fuzzy' or match_mode='exact'.")

    if scenario == "software_deal":
        game_title = data.get("game_title")
        if not isinstance(game_title, str) or not game_title.strip():
            raise RuntimeError(
                "request.json must contain a non-empty game_title for software_deal."
            )
        return {
            "request_id": request_id.strip(),
            "scenario": scenario,
            "match_mode": match_mode,
            "game_title": game_title.strip(),
        }

    if scenario == "local_console_search":
        product_name = data.get("product_name")
        max_price = data.get("max_price")
        radius_km = data.get("radius_km")

        if not isinstance(product_name, str) or not product_name.strip():
            raise RuntimeError(
                "request.json must contain a non-empty product_name for local_console_search."
            )

        if not isinstance(max_price, (int, float)) or max_price <= 0:
            raise RuntimeError(
                "request.json must contain a positive numeric max_price for local_console_search."
            )

        if not isinstance(radius_km, (int, float)) or radius_km <= 0:
            raise RuntimeError(
                "request.json must contain a positive numeric radius_km for local_console_search."
            )

        return {
            "request_id": request_id.strip(),
            "scenario": scenario,
            "match_mode": match_mode,
            "product_name": product_name.strip(),
            "max_price": float(max_price),
            "radius_km": float(radius_km),
        }

    raise RuntimeError(
        "request.json must contain scenario='software_deal' or scenario='local_console_search'."
    )


def load_request() -> dict:
    if not REQUEST_FILE.exists():
        raise RuntimeError("Missing request.json in project root.")

    try:
        data = json.loads(REQUEST_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in request.json: {exc}") from exc

    return validate_request_data(data)
