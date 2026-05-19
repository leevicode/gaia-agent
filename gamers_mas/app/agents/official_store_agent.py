import json

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message

from app.matching import resolve_catalog_key
from app.protocols import OFFICIAL_RESULTS, SEARCH_OFFICIAL
from app.sources.mock_sources import MockOfficialStoreSource


def build_official_store_search_result(
    search_title: str,
    match_mode: str = "fuzzy",
    max_price: float | None = None,
    source: MockOfficialStoreSource | None = None,
) -> dict:
    if source is None:
        source = MockOfficialStoreSource()

    match_result = resolve_catalog_key(
        search_title,
        source.deal_catalog.keys(),
        match_mode=match_mode,
    )

    resolved_title = match_result["resolved_key"]

    if resolved_title:
        deals = source.search_deals(
            resolved_title,
            max_price=max_price,
        )
    else:
        deals = []

    return {
        "search_title": search_title,
        "resolved_title": resolved_title,
        "match_status": match_result["status"],
        "suggestions": match_result["suggestions"],
        "deals": deals,
        "source_adapter": source.source_name,
    }


class OfficialStoreAgent(Agent):
    class ReceiveSearchBehaviour(CyclicBehaviour):
        async def run(self) -> None:
            msg = await self.receive(timeout=10)
            if msg is None:
                return

            protocol = msg.get_metadata("protocol")
            if protocol != SEARCH_OFFICIAL:
                return

            try:
                payload = json.loads(msg.body)
            except json.JSONDecodeError:
                print("[OfficialStoreAgent] Received invalid JSON payload.")
                return

            search_title = payload.get("game_title") or payload.get("product_name")
            max_price = payload.get("max_price")
            match_mode = payload.get("match_mode", "fuzzy")

            if not isinstance(search_title, str) or not search_title.strip():
                print("[OfficialStoreAgent] Missing search title.")
                return

            if match_mode not in {"fuzzy", "exact"}:
                print("[OfficialStoreAgent] Invalid match_mode.")
                return

            result = build_official_store_search_result(
                search_title=search_title.strip(),
                match_mode=match_mode,
                max_price=max_price,
            )

            reply = Message(to=str(msg.sender))
            reply.set_metadata("performative", "inform")
            reply.set_metadata("protocol", OFFICIAL_RESULTS)
            reply.body = json.dumps(result)

            await self.send(reply)

            resolved_title = result["resolved_title"]
            deals = result["deals"]
            match_status = result["match_status"]
            suggestions = result["suggestions"]

            if resolved_title:
                print(
                    f"[OfficialStoreAgent] Returned {len(deals)} official deal(s) for {resolved_title}."
                )
            elif match_status == "ambiguous":
                print(
                    f"[OfficialStoreAgent] Ambiguous search title '{search_title}'. Suggestions: {suggestions}"
                )
            else:
                print(f"[OfficialStoreAgent] No match found for '{search_title}'.")

    async def setup(self) -> None:
        print(f"[OfficialStoreAgent] Started as {self.jid}")
        self.add_behaviour(self.ReceiveSearchBehaviour())