#!/usr/bin/env bash
# ✨ Check everything under deploy/ that can be checked without a cluster: the scripts with shellcheck, and
# both charts with helm, rendered with the defaults and with each environment's values, and the pathways the
# publish-pathway workflow offers against pathways/. The build workflow runs this, and so can you.
# Needs shellcheck, helm and yq.

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

echo "== The pathways the publish-pathway workflow offers"
# A choice input's options are fixed in the workflow, so they are kept to what pathways/ holds.
offered=$(yq '.on.workflow_dispatch.inputs.pathway.options[]' ../.github/workflows/publish-pathway.yml | sort)
present=$(for document in ../pathways/*.json; do basename "$document"; done | sort)
if [ "$offered" != "$present" ]; then
  echo "The workflow offers:" >&2
  echo "$offered" >&2
  echo "pathways/ holds:" >&2
  echo "$present" >&2
  echo "Make the pathway options in .github/workflows/publish-pathway.yml the files in pathways/." >&2
  exit 1
fi

echo "All of deploy/ checks out."
