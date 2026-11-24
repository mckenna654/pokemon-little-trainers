#!/usr/bin/env bash
# Build the Floating IPS command-line tool (Alcaro/Flips, GPLv3) into work/flips for independent
# BPS verification. Optional: build.sh falls back to tools/bps.py when it is absent.
. "$(dirname "$0")/lib.sh"
FLIPS_COMMIT=fdd5c6e34285beef5b9be759c9b91390df486c66
mkdir -p "$WORK"
if [ ! -d "$WORK/flips/.git" ]; then git clone --quiet https://github.com/Alcaro/Flips.git "$WORK/flips"; fi
cd "$WORK/flips" || exit 1
git -c advice.detachedHead=false checkout --quiet "$FLIPS_COMMIT" 2>/dev/null || warn "pinned Flips commit not found, using $(git rev-parse --short HEAD)"
cc -O2 -w -c divsufsort.c -o divsufsort.o 2>"$WORK/flips-build.log" \
  && c++ -O2 -std=c++11 -DFLIPS_CLI -w ./*.cpp divsufsort.o -o flips 2>>"$WORK/flips-build.log" \
  || die "Flips build failed, see work/flips-build.log"
./flips --version 2>/dev/null | head -n 1 || true
echo "built work/flips/flips"
