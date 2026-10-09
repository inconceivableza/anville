#!/usr/bin/env bash
# ✨ Install k9s, a terminal view of the host's k3s cluster, for the operator (deploy/README.md, "Day to day").
#
# A pinned release from GitHub, checked against the checksum it was published with, and an alias in the
# operator's ~/.bashrc that runs it with the right kubeconfig, showing every namespace:
#
#   k9          sudo k9s --kubeconfig /etc/rancher/k3s/k3s.yaml -A
#
# Usage, as root: install-k9s.sh [<operator>]
#
#   <operator>  The account to give the alias. Default: the one that ran sudo
#
# Each host gets it on its first boot, from cloud-init.yaml.template. Unattended upgrades do not update it: to
# change the version, edit the three values below and run this on each host:
#
#   ssh <operator>@<host> 'sudo bash -s' < deploy/infra/install-k9s.sh
#
# Running it again changes nothing that is already in place.

set -euo pipefail

VERSION=v0.51.0
# From the release's checksums.sha256.
SHA256_AMD64=56b539a509eb2d6357cf4f575ed38c089f0e4880c95f79a70196b54f14954908
SHA256_ARM64=9dbc652cb3a6ede7279216e49c638ac2d5dfb701edd4e407e89dc42cb9920423

ALIAS="alias k9='sudo k9s --kubeconfig /etc/rancher/k3s/k3s.yaml -A'"

die() {
  echo "install-k9s.sh: $*" >&2
  exit 1
}

install_package() {
  local dir
  dir=$(mktemp -d)
  # Neither command may read standard input: run through bash -s, the rest of this script is standard input.
  curl -fsSL -o "$dir/k9s.deb" "https://github.com/derailed/k9s/releases/download/$VERSION/k9s_linux_$ARCH.deb" < /dev/null
  if ! echo "$SHA256  $dir/k9s.deb" | sha256sum -c --quiet -; then
    rm -f "$dir/k9s.deb"
    rmdir "$dir"
    die "the k9s $VERSION package does not match its checksum"
  fi
  # apt reads a local package as root: its note that it cannot drop privileges to fetch it is expected.
  apt-get -o DPkg::Lock::Timeout=300 install -y "$dir/k9s.deb" < /dev/null
  rm -f "$dir/k9s.deb"
  rmdir "$dir"
}

[ "$(id -u)" -eq 0 ] || die "run it as root"
[ $# -le 1 ] || die "usage: install-k9s.sh [<operator>]"
OPERATOR=${1:-${SUDO_USER:-}}
[ -n "$OPERATOR" ] && [ "$OPERATOR" != root ] || die "name the operator: install-k9s.sh <operator>"
HOME_DIR=$({ getent passwd "$OPERATOR" || true; } | cut -d: -f6)
[ -n "$HOME_DIR" ] && [ -d "$HOME_DIR" ] || die "there is no account $OPERATOR with a home directory"

ARCH=$(dpkg --print-architecture)
case "$ARCH" in
  amd64) SHA256=$SHA256_AMD64 ;;
  arm64) SHA256=$SHA256_ARM64 ;;
  *) die "there is no k9s package here for $ARCH" ;;
esac

if [ "$(dpkg-query -W -f '${Version}' k9s 2> /dev/null || true)" = "${VERSION#v}" ]; then
  echo "k9s $VERSION is installed already"
else
  install_package
  echo "k9s $VERSION is installed"
fi

BASHRC=$HOME_DIR/.bashrc
if grep -qxF "$ALIAS" "$BASHRC" 2> /dev/null; then
  echo "$OPERATOR has the k9 alias already"
elif grep -q "^alias k9=" "$BASHRC" 2> /dev/null; then
  # An earlier k9 alias, from an earlier version of this script or written by hand, is replaced, not repeated.
  sed -i "s|^alias k9=.*|$ALIAS|" "$BASHRC"
  echo "$OPERATOR's k9 alias is changed, in a new shell: k9 runs k9s"
else
  printf '\n# k9s, with k3s'\''s kubeconfig, which is root'\''s alone (added by install-k9s.sh)\n%s\n' "$ALIAS" >> "$BASHRC"
  chown "$OPERATOR:" "$BASHRC"
  echo "$OPERATOR has the k9 alias, in a new shell: k9 runs k9s"
fi
