import json

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message

from app.bdi import BDIState, Goal, Plan
from app.protocols import RANK_DEALS, RANKED_DEALS


def deal_value_key(deal: dict) -> tuple:
    return (
        deal["price_eur"] + deal.get("shipping_eur", 0.0),
        -deal.get("trust_score", 0.0),
        deal.get("distance_km", 999999.0),
    )


def rank_deals_by_value(deals: list[dict]) -> list[dict]:
    return sorted(
        deals,
        key=deal_value_key,
    )


def count_used_or_refurbished_deals(deals: list[dict]) -> int:
    count = 0

    for deal in deals:
        condition = str(deal.get("condition", "")).lower()
        if "used" in condition or "refurbished" in condition:
            count += 1

    return count


def count_lower_trust_deals(deals: list[dict], threshold: float = 0.8) -> int:
    return sum(
        1 for deal in deals
        if deal.get("trust_score", 0.0) < threshold
    )


def build_value_ranker_bdi_state(
    agent_name: str,
    product_name: str,
    deals: list[dict],
) -> BDIState:
    state = BDIState(agent_name=agent_name)

    state.set_belief("product_name", product_name)
    state.set_belief("total_deal_count", len(deals))
    state.set_belief("deals_available", len(deals) > 0)
    state.set_belief(
        "used_or_refurbished_deal_count",
        count_used_or_refurbished_deals(deals),
    )
    state.set_belief(
        "lower_trust_deal_count",
        count_lower_trust_deals(deals),
    )
    state.set_belief(
        "ranking_uses_price_shipping_trust_and_distance",
        True,
    )

    state.add_goal(
        Goal(
            name="rank_local_console_deals_by_value",
            priority=10,
            description="Rank available local console deals using value-related factors.",
        )
    )
    state.add_goal(
        Goal(
            name="avoid_blindly_selecting_cheapest_offer",
            priority=9,
            description="Consider trust and distance, not only price.",
        )
    )
    state.add_goal(
        Goal(
            name="support_warning_generation",
            priority=8,
            description="Preserve information that helps the output layer warn about risk.",
        )
    )

    state.add_plan(
        Plan(
            name="rank_available_deals",
            trigger="deals_available",
            priority=10,
            description="Rank deals by price plus shipping, then trust, then distance.",
        )
    )
    state.add_plan(
        Plan(
            name="report_no_deals",
            trigger="no_deals_available",
            priority=9,
            description="Report that no deals are available for ranking.",
        )
    )

    return state


def select_value_ranking_plan(state: BDIState):
    deals_available = state.get_belief("deals_available", False)

    if deals_available:
        return state.select_highest_priority_plan(
            trigger="deals_available",
            reason=(
                "Deals are available, so the agent ranks them using price, shipping, "
                "trust, and distance instead of selecting randomly."
            ),
        )

    return state.select_highest_priority_plan(
        trigger="no_deals_available",
        reason=(
            "No deals are available, so the agent cannot produce a ranked list."
        ),
    )


def build_ranking_result(product_name: str, deals: list[dict]) -> dict:
    ranked_deals = rank_deals_by_value(deals)

    bdi_state = build_value_ranker_bdi_state(
        agent_name="ValueRankerAgent",
        product_name=product_name,
        deals=deals,
    )
    bdi_decision = select_value_ranking_plan(bdi_state)

    return {
        "product_name": product_name,
        "ranked_deals": ranked_deals,
        "bdi_trace": bdi_decision.to_dict(),
    }


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

            result = build_ranking_result(
                product_name=product_name,
                deals=deals,
            )

            reply = Message(to=str(msg.sender))
            reply.set_metadata("performative", "inform")
            reply.set_metadata("protocol", RANKED_DEALS)
            reply.body = json.dumps(result)

            await self.send(reply)

            bdi_trace = result["bdi_trace"]
            ranked_deals = result["ranked_deals"]

            print(
                f"[ValueRankerAgent] BDI selected plan: "
                f"{bdi_trace['selected_plan']}."
            )
            print(
                f"[ValueRankerAgent] Ranked {len(ranked_deals)} deal(s) for {product_name}."
            )

    async def setup(self) -> None:
        print(f"[ValueRankerAgent] Started as {self.jid}")
        self.add_behaviour(self.ReceiveRankingRequestBehaviour())