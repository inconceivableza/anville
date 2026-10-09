#!/usr/bin/env bash
# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

# ✨ Deploy one environment to the host whose k3s API kubectl can already reach (docs/server-approach.md,
# section 8). The deploy workflow opens the tunnel, then runs this; it holds no secret of its own.
#
# Usage: deploy.sh [--skip-bootstrap] [--no-wait] <environment> <image digest>
#
#   <environment>      A directory of deploy/environments/, which is also its namespace
#   <image digest>     sha256:…, from resolve-image-digest.sh
#   --skip-bootstrap   Leave cert-manager and the issuers as they are, on a host that already has them
#   --no-wait          Return once everything is applied, without waiting for the pods. For rehearsing
#                      against an API server that has no node to run them. Use it with --skip-bootstrap
#                      there: cert-manager checks itself with a job as it installs, and the issuers
#                      cannot be created until its webhook is running, so both need a node
#
# From the environment, as deploy/environments/<environment>/secrets.example.yaml describes:
#   DJANGO_SECRET_KEY
#   ANVILLE_ENROLMENT_CODE                              when enrolment.required
#   POSTGRES_PASSWORD                                   when postgres.enabled
#   DATABASE_URL                                        when not
#   BACKUP_TARGET, BACKUP_SSH_KEY, BACKUP_KNOWN_HOSTS   when backup.enabled
#   EMAIL_URL                                           optional on staging, required on production; needs email.from
#   ACME_EMAIL                                          optional
#
# Needs kubectl, helm and yq.

set -euo pipefail

CERT_MANAGER_VERSION=v1.21.2
CERT_MANAGER_CHART=oci://quay.io/jetstack/charts/cert-manager

die() {
  echo "deploy.sh: $*" >&2
  exit 1
}

BOOTSTRAP=true
WAIT=true
while [ $# -gt 0 ]; do
  case "$1" in
    --skip-bootstrap) BOOTSTRAP=false ;;
    --no-wait) WAIT=false ;;
    -*) die "unknown option $1" ;;
    *) break ;;
  esac
  shift
done
[ $# -eq 2 ] || die "usage: deploy.sh [--skip-bootstrap] [--no-wait] <environment> <image digest>"

ENVIRONMENT=$1
DIGEST=$2
HERE=$(cd "$(dirname "$0")" && pwd)
CHART=$HERE/chart/anville
VALUES=$HERE/environments/$ENVIRONMENT/values.yaml
SECRET=anville

# How long each helm call waits for what it installed to be ready, unless told not to wait at all.
waiting() {
  if $WAIT; then WAITING=(--wait --timeout "$1"); else WAITING=(); fi
}

[[ "$ENVIRONMENT" =~ ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$ ]] || die "'$ENVIRONMENT' is not an environment's name"
[ -f "$VALUES" ] || die "there is no environment $ENVIRONMENT in deploy/environments/"
[[ "$DIGEST" =~ ^sha256:[0-9a-f]{64}$ ]] || die "'$DIGEST' is not an image digest"

# What the environment is, with the chart's defaults for whatever its own values leave out.
setting() {
  # shellcheck disable=SC2016  # $item is yq's own variable
  yq eval-all '. as $item ireduce ({}; . * $item)' "$CHART/values.yaml" "$VALUES" | yq "$1"
}
TIER=$(setting .tier)
HOST=$(setting .host)
HOSTNAME_SERVED=$(setting .hostname)
[ -n "$HOST" ] || die "$ENVIRONMENT names no host: its values.yaml needs host, the canonical name of the host that carries it"
POSTGRES=$(setting .postgres.enabled)
ENROLMENT=$(setting .enrolment.required)
BACKUP=$(setting .backup.enabled)
FROM=$(setting .email.from)

# The secrets this environment needs, by what it is. Nothing is applied until all are there.
NEEDED=(DJANGO_SECRET_KEY)
if [ "$ENROLMENT" = true ]; then NEEDED+=(ANVILLE_ENROLMENT_CODE); fi
if [ "$POSTGRES" = true ]; then NEEDED+=(POSTGRES_PASSWORD); else NEEDED+=(DATABASE_URL); fi
if [ "$BACKUP" = true ]; then NEEDED+=(BACKUP_TARGET BACKUP_SSH_KEY BACKUP_KNOWN_HOSTS); fi
# Fake email on production would write participants' and observers' links to a log and deliver nothing.
if [ "$TIER" = production ]; then NEEDED+=(EMAIL_URL); fi
MISSING=()
for name in "${NEEDED[@]}"; do
  [ -n "${!name:-}" ] || MISSING+=("$name")
done
[ ${#MISSING[@]} -eq 0 ] || die "$ENVIRONMENT needs these secrets, which are not set: ${MISSING[*]}"
# Real email from Django's webmaster@localhost would be refused by the provider, message by message.
if [ -n "${EMAIL_URL:-}" ] && [ -z "$FROM" ]; then
  die "$ENVIRONMENT has EMAIL_URL, so its values.yaml needs email.from: an address at the domain the provider has validated"
fi
if [ "$POSTGRES" = true ] && ! [[ "$POSTGRES_PASSWORD" =~ ^[A-Za-z0-9_-]+$ ]]; then
  die "POSTGRES_PASSWORD becomes part of a URL, so it may hold only letters, digits, - and _"
fi

echo "== The host"
# A production environment aimed at a staging host, or the reverse, stops here.
HOST_TIERS=$(kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.labels.anville-tier}{"\n"}{end}' | sort -u)
[ "$HOST_TIERS" = "$TIER" ] || die "$ENVIRONMENT is a $TIER environment, and this host's tier is '${HOST_TIERS:-not set}'"
# So does a kubeconfig, or a tunnel, that reaches a host other than the one the environment's values name.
HOST_NAMES=$(kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.labels.anville-host}{"\n"}{end}' | sort -u)
[ "$HOST_NAMES" = "$HOST" ] || die "$ENVIRONMENT belongs on $HOST, and this host is '${HOST_NAMES:-not named}'"
echo "$HOST, a $TIER host, for a $TIER environment"

echo "== Namespace and secrets"
kubectl create namespace "$ENVIRONMENT" --dry-run=client -o yaml | kubectl apply -f -
SECRETS=$(mktemp -d)
trap 'rm -r "$SECRETS"' EXIT
(
  umask 077
  for name in "${NEEDED[@]}" EMAIL_URL; do
    # One file for each secret that has a value. EMAIL_URL is left out when absent, which means fake email.
    [ -z "${!name:-}" ] || printf '%s' "${!name}" > "$SECRETS/$name"
  done
)
kubectl -n "$ENVIRONMENT" create secret generic "$SECRET" --from-file="$SECRETS" --dry-run=client -o yaml \
  | kubectl apply -f - > /dev/null
echo "secret/$SECRET applied, with: $(cd "$SECRETS" && echo *)"
# The pods restart when this changes, and only then.
CHECKSUM=$(cd "$SECRETS" && for name in *; do echo "$name"; cat "$name"; echo; done | sha256sum | cut -d' ' -f1)

if $BOOTSTRAP; then
  echo "== cert-manager $CERT_MANAGER_VERSION and the issuers"
  waiting 5m
  helm upgrade --install cert-manager "$CERT_MANAGER_CHART" \
    --version "$CERT_MANAGER_VERSION" \
    --namespace cert-manager --create-namespace \
    --set crds.enabled=true \
    ${WAITING[@]+"${WAITING[@]}"}
  waiting 2m
  helm upgrade --install anville-bootstrap "$HERE/chart/anville-bootstrap" \
    --namespace cert-manager \
    --set acmeEmail="${ACME_EMAIL:-}" \
    ${WAITING[@]+"${WAITING[@]}"}
fi

echo "== $ENVIRONMENT at $DIGEST"
waiting 10m
if ! helm upgrade --install anville "$CHART" \
  --namespace "$ENVIRONMENT" \
  --values "$VALUES" \
  --set image.digest="$DIGEST" \
  --set secretChecksum="$CHECKSUM" \
  ${WAITING[@]+"${WAITING[@]}"}; then
  # Enough to see why, without printing anything a pod was given.
  kubectl -n "$ENVIRONMENT" get pods -o wide || true
  kubectl -n "$ENVIRONMENT" logs deployment/anville --container migrate --tail 40 || true
  kubectl -n "$ENVIRONMENT" get events --sort-by .lastTimestamp | tail -n 20 || true
  die "$ENVIRONMENT did not come up. The release is left as it is, for you to look at"
fi

echo "$ENVIRONMENT is deployed${HOSTNAME_SERVED:+, at https://$HOSTNAME_SERVED}"
