#!/usr/bin/env bash
# ✨ Create an Anville host on Hetzner Cloud (docs/server-approach.md, section 9).
#
# It makes sure the firewall and the operator's SSH key exist in the named Hetzner project, then creates one
# server whose first boot is cloud-init.yaml.template, with backups on. Run it once per host.
#
# Each host has a canonical name, such as anville-staging-01.vabl.dev: its server's name in Hetzner, its own
# hostname, its reverse DNS and the name every environment on it uses to reach it. The A record for that name
# is made by hand, once the script has printed the address.

set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: hcloud-create.sh [--render] <project> <host> <tier>

  <project>     The hcloud context for the Hetzner project the host belongs in, named after that project
                (hcloud context create <project>, with an API token made in that project). Only this
                context is used, whichever is active
  <host>        The host's canonical name, such as anville-staging-01.vabl.dev. Used for no other host:
                a name that already resolves is refused. Its first label names the tier
  <tier>        staging or production. It becomes a label on the k3s node, which every deploy checks
  --render      Print the cloud-init the host would be given, and create nothing

From the environment:
  ADMIN_USER            The operator's account name on the host (required)
  ADMIN_SSH_KEY_FILE    The operator's public key file (required)
  DEPLOY_SSH_KEY_FILE   The deploy workflow's public key file (required). The matching private key
                        becomes the DEPLOY_SSH_KEY secret of each environment on this host
  SERVER_TYPE           Default: cx23 for staging, cx33 for production
  LOCATION              Default: fsn1. Keep to the EU: fsn1, nbg1 or hel1
  IMAGE                 Default: ubuntu-24.04
  K3S_CHANNEL           Default: stable

HCLOUD_TOKEN must not be set: it would override the context's token, so the project would be whichever
the token belongs to. Needs the hcloud CLI, and getent, dig or python3 to look the name up.
USAGE
}

die() {
  echo "hcloud-create.sh: $*" >&2
  exit 1
}

# The key's type and body, without its comment, so that nothing the comment holds reaches the template.
public_key() {
  local file=$1 type body rest
  [ -r "$file" ] || die "cannot read $file"
  read -r type body rest < "$file" || true
  case "$type" in
    ssh-ed25519 | ssh-rsa | ecdsa-sha2-nistp256 | ecdsa-sha2-nistp384 | ecdsa-sha2-nistp521) ;;
    *) die "$file does not look like a public key (a private key must never be given here)" ;;
  esac
  [[ "$body" =~ ^[A-Za-z0-9+/=]+$ ]] || die "$file does not look like a public key"
  echo "$type $body"
}

render() {
  local text
  text=$(< "$TEMPLATE")
  text=${text//__TIER__/$TIER}
  text=${text//__HOST__/$HOST}
  text=${text//__SHORT_NAME__/$SHORT_NAME}
  text=${text//__ADMIN_USER__/$ADMIN_USER}
  text=${text//__ADMIN_SSH_PUBLIC_KEY__/$ADMIN_KEY}
  text=${text//__DEPLOY_SSH_PUBLIC_KEY__/$DEPLOY_KEY}
  text=${text//__K3S_CHANNEL__/$K3S_CHANNEL}
  printf '%s\n' "$text"
}

# The addresses the name has in public DNS now, if any. getent on Linux; dig on macOS, which has no getent.
addresses_of() {
  if command -v getent > /dev/null; then
    { getent ahosts "$1" || true; } | awk '{ print $1 }' | sort -u
  elif command -v dig > /dev/null; then
    { dig +short A "$1"; dig +short AAAA "$1"; } | grep -v '\.$' || true
  elif command -v python3 > /dev/null; then
    python3 -c 'import socket, sys
try:
    print("\n".join(sorted({a[4][0] for a in socket.getaddrinfo(sys.argv[1], None)})))
except socket.gaierror:
    pass' "$1"
  else
    die "cannot look $1 up: needs getent, dig or python3"
  fi
}

# Every hcloud call goes to the named project's context, never to whichever one happens to be active.
hc() {
  hcloud --context "$PROJECT" "$@"
}

RENDER_ONLY=false
if [ "${1:-}" = "--render" ]; then
  RENDER_ONLY=true
  shift
fi
if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi
if [ $# -ne 3 ]; then
  usage >&2
  exit 2
fi

PROJECT=$1
HOST=$2
TIER=$3
SHORT_NAME=${HOST%%.*}
HERE=$(cd "$(dirname "$0")" && pwd)
TEMPLATE=$HERE/cloud-init.yaml.template
RULES=$HERE/firewall-rules.json
FIREWALL=anville-web

case "$TIER" in
  staging) DEFAULT_TYPE=cx23 ;;
  production) DEFAULT_TYPE=cx33 ;;
  *) die "the tier must be staging or production, not '$TIER'" ;;
esac
[[ "$PROJECT" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]*$ ]] || die "'$PROJECT' is not a usable context name"
# A fully qualified name, short enough to be a Kubernetes label's value as well.
[[ "$HOST" =~ ^([a-z0-9]([a-z0-9-]*[a-z0-9])?\.)+[a-z]([a-z0-9-]*[a-z0-9])?$ ]] \
  || die "'$HOST' is not a fully qualified host name, such as anville-$TIER-01.vabl.dev"
[ ${#HOST} -le 63 ] || die "'$HOST' is longer than 63 characters"
case "$SHORT_NAME" in
  *"$TIER"*) ;;
  *) die "'$HOST' does not name its tier: a $TIER host's first label says $TIER, such as anville-$TIER-01" ;;
esac

: "${ADMIN_USER:?set it to the account name the operator will use on the host}"
: "${ADMIN_SSH_KEY_FILE:?set it to the public key file of the operator}"
: "${DEPLOY_SSH_KEY_FILE:?set it to the public key file of the deploy workflow}"
[[ "$ADMIN_USER" =~ ^[a-z][a-z0-9_-]*$ ]] || die "'$ADMIN_USER' is not a usable account name"
case "$ADMIN_USER" in
  deploy | root) die "ADMIN_USER cannot be '$ADMIN_USER'" ;;
esac

SERVER_TYPE=${SERVER_TYPE:-$DEFAULT_TYPE}
LOCATION=${LOCATION:-fsn1}
IMAGE=${IMAGE:-ubuntu-24.04}
K3S_CHANNEL=${K3S_CHANNEL:-stable}
ADMIN_KEY=$(public_key "$ADMIN_SSH_KEY_FILE")
DEPLOY_KEY=$(public_key "$DEPLOY_SSH_KEY_FILE")
[ "$ADMIN_KEY" != "$DEPLOY_KEY" ] || die "the operator and the deploy workflow must not share a key"

if $RENDER_ONLY; then
  render
  exit 0
fi

command -v hcloud > /dev/null || die "the hcloud CLI is not installed"
[ -z "${HCLOUD_TOKEN:-}" ] \
  || die "unset HCLOUD_TOKEN: it overrides the context's token, so the host could land in another project"
hcloud context list -o noheader -o columns=name | grep -qxF "$PROJECT" \
  || die "there is no hcloud context named $PROJECT. Make one with an API token from that Hetzner project: hcloud context create $PROJECT"

# A canonical name names one host. One that resolves belongs to a host already, or is a stale record.
EXISTING=$(addresses_of "$HOST")
[ -z "$EXISTING" ] || die "$HOST already resolves, to $(echo "$EXISTING" | paste -sd ' ' -). Choose the next number, or remove the record if its host is gone"
if hc server describe "$HOST" > /dev/null 2>&1; then
  die "a server named $HOST already exists in the Hetzner project $PROJECT"
fi

if ! hc firewall describe "$FIREWALL" > /dev/null 2>&1; then
  echo "Creating the firewall $FIREWALL (22, 80, 443 and ping)"
  hc firewall create --name "$FIREWALL" --rules-file "$RULES"
fi

# Given to Hetzner so that it sets no root password and emails none. Root cannot sign in over SSH either way.
SSH_KEY_NAME=anville-$ADMIN_USER
if ! hc ssh-key describe "$SSH_KEY_NAME" > /dev/null 2>&1; then
  echo "Adding the operator's key to the Hetzner project as $SSH_KEY_NAME"
  hc ssh-key create --name "$SSH_KEY_NAME" --public-key "$ADMIN_KEY"
fi

USER_DATA=$(mktemp)
trap 'rm -f "$USER_DATA"' EXIT
render > "$USER_DATA"

echo "Creating $HOST in the Hetzner project $PROJECT: $SERVER_TYPE in $LOCATION, $IMAGE, tier $TIER"
hc server create \
  --name "$HOST" \
  --type "$SERVER_TYPE" \
  --image "$IMAGE" \
  --location "$LOCATION" \
  --ssh-key "$SSH_KEY_NAME" \
  --firewall "$FIREWALL" \
  --enable-backup \
  --label project=anville \
  --label "tier=$TIER" \
  --user-data-from-file "$USER_DATA"

ADDRESS=$(hc server ip "$HOST")
echo "Setting the reverse DNS of $ADDRESS to $HOST"
hc server set-rdns --ip "$ADDRESS" --hostname "$HOST" "$HOST"

cat <<NEXT

$HOST is created in the Hetzner project $PROJECT, at $ADDRESS. Its first boot takes a few minutes. Then:

  1. Create its DNS record by hand, DNS only (not proxied in Cloudflare), and no AAAA record:
       $HOST.  A  $ADDRESS
     and wait until it resolves:
       dig +short $HOST

  2. Wait for the first boot to finish, and confirm the node is ready with its tier and name:
       ssh $ADMIN_USER@$HOST 'cloud-init status --wait && sudo k3s kubectl get nodes --show-labels'

  3. Confirm the k3s API is not reachable from outside (this should time out):
       nc -vz -w 5 $HOST 6443

  4. For each environment on this host:
       in its values.yaml:      host: $HOST
       in its GitHub Environment:
         DEPLOY_KNOWN_HOSTS     the output of: ssh-keyscan -t ed25519 $HOST
         KUBECONFIG             the output of: ssh $ADMIN_USER@$HOST 'sudo cat /etc/rancher/k3s/k3s.yaml'
         DEPLOY_SSH_KEY         the private key that matches $DEPLOY_SSH_KEY_FILE

  5. Point each environment's hostname at the host: a CNAME to $HOST, or, where the hostname is a
     zone's apex and the DNS provider cannot flatten a CNAME, an A record to $ADDRESS.
NEXT
