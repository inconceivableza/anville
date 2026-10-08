#!/usr/bin/env bash
# ✨ Install k9s, a terminal view of the host's k3s cluster, for the operator (deploy/README.md, "Day to day").
#
# A pinned release from GitHub, checked against the checksum it was published with. Each host gets it on its
# first boot, from cloud-init.yaml.template. Unattended upgrades do not update it: to change the version, edit
# the three values below and run this on each host, as root:
#
#   ssh <operator>@<host> 'sudo bash -s' < deploy/infra/install-k9s.sh
#
# Running it again with the version already installed changes nothing.

set -euo pipefail

VERSION=v0.51.0
# From the release's checksums.sha256.
SHA256_AMD64=56b539a509eb2d6357cf4f575ed38c089f0e4880c95f79a70196b54f14954908
SHA256_ARM64=9dbc652cb3a6ede7279216e49c638ac2d5dfb701edd4e407e89dc42cb9920423

die() {
  echo "install-k9s.sh: $*" >&2
  exit 1
}

[ "$(id -u)" -eq 0 ] || die "run it as root"

ARCH=$(dpkg --print-architecture)
case "$ARCH" in
  amd64) SHA256=$SHA256_AMD64 ;;
  arm64) SHA256=$SHA256_ARM64 ;;
  *) die "there is no k9s package here for $ARCH" ;;
esac

if [ "$(dpkg-query -W -f '${Version}' k9s 2> /dev/null || true)" = "${VERSION#v}" ]; then
  echo "k9s $VERSION is installed already"
  exit 0
fi

DIR=$(mktemp -d)
trap 'rm -f "$DIR/k9s.deb"; rmdir "$DIR"' EXIT
# Neither command may read standard input: run through bash -s, the rest of this script is standard input.
curl -fsSL -o "$DIR/k9s.deb" "https://github.com/derailed/k9s/releases/download/$VERSION/k9s_linux_$ARCH.deb" < /dev/null
echo "$SHA256  $DIR/k9s.deb" | sha256sum -c --quiet - || die "the k9s $VERSION package does not match its checksum"
# apt reads a local package as root: its note that it cannot drop privileges to fetch it is expected.
apt-get -o DPkg::Lock::Timeout=300 install -y "$DIR/k9s.deb" < /dev/null
echo "k9s $VERSION is installed: run it with sudo k9s --kubeconfig /etc/rancher/k3s/k3s.yaml"
