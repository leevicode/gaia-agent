#!/bin/sh
set -eu

DOMAIN="${XMPP_DOMAIN:-localhost}"

register_user() {
  USERNAME="$1"
  PASSWORD="$2"

  echo "Registering ${USERNAME}@${DOMAIN} ..."
  prosodyctl register "${USERNAME}" "${DOMAIN}" "${PASSWORD}" || true
}

register_user "user_agent" "${USER_AGENT_PASSWORD}"
register_user "software_coordinator" "${SOFTWARE_COORDINATOR_PASSWORD}"
register_user "local_coordinator" "${LOCAL_COORDINATOR_PASSWORD}"

register_user "official_store_agent" "${OFFICIAL_STORE_AGENT_PASSWORD}"
register_user "authorized_reseller_agent" "${AUTHORIZED_RESELLER_PASSWORD}"
register_user "gray_market_agent" "${GRAY_MARKET_AGENT_PASSWORD}"
register_user "marketplace_agent" "${MARKETPLACE_AGENT_PASSWORD}"
register_user "value_ranker_agent" "${VALUE_RANKER_PASSWORD}"

register_user "recommendation_agent" "${RECOMMENDATION_AGENT_PASSWORD}"
register_user "output_agent" "${OUTPUT_AGENT_PASSWORD}"

echo "Prosody account bootstrap finished."
