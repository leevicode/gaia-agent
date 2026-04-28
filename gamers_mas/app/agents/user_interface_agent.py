import asyncio
import json

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message

from app.protocols import REQUEST_LOCAL_CONSOLE_SEARCH, REQUEST_SOFTWARE_DEAL
from app.request_bus import read_request_if_exists
from app.request_loader import validate_request_data
from app.settings import LOCAL_COORDINATOR_JID, SOFTWARE_COORDINATOR_JID


class UserInterfaceAgent(Agent):
    class WatchRequestBehaviour(CyclicBehaviour):
        def __init__(self) -> None:
            super().__init__()
            self.last_processed_request_id = None

        async def run(self) -> None:
            raw_request = read_request_if_exists()
            if raw_request is None:
                await asyncio.sleep(1)
                return

            try:
                request_data = validate_request_data(raw_request)
            except RuntimeError as exc:
                print(f"[UserInterfaceAgent] Ignoring invalid request.json: {exc}")
                await asyncio.sleep(1)
                return

            request_id = request_data["request_id"]
            if request_id == self.last_processed_request_id:
                await asyncio.sleep(1)
                return

            scenario = request_data["scenario"]

            if scenario == "software_deal":
                msg = Message(to=SOFTWARE_COORDINATOR_JID)
                msg.set_metadata("performative", "request")
                msg.set_metadata("protocol", REQUEST_SOFTWARE_DEAL)
                msg.body = json.dumps(request_data)
                await self.send(msg)
                self.last_processed_request_id = request_id
                print(
                    f"[UserInterfaceAgent] Loaded request.json and sent software request for {request_data['game_title']} "
                    f"(match_mode={request_data['match_mode']})."
                )
                await asyncio.sleep(1)
                return

            if scenario == "local_console_search":
                msg = Message(to=LOCAL_COORDINATOR_JID)
                msg.set_metadata("performative", "request")
                msg.set_metadata("protocol", REQUEST_LOCAL_CONSOLE_SEARCH)
                msg.body = json.dumps(request_data)
                await self.send(msg)
                self.last_processed_request_id = request_id
                print(
                    f"[UserInterfaceAgent] Loaded request.json and sent local console request for {request_data['product_name']} "
                    f"(match_mode={request_data['match_mode']})."
                )
                await asyncio.sleep(1)
                return

            await asyncio.sleep(1)

    async def setup(self) -> None:
        print(f"[UserInterfaceAgent] Started as {self.jid}")
        self.add_behaviour(self.WatchRequestBehaviour())
