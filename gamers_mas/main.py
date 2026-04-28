from app.python_guard import enforce_python_312

enforce_python_312()

import asyncio

import spade

from app.agents.authorized_reseller_agent import AuthorizedResellerAgent
from app.agents.gray_market_agent import GrayMarketAgent
from app.agents.local_coordinator_agent import LocalCoordinatorAgent
from app.agents.marketplace_agent import MarketplaceAgent
from app.agents.official_store_agent import OfficialStoreAgent
from app.agents.output_agent import OutputAgent
from app.agents.recommendation_agent import RecommendationAgent
from app.agents.software_coordinator_agent import SoftwareCoordinatorAgent
from app.agents.user_interface_agent import UserInterfaceAgent
from app.agents.value_ranker_agent import ValueRankerAgent
from app.request_bus import clear_request_file
from app.runtime_response import clear_response_file
from app.settings import (
    AUTHORIZED_RESELLER_AGENT_JID,
    AUTHORIZED_RESELLER_PASSWORD,
    GRAY_MARKET_AGENT_JID,
    GRAY_MARKET_AGENT_PASSWORD,
    LOCAL_COORDINATOR_JID,
    LOCAL_COORDINATOR_PASSWORD,
    MARKETPLACE_AGENT_JID,
    MARKETPLACE_AGENT_PASSWORD,
    OFFICIAL_STORE_AGENT_JID,
    OFFICIAL_STORE_AGENT_PASSWORD,
    OUTPUT_AGENT_JID,
    OUTPUT_AGENT_PASSWORD,
    RECOMMENDATION_AGENT_JID,
    RECOMMENDATION_AGENT_PASSWORD,
    SOFTWARE_COORDINATOR_JID,
    SOFTWARE_COORDINATOR_PASSWORD,
    USER_AGENT_JID,
    USER_AGENT_PASSWORD,
    VALUE_RANKER_AGENT_JID,
    VALUE_RANKER_PASSWORD,
)


async def main() -> None:
    clear_request_file()
    clear_response_file()

    started_agents = []

    agents = [
        OfficialStoreAgent(
            OFFICIAL_STORE_AGENT_JID,
            OFFICIAL_STORE_AGENT_PASSWORD,
        ),
        AuthorizedResellerAgent(
            AUTHORIZED_RESELLER_AGENT_JID,
            AUTHORIZED_RESELLER_PASSWORD,
        ),
        GrayMarketAgent(
            GRAY_MARKET_AGENT_JID,
            GRAY_MARKET_AGENT_PASSWORD,
        ),
        MarketplaceAgent(
            MARKETPLACE_AGENT_JID,
            MARKETPLACE_AGENT_PASSWORD,
        ),
        ValueRankerAgent(
            VALUE_RANKER_AGENT_JID,
            VALUE_RANKER_PASSWORD,
        ),
        RecommendationAgent(
            RECOMMENDATION_AGENT_JID,
            RECOMMENDATION_AGENT_PASSWORD,
        ),
        OutputAgent(
            OUTPUT_AGENT_JID,
            OUTPUT_AGENT_PASSWORD,
        ),
        SoftwareCoordinatorAgent(
            SOFTWARE_COORDINATOR_JID,
            SOFTWARE_COORDINATOR_PASSWORD,
        ),
        LocalCoordinatorAgent(
            LOCAL_COORDINATOR_JID,
            LOCAL_COORDINATOR_PASSWORD,
        ),
        UserInterfaceAgent(
            USER_AGENT_JID,
            USER_AGENT_PASSWORD,
        ),
    ]

    try:
        for agent in agents:
            await agent.start(auto_register=False)
            started_agents.append(agent)

        print("[Main] MAS service is running.")
        print("[Main] Agents will stay idle between requests.")
        print("[Main] Submit requests with launcher.py and stop this service with Ctrl+C.")

        while True:
            await asyncio.sleep(3600)

    finally:
        for agent in reversed(started_agents):
            await agent.stop()

        clear_request_file()
        clear_response_file()
        print("[Main] MAS service stopped cleanly.")


if __name__ == "__main__":
    try:
        spade.run(main())
    except KeyboardInterrupt:
        print("[Main] Shutdown requested by user.")
