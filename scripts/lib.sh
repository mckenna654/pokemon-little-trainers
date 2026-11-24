#!/usr/bin/env bash
# Shared helpers for Little Trainers scripts. Source this; do not run it.
# shellcheck disable=SC2034  # variables are used by the scripts that source this file
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$ROOT/work"
GAME="$ROOT/game"
AGBCC_DIR="$WORK/agbcc"
BRANCH="little-trainers"
eval "$(grep -E '^[A-Z0-9_]+=[A-Za-z0-9_.:/-]*$' "$ROOT/upstream.lock")"
FORMAT_PATCH=(format-patch --quiet --zero-commit --no-signature --no-stat --keep-subject --binary)
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
BASE_ROM="$ROOT/original-rom/firered-rev1.gba"
ROM_NAME="Pokemon - Little Trainers"

if [ "$(uname -s)" = "Darwin" ]; then
  JOBS="$(sysctl -n hw.ncpu)"
  sha1()   { shasum -a 1 "$1" | cut -d' ' -f1; }
  sha256() { shasum -a 256 "$1" | cut -d' ' -f1; }
else
  JOBS="$(nproc)"
  sha1()   { sha1sum "$1" | cut -d' ' -f1; }
  sha256() { sha256sum "$1" | cut -d' ' -f1; }
fi

say()  { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mwarning:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }
need() { for t in "$@"; do command -v "$t" >/dev/null || die "missing tool: $t (run scripts/setup.sh)"; done; }
