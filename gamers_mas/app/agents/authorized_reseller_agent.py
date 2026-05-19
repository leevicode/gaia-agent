import json
from typing import Any

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message

from app.bdi import BDIState, Goal, Plan
from app.matching import resolve_catalog_key
from app.protocols import AUTHORIZED_RESULTS, SEARCH_AUTHORIZED
from app.sources.cheapshark_source import CheapSharkSource
from app.sources.mock_sources import MockAuthorizedResellerSource


def build_authorized_source_bdi_state(
    agent_name: str,
    game_title: str,
    match_mode: str,
    real_source_enabled: bool,
    real_source_available: bool,
    real_source_returned_deals: bool,
    mock_fallback_available: bool,
    real_source_error: str | None = None,
) -> BDIState:
    state = BDIState(agent_name=agent_name)

    state.set_belief("game_title", game_title)
    state.set_belief("match_mode", match_mode)
    state.set_belief("source_type", "authorized_reseller")
    state.set_belief("real_source_enabled", real_source_enabled)
    state.set_belief("real_source_available", real_source_available)
    state.set_belief("real_source_returned_deals", real_source_returned_deals)
    state.set_belief("mock_fallback_available", mock_fallback_available)
    state.set_belief("mock_source_available", True)
    state.set_belief("preserve_demo_stability", True)
    state.set_belief("real_source_error", real_source_error)

    state.add_goal(
        Goal(
            name="find_authorized_reseller_deals",
            priority=10,
            description="Find authorized reseller deals for the requested game.",
        )
    )
    state.add_goal(
        Goal(
            name="preserve_demo_stability",
            priority=9,
            description="Keep the demo stable even when real sources are unavailable.",
        )
    )
    state.add_goal(
        Goal(
            name="prepare_for_real_source_integration",
            priority=8,
            description="Keep the agent ready for later real data source integration.",
        )
    )

    state.add_plan(
        Plan(
            name="query_real_source",
            trigger="real_source_enabled_available_and_useful",
            priority=10,
            description="Query the real authorized reseller source.",
        )
    )
    state.add_plan(
        Plan(
            name="fallback_to_mock_source",
            trigger="real_source_not_useful_with_mock_fallback",
            priority=9,
            description="Use mock data when the real source is unavailable, fails, or returns no deals.",
        )
    )
    state.add_plan(
        Plan(
            name="use_mock_source",
            trigger="real_source_disabled",
            priority=8,
            description="Use mock authorized reseller data for stable demonstration.",
        )
    )
    state.add_plan(
        Plan(
            name="return_no_results",
            trigger="real_source_not_useful_without_mock_fallback",
            priority=7,
            description="Return no results when real source is enabled but no fallback is allowed.",
        )
    )

    return state


def select_authorized_source_plan(state: BDIState):
    real_source_enabled = state.get_belief("real_source_enabled", False)
    real_source_available = state.get_belief("real_source_available", False)
    real_source_returned_deals = state.get_belief("real_source_returned_deals", False)
    mock_fallback_available = state.get_belief("mock_fallback_available", True)

    if not real_source_enabled:
        return state.select_highest_priority_plan(
            trigger="real_source_disabled",
            reason=(
                "Real authorized reseller integration is disabled, "
                "so the agent uses mock data for the current MAS demonstration."
            ),
        )

    if real_source_available and real_source_returned_deals:
        return state.select_highest_priority_plan(
            trigger="real_source_enabled_available_and_useful",
            reason=(
                "A real authorized reseller source is enabled, available, and returned deals, "
                "so the agent selects the real-source plan."
            ),
        )

    if mock_fallback_available:
        return state.select_highest_priority_plan(
            trigger="real_source_not_useful_with_mock_fallback",
            reason=(
                "The real authorized reseller source is enabled but unavailable, failed, "
                "or returned no deals, so the agent falls back to mock data to preserve demo stability."
            ),
        )

    return state.select_highest_priority_plan(
        trigger="real_source_not_useful_without_mock_fallback",
        reason=(
            "The real authorized reseller source is enabled but did not produce usable deals, "
            "and mock fallback is disabled, so the agent returns no results."
        ),
    )


def build_mock_authorized_reseller_result(
    game_title: str,
    match_mode: str,
    source: MockAuthorizedResellerSource,
) -> tuple[dict[str, Any], str | None, list[dict]]:
    match_result = resolve_catalog_key(
        game_title,
        source.deal_catalog.keys(),
        match_mode=match_mode,
    )

    resolved_title = match_result["resolved_key"]

    if resolved_title:
        deals = source.search_deals(resolved_title)
    else:
        deals = []

    return match_result, resolved_title, deals


def build_authorized_reseller_search_result(
    game_title: str,
    match_mode: str = "fuzzy",
    mock_source: MockAuthorizedResellerSource | None = None,
    real_source: CheapSharkSource | None = None,
    real_source_enabled: bool = False,
    mock_fallback_available: bool = True,
    cheapshark_timeout_seconds: float = 8.0,
    enable_currency_conversion: bool = True,
    currency_rate_provider: str = "ecb",
    currency_rate_timeout_seconds: float = 8.0,
    allow_currency_fallback_rate: bool = True,
    fallback_usd_to_eur_rate: float | None = None,
    fallback_usd_to_eur_rate_source: str = "manual_fallback_rate",
    fallback_usd_to_eur_rate_date: str = "not_specified",
) -> dict:
    if mock_source is None:
        mock_source = MockAuthorizedResellerSource()

    real_source_deals = []
    real_source_available = False
    real_source_error = None

    if real_source_enabled:
        if real_source is None:
            real_source = CheapSharkSource(
                timeout_seconds=cheapshark_timeout_seconds,
                enable_currency_conversion=enable_currency_conversion,
                currency_rate_provider=currency_rate_provider,
                currency_rate_timeout_seconds=currency_rate_timeout_seconds,
                allow_currency_fallback_rate=allow_currency_fallback_rate,
                fallback_usd_to_eur_rate=fallback_usd_to_eur_rate,
                fallback_usd_to_eur_rate_source=fallback_usd_to_eur_rate_source,
                fallback_usd_to_eur_rate_date=fallback_usd_to_eur_rate_date,
            )

        try:
            real_source_deals = real_source.search_deals(game_title)
            real_source_available = True
        except Exception as exc:
            real_source_error = str(exc)
            real_source_deals = []
            real_source_available = False

    bdi_state = build_authorized_source_bdi_state(
        agent_name="AuthorizedResellerAgent",
        game_title=game_title,
        match_mode=match_mode,
        real_source_enabled=real_source_enabled,
        real_source_available=real_source_available,
        real_source_returned_deals=len(real_source_deals) > 0,
        mock_fallback_available=mock_fallback_available,
        real_source_error=real_source_error,
    )
    bdi_decision = select_authorized_source_plan(bdi_state)

    selected_plan = bdi_decision.selected_plan

    if selected_plan == "query_real_source":
        return {
            "search_title": game_title,
            "resolved_title": game_title,
            "match_status": "resolved",
            "suggestions": [],
            "deals": real_source_deals,
            "source_adapter": real_source.source_name if real_source else "cheapshark",
            "real_source_error": None,
            "bdi_trace": bdi_decision.to_dict(),
        }

    if selected_plan == "return_no_results":
        return {
            "search_title": game_title,
            "resolved_title": None,
            "match_status": "not_found",
            "suggestions": [],
            "deals": [],
            "source_adapter": "none",
            "real_source_error": real_source_error,
            "bdi_trace": bdi_decision.to_dict(),
        }

    match_result, resolved_title, deals = build_mock_authorized_reseller_result(
        game_title=game_title,
        match_mode=match_mode,
        source=mock_source,
    )

    return {
        "search_title": game_title,
        "resolved_title": resolved_title,
        "match_status": match_result["status"],
        "suggestions": match_result["suggestions"],
        "deals": deals,
        "source_adapter": mock_source.source_name,
        "real_source_error": real_source_error,
        "bdi_trace": bdi_decision.to_dict(),
    }


class AuthorizedResellerAgent(Agent):
    class ReceiveSearchBehaviour(CyclicBehaviour):
        async def run(self) -> None:
            msg = await self.receive(timeout=10)
            if msg is None:
                return

            protocol = msg.get_metadata("protocol")
            if protocol != SEARCH_AUTHORIZED:
                return

            try:
                payload = json.loads(msg.body)
            except json.JSONDecodeError:
                print("[AuthorizedResellerAgent] Received invalid JSON payload.")
                return

            game_title = payload.get("game_title")
            match_mode = payload.get("match_mode", "fuzzy")

            if not isinstance(game_title, str) or not game_title.strip():
                print("[AuthorizedResellerAgent] Missing game title.")
                return

            if match_mode not in {"fuzzy", "exact"}:
                print("[AuthorizedResellerAgent] Invalid match_mode.")
                return

            from app.settings import (
                ALLOW_CURRENCY_FALLBACK_RATE,
                CHEAPSHARK_TIMEOUT_SECONDS,
                CURRENCY_RATE_PROVIDER,
                CURRENCY_RATE_TIMEOUT_SECONDS,
                ENABLE_CURRENCY_CONVERSION,
                FALLBACK_USD_TO_EUR_RATE,
                FALLBACK_USD_TO_EUR_RATE_DATE,
                FALLBACK_USD_TO_EUR_RATE_SOURCE,
                USE_REAL_CHEAPSHARK,
            )

            result = build_authorized_reseller_search_result(
                game_title=game_title.strip(),
                match_mode=match_mode,
                real_source_enabled=USE_REAL_CHEAPSHARK,
                mock_fallback_available=True,
                cheapshark_timeout_seconds=CHEAPSHARK_TIMEOUT_SECONDS,
                enable_currency_conversion=ENABLE_CURRENCY_CONVERSION,
                currency_rate_provider=CURRENCY_RATE_PROVIDER,
                currency_rate_timeout_seconds=CURRENCY_RATE_TIMEOUT_SECONDS,
                allow_currency_fallback_rate=ALLOW_CURRENCY_FALLBACK_RATE,
                fallback_usd_to_eur_rate=FALLBACK_USD_TO_EUR_RATE,
                fallback_usd_to_eur_rate_source=FALLBACK_USD_TO_EUR_RATE_SOURCE,
                fallback_usd_to_eur_rate_date=FALLBACK_USD_TO_EUR_RATE_DATE,
            )

            reply = Message(to=str(msg.sender))
            reply.set_metadata("performative", "inform")
            reply.set_metadata("protocol", AUTHORIZED_RESULTS)
            reply.body = json.dumps(result)

            await self.send(reply)

            resolved_title = result["resolved_title"]
            deals = result["deals"]
            match_status = result["match_status"]
            suggestions = result["suggestions"]
            bdi_trace = result["bdi_trace"]

            print(
                f"[AuthorizedResellerAgent] BDI selected plan: "
                f"{bdi_trace['selected_plan']}."
            )

            if result.get("real_source_error"):
                print(
                    f"[AuthorizedResellerAgent] Real source error: "
                    f"{result['real_source_error']}"
                )

            if resolved_title:
                print(
                    f"[AuthorizedResellerAgent] Returned {len(deals)} authorized reseller deal(s) for {resolved_title} "
                    f"using {result['source_adapter']}."
                )
            elif match_status == "ambiguous":
                print(
                    f"[AuthorizedResellerAgent] Ambiguous game title '{game_title}'. Suggestions: {suggestions}"
                )
            else:
                print(f"[AuthorizedResellerAgent] No match found for '{game_title}'.")

    async def setup(self) -> None:
        print(f"[AuthorizedResellerAgent] Started as {self.jid}")
        self.add_behaviour(self.ReceiveSearchBehaviour())
