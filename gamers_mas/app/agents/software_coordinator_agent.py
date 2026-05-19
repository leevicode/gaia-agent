import json

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message

from app.bdi import BDIState, Goal, Plan
from app.catalogs import get_software_catalog_titles
from app.matching import resolve_catalog_key
from app.protocols import (
    AUTHORIZED_RESULTS,
    GRAY_MARKET_RESULTS,
    OFFICIAL_RESULTS,
    PRESENT_RECOMMENDATION,
    RECOMMEND_BEST,
    RECOMMENDATION_RESULT,
    REQUEST_SOFTWARE_DEAL,
    SEARCH_AUTHORIZED,
    SEARCH_GRAY_MARKET,
    SEARCH_OFFICIAL,
)
from app.settings import (
    AUTHORIZED_RESELLER_AGENT_JID,
    GRAY_MARKET_AGENT_JID,
    OFFICIAL_STORE_AGENT_JID,
    OUTPUT_AGENT_JID,
    RECOMMENDATION_AGENT_JID,
)


def build_software_coordinator_bdi_state(
    agent_name: str,
    game_title: str,
    match_mode: str,
    match_status: str,
    resolved_game_title: str | None,
    suggestions: list[str],
) -> BDIState:
    state = BDIState(agent_name=agent_name)

    state.set_belief("game_title", game_title)
    state.set_belief("match_mode", match_mode)
    state.set_belief("match_status", match_status)
    state.set_belief("resolved_game_title", resolved_game_title)
    state.set_belief("suggestion_count", len(suggestions))
    state.set_belief("title_is_resolved", match_status == "resolved")
    state.set_belief("title_is_ambiguous", match_status == "ambiguous")
    state.set_belief("title_not_found", match_status == "not_found")
    state.set_belief("exact_match_required_before_source_query", True)
    state.set_belief("software_source_agents_available", True)

    state.add_goal(
        Goal(
            name="resolve_software_title",
            priority=10,
            description="Resolve the requested game title before querying source agents.",
        )
    )
    state.add_goal(
        Goal(
            name="avoid_edition_mixups",
            priority=9,
            description="Avoid mixing base games, deluxe editions, or related titles.",
        )
    )
    state.add_goal(
        Goal(
            name="query_sources_only_after_resolution",
            priority=8,
            description="Query source agents only after a single exact title is known.",
        )
    )

    state.add_plan(
        Plan(
            name="handle_ambiguity",
            trigger="ambiguous",
            priority=10,
            description="Ask the user to choose one exact title before querying source agents.",
        )
    )
    state.add_plan(
        Plan(
            name="query_software_sources",
            trigger="resolved",
            priority=9,
            description="Query official, authorized reseller, and gray-market source agents.",
        )
    )
    state.add_plan(
        Plan(
            name="handle_not_found",
            trigger="not_found",
            priority=8,
            description="Report that no matching software title was found.",
        )
    )

    return state


def select_software_coordinator_plan(state: BDIState):
    match_status = state.get_belief("match_status")

    if match_status == "ambiguous":
        return state.select_highest_priority_plan(
            trigger="ambiguous",
            reason=(
                "The requested game title is ambiguous, so the coordinator must ask "
                "the user to choose an exact title before querying source agents."
            ),
        )

    if match_status == "resolved":
        return state.select_highest_priority_plan(
            trigger="resolved",
            reason=(
                "The requested game title resolved to one exact title, so source "
                "agents can be queried safely."
            ),
        )

    return state.select_highest_priority_plan(
        trigger="not_found",
        reason=(
            "The requested game title did not match the software catalog, so no "
            "source agents should be queried."
        ),
    )


def build_software_resolution_result(game_title: str, match_mode: str) -> dict:
    catalog_match = resolve_catalog_key(
        game_title,
        get_software_catalog_titles(),
        match_mode=match_mode,
    )

    resolved_game_title = catalog_match["resolved_key"]
    match_status = catalog_match["status"]
    suggestions = catalog_match["suggestions"]

    search_notices = []
    if resolved_game_title and resolved_game_title.casefold() != game_title.casefold():
        search_notices.append(
            f"Matched '{game_title}' to '{resolved_game_title}'."
        )

    bdi_state = build_software_coordinator_bdi_state(
        agent_name="SoftwareCoordinatorAgent",
        game_title=game_title,
        match_mode=match_mode,
        match_status=match_status,
        resolved_game_title=resolved_game_title,
        suggestions=suggestions,
    )
    bdi_decision = select_software_coordinator_plan(bdi_state)

    return {
        "game_title": game_title,
        "match_mode": match_mode,
        "match_status": match_status,
        "resolved_game_title": resolved_game_title,
        "suggestions": suggestions,
        "search_notices": search_notices,
        "bdi_trace": bdi_decision.to_dict(),
    }


def build_software_presentation_payload(
    request_id: str,
    recommendation_payload: dict,
    search_notices: list[str],
    coordinator_bdi_trace: dict,
    authorized_reseller_bdi_trace: dict | None = None,
) -> dict:
    return {
        "request_id": request_id,
        "game_title": recommendation_payload.get("game_title"),
        "best_legitimate_deal": recommendation_payload.get("best_legitimate_deal"),
        "gray_market_warning_deal": recommendation_payload.get("gray_market_warning_deal"),
        "foreign_currency_deals": recommendation_payload.get("foreign_currency_deals", []),
        "search_notices": search_notices,
        "bdi_trace": coordinator_bdi_trace,
        "authorized_reseller_bdi_trace": authorized_reseller_bdi_trace,
        "recommendation_bdi_trace": recommendation_payload.get("bdi_trace"),
    }


class SoftwareCoordinatorAgent(Agent):
    class RequestDealsBehaviour(CyclicBehaviour):
        async def run(self) -> None:
            request_msg = await self.receive(timeout=10)
            if request_msg is None:
                return

            protocol = request_msg.get_metadata("protocol")
            if protocol != REQUEST_SOFTWARE_DEAL:
                return

            try:
                request_data = json.loads(request_msg.body)
            except json.JSONDecodeError:
                print("[SoftwareCoordinatorAgent] Received invalid JSON request payload.")
                return

            request_id = request_data.get("request_id")
            game_title = request_data.get("game_title")
            match_mode = request_data.get("match_mode", "fuzzy")

            if not isinstance(request_id, str) or not request_id.strip():
                print("[SoftwareCoordinatorAgent] Invalid or missing request_id.")
                return

            if not isinstance(game_title, str) or not game_title.strip():
                print("[SoftwareCoordinatorAgent] Invalid or missing game_title.")
                return

            if match_mode not in {"fuzzy", "exact"}:
                print("[SoftwareCoordinatorAgent] Invalid match_mode.")
                return

            request_id = request_id.strip()
            game_title = game_title.strip()

            print(
                f"[SoftwareCoordinatorAgent] Received request from UserInterfaceAgent for game: {game_title} "
                f"(match_mode={match_mode})"
            )

            resolution_result = build_software_resolution_result(
                game_title=game_title,
                match_mode=match_mode,
            )

            bdi_trace = resolution_result["bdi_trace"]
            match_status = resolution_result["match_status"]
            resolved_game_title = resolution_result["resolved_game_title"]
            suggestions = resolution_result["suggestions"]
            search_notices = resolution_result["search_notices"]

            print(
                f"[SoftwareCoordinatorAgent] BDI selected plan: "
                f"{bdi_trace['selected_plan']}."
            )

            if match_status == "ambiguous":
                presentation_msg = Message(to=OUTPUT_AGENT_JID)
                presentation_msg.set_metadata("performative", "inform")
                presentation_msg.set_metadata("protocol", PRESENT_RECOMMENDATION)
                presentation_msg.body = json.dumps(
                    {
                        "request_id": request_id,
                        "game_title": game_title,
                        "match_status": "ambiguous",
                        "search_notices": [],
                        "suggestions": suggestions,
                        "bdi_trace": bdi_trace,
                    }
                )
                await self.send(presentation_msg)
                print("[SoftwareCoordinatorAgent] Sent ambiguity choices to OutputAgent before querying sources.")
                return

            if match_status == "not_found":
                presentation_msg = Message(to=OUTPUT_AGENT_JID)
                presentation_msg.set_metadata("performative", "inform")
                presentation_msg.set_metadata("protocol", PRESENT_RECOMMENDATION)
                presentation_msg.body = json.dumps(
                    {
                        "request_id": request_id,
                        "game_title": game_title,
                        "match_status": "not_found",
                        "search_notices": [],
                        "suggestions": [],
                        "bdi_trace": bdi_trace,
                    }
                )
                await self.send(presentation_msg)
                print("[SoftwareCoordinatorAgent] Sent not-found response to OutputAgent before querying sources.")
                return

            request_payload = {
                "game_title": resolved_game_title,
                "match_mode": "exact",
            }

            official_request = Message(to=OFFICIAL_STORE_AGENT_JID)
            official_request.set_metadata("performative", "request")
            official_request.set_metadata("protocol", SEARCH_OFFICIAL)
            official_request.body = json.dumps(request_payload)
            await self.send(official_request)
            print("[SoftwareCoordinatorAgent] Sent official store search request.")

            authorized_request = Message(to=AUTHORIZED_RESELLER_AGENT_JID)
            authorized_request.set_metadata("performative", "request")
            authorized_request.set_metadata("protocol", SEARCH_AUTHORIZED)
            authorized_request.body = json.dumps(request_payload)
            await self.send(authorized_request)
            print("[SoftwareCoordinatorAgent] Sent authorized reseller search request.")

            gray_market_request = Message(to=GRAY_MARKET_AGENT_JID)
            gray_market_request.set_metadata("performative", "request")
            gray_market_request.set_metadata("protocol", SEARCH_GRAY_MARKET)
            gray_market_request.body = json.dumps(request_payload)
            await self.send(gray_market_request)
            print("[SoftwareCoordinatorAgent] Sent gray-market search request.")

            all_deals = []
            authorized_reseller_bdi_trace = None

            for _ in range(3):
                reply = await self.receive(timeout=10)
                if reply is None:
                    print("[SoftwareCoordinatorAgent] Timed out waiting for search results.")
                    return

                reply_protocol = reply.get_metadata("protocol")

                try:
                    payload = json.loads(reply.body)
                except json.JSONDecodeError:
                    print("[SoftwareCoordinatorAgent] Received invalid JSON payload.")
                    return

                deals = payload.get("deals", [])

                if reply_protocol == OFFICIAL_RESULTS:
                    print(
                        f"[SoftwareCoordinatorAgent] Received {len(deals)} official deal(s)."
                    )
                    all_deals.extend(deals)
                elif reply_protocol == AUTHORIZED_RESULTS:
                    authorized_reseller_bdi_trace = payload.get("bdi_trace")
                    print(
                        f"[SoftwareCoordinatorAgent] Received {len(deals)} authorized reseller deal(s)."
                    )
                    all_deals.extend(deals)
                elif reply_protocol == GRAY_MARKET_RESULTS:
                    print(
                        f"[SoftwareCoordinatorAgent] Received {len(deals)} gray-market deal(s)."
                    )
                    all_deals.extend(deals)
                else:
                    print(
                        f"[SoftwareCoordinatorAgent] Received unexpected protocol: {reply_protocol}"
                    )
                    return

            recommendation_request = Message(to=RECOMMENDATION_AGENT_JID)
            recommendation_request.set_metadata("performative", "request")
            recommendation_request.set_metadata("protocol", RECOMMEND_BEST)
            recommendation_request.body = json.dumps(
                {
                    "game_title": resolved_game_title,
                    "deals": all_deals,
                }
            )
            await self.send(recommendation_request)
            print("[SoftwareCoordinatorAgent] Sent combined deals to RecommendationAgent.")

            recommendation_reply = await self.receive(timeout=10)
            if recommendation_reply is None:
                print("[SoftwareCoordinatorAgent] Timed out waiting for recommendation.")
                return

            recommendation_protocol = recommendation_reply.get_metadata("protocol")
            if recommendation_protocol != RECOMMENDATION_RESULT:
                print(
                    f"[SoftwareCoordinatorAgent] Received unexpected protocol: {recommendation_protocol}"
                )
                return

            try:
                payload = json.loads(recommendation_reply.body)
            except json.JSONDecodeError:
                print("[SoftwareCoordinatorAgent] Received invalid recommendation payload.")
                return

            presentation_msg = Message(to=OUTPUT_AGENT_JID)
            presentation_msg.set_metadata("performative", "inform")
            presentation_msg.set_metadata("protocol", PRESENT_RECOMMENDATION)
            presentation_msg.body = json.dumps(
                build_software_presentation_payload(
                    request_id=request_id,
                    recommendation_payload=payload,
                    search_notices=search_notices,
                    coordinator_bdi_trace=bdi_trace,
                    authorized_reseller_bdi_trace=authorized_reseller_bdi_trace,
                )
            )
            await self.send(presentation_msg)
            print("[SoftwareCoordinatorAgent] Sent final presentation to OutputAgent.")

    async def setup(self) -> None:
        print(f"[SoftwareCoordinatorAgent] Started as {self.jid}")
        self.add_behaviour(self.RequestDealsBehaviour())