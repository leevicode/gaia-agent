import json

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message

from app.protocols import RECOMMEND_BEST, RECOMMENDATION_RESULT


class RecommendationAgent(Agent):
    class ReceiveRecommendationRequestBehaviour(CyclicBehaviour):
        async def run(self) -> None:
            msg = await self.receive(timeout=10)
            if msg is None:
                return

            protocol = msg.get_metadata("protocol")
            if protocol != RECOMMEND_BEST:
                return

            try:
                payload = json.loads(msg.body)
            except json.JSONDecodeError:
                print("[RecommendationAgent] Received invalid JSON payload.")
                return

            game_title = payload.get("game_title")
            deals = payload.get("deals", [])

            legitimate_deals = [
                deal for deal in deals if deal.get("source_type") != "gray_market"
            ]
            gray_market_deals = [
                deal for deal in deals if deal.get("source_type") == "gray_market"
            ]

            if legitimate_deals:
                best_legitimate_deal = min(
                    legitimate_deals,
                    key=lambda deal: (deal["price_eur"], -deal["trust_score"]),
                )
            else:
                best_legitimate_deal = None

            if gray_market_deals:
                cheapest_gray_market_deal = min(
                    gray_market_deals,
                    key=lambda deal: (deal["price_eur"], -deal["trust_score"]),
                )
            else:
                cheapest_gray_market_deal = None

            reply = Message(to=str(msg.sender))
            reply.set_metadata("performative", "inform")
            reply.set_metadata("protocol", RECOMMENDATION_RESULT)
            reply.body = json.dumps(
                {
                    "game_title": game_title,
                    "best_legitimate_deal": best_legitimate_deal,
                    "gray_market_warning_deal": cheapest_gray_market_deal,
                }
            )

            await self.send(reply)

            if best_legitimate_deal is None:
                print(f"[RecommendationAgent] No legitimate deal found for {game_title}.")
            else:
                print(
                    f"[RecommendationAgent] Selected best legitimate deal for {game_title}: "
                    f"{best_legitimate_deal['store']} - €{best_legitimate_deal['price_eur']}"
                )

    async def setup(self) -> None:
        print(f"[RecommendationAgent] Started as {self.jid}")
        self.add_behaviour(self.ReceiveRecommendationRequestBehaviour())
