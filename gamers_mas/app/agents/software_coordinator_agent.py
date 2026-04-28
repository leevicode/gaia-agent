import json

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message

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

            catalog_match = resolve_catalog_key(
                game_title,
                get_software_catalog_titles(),
                match_mode=match_mode,
            )

            search_notices = []
            resolved_game_title = catalog_match["resolved_key"]

            if catalog_match["status"] == "ambiguous":
                presentation_msg = Message(to=OUTPUT_AGENT_JID)
                presentation_msg.set_metadata("performative", "inform")
                presentation_msg.set_metadata("protocol", PRESENT_RECOMMENDATION)
                presentation_msg.body = json.dumps(
                    {
                        "request_id": request_id,
                        "game_title": game_title,
                        "match_status": "ambiguous",
                        "search_notices": [],
                        "suggestions": catalog_match["suggestions"],
                    }
                )
                await self.send(presentation_msg)
                print("[SoftwareCoordinatorAgent] Sent ambiguity choices to OutputAgent before querying sources.")
                return

            if catalog_match["status"] == "not_found":
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
                    }
                )
                await self.send(presentation_msg)
                print("[SoftwareCoordinatorAgent] Sent not-found response to OutputAgent before querying sources.")
                return

            if resolved_game_title and resolved_game_title.casefold() != game_title.casefold():
                search_notices.append(
                    f"Matched '{game_title}' to '{resolved_game_title}'."
                )

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
                {
                    "request_id": request_id,
                    "game_title": payload.get("game_title"),
                    "best_legitimate_deal": payload.get("best_legitimate_deal"),
                    "gray_market_warning_deal": payload.get("gray_market_warning_deal"),
                    "search_notices": search_notices,
                }
            )
            await self.send(presentation_msg)
            print("[SoftwareCoordinatorAgent] Sent final presentation to OutputAgent.")

    async def setup(self) -> None:
        print(f"[SoftwareCoordinatorAgent] Started as {self.jid}")
        self.add_behaviour(self.RequestDealsBehaviour())
