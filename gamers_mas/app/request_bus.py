import json
from pathlib import Path


REQUEST_FILE = Path("request.json")


def clear_request_file() -> None:
    if REQUEST_FILE.exists():
        REQUEST_FILE.unlink()


def write_request(data: dict) -> None:
    REQUEST_FILE.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )


def read_request_if_exists() -> dict | None:
    if not REQUEST_FILE.exists():
        return None

    try:
        return json.loads(REQUEST_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in request.json: {exc}") from exc
