import os

from dotenv import load_dotenv


load_dotenv()


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


AGENT_DOMAIN = os.getenv("XMPP_DOMAIN", "localhost")

USER_AGENT_JID = f"user_agent@{AGENT_DOMAIN}"
SOFTWARE_COORDINATOR_JID = f"software_coordinator@{AGENT_DOMAIN}"
LOCAL_COORDINATOR_JID = f"local_coordinator@{AGENT_DOMAIN}"

OFFICIAL_STORE_AGENT_JID = f"official_store_agent@{AGENT_DOMAIN}"
AUTHORIZED_RESELLER_AGENT_JID = f"authorized_reseller_agent@{AGENT_DOMAIN}"
GRAY_MARKET_AGENT_JID = f"gray_market_agent@{AGENT_DOMAIN}"
MARKETPLACE_AGENT_JID = f"marketplace_agent@{AGENT_DOMAIN}"
VALUE_RANKER_AGENT_JID = f"value_ranker_agent@{AGENT_DOMAIN}"

RECOMMENDATION_AGENT_JID = f"recommendation_agent@{AGENT_DOMAIN}"
OUTPUT_AGENT_JID = f"output_agent@{AGENT_DOMAIN}"

USER_AGENT_PASSWORD = require_env("USER_AGENT_PASSWORD")
SOFTWARE_COORDINATOR_PASSWORD = require_env("SOFTWARE_COORDINATOR_PASSWORD")
LOCAL_COORDINATOR_PASSWORD = require_env("LOCAL_COORDINATOR_PASSWORD")

OFFICIAL_STORE_AGENT_PASSWORD = require_env("OFFICIAL_STORE_AGENT_PASSWORD")
AUTHORIZED_RESELLER_PASSWORD = require_env("AUTHORIZED_RESELLER_PASSWORD")
GRAY_MARKET_AGENT_PASSWORD = require_env("GRAY_MARKET_AGENT_PASSWORD")
MARKETPLACE_AGENT_PASSWORD = require_env("MARKETPLACE_AGENT_PASSWORD")
VALUE_RANKER_PASSWORD = require_env("VALUE_RANKER_PASSWORD")

RECOMMENDATION_AGENT_PASSWORD = require_env("RECOMMENDATION_AGENT_PASSWORD")
OUTPUT_AGENT_PASSWORD = require_env("OUTPUT_AGENT_PASSWORD")
