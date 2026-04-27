import json

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message

from app.matching import resolve_catalog_key
from app.mock_data import GRAY_MARKET_DEALS
from app.protocols import GRAY_MARKET_RESULTS, SEARCH_GRAY_MARKET


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

            match_result = resolve_catalog_key(
                game_title,
                GRAY_MARKET_DEALS.keys(),
                match_mode=match_mode,
            )
            resolved_title = match_result["resolved_key"]
            deals = GRAY_MARKET_DEALS.get(resolved_title, []) if resolved_title else []

            reply = Message(to=str(msg.sender))
            reply.set_metadata("performative", "inform")
            reply.set_metadata("protocol", GRAY_MARKET_RESULTS)
            reply.body = json.dumps(
                {
                    "search_title": game_title,
                    "resolved_title": resolved_title,
                    "match_status": match_result["status"],
                    "suggestions": match_result["suggestions"],
                    "deals": deals,
                }
            )

            await self.send(reply)

            if resolved_title:
                print(
                    f"[GrayMarketAgent] Returned {len(deals)} gray-market deal(s) for {resolved_title}."
                )
            elif match_result["status"] == "ambiguous":
                print(
                    f"[GrayMarketAgent] Ambiguous game title '{game_title}'. Suggestions: {match_result['suggestions']}"
                )
            else:
                print(f"[GrayMarketAgent] No match found for '{game_title}'.")

    async def setup(self) -> None:
        print(f"[GrayMarketAgent] Started as {self.jid}")
        self.add_behaviour(self.ReceiveSearchBehaviour())
