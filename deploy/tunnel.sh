#!/usr/bin/env bash
# ✨ Open or close the SSH tunnel to a host's k3s API (docs/server-approach.md, section 8).
#
# The API listens on the host and is not reachable from outside: no firewall admits 6443. The deploy
# account's key can do one thing, forward a port to it. With the tunnel open, a kubeconfig that names
# https://127.0.0.1:6443 reaches the host's cluster.
#
# Usage: tunnel.sh open | close
#
# From the environment, for open:
#   DEPLOY_HOST          the host's address
#   DEPLOY_SSH_KEY       the deploy account's private key, itself and not a file's name
#   DEPLOY_KNOWN_HOSTS   the host's key, as ssh-keyscan prints it. A host that shows another is refused
#   DEPLOY_SSH_PORT      default 22
#   LOCAL_PORT           default 6443

set -euo pipefail

DIR=${TUNNEL_DIR:-${RUNNER_TEMP:-${TMPDIR:-/tmp}}/anville-tunnel}

case "${1:-}" in
  open)
    : "${DEPLOY_HOST:?set it to the address of the host}"
    : "${DEPLOY_SSH_KEY:?set it to the private key of the deploy account}"
    : "${DEPLOY_KNOWN_HOSTS:?set it to the host key, as ssh-keyscan prints it}"
    (
      umask 077
      mkdir -p "$DIR"
      printf '%s\n' "$DEPLOY_SSH_KEY" > "$DIR/key"
      printf '%s\n' "$DEPLOY_KNOWN_HOSTS" > "$DIR/known_hosts"
    )
    LOCAL_PORT=${LOCAL_PORT:-6443}
    ssh -N \
      -i "$DIR/key" \
      -o IdentitiesOnly=yes \
      -o BatchMode=yes \
      -o StrictHostKeyChecking=yes \
      -o UserKnownHostsFile="$DIR/known_hosts" \
      -o ExitOnForwardFailure=yes \
      -o ServerAliveInterval=30 \
      -p "${DEPLOY_SSH_PORT:-22}" \
      -L "127.0.0.1:$LOCAL_PORT:127.0.0.1:6443" \
      "deploy@$DEPLOY_HOST" < /dev/null > "$DIR/log" 2>&1 &
    echo $! > "$DIR/pid"

    # Open means the local port answers. If ssh has gone instead, say what it said.
    for _ in $(seq 1 30); do
      if ! kill -0 "$(cat "$DIR/pid")" 2> /dev/null; then
        cat "$DIR/log" >&2
        echo "tunnel.sh: the tunnel to $DEPLOY_HOST did not open" >&2
        exit 1
      fi
      if (exec 3<> "/dev/tcp/127.0.0.1/$LOCAL_PORT") 2> /dev/null; then
        echo "The tunnel to $DEPLOY_HOST is open on 127.0.0.1:$LOCAL_PORT"
        exit 0
      fi
      sleep 1
    done
    echo "tunnel.sh: the tunnel to $DEPLOY_HOST did not open within 30 seconds" >&2
    exit 1
    ;;
  close)
    if [ -f "$DIR/pid" ]; then
      kill "$(cat "$DIR/pid")" 2> /dev/null || true
    fi
    # The key goes with it.
    if [ -d "$DIR" ]; then
      rm -r "$DIR"
    fi
    echo "The tunnel is closed"
    ;;
  *)
    echo "Usage: tunnel.sh open | close" >&2
    exit 2
    ;;
esac
