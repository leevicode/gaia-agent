import os

from dotenv import load_dotenv


load_dotenv()


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def read_bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    normalized_value = value.strip().lower()

    if normalized_value in {"1", "true", "yes", "y", "on"}:
        return True

    if normalized_value in {"0", "false", "no", "n", "off"}:
        return False

    raise RuntimeError(
        f"Invalid boolean value for {name}: {value}. "
        "Use true or false."
    )


def read_float_env(name: str, default: float) -> float:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        parsed_value = float(value)
    except ValueError as exc:
        raise RuntimeError(
            f"Invalid numeric value for {name}: {value}."
        ) from exc

    if parsed_value <= 0:
        raise RuntimeError(
            f"Invalid numeric value for {name}: {value}. "
            "The value must be greater than 0."
        )

    return parsed_value


def read_optional_float_env(name: str) -> float | None:
    value = os.getenv(name)

    if value is None or not value.strip():
        return None

    try:
        parsed_value = float(value)
    except ValueError as exc:
        raise RuntimeError(
            f"Invalid numeric value for {name}: {value}."
        ) from exc

    if parsed_value <= 0:
        raise RuntimeError(
            f"Invalid numeric value for {name}: {value}. "
            "The value must be greater than 0."
        )

    return parsed_value


def read_str_env(name: str, default: str) -> str:
    value = os.getenv(name)

    if value is None:
        return default

    cleaned_value = value.strip()
    if not cleaned_value:
        return default

    return cleaned_value


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

USE_REAL_CHEAPSHARK = read_bool_env(
    name="USE_REAL_CHEAPSHARK",
    default=True,
)

CHEAPSHARK_TIMEOUT_SECONDS = read_float_env(
    name="CHEAPSHARK_TIMEOUT_SECONDS",
    default=8.0,
)

ENABLE_CURRENCY_CONVERSION = read_bool_env(
    name="ENABLE_CURRENCY_CONVERSION",
    default=True,
)

CURRENCY_RATE_PROVIDER = read_str_env(
    name="CURRENCY_RATE_PROVIDER",
    default="ecb",
)

CURRENCY_RATE_TIMEOUT_SECONDS = read_float_env(
    name="CURRENCY_RATE_TIMEOUT_SECONDS",
    default=8.0,
)

ALLOW_CURRENCY_FALLBACK_RATE = read_bool_env(
    name="ALLOW_CURRENCY_FALLBACK_RATE",
    default=True,
)

FALLBACK_USD_TO_EUR_RATE = read_optional_float_env(
    name="FALLBACK_USD_TO_EUR_RATE",
)

FALLBACK_USD_TO_EUR_RATE_SOURCE = read_str_env(
    name="FALLBACK_USD_TO_EUR_RATE_SOURCE",
    default="manual_fallback_rate",
)

FALLBACK_USD_TO_EUR_RATE_DATE = read_str_env(
    name="FALLBACK_USD_TO_EUR_RATE_DATE",
    default="not_specified",
)
