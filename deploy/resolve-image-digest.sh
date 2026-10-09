#!/usr/bin/env bash
# Copyright (C) New Community Church SE London 2026.
# For licensing information see ../LICENSE.md

# ✨ Turn an image tag into what a deploy pins: the digest, and the commit the image was built from
# (docs/server-approach.md, section 8). A tag can move; a digest cannot.
#
# Usage: resolve-image-digest.sh <tag> [image]
# Prints two lines, digest=sha256:… and commit=…, in the form $GITHUB_OUTPUT takes.
#
# The image is public, so the registry is asked without credentials. Needs curl and jq.

set -euo pipefail

TAG=${1:?Usage: resolve-image-digest.sh <tag> [image]}
IMAGE=${2:-ghcr.io/inconceivableza/anville}

case "$IMAGE" in
  ghcr.io/*) REPOSITORY=${IMAGE#ghcr.io/} ;;
  *) echo "resolve-image-digest.sh: only images on ghcr.io are understood, not $IMAGE" >&2; exit 1 ;;
esac
REGISTRY=https://ghcr.io
ACCEPT="Accept: application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.v2+json"

die() {
  echo "resolve-image-digest.sh: $*" >&2
  exit 1
}

TOKEN=$(curl -fsS --max-time 30 "$REGISTRY/token?scope=repository:$REPOSITORY:pull" | jq -r '.token // empty') \
  || die "$REGISTRY will not answer for $REPOSITORY. Has the build workflow pushed the image, and is the package public?"
[ -n "$TOKEN" ] || die "$REGISTRY gave no token for $REPOSITORY. Is the package public?"

fetch() {
  curl -fsSL --max-time 60 -H "Authorization: Bearer $TOKEN" "$@"
}

HEADERS=$(mktemp)
MANIFEST=$(mktemp)
trap 'rm -f "$HEADERS" "$MANIFEST"' EXIT

fetch -H "$ACCEPT" -D "$HEADERS" -o "$MANIFEST" "$REGISTRY/v2/$REPOSITORY/manifests/$TAG" \
  || die "there is no image $IMAGE:$TAG. Has the build workflow pushed it, and is the package public?"

DIGEST=$(tr -d '\r' < "$HEADERS" | awk 'tolower($1) == "docker-content-digest:" { print $2 }' | tail -n 1)
[[ "$DIGEST" =~ ^sha256:[0-9a-f]{64}$ ]] || die "the registry named no digest for $IMAGE:$TAG"

# The tag may name one image, or an index of several of which one is the amd64 image the hosts run.
if jq -e '.manifests' "$MANIFEST" > /dev/null; then
  PLATFORM=$(jq -r '[.manifests[] | select(.platform.os == "linux" and .platform.architecture == "amd64")][0].digest // empty' "$MANIFEST")
  [ -n "$PLATFORM" ] || die "$IMAGE:$TAG holds no linux/amd64 image"
  fetch -H "$ACCEPT" -o "$MANIFEST" "$REGISTRY/v2/$REPOSITORY/manifests/$PLATFORM"
fi

CONFIG=$(jq -r '.config.digest // empty' "$MANIFEST")
[ -n "$CONFIG" ] || die "could not read the manifest of $IMAGE:$TAG"
COMMIT=$(fetch "$REGISTRY/v2/$REPOSITORY/blobs/$CONFIG" | jq -r '.config.Labels["org.opencontainers.image.revision"] // empty')
[ -n "$COMMIT" ] || die "$IMAGE:$TAG does not say which commit it was built from"

echo "digest=$DIGEST"
echo "commit=$COMMIT"
