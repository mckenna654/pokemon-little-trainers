#!/usr/bin/env bash
# Environment setup for macOS, Linux, WSL and Docker. Safe to re-run.
#   1. installs build dependencies (Homebrew or apt) unless --no-deps
#   2. fetches pret/pokefirered (into game/) and pret/agbcc at the commits pinned in upstream.lock
#   3. builds agbcc and installs it into game/
#   4. creates the local "little-trainers" branch in game/ and applies patches/*.patch
#   5. installs the git pre-commit guard
. "$(dirname "$0")/lib.sh"

NO_DEPS=0
[ "${1:-}" = "--no-deps" ] && NO_DEPS=1

if [ "$NO_DEPS" = 0 ]; then
  say "Installing build dependencies"
  if [ "$(uname -s)" = "Darwin" ]; then
    command -v brew >/dev/null || die "Homebrew is required: https://brew.sh"
    xcode-select -p >/dev/null 2>&1 || die "Install the Xcode Command Line Tools first: xcode-select --install"
    brew install arm-none-eabi-binutils arm-none-eabi-gcc libpng pkgconf cmake
  elif command -v apt-get >/dev/null; then
    SUDO=""; [ "$(id -u)" != 0 ] && SUDO="sudo"
    $SUDO apt-get update
    $SUDO apt-get install -y build-essential binutils-arm-none-eabi git libpng-dev pkg-config python3 cmake zlib1g-dev
  else
    warn "Unknown package manager. Install: a C compiler, make, arm-none-eabi binutils, libpng, pkg-config, git, python3, cmake"
  fi
fi

need git make python3 arm-none-eabi-as
mkdir -p "$WORK"

fetch() { # dir url commit remote-name
  if [ ! -d "$1/.git" ]; then
    say "Cloning $2"
    git clone --quiet --origin "$4" "$2" "$1"
  fi
  git -C "$1" cat-file -e "$3^{commit}" 2>/dev/null || git -C "$1" fetch --quiet "$4"
}

fetch "$AGBCC_DIR" "$AGBCC_URL" "$AGBCC_COMMIT" origin
if [ -d "$GAME/.git" ] && git -C "$GAME" remote | grep -qx origin; then git -C "$GAME" remote rename origin upstream; fi
fetch "$GAME" "$UPSTREAM_URL" "$UPSTREAM_COMMIT" upstream
# pret's remote is "upstream"; make pushing to it impossible.
git -C "$GAME" remote set-url --push upstream DISABLED-do-not-push-to-pret

stamp="$AGBCC_COMMIT $(uname -sm)"
if [ ! -x "$GAME/tools/agbcc/bin/agbcc" ] || [ "$(cat "$WORK/.agbcc-stamp" 2>/dev/null)" != "$stamp" ]; then
  say "Building agbcc $AGBCC_COMMIT (takes a minute)"
  # agbcc's 1990s configure scripts break when the path contains spaces (e.g. "Claude Code"),
  # so build a clean export in a temporary directory and copy the finished tools into game/.
  tmp="$(mktemp -d)"
  case "$tmp" in *" "*) die "temporary directory path contains a space: $tmp" ;; esac
  git -C "$AGBCC_DIR" archive --prefix=agbcc/ "$AGBCC_COMMIT" | tar -x -C "$tmp"
  mkdir -p "$tmp/out"
  (cd "$tmp/agbcc" && ./build.sh >"$WORK/agbcc-build.log" 2>&1 && ./install.sh ../out >>"$WORK/agbcc-build.log" 2>&1) \
    || { rm -rf "$tmp"; die "agbcc build failed, see work/agbcc-build.log"; }
  rm -rf "$GAME/tools/agbcc"
  cp -R "$tmp/out/tools/agbcc" "$GAME/tools/agbcc"
  rm -rf "$tmp"
  echo "$stamp" > "$WORK/.agbcc-stamp"
fi

"$ROOT/scripts/apply-patches.sh"

git -C "$ROOT" config core.hooksPath .githooks 2>/dev/null || true

# Optional helpers: patch tool and headless emulator for tests. Failures here do not block building.
[ -x "$WORK/flips/flips" ] || "$ROOT/scripts/build-flips.sh" >/dev/null 2>&1 || warn "Floating IPS not built (scripts/build-flips.sh); build.sh will use tools/bps.py alone"
[ -x "$WORK/gbarun" ] || "$ROOT/scripts/build-emu.sh" >/dev/null 2>&1 || warn "headless emulator not built (scripts/build-emu.sh needs cmake); emulator tests will be skipped"

say "Setup complete."
[ -f "$BASE_ROM" ] || warn "No base ROM yet. Put your FireRed v1.1 ROM at original-rom/firered-rev1.gba (see original-rom/README.md)."
echo "Next: scripts/build.sh"
