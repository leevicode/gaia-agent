import json

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message

from app.catalogs import get_console_catalog_titles
from app.matching import resolve_catalog_key
from app.protocols import (
    MARKETPLACE_RESULTS,
    OFFICIAL_RESULTS,
    PRESENT_RECOMMENDATION,
    RANK_DEALS,
    RANKED_DEALS,
    REQUEST_LOCAL_CONSOLE_SEARCH,
    SEARCH_MARKETPLACES,
    SEARCH_OFFICIAL,
)
from app.settings import (
    MARKETPLACE_AGENT_JID,
    OFFICIAL_STORE_AGENT_JID,
    OUTPUT_AGENT_JID,
    VALUE_RANKER_AGENT_JID,
)


class LocalCoordinatorAgent(Agent):
    class RequestDealsBehaviour(CyclicBehaviour):
        async def run(self) -> None:
            request_msg = await self.receive(timeout=10)
            if request_msg is None:
                return

            protocol = request_msg.get_metadata("protocol")
            if protocol != REQUEST_LOCAL_CONSOLE_SEARCH:
                return

            try:
                request_data = json.loads(request_msg.body)
            except json.JSONDecodeError:
                print("[LocalCoordinatorAgent] Received invalid JSON request payload.")
                return

            request_id = request_data.get("request_id")
            product_name = request_data.get("product_name")
            max_price = request_data.get("max_price")
            radius_km = request_data.get("radius_km")
            match_mode = request_data.get("match_mode", "fuzzy")

            if not isinstance(request_id, str) or not request_id.strip():
                print("[LocalCoordinatorAgent] Invalid or missing request_id.")
                return

            if not isinstance(product_name, str) or not product_name.strip():
                print("[LocalCoordinatorAgent] Invalid or missing product_name.")
                return

            if not isinstance(max_price, (int, float)):
                print("[LocalCoordinatorAgent] Invalid or missing max_price.")
                return

            if not isinstance(radius_km, (int, float)):
                print("[LocalCoordinatorAgent] Invalid or missing radius_km.")
                return

            if match_mode not in {"fuzzy", "exact"}:
                print("[LocalCoordinatorAgent] Invalid match_mode.")
                return

            request_id = request_id.strip()
            product_name = product_name.strip()

            print(
                f"[LocalCoordinatorAgent] Received request from UserInterfaceAgent for product: {product_name} "
                f"(match_mode={match_mode})"
            )

            catalog_match = resolve_catalog_key(
                product_name,
                get_console_catalog_titles(),
                match_mode=match_mode,
            )

            search_notices = []
            resolved_product_name = catalog_match["resolved_key"]

            if catalog_match["status"] == "ambiguous":
                presentation_msg = Message(to=OUTPUT_AGENT_JID)
                presentation_msg.set_metadata("performative", "inform")
                presentation_msg.set_metadata("protocol", PRESENT_RECOMMENDATION)
                presentation_msg.body = json.dumps(
                    {
                        "request_id": request_id,
                        "scenario": "local_console_search",
                        "product_name": product_name,
                        "match_status": "ambiguous",
                        "search_notices": [],
                        "suggestions": catalog_match["suggestions"],
                    }
                )
                await self.send(presentation_msg)
                print("[LocalCoordinatorAgent] Sent ambiguity choices to OutputAgent before querying sources.")
                return

            if catalog_match["status"] == "not_found":
                presentation_msg = Message(to=OUTPUT_AGENT_JID)
                presentation_msg.set_metadata("performative", "inform")
                presentation_msg.set_metadata("protocol", PRESENT_RECOMMENDATION)
                presentation_msg.body = json.dumps(
                    {
                        "request_id": request_id,
                        "scenario": "local_console_search",
                        "product_name": product_name,
                        "match_status": "not_found",
                        "search_notices": [],
                        "suggestions": [],
                    }
                )
                await self.send(presentation_msg)
                print("[LocalCoordinatorAgent] Sent not-found response to OutputAgent before querying sources.")
                return

            if resolved_product_name and resolved_product_name.casefold() != product_name.casefold():
                search_notices.append(
                    f"Matched '{product_name}' to '{resolved_product_name}'."
                )

            request_payload = {
                "product_name": resolved_product_name,
                "max_price": max_price,
                "radius_km": radius_km,
                "match_mode": "exact",
            }

            official_request = Message(to=OFFICIAL_STORE_AGENT_JID)
            official_request.set_metadata("performative", "request")
            official_request.set_metadata("protocol", SEARCH_OFFICIAL)
            official_request.body = json.dumps(request_payload)
            await self.send(official_request)
            print("[LocalCoordinatorAgent] Sent official store search request.")

            marketplace_request = Message(to=MARKETPLACE_AGENT_JID)
            marketplace_request.set_metadata("performative", "request")
            marketplace_request.set_metadata("protocol", SEARCH_MARKETPLACES)
            marketplace_request.body = json.dumps(request_payload)
            await self.send(marketplace_request)
            print("[LocalCoordinatorAgent] Sent marketplace search request.")

            all_deals = []

            for _ in range(2):
                reply = await self.receive(timeout=10)
                if reply is None:
                    print("[LocalCoordinatorAgent] Timed out waiting for search results.")
                    return

                reply_protocol = reply.get_metadata("protocol")

                try:
                    payload = json.loads(reply.body)
                except json.JSONDecodeError:
                    print("[LocalCoordinatorAgent] Received invalid JSON payload.")
                    return

                deals = payload.get("deals", [])

                if reply_protocol == OFFICIAL_RESULTS:
                    print(
                        f"[LocalCoordinatorAgent] Received {len(deals)} official deal(s)."
                    )
                    all_deals.extend(deals)
                elif reply_protocol == MARKETPLACE_RESULTS:
                    print(
                        f"[LocalCoordinatorAgent] Received {len(deals)} marketplace deal(s)."
                    )
                    all_deals.extend(deals)
                else:
                    print(
                        f"[LocalCoordinatorAgent] Received unexpected protocol: {reply_protocol}"
                    )
                    return

            ranking_request = Message(to=VALUE_RANKER_AGENT_JID)
            ranking_request.set_metadata("performative", "request")
            ranking_request.set_metadata("protocol", RANK_DEALS)
            ranking_request.body = json.dumps(
                {
                    "product_name": resolved_product_name,
                    "deals": all_deals,
                }
            )
            await self.send(ranking_request)
            print("[LocalCoordinatorAgent] Sent combined deals to ValueRankerAgent.")

            ranking_reply = await self.receive(timeout=10)
            if ranking_reply is None:
                print("[LocalCoordinatorAgent] Timed out waiting for ranked deals.")
                return

            ranking_protocol = ranking_reply.get_metadata("protocol")
            if ranking_protocol != RANKED_DEALS:
                print(
                    f"[LocalCoordinatorAgent] Received unexpected protocol: {ranking_protocol}"
                )
                return

            try:
                payload = json.loads(ranking_reply.body)
            except json.JSONDecodeError:
                print("[LocalCoordinatorAgent] Received invalid ranking payload.")
                return

            presentation_msg = Message(to=OUTPUT_AGENT_JID)
            presentation_msg.set_metadata("performative", "inform")
            presentation_msg.set_metadata("protocol", PRESENT_RECOMMENDATION)
            presentation_msg.body = json.dumps(
                {
                    "request_id": request_id,
                    "scenario": "local_console_search",
                    "product_name": payload.get("product_name"),
                    "ranked_deals": payload.get("ranked_deals", []),
                    "search_notices": search_notices,
                }
            )
            await self.send(presentation_msg)
            print("[LocalCoordinatorAgent] Sent ranked deals to OutputAgent.")

    async def setup(self) -> None:
        print(f"[LocalCoordinatorAgent] Started as {self.jid}")
        self.add_behaviour(self.RequestDealsBehaviour())
