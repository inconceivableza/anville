#!/usr/bin/env bash
# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

# ✨ Confirm from outside that an environment is serving the commit just deployed (docs/server-approach.md,
# section 8). It catches a wrong DNS record, a certificate that was not issued and a pod that never became
# ready, none of which the cluster can see for itself.
#
# Usage: assert-version.sh <url of /healthz> <commit>
# Keeps asking for up to WAIT_SECONDS (default 300): a first certificate takes a minute or two.
# Needs curl and jq.

set -euo pipefail

URL=${1:?Usage: assert-version.sh <url of /healthz> <commit>}
EXPECTED=${2:?Usage: assert-version.sh <url of /healthz> <commit>}
WAIT_SECONDS=${WAIT_SECONDS:-300}
DEADLINE=$(($(date +%s) + WAIT_SECONDS))

while true; do
  if BODY=$(curl -fsS --max-time 10 "$URL" 2>&1); then
    SERVING=$(echo "$BODY" | jq -r '.commit // empty' 2> /dev/null || true)
    if [ "$SERVING" = "$EXPECTED" ]; then
      echo "$URL is serving $EXPECTED"
      exit 0
    fi
    PROBLEM="it is serving '${SERVING:-nothing recognisable}'"
  else
    PROBLEM=$BODY
  fi
  if [ "$(date +%s)" -ge "$DEADLINE" ]; then
    echo "assert-version.sh: $URL is not serving $EXPECTED after $WAIT_SECONDS seconds: $PROBLEM" >&2
    exit 1
  fi
  sleep 10
done
