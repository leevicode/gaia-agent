import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
project_root_str = str(PROJECT_ROOT)

if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)


from app.python_guard import enforce_python_312
from app.sources.cheapshark_source import CheapSharkSource


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Manual live CheapShark smoke test. "
            "This script is intentionally not part of pytest."
        )
    )

    parser.add_argument(
        "title",
        help="Game title to search for, for example: Crimson Desert",
    )

    parser.add_argument(
        "--max-price",
        type=float,
        default=None,
        help="Optional upper price filter in USD.",
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=8.0,
        help="HTTP timeout in seconds.",
    )

    parser.add_argument(
        "--page-size",
        type=int,
        default=5,
        help="Maximum number of deals to request.",
    )

    return parser


def main() -> int:
    enforce_python_312()

    parser = build_parser()
    args = parser.parse_args()

    source = CheapSharkSource(
        timeout_seconds=args.timeout,
        page_size=args.page_size,
    )

    print("[CheapShark smoke test] Starting live request...")
    print(f"[CheapShark smoke test] Title: {args.title}")
    print(f"[CheapShark smoke test] Max price USD: {args.max_price}")
    print(f"[CheapShark smoke test] Timeout seconds: {args.timeout}")
    print(f"[CheapShark smoke test] Page size: {args.page_size}")

    try:
        deals = source.search_deals(
            args.title,
            max_price=args.max_price,
        )
    except Exception as exc:
        print("[CheapShark smoke test] FAILED.")
        print(f"[CheapShark smoke test] Error: {exc}")
        return 1

    print("[CheapShark smoke test] Request completed.")
    print(f"[CheapShark smoke test] Deals returned: {len(deals)}")

    if not deals:
        print(
            "[CheapShark smoke test] No deals returned. "
            "This can be valid for uncommon titles or strict filters."
        )
        return 0

    print("[CheapShark smoke test] First mapped deal:")
    print(
        json.dumps(
            deals[0],
            indent=2,
            ensure_ascii=False,
        )
    )

    if deals[0].get("price_eur") is not None:
        print(
            "[CheapShark smoke test] WARNING: price_eur should be None. "
            "CheapShark prices should not be treated as EUR without conversion."
        )
        return 1

    if deals[0].get("currency") != "USD":
        print(
            "[CheapShark smoke test] WARNING: currency should be USD for CheapShark deals."
        )
        return 1

    print("[CheapShark smoke test] Currency safety check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())