# Architecture

This project is a **mock-data-only SPADE MAS prototype**. Its purpose is to demonstrate multi-agent coordination patterns, not live store integration.

## Python constraint

The architecture is validated only on **Python 3.12.x**.

Constraint enforcement points:

- `pyproject.toml` declares `requires-python = ">=3.12,<3.13"`
- `.python-version` is set to `3.12`
- runtime checks in `main.py` and `launcher.py`
- a test-suite guard in `tests/conftest.py`
- Docker runtime pinned to Python 3.12

## Agents

- `UserInterfaceAgent` - accepts launcher-submitted requests
- `SoftwareCoordinatorAgent` - coordinates software-deal requests
- `LocalCoordinatorAgent` - coordinates console-search requests
- `OfficialStoreAgent` - official-source mock results
- `AuthorizedResellerAgent` - authorized reseller mock results
- `GrayMarketAgent` - gray-market mock results with warning semantics
- `MarketplaceAgent` - local marketplace mock results
- `RecommendationAgent` - selects the best legitimate software deal
- `ValueRankerAgent` - ranks console deals
- `OutputAgent` - writes structured final responses and prints human-readable summaries

## Runtime model

The MAS starts once and remains idle between requests. Requests are pushed in through `launcher.py`, written to `request.json`, and consumed by the agents already running inside `main.py`.

After each completed request:

- ambiguity may trigger a launcher-guided exact-title rerun
- transient request/response files are cleared
- agents return to idle

## Matching model

There are two matching modes:

- `fuzzy` - case-insensitive and partial matching for initial user input
- `exact` - normalized exact matching only after the user has selected one concrete title

This prevents edition-mixing after ambiguity resolution.
