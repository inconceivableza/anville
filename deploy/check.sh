#!/usr/bin/env bash
# ✨ Check everything under deploy/ that can be checked without a cluster: the scripts with shellcheck, and
# both charts with helm, rendered with the defaults and with each environment's values. The build workflow
# runs this, and so can you. Needs shellcheck and helm.

set -euo pipefail
cd "$(dirname "$0")"

# Any digest will do to render with. A deploy sets the real one.
DIGEST=sha256:0000000000000000000000000000000000000000000000000000000000000000

echo "== Scripts"
shellcheck ./*.sh infra/*.sh chart/anville/files/*.sh

echo "== anville-bootstrap"
helm lint --quiet chart/anville-bootstrap
helm template anville-bootstrap chart/anville-bootstrap > /dev/null

echo "== anville, with its defaults"
helm lint --quiet chart/anville --set image.digest="$DIGEST"
helm template anville chart/anville --namespace scratch --set image.digest="$DIGEST" > /dev/null

for values in environments/*/values.yaml; do
  [ -e "$values" ] || continue
  environment=$(basename "$(dirname "$values")")
  echo "== anville, as $environment"
  helm lint --quiet chart/anville --values "$values" --set image.digest="$DIGEST"
  helm template anville chart/anville --namespace "$environment" --values "$values" --set image.digest="$DIGEST" > /dev/null
done

echo "All of deploy/ checks out."
