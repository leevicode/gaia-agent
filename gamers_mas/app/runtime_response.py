import json
from pathlib import Path


RESPONSE_FILE = Path("runtime_response.json")


def clear_response_file() -> None:
    if RESPONSE_FILE.exists():
        RESPONSE_FILE.unlink()


def write_response(data: dict) -> None:
    RESPONSE_FILE.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )


def read_response_if_exists() -> dict | None:
    if not RESPONSE_FILE.exists():
        return None

    try:
        return json.loads(RESPONSE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in runtime_response.json: {exc}") from exc
