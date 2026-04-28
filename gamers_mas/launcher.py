from app.python_guard import enforce_python_312

enforce_python_312()

import time
import uuid

from app.request_bus import clear_request_file, write_request
from app.runtime_response import clear_response_file, read_response_if_exists


def ask_non_empty_text(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Input cannot be empty.")


def ask_positive_number(prompt: str) -> float:
    while True:
        raw = input(prompt).strip()
        try:
            value = float(raw)
        except ValueError:
            print("Please enter a valid number.")
            continue

        if value <= 0:
            print("Please enter a number greater than 0.")
            continue

        return value


def ask_scenario() -> str:
    while True:
        print()
        print("Choose a scenario:")
        print("1. Software deal search")
        print("2. Local console search")
        choice = input("Enter 1 or 2: ").strip()

        if choice == "1":
            return "software_deal"
        if choice == "2":
            return "local_console_search"

        print("Invalid choice. Please enter 1 or 2.")


def ask_choice_from_suggestions(suggestions: list[str]) -> str:
    while True:
        print()
        print("Your input is ambiguous. Please choose one of these:")
        for index, suggestion in enumerate(suggestions, start=1):
            print(f"{index}. {suggestion}")

        raw = input(f"Enter a number from 1 to {len(suggestions)}: ").strip()
        try:
            selected_index = int(raw)
        except ValueError:
            print("Please enter a valid number.")
            continue

        if 1 <= selected_index <= len(suggestions):
            return suggestions[selected_index - 1]

        print("Choice out of range.")


def new_request_id() -> str:
    return str(uuid.uuid4())


def build_request() -> dict:
    scenario = ask_scenario()

    if scenario == "software_deal":
        game_title = ask_non_empty_text("Enter game title: ")
        return {
            "request_id": new_request_id(),
            "scenario": "software_deal",
            "match_mode": "fuzzy",
            "game_title": game_title,
        }

    product_name = ask_non_empty_text("Enter product name: ")
    max_price = ask_positive_number("Enter max price: ")
    radius_km = ask_positive_number("Enter radius in km: ")

    return {
        "request_id": new_request_id(),
        "scenario": "local_console_search",
        "match_mode": "fuzzy",
        "product_name": product_name,
        "max_price": max_price,
        "radius_km": radius_km,
    }


def submit_request(request_data: dict) -> dict:
    clear_response_file()
    write_request(request_data)

    print()
    print("Submitted request to request.json:")
    print(request_data)
    print("Waiting for MAS service response ...")

    timeout_seconds = 60
    poll_interval_seconds = 0.5
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        response_data = read_response_if_exists()
        if response_data is not None and response_data.get("request_id") == request_data["request_id"]:
            clear_request_file()
            clear_response_file()
            return response_data

        time.sleep(poll_interval_seconds)

    raise RuntimeError(
        "Timed out waiting for runtime_response.json. Make sure main.py is already running."
    )


def resolve_ambiguity(request_data: dict, response_data: dict) -> dict:
    suggestions = response_data.get("suggestions", [])
    if not suggestions:
        raise RuntimeError("Ambiguous response received without suggestions.")

    chosen_title = ask_choice_from_suggestions(suggestions)

    updated_request = dict(request_data)
    updated_request["request_id"] = new_request_id()
    updated_request["match_mode"] = "exact"

    if updated_request["scenario"] == "software_deal":
        updated_request["game_title"] = chosen_title
    elif updated_request["scenario"] == "local_console_search":
        updated_request["product_name"] = chosen_title
    else:
        raise RuntimeError(f"Unsupported scenario: {updated_request['scenario']}")

    print()
    print(f"Selected exact title: {chosen_title}")
    return updated_request


def main() -> None:
    request_data = build_request()

    while True:
        response_data = submit_request(request_data)
        status = response_data.get("status")

        if status == "ambiguous":
            request_data = resolve_ambiguity(request_data, response_data)
            continue

        if status == "ok":
            break

        raise RuntimeError(f"Unexpected runtime response status: {status}")


if __name__ == "__main__":
    main()
