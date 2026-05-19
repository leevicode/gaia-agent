import json
from typing import Any

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message

from app.bdi import BDIState, Goal, Plan
from app.protocols import RECOMMEND_BEST, RECOMMENDATION_RESULT


def has_numeric_price_eur(deal: dict[str, Any]) -> bool:
    return isinstance(deal.get("price_eur"), (int, float))


def split_deals_by_legitimacy(deals: list[dict]) -> tuple[list[dict], list[dict]]:
    legitimate_deals = [
        deal for deal in deals
        if deal.get("source_type") != "gray_market"
    ]
    gray_market_deals = [
        deal for deal in deals
        if deal.get("source_type") == "gray_market"
    ]

    return legitimate_deals, gray_market_deals


def split_recommendable_and_foreign_currency_deals(
    legitimate_deals: list[dict],
) -> tuple[list[dict], list[dict]]:
    recommendable_deals = [
        deal for deal in legitimate_deals
        if has_numeric_price_eur(deal)
    ]
    foreign_currency_deals = [
        deal for deal in legitimate_deals
        if not has_numeric_price_eur(deal)
    ]

    return recommendable_deals, foreign_currency_deals


def select_best_legitimate_deal(legitimate_deals: list[dict]) -> dict | None:
    recommendable_deals, _ = split_recommendable_and_foreign_currency_deals(
        legitimate_deals
    )

    if not recommendable_deals:
        return None

    return min(
        recommendable_deals,
        key=lambda deal: (
            deal["price_eur"],
            -deal["trust_score"],
        ),
    )


def select_cheapest_gray_market_warning(gray_market_deals: list[dict]) -> dict | None:
    eur_gray_market_deals = [
        deal for deal in gray_market_deals
        if has_numeric_price_eur(deal)
    ]

    if not eur_gray_market_deals:
        return None

    return min(
        eur_gray_market_deals,
        key=lambda deal: (
            deal["price_eur"],
            -deal["trust_score"],
        ),
    )


def build_recommendation_bdi_state(
    agent_name: str,
    game_title: str,
    deals: list[dict],
) -> BDIState:
    legitimate_deals, gray_market_deals = split_deals_by_legitimacy(deals)
    recommendable_legitimate_deals, foreign_currency_deals = (
        split_recommendable_and_foreign_currency_deals(legitimate_deals)
    )

    state = BDIState(agent_name=agent_name)

    state.set_belief("game_title", game_title)
    state.set_belief("total_deal_count", len(deals))
    state.set_belief("legitimate_deal_count", len(legitimate_deals))
    state.set_belief("recommendable_legitimate_deal_count", len(recommendable_legitimate_deals))
    state.set_belief("foreign_currency_deal_count", len(foreign_currency_deals))
    state.set_belief("gray_market_deal_count", len(gray_market_deals))
    state.set_belief("legitimate_deal_available", len(recommendable_legitimate_deals) > 0)
    state.set_belief("foreign_currency_deal_available", len(foreign_currency_deals) > 0)
    state.set_belief("gray_market_available", len(gray_market_deals) > 0)
    state.set_belief("gray_market_is_risky", True)
    state.set_belief("do_not_compare_usd_as_eur", True)

    state.add_goal(
        Goal(
            name="recommend_best_legitimate_deal",
            priority=10,
            description="Recommend the best available legitimate software deal.",
        )
    )
    state.add_goal(
        Goal(
            name="avoid_recommending_gray_market_as_main_choice",
            priority=9,
            description="Do not recommend gray-market deals as the main answer.",
        )
    )
    state.add_goal(
        Goal(
            name="avoid_mixing_currencies_without_conversion",
            priority=9,
            description="Do not compare USD-only external deals as if they were EUR deals.",
        )
    )
    state.add_goal(
        Goal(
            name="warn_about_gray_market",
            priority=8,
            description="Warn the user when gray-market alternatives exist.",
        )
    )

    state.add_plan(
        Plan(
            name="select_legitimate_and_warn",
            trigger="legitimate_and_gray_market_available",
            priority=10,
            description="Select the best legitimate deal and show gray-market only as a warning.",
        )
    )
    state.add_plan(
        Plan(
            name="select_legitimate_only",
            trigger="only_legitimate_available",
            priority=9,
            description="Select the best legitimate deal when no gray-market warning is needed.",
        )
    )
    state.add_plan(
        Plan(
            name="report_no_legitimate_deal",
            trigger="no_legitimate_deal_available",
            priority=8,
            description="Report that no EUR-comparable legitimate deal is available.",
        )
    )

    return state


def select_recommendation_plan(state: BDIState):
    legitimate_deal_available = state.get_belief("legitimate_deal_available", False)
    gray_market_available = state.get_belief("gray_market_available", False)

    if legitimate_deal_available and gray_market_available:
        return state.select_highest_priority_plan(
            trigger="legitimate_and_gray_market_available",
            reason=(
                "A EUR-comparable legitimate deal exists and gray-market offers are present, "
                "so the agent selects a legitimate deal and treats gray-market offers as warnings."
            ),
        )

    if legitimate_deal_available:
        return state.select_highest_priority_plan(
            trigger="only_legitimate_available",
            reason=(
                "At least one EUR-comparable legitimate deal exists and no gray-market warning is needed."
            ),
        )

    return state.select_highest_priority_plan(
        trigger="no_legitimate_deal_available",
        reason=(
            "No EUR-comparable legitimate deal exists, so the agent cannot make a main recommendation."
        ),
    )


def build_recommendation_result(game_title: str, deals: list[dict]) -> dict:
    legitimate_deals, gray_market_deals = split_deals_by_legitimacy(deals)
    _, foreign_currency_deals = split_recommendable_and_foreign_currency_deals(
        legitimate_deals
    )

    best_legitimate_deal = select_best_legitimate_deal(legitimate_deals)
    gray_market_warning_deal = select_cheapest_gray_market_warning(gray_market_deals)

    bdi_state = build_recommendation_bdi_state(
        agent_name="RecommendationAgent",
        game_title=game_title,
        deals=deals,
    )
    bdi_decision = select_recommendation_plan(bdi_state)

    return {
        "game_title": game_title,
        "best_legitimate_deal": best_legitimate_deal,
        "gray_market_warning_deal": gray_market_warning_deal,
        "foreign_currency_deals": foreign_currency_deals,
        "bdi_trace": bdi_decision.to_dict(),
    }


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

            result = build_recommendation_result(
                game_title=game_title,
                deals=deals,
            )

            reply = Message(to=str(msg.sender))
            reply.set_metadata("performative", "inform")
            reply.set_metadata("protocol", RECOMMENDATION_RESULT)
            reply.body = json.dumps(result)

            await self.send(reply)

            bdi_trace = result["bdi_trace"]
            best_legitimate_deal = result["best_legitimate_deal"]
            foreign_currency_deals = result["foreign_currency_deals"]

            print(
                f"[RecommendationAgent] BDI selected plan: "
                f"{bdi_trace['selected_plan']}."
            )

            if foreign_currency_deals:
                print(
                    f"[RecommendationAgent] Ignored {len(foreign_currency_deals)} foreign-currency deal(s) "
                    "for EUR ranking because no currency conversion is applied."
                )

            if best_legitimate_deal is None:
                print(f"[RecommendationAgent] No EUR-comparable legitimate deal found for {game_title}.")
            else:
                print(
                    f"[RecommendationAgent] Selected best legitimate deal for {game_title}: "
                    f"{best_legitimate_deal['store']} - €{best_legitimate_deal['price_eur']}"
                )

    async def setup(self) -> None:
        print(f"[RecommendationAgent] Started as {self.jid}")
        self.add_behaviour(self.ReceiveRecommendationRequestBehaviour())