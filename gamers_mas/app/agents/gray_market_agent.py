import json

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message

from app.matching import resolve_catalog_key
from app.protocols import GRAY_MARKET_RESULTS, SEARCH_GRAY_MARKET
from app.sources.mock_sources import MockGrayMarketSource


def build_gray_market_search_result(
    game_title: str,
    match_mode: str = "fuzzy",
    source: MockGrayMarketSource | None = None,
) -> dict:
    if source is None:
        source = MockGrayMarketSource()

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

    return {
        "search_title": game_title,
        "resolved_title": resolved_title,
        "match_status": match_result["status"],
        "suggestions": match_result["suggestions"],
        "deals": deals,
        "source_adapter": source.source_name,
    }


class GrayMarketAgent(Agent):
    class ReceiveSearchBehaviour(CyclicBehaviour):
        async def run(self) -> None:
            msg = await self.receive(timeout=10)
            if msg is None:
                return

            protocol = msg.get_metadata("protocol")
            if protocol != SEARCH_GRAY_MARKET:
                return

            try:
                payload = json.loads(msg.body)
            except json.JSONDecodeError:
                print("[GrayMarketAgent] Received invalid JSON payload.")
                return

            game_title = payload.get("game_title")
            match_mode = payload.get("match_mode", "fuzzy")

            if not isinstance(game_title, str) or not game_title.strip():
                print("[GrayMarketAgent] Missing game title.")
                return

            if match_mode not in {"fuzzy", "exact"}:
                print("[GrayMarketAgent] Invalid match_mode.")
                return

            result = build_gray_market_search_result(
                game_title=game_title.strip(),
                match_mode=match_mode,
            )

            reply = Message(to=str(msg.sender))
            reply.set_metadata("performative", "inform")
            reply.set_metadata("protocol", GRAY_MARKET_RESULTS)
            reply.body = json.dumps(result)

            await self.send(reply)

            resolved_title = result["resolved_title"]
            deals = result["deals"]
            match_status = result["match_status"]
            suggestions = result["suggestions"]

            if resolved_title:
                print(
                    f"[GrayMarketAgent] Returned {len(deals)} gray-market deal(s) for {resolved_title}."
                )
            elif match_status == "ambiguous":
                print(
                    f"[GrayMarketAgent] Ambiguous game title '{game_title}'. Suggestions: {suggestions}"
                )
            else:
                print(f"[GrayMarketAgent] No match found for '{game_title}'.")

    async def setup(self) -> None:
        print(f"[GrayMarketAgent] Started as {self.jid}")
        self.add_behaviour(self.ReceiveSearchBehaviour())