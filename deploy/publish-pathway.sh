#!/usr/bin/env bash
# ✨ Publish a pathway document from this checkout to one environment (docs/server-approach.md, section 8).
# The publish-pathway workflow opens the tunnel, then runs this; it holds no secret of its own.
#
# Usage: publish-pathway.sh <environment> <pathway>
#
#   <environment>   A directory of deploy/environments/, which is also its namespace
#   <pathway>       A document in pathways/, such as whatever-you-do.json
#
# The document is sent from this checkout into the environment's running pod and loaded there with
# load_pathway, so the code that checks it is the code that will serve it: a document the deployed version
# cannot read is refused, and nothing changes. Content already published is left as it is.
#
# Needs kubectl.

set -euo pipefail

die() {
  echo "publish-pathway.sh: $*" >&2
  exit 1
}

[ $# -eq 2 ] || die "usage: publish-pathway.sh <environment> <pathway>"
ENVIRONMENT=$1
PATHWAY=$2
HERE=$(cd "$(dirname "$0")" && pwd)
DOCUMENT=$HERE/../pathways/$PATHWAY

[[ "$ENVIRONMENT" =~ ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$ ]] || die "'$ENVIRONMENT' is not an environment's name"
[ -f "$HERE/environments/$ENVIRONMENT/values.yaml" ] || die "there is no environment $ENVIRONMENT in deploy/environments/"
[[ "$PATHWAY" =~ ^[a-z0-9][a-z0-9._-]*\.json$ ]] && [ -f "$DOCUMENT" ] || die "there is no pathway $PATHWAY in pathways/"

echo "== Waiting for $ENVIRONMENT to be running"
kubectl -n "$ENVIRONMENT" rollout status deployment/anville --timeout 5m

echo "== Publishing pathways/$PATHWAY to $ENVIRONMENT"
# The pod's root filesystem is read-only, and /tmp is its own scratch volume.
# shellcheck disable=SC2016  # $1 is expanded by the pod's shell
kubectl -n "$ENVIRONMENT" exec -i deployment/anville -c web -- sh -c '
  file=/tmp/$1
  cat > "$file" || exit 1
  python manage.py load_pathway "$file"
  status=$?
  rm -f "$file"
  exit $status
' sh "$PATHWAY" < "$DOCUMENT"
