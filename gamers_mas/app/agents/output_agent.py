import json

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour

from app.bdi_trace_store import append_bdi_traces
from app.protocols import PRESENT_RECOMMENDATION
from app.runtime_response import write_response


def format_foreign_currency_deal(deal: dict) -> str:
    store = deal.get("store", "Unknown store")
    price_usd = deal.get("price_usd")
    currency = deal.get("currency", "USD")
    source_adapter = deal.get("source_adapter", "unknown source")

    if isinstance(price_usd, (int, float)):
        price_text = f"{price_usd:.2f} {currency}"
    else:
        price_text = f"unknown price {currency}"

    return (
        f"{store} - {price_text} | source={source_adapter} | "
        "not compared with EUR results"
    )


def build_foreign_currency_summary(foreign_currency_deals: list[dict]) -> list[str]:
    return [
        format_foreign_currency_deal(deal)
        for deal in foreign_currency_deals
    ]


def format_recommended_legitimate_deal(deal: dict) -> str:
    store = deal.get("store", "Unknown store")
    price_eur = deal.get("price_eur")
    trust_score = deal.get("trust_score")
    source_type = deal.get("source_type")

    if isinstance(price_eur, (int, float)):
        price_text = f"€{price_eur:.2f}"
    else:
        price_text = "unknown EUR price"

    if deal.get("currency_conversion_applied") is True:
        original_price_usd = deal.get("original_price_usd", deal.get("price_usd"))
        conversion_rate = deal.get("conversion_rate")
        conversion_rate_source = deal.get("conversion_rate_source", "unknown rate source")
        conversion_rate_date = deal.get("conversion_rate_date", "unknown date")

        if isinstance(original_price_usd, (int, float)):
            original_text = f"{original_price_usd:.2f} USD"
        else:
            original_text = "unknown USD price"

        if isinstance(conversion_rate, (int, float)):
            rate_text = f"1 USD = {conversion_rate:.6f} EUR"
        else:
            rate_text = "unknown conversion rate"

        return (
            f"Recommended legitimate deal: {store} - {price_text} | "
            f"converted from {original_text} | {rate_text} | "
            f"rate source={conversion_rate_source} | rate date={conversion_rate_date} | "
            f"trust={trust_score} | type={source_type}"
        )

    return (
        f"Recommended legitimate deal: {store} - {price_text} | "
        f"trust={trust_score} | type={source_type}"
    )


def build_software_bdi_trace_list(
    coordinator_bdi_trace: dict | None,
    authorized_reseller_bdi_trace: dict | None,
    recommendation_bdi_trace: dict | None,
) -> list[dict | None]:
    return [
        coordinator_bdi_trace,
        authorized_reseller_bdi_trace,
        recommendation_bdi_trace,
    ]


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
            coordinator_bdi_trace = payload.get("bdi_trace")
            authorized_reseller_bdi_trace = payload.get("authorized_reseller_bdi_trace")
            recommendation_bdi_trace = payload.get("recommendation_bdi_trace")
            value_ranker_bdi_trace = payload.get("value_ranker_bdi_trace")

            if scenario == "local_console_search":
                product_name = payload.get("product_name")
                ranked_deals = payload.get("ranked_deals", [])

                append_bdi_traces(
                    request_id=request_id,
                    scenario="local_console_search",
                    query=product_name,
                    traces=[
                        coordinator_bdi_trace,
                        value_ranker_bdi_trace,
                    ],
                )

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
            foreign_currency_deals = payload.get("foreign_currency_deals", [])

            append_bdi_traces(
                request_id=request_id,
                scenario="software_deal",
                query=game_title,
                traces=build_software_bdi_trace_list(
                    coordinator_bdi_trace=coordinator_bdi_trace,
                    authorized_reseller_bdi_trace=authorized_reseller_bdi_trace,
                    recommendation_bdi_trace=recommendation_bdi_trace,
                ),
            )

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
                        "foreign_currency_deals": foreign_currency_deals,
                        "search_notices": search_notices,
                        "match_status": "not_found",
                    }
                )
                return

            if best_legitimate_deal:
                print(f"  {format_recommended_legitimate_deal(best_legitimate_deal)}")
            else:
                print("  No EUR-comparable legitimate deal found.")

            if foreign_currency_deals:
                print("  Foreign-currency deal(s) found but not used for EUR ranking:")
                for summary in build_foreign_currency_summary(foreign_currency_deals[:3]):
                    print(f"    - {summary}")
                print("  Currency note: no USD-to-EUR conversion has been applied.")

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
                    "foreign_currency_deals": foreign_currency_deals,
                    "search_notices": search_notices,
                }
            )

    async def setup(self) -> None:
        print(f"[OutputAgent] Started as {self.jid}")
        self.add_behaviour(self.ReceivePresentationBehaviour())
