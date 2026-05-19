# Architecture

This document explains the complete architecture of the Game Deal-Finding MAS. It is written for readers who may be new to multi-agent systems, SPADE, BDI reasoning, or the project codebase.

## Architecture summary

The system is a SPADE-based multi-agent system. Each agent has a focused role. Agents communicate by sending messages through Prosody, an XMPP server.

The system supports two scenarios:

1. **Software deal search**
   - resolves software title ambiguity
   - queries official, authorized reseller, and gray-market source agents
   - uses CheapShark as a live authorized reseller source by default
   - converts CheapShark USD prices to EUR using ECB reference rates
   - recommends the best legitimate EUR-comparable deal
   - warns about gray-market options

2. **Local console search**
   - resolves console product ambiguity
   - queries official and marketplace source agents
   - ranks deals by price, shipping, trust, distance, and condition
   - warns about used, refurbished, and lower-trust offers

The system uses manual BDI-style reasoning. BDI means beliefs, goals, and plans.

## Why this architecture exists

The assignment requires a MAS implementation with:

- at least two scenarios
- goals, cooperation, and decision making
- at least one non-trivial decision-making scenario
- BDI-style reasoning
- clear evidence of beliefs, goals, and plans

This architecture addresses those requirements directly.

The project does not try to be a production marketplace. It is a controlled MAS demonstration with live source integration where useful and mock fallback where stability matters.

## Runtime model

The system uses a long-running idle-service model.

```text
main.py starts all agents
agents stay alive
launcher.py submits a request
agents cooperate to answer it
OutputAgent prints the result
agents return to idle
```

This is different from a one-shot script. You start the MAS once, then submit multiple requests.

## Main runtime files

| File | Responsibility |
|---|---|
| `main.py` | Starts all SPADE agents and keeps them running |
| `launcher.py` | Collects user input and submits requests |
| `request.json` | Temporary request file used by launcher and UserInterfaceAgent |
| `runtime_response.json` | Temporary response file used by OutputAgent and launcher |
| `bdi_trace.json` | Persistent trace of BDI decisions |
| `.env` | Local configuration and agent passwords |
| `.env.example` | Safe template configuration |

## Agent list

| Agent | Main role |
|---|---|
| `UserInterfaceAgent` | Reads requests from `request.json` and routes them |
| `SoftwareCoordinatorAgent` | Coordinates software deal search |
| `LocalCoordinatorAgent` | Coordinates local console search |
| `OfficialStoreAgent` | Provides official-source results |
| `AuthorizedResellerAgent` | Uses CheapShark first and mock authorized reseller fallback |
| `GrayMarketAgent` | Provides risky gray-market options |
| `MarketplaceAgent` | Provides local marketplace console offers |
| `RecommendationAgent` | Selects best legitimate software deal and handles gray-market warning logic |
| `ValueRankerAgent` | Ranks local console deals |
| `OutputAgent` | Prints final results and persists BDI traces |

## Communication protocols

Message protocol names are stored in `app/protocols.py`.

| Protocol | Meaning |
|---|---|
| `REQUEST_SOFTWARE_DEAL` | User requests a software deal search |
| `REQUEST_LOCAL_CONSOLE_SEARCH` | User requests a local console search |
| `SEARCH_OFFICIAL` | Coordinator asks official source agent to search |
| `OFFICIAL_RESULTS` | Official source agent replies |
| `SEARCH_AUTHORIZED` | Coordinator asks authorized reseller agent to search |
| `AUTHORIZED_RESULTS` | Authorized reseller agent replies |
| `SEARCH_GRAY_MARKET` | Coordinator asks gray-market agent to search |
| `GRAY_MARKET_RESULTS` | Gray-market agent replies |
| `SEARCH_MARKETPLACES` | Coordinator asks marketplace agent to search |
| `MARKETPLACE_RESULTS` | Marketplace agent replies |
| `RECOMMEND_BEST` | Coordinator asks RecommendationAgent to decide |
| `RECOMMENDATION_RESULT` | RecommendationAgent replies |
| `RANK_DEALS` | Coordinator asks ValueRankerAgent to rank |
| `RANKED_DEALS` | ValueRankerAgent replies |
| `PRESENT_RECOMMENDATION` | Coordinator asks OutputAgent to present final output |

## Scenario 1: software deal search

### High-level flow

```text
launcher.py
-> request.json
-> UserInterfaceAgent
-> SoftwareCoordinatorAgent
-> OfficialStoreAgent
-> AuthorizedResellerAgent
-> GrayMarketAgent
-> RecommendationAgent
-> SoftwareCoordinatorAgent
-> OutputAgent
```

### Detailed flow

1. User starts `launcher.py`.
2. User chooses software deal search.
3. User enters a title.
4. `launcher.py` writes `request.json`.
5. `UserInterfaceAgent` reads the request and sends it to `SoftwareCoordinatorAgent`.
6. `SoftwareCoordinatorAgent` resolves the title with `app/matching.py`.
7. If the title is ambiguous, the system asks the user to choose an exact title.
8. If the title is resolved, the coordinator queries source agents.
9. `OfficialStoreAgent` returns official deals.
10. `AuthorizedResellerAgent` tries CheapShark by default.
11. If CheapShark fails or returns no usable exact-title deals, the authorized reseller agent falls back to mock data.
12. `GrayMarketAgent` returns gray-market deals with risk warnings.
13. `RecommendationAgent` selects the best legitimate EUR-comparable deal.
14. `OutputAgent` prints the result and writes BDI traces.

### Software title safety

The system uses controlled title resolution before live source lookup.

Example:

```text
User input: crimson
Result: ambiguous
Choices:
- Crimson Desert
- Crimson Desert Deluxe Edition
```

The system does not query CheapShark until the user chooses an exact title.

After exact resolution, CheapShark is queried by exact gameID lookup. This prevents related products such as Deluxe Pack or Digital Deluxe from being ranked as the base game.

### Software decision making

The software scenario contains several non-trivial decisions:

| Agent | Decision |
|---|---|
| `SoftwareCoordinatorAgent` | Decide whether to handle ambiguity, not found, or query sources |
| `AuthorizedResellerAgent` | Decide whether to use CheapShark, fallback to mock, or return no results |
| `RecommendationAgent` | Decide the best legitimate deal and warn about gray-market risk |

## Scenario 2: local console search

### High-level flow

```text
launcher.py
-> request.json
-> UserInterfaceAgent
-> LocalCoordinatorAgent
-> OfficialStoreAgent
-> MarketplaceAgent
-> ValueRankerAgent
-> LocalCoordinatorAgent
-> OutputAgent
```

### Detailed flow

1. User starts `launcher.py`.
2. User chooses local console search.
3. User enters product name, max price, and radius.
4. `launcher.py` writes `request.json`.
5. `UserInterfaceAgent` sends the request to `LocalCoordinatorAgent`.
6. `LocalCoordinatorAgent` resolves product ambiguity.
7. If ambiguous, it asks the user to choose an exact console edition.
8. If resolved, it queries official and marketplace source agents.
9. `OfficialStoreAgent` returns official console offers.
10. `MarketplaceAgent` returns local marketplace offers filtered by max price and radius.
11. `ValueRankerAgent` ranks all returned deals.
12. `OutputAgent` prints best overall deal, best official deal, best local pickup deal, top 3 ranked deals, and warnings.

### Console title safety

Example:

```text
User input: Playstation
Result: ambiguous
Choices:
- PlayStation 5 Digital Edition
- PlayStation 5 Disc Edition
```

The system does not mix Disc and Digital editions after exact resolution.

### Console decision making

The local console scenario contains these decisions:

| Agent | Decision |
|---|---|
| `LocalCoordinatorAgent` | Resolve product, handle ambiguity, or query sources |
| `MarketplaceAgent` | Apply price and radius filters |
| `ValueRankerAgent` | Rank by price, shipping, trust, and distance |
| `OutputAgent` | Show warnings for used, refurbished, and lower-trust deals |

## Source adapter architecture

Source adapters live in:

```text
app/sources/
```

| File | Responsibility |
|---|---|
| `base.py` | Defines the common `DealSource` interface |
| `mock_sources.py` | Wraps deterministic mock dictionaries |
| `cheapshark_source.py` | Calls CheapShark and maps live data into project deal format |

The source adapter interface is:

```python
source.search_deals(title, **filters)
```

This keeps external source logic out of agent coordination logic.

## CheapShark integration architecture

CheapShark is used only in the software scenario.

The correct flow is:

```text
Resolved project title
-> CheapShark /games search
-> exact title match
-> exact CheapShark gameID
-> game details and deals for that exact gameID
-> map deals
-> convert USD to EUR
-> pass to RecommendationAgent
```

The project does not use CheapShark for local console search.

## Currency conversion architecture

Currency conversion lives in:

```text
app/currency/
```

| File | Responsibility |
|---|---|
| `ecb_rate_source.py` | Fetch and parse ECB USD reference rate |
| `converter.py` | Convert USD prices to EUR and annotate deals |

The conversion flow is:

```text
CheapShark USD price
-> resolve USD to EUR rate
-> use ECB if available
-> use configured fallback if ECB fails and fallback is allowed
-> write converted EUR price
-> preserve original USD price and conversion metadata
```

A converted deal includes fields such as:

```text
price_usd
original_price_usd
price_eur
currency_conversion_applied
conversion_rate
conversion_rate_source
conversion_rate_date
```

## BDI architecture

BDI structures live in:

```text
app/bdi.py
```

The key classes are:

| Class | Meaning |
|---|---|
| `Goal` | What an agent wants to achieve |
| `Plan` | An action option |
| `BDIState` | Beliefs, goals, and plans for one decision |
| `PlanDecision` | Selected plan and traceable reasoning output |

BDI traces are written by:

```text
app/bdi_trace_store.py
```

The trace file is:

```text
bdi_trace.json
```

The trace records:

```text
agent_name
beliefs
goals
considered_plans
selected_plan
reason
```

## BDI-enabled agents

| Agent | BDI role |
|---|---|
| `SoftwareCoordinatorAgent` | Title resolution and source-query plan selection |
| `LocalCoordinatorAgent` | Product resolution and local source-query plan selection |
| `AuthorizedResellerAgent` | Real source, mock fallback, and failure handling |
| `RecommendationAgent` | Legitimate deal selection and gray-market avoidance |
| `ValueRankerAgent` | Local console ranking decision |

## Request and response handoff

The system uses files for launcher-to-agent handoff because the user interface is a simple command-line launcher.

| File | Direction |
|---|---|
| `request.json` | `launcher.py` writes, `UserInterfaceAgent` reads |
| `runtime_response.json` | `OutputAgent` writes, `launcher.py` reads |
| `bdi_trace.json` | `OutputAgent` appends BDI evidence |

The runtime response file is temporary and may disappear after the launcher reads it. That is normal.

## Why the system uses both live and mock data

The project uses live and mock data together for practical reasons:

- CheapShark makes the software scenario more realistic.
- Mock data keeps the demo stable if a live source is unavailable.
- Local console search remains mock-based because CheapShark is a PC game source, not a local console marketplace.
- Gray-market examples remain mock-based so the risk-warning behavior is deterministic.

## Key limitations

The implementation intentionally has limits:

- It does not support arbitrary software titles outside the internal catalog.
- CheapShark is queried only after internal title resolution.
- The project does not verify region locks or activation restrictions.
- The project does not make purchases.
- The project does not scrape websites.
- The local console scenario uses mock local marketplace data.
- ECB rates are reference rates, not transaction rates.
- The manual fallback exchange rate is configured for demo stability, not for production financial use.

