#!/usr/bin/env bash
# ✨ Create an Anville host on Hetzner Cloud (docs/server-approach.md, section 9).
#
# It makes sure the firewall and the operator's SSH key exist in the Hetzner project, then creates one
# server whose first boot is cloud-init.yaml.template, with backups on. Run it once per host.

set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: hcloud-create.sh [--render] <host-name> <tier>

  <host-name>   The server's name, such as staging-1
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
  HCLOUD_TOKEN          Read by hcloud itself, unless it has an active context

Needs the hcloud CLI, signed in to the Hetzner project the host belongs to.
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
  text=${text//__ADMIN_USER__/$ADMIN_USER}
  text=${text//__ADMIN_SSH_PUBLIC_KEY__/$ADMIN_KEY}
  text=${text//__DEPLOY_SSH_PUBLIC_KEY__/$DEPLOY_KEY}
  text=${text//__K3S_CHANNEL__/$K3S_CHANNEL}
  printf '%s\n' "$text"
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
if [ $# -ne 2 ]; then
  usage >&2
  exit 2
fi

HOST_NAME=$1
TIER=$2
HERE=$(cd "$(dirname "$0")" && pwd)
TEMPLATE=$HERE/cloud-init.yaml.template
RULES=$HERE/firewall-rules.json
FIREWALL=anville-web

case "$TIER" in
  staging) DEFAULT_TYPE=cx23 ;;
  production) DEFAULT_TYPE=cx33 ;;
  *) die "the tier must be staging or production, not '$TIER'" ;;
esac
[[ "$HOST_NAME" =~ ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$ ]] || die "'$HOST_NAME' is not a usable server name"

: "${ADMIN_USER:?set it to the account name the operator will use on the host}"
: "${ADMIN_SSH_KEY_FILE:?set it to the public key file of the operator}"
: "${DEPLOY_SSH_KEY_FILE:?set it to the public key file of the deploy workflow}"
[[ "$ADMIN_USER" =~ ^[a-z][a-z0-9_-]*$ ]] || die "'$ADMIN_USER' is not a usable account name"
[ "$ADMIN_USER" != deploy ] && [ "$ADMIN_USER" != root ] || die "ADMIN_USER cannot be '$ADMIN_USER'"

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
if hcloud server describe "$HOST_NAME" > /dev/null 2>&1; then
  die "a server named $HOST_NAME already exists in this Hetzner project"
fi

if ! hcloud firewall describe "$FIREWALL" > /dev/null 2>&1; then
  echo "Creating the firewall $FIREWALL (22, 80, 443 and ping)"
  hcloud firewall create --name "$FIREWALL" --rules-file "$RULES"
fi

# Given to Hetzner so that it sets no root password and emails none. Root cannot sign in over SSH either way.
SSH_KEY_NAME=anville-$ADMIN_USER
if ! hcloud ssh-key describe "$SSH_KEY_NAME" > /dev/null 2>&1; then
  echo "Adding the operator's key to the Hetzner project as $SSH_KEY_NAME"
  hcloud ssh-key create --name "$SSH_KEY_NAME" --public-key "$ADMIN_KEY"
fi

USER_DATA=$(mktemp)
trap 'rm -f "$USER_DATA"' EXIT
render > "$USER_DATA"

echo "Creating $HOST_NAME: $SERVER_TYPE in $LOCATION, $IMAGE, tier $TIER"
hcloud server create \
  --name "$HOST_NAME" \
  --type "$SERVER_TYPE" \
  --image "$IMAGE" \
  --location "$LOCATION" \
  --ssh-key "$SSH_KEY_NAME" \
  --firewall "$FIREWALL" \
  --enable-backup \
  --label project=anville \
  --label "tier=$TIER" \
  --user-data-from-file "$USER_DATA"

ADDRESS=$(hcloud server ip "$HOST_NAME")

cat <<NEXT

$HOST_NAME is created at $ADDRESS. Its first boot takes a few minutes. Then:

  1. Wait for it to finish, and confirm the node is ready with its tier:
       ssh $ADMIN_USER@$ADDRESS 'cloud-init status --wait && sudo k3s kubectl get nodes --show-labels'

  2. Confirm the k3s API is not reachable from outside (this should time out):
       nc -vz -w 5 $ADDRESS 6443

  3. For each environment on this host, in its GitHub Environment:
       DEPLOY_HOST          $ADDRESS
       DEPLOY_KNOWN_HOSTS   the output of: ssh-keyscan -t ed25519 $ADDRESS
       KUBECONFIG           the output of: ssh $ADMIN_USER@$ADDRESS 'sudo cat /etc/rancher/k3s/k3s.yaml'
       DEPLOY_SSH_KEY       the private key that matches $DEPLOY_SSH_KEY_FILE

  4. Point each environment's DNS A record at $ADDRESS.
NEXT
