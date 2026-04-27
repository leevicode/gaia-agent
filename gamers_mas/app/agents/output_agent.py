import json

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour

from app.protocols import PRESENT_RECOMMENDATION
from app.runtime_response import write_response


class OutputAgent(Agent):
    class ReceivePresentationBehaviour(CyclicBehaviour):
        async def run(self) -> None:
            msg = await self.receive(timeout=10)
            if msg is None:
                return

            protocol = msg.get_metadata("protocol")
            if protocol != PRESENT_RECOMMENDATION:
                return

            try:
                payload = json.loads(msg.body)
            except json.JSONDecodeError:
                print("[OutputAgent] Received invalid JSON payload.")
                return

            request_id = payload.get("request_id")
            scenario = payload.get("scenario")
            search_notices = payload.get("search_notices", [])
            match_status = payload.get("match_status")
            suggestions = payload.get("suggestions", [])

            if scenario == "local_console_search":
                product_name = payload.get("product_name")
                ranked_deals = payload.get("ranked_deals", [])

                print(f"[OutputAgent] Final presentation for {product_name}:")

                if search_notices:
                    print("  Matching notes:")
                    for notice in search_notices:
                        print(f"    - {notice}")

                if match_status == "ambiguous":
                    print("  Matching issue: your input is ambiguous.")
                    if suggestions:
                        print("  Please choose one of these:")
                        for suggestion in suggestions:
                            print(f"    - {suggestion}")

                    write_response(
                        {
                            "status": "ambiguous",
                            "request_id": request_id,
                            "scenario": "local_console_search",
                            "query": product_name,
                            "suggestions": suggestions,
                            "search_notices": search_notices,
                        }
                    )
                    return

                if match_status == "not_found":
                    print("  No matching product found.")
                    write_response(
                        {
                            "status": "ok",
                            "request_id": request_id,
                            "scenario": "local_console_search",
                            "query": product_name,
                            "ranked_deals": [],
                            "search_notices": search_notices,
                            "match_status": "not_found",
                        }
                    )
                    return

                if not ranked_deals:
                    print("  No ranked deals found.")
                    write_response(
                        {
                            "status": "ok",
                            "request_id": request_id,
                            "scenario": "local_console_search",
                            "query": product_name,
                            "ranked_deals": [],
                            "search_notices": search_notices,
                        }
                    )
                    return

                best_overall_deal = ranked_deals[0]

                official_deals = [
                    deal for deal in ranked_deals
                    if deal.get("source_type") == "official"
                ]
                marketplace_deals = [
                    deal for deal in ranked_deals
                    if deal.get("source_type") == "marketplace"
                ]

                best_official_deal = official_deals[0] if official_deals else None

                marketplace_pickup_deals = [
                    deal for deal in marketplace_deals
                    if "distance_km" in deal
                ]
                best_local_pickup_deal = (
                    min(
                        marketplace_pickup_deals,
                        key=lambda deal: (
                            deal.get("distance_km", 999999.0),
                            deal["price_eur"],
                            -deal.get("trust_score", 0.0),
                        ),
                    )
                    if marketplace_pickup_deals
                    else None
                )

                print(
                    f"  Best overall deal: {best_overall_deal['store']} - "
                    f"€{best_overall_deal['price_eur']} | "
                    f"trust={best_overall_deal['trust_score']} | "
                    f"type={best_overall_deal['source_type']} | "
                    f"condition={best_overall_deal['condition']}"
                )

                if best_official_deal:
                    print(
                        f"  Best official deal: {best_official_deal['store']} - "
                        f"€{best_official_deal['price_eur']} | "
                        f"trust={best_official_deal['trust_score']} | "
                        f"condition={best_official_deal['condition']}"
                    )

                if best_local_pickup_deal:
                    print(
                        f"  Best local pickup deal: {best_local_pickup_deal['store']} - "
                        f"€{best_local_pickup_deal['price_eur']} | "
                        f"trust={best_local_pickup_deal['trust_score']} | "
                        f"distance={best_local_pickup_deal['distance_km']} km | "
                        f"condition={best_local_pickup_deal['condition']}"
                    )

                print("  Top 3 ranked deals:")
                for index, deal in enumerate(ranked_deals[:3], start=1):
                    extra = ""
                    if "distance_km" in deal:
                        extra += f" | distance={deal['distance_km']} km"
                    if "shipping_eur" in deal:
                        extra += f" | shipping=€{deal['shipping_eur']}"
                    print(
                        f"    {index}. {deal['store']} - €{deal['price_eur']} | "
                        f"trust={deal['trust_score']} | type={deal['source_type']} | "
                        f"condition={deal['condition']}{extra}"
                    )

                print("  Warnings:")
                warning_count = 0
                for deal in ranked_deals[:5]:
                    condition = str(deal.get("condition", "")).lower()
                    trust_score = deal.get("trust_score", 0.0)

                    if "refurbished" in condition:
                        print(
                            f"    - {deal['store']}: refurbished condition, inspect warranty details."
                        )
                        warning_count += 1

                    elif "used" in condition:
                        print(
                            f"    - {deal['store']}: used condition, verify accessories and wear."
                        )
                        warning_count += 1

                    if trust_score < 0.8:
                        print(
                            f"    - {deal['store']}: lower trust score ({trust_score}), review seller details carefully."
                        )
                        warning_count += 1

                if warning_count == 0:
                    print("    - No obvious warnings in the top ranked deals.")

                write_response(
                    {
                        "status": "ok",
                        "request_id": request_id,
                        "scenario": "local_console_search",
                        "query": product_name,
                        "best_overall_deal": best_overall_deal,
                        "best_official_deal": best_official_deal,
                        "best_local_pickup_deal": best_local_pickup_deal,
                        "ranked_deals": ranked_deals,
                        "search_notices": search_notices,
                    }
                )
                return

            game_title = payload.get("game_title")
            best_legitimate_deal = payload.get("best_legitimate_deal")
            gray_market_warning_deal = payload.get("gray_market_warning_deal")

            print(f"[OutputAgent] Final presentation for {game_title}:")

            if search_notices:
                print("  Matching notes:")
                for notice in search_notices:
                    print(f"    - {notice}")

            if match_status == "ambiguous":
                print("  Matching issue: your input is ambiguous.")
                if suggestions:
                    print("  Please choose one of these:")
                    for suggestion in suggestions:
                        print(f"    - {suggestion}")

                write_response(
                    {
                        "status": "ambiguous",
                        "request_id": request_id,
                        "scenario": "software_deal",
                        "query": game_title,
                        "suggestions": suggestions,
                        "search_notices": search_notices,
                    }
                )
                return

            if match_status == "not_found":
                print("  No matching title found.")
                write_response(
                    {
                        "status": "ok",
                        "request_id": request_id,
                        "scenario": "software_deal",
                        "query": game_title,
                        "best_legitimate_deal": None,
                        "gray_market_warning_deal": None,
                        "search_notices": search_notices,
                        "match_status": "not_found",
                    }
                )
                return

            if best_legitimate_deal:
                print(
                    f"  Recommended legitimate deal: {best_legitimate_deal['store']} - "
                    f"€{best_legitimate_deal['price_eur']} | "
                    f"trust={best_legitimate_deal['trust_score']} | "
                    f"type={best_legitimate_deal['source_type']}"
                )
            else:
                print("  No legitimate deal found.")

            if gray_market_warning_deal:
                print("  WARNING: Gray-market option detected.")
                print(
                    f"  Cheapest gray-market deal: {gray_market_warning_deal['store']} - "
                    f"€{gray_market_warning_deal['price_eur']} | "
                    f"trust={gray_market_warning_deal['trust_score']} | "
                    f"type={gray_market_warning_deal['source_type']}"
                )
                if gray_market_warning_deal.get("warning"):
                    print(f"  Risk note: {gray_market_warning_deal['warning']}")

            write_response(
                {
                    "status": "ok",
                    "request_id": request_id,
                    "scenario": "software_deal",
                    "query": game_title,
                    "best_legitimate_deal": best_legitimate_deal,
                    "gray_market_warning_deal": gray_market_warning_deal,
                    "search_notices": search_notices,
                }
            )

    async def setup(self) -> None:
        print(f"[OutputAgent] Started as {self.jid}")
        self.add_behaviour(self.ReceivePresentationBehaviour())
