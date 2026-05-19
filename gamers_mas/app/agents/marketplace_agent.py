import json

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message

from app.matching import resolve_catalog_key
from app.protocols import MARKETPLACE_RESULTS, SEARCH_MARKETPLACES
from app.sources.mock_sources import MockMarketplaceSource


def build_marketplace_search_result(
    product_name: str,
    max_price: float | None = None,
    radius_km: float | None = None,
    match_mode: str = "fuzzy",
    source: MockMarketplaceSource | None = None,
) -> dict:
    if source is None:
        source = MockMarketplaceSource()

    match_result = resolve_catalog_key(
        product_name,
        source.deal_catalog.keys(),
        match_mode=match_mode,
    )

    resolved_title = match_result["resolved_key"]

    if resolved_title:
        deals = source.search_deals(
            resolved_title,
            max_price=max_price,
            radius_km=radius_km,
        )
    else:
        deals = []

    return {
        "search_title": product_name,
        "resolved_title": resolved_title,
        "match_status": match_result["status"],
        "suggestions": match_result["suggestions"],
        "deals": deals,
        "source_adapter": source.source_name,
    }


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

            result = build_marketplace_search_result(
                product_name=product_name.strip(),
                max_price=max_price,
                radius_km=radius_km,
                match_mode=match_mode,
            )

            reply = Message(to=str(msg.sender))
            reply.set_metadata("performative", "inform")
            reply.set_metadata("protocol", MARKETPLACE_RESULTS)
            reply.body = json.dumps(result)

            await self.send(reply)

            resolved_title = result["resolved_title"]
            deals = result["deals"]
            match_status = result["match_status"]
            suggestions = result["suggestions"]

            if resolved_title:
                print(
                    f"[MarketplaceAgent] Returned {len(deals)} marketplace deal(s) for {resolved_title}."
                )
            elif match_status == "ambiguous":
                print(
                    f"[MarketplaceAgent] Ambiguous product name '{product_name}'. Suggestions: {suggestions}"
                )
            else:
                print(f"[MarketplaceAgent] No match found for '{product_name}'.")

    async def setup(self) -> None:
        print(f"[MarketplaceAgent] Started as {self.jid}")
        self.add_behaviour(self.ReceiveSearchBehaviour())