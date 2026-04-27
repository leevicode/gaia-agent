import json

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message

from app.protocols import RANK_DEALS, RANKED_DEALS


class ValueRankerAgent(Agent):
    class ReceiveRankingRequestBehaviour(CyclicBehaviour):
        async def run(self) -> None:
            msg = await self.receive(timeout=10)
            if msg is None:
                return

            protocol = msg.get_metadata("protocol")
            if protocol != RANK_DEALS:
                return

            try:
                payload = json.loads(msg.body)
            except json.JSONDecodeError:
                print("[ValueRankerAgent] Received invalid JSON payload.")
                return

            product_name = payload.get("product_name")
            deals = payload.get("deals", [])

            ranked_deals = sorted(
                deals,
                key=lambda deal: (
                    deal["price_eur"] + deal.get("shipping_eur", 0.0),
                    -deal.get("trust_score", 0.0),
                    deal.get("distance_km", 999999.0),
                ),
            )

            reply = Message(to=str(msg.sender))
            reply.set_metadata("performative", "inform")
            reply.set_metadata("protocol", RANKED_DEALS)
            reply.body = json.dumps(
                {
                    "product_name": product_name,
                    "ranked_deals": ranked_deals,
                }
            )

            await self.send(reply)
            print(
                f"[ValueRankerAgent] Ranked {len(ranked_deals)} deal(s) for {product_name}."
            )

    async def setup(self) -> None:
        print(f"[ValueRankerAgent] Started as {self.jid}")
        self.add_behaviour(self.ReceiveRankingRequestBehaviour())
