import json

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message

from app.matching import resolve_catalog_key
from app.mock_data import MARKETPLACE_DEALS
from app.protocols import MARKETPLACE_RESULTS, SEARCH_MARKETPLACES


class MarketplaceAgent(Agent):
    class ReceiveSearchBehaviour(CyclicBehaviour):
        async def run(self) -> None:
            msg = await self.receive(timeout=10)
            if msg is None:
                return

            protocol = msg.get_metadata("protocol")
            if protocol != SEARCH_MARKETPLACES:
                return

            try:
                payload = json.loads(msg.body)
            except json.JSONDecodeError:
                print("[MarketplaceAgent] Received invalid JSON payload.")
                return

            product_name = payload.get("product_name")
            max_price = payload.get("max_price")
            radius_km = payload.get("radius_km")
            match_mode = payload.get("match_mode", "fuzzy")

            if not isinstance(product_name, str) or not product_name.strip():
                print("[MarketplaceAgent] Missing product name.")
                return

            if match_mode not in {"fuzzy", "exact"}:
                print("[MarketplaceAgent] Invalid match_mode.")
                return

            match_result = resolve_catalog_key(
                product_name,
                MARKETPLACE_DEALS.keys(),
                match_mode=match_mode,
            )
            resolved_title = match_result["resolved_key"]
            deals = MARKETPLACE_DEALS.get(resolved_title, []) if resolved_title else []

            filtered_deals = []
            for deal in deals:
                if isinstance(max_price, (int, float)) and deal["price_eur"] > float(max_price):
                    continue
                if isinstance(radius_km, (int, float)) and deal.get("distance_km", 999999) > float(radius_km):
                    continue
                filtered_deals.append(deal)

            reply = Message(to=str(msg.sender))
            reply.set_metadata("performative", "inform")
            reply.set_metadata("protocol", MARKETPLACE_RESULTS)
            reply.body = json.dumps(
                {
                    "search_title": product_name,
                    "resolved_title": resolved_title,
                    "match_status": match_result["status"],
                    "suggestions": match_result["suggestions"],
                    "deals": filtered_deals,
                }
            )

            await self.send(reply)

            if resolved_title:
                print(
                    f"[MarketplaceAgent] Returned {len(filtered_deals)} marketplace deal(s) for {resolved_title}."
                )
            elif match_result["status"] == "ambiguous":
                print(
                    f"[MarketplaceAgent] Ambiguous product name '{product_name}'. Suggestions: {match_result['suggestions']}"
                )
            else:
                print(f"[MarketplaceAgent] No match found for '{product_name}'.")

    async def setup(self) -> None:
        print(f"[MarketplaceAgent] Started as {self.jid}")
        self.add_behaviour(self.ReceiveSearchBehaviour())
