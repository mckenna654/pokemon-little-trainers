#!/usr/bin/env bash
# Build Pokemon: Little Trainers.
#   scripts/build.sh            build the modified ROM into builds/ and make + verify the BPS patch
#   scripts/build.sh baseline   build the untouched upstream source; must match official v1.1 byte-for-byte
#   scripts/build.sh clean      remove build outputs in game/ (keeps tools), then build
. "$(dirname "$0")/lib.sh"
need make arm-none-eabi-as python3
[ -x "$GAME/tools/agbcc/bin/agbcc" ] || die "Run scripts/setup.sh first"
cd "$GAME" || exit 1
mkdir -p "$ROOT/builds"

if [ "${1:-}" = "baseline" ]; then
  [ -z "$(git status --porcelain --untracked-files=no)" ] || die "Commit or export game/ changes first"
  current="$(git rev-parse --abbrev-ref HEAD)"
  git -c advice.detachedHead=false checkout --quiet --detach "$UPSTREAM_COMMIT"
  say "Building unmodified upstream ($BUILD_TARGET) and comparing to the official checksum"
  rc=0; make "compare_$BUILD_TARGET" -j"$JOBS" >"$WORK/baseline.log" 2>&1 || rc=$?
  if [ $rc = 0 ]; then
    cp "poke$BUILD_TARGET.gba" "$ROOT/builds/baseline-firered-rev1.gba"
    arm-none-eabi-nm -n "poke$BUILD_TARGET.elf" > "$ROOT/builds/baseline-firered-rev1.sym"
  fi
  git checkout --quiet "$current"
  tail -n 1 "$WORK/baseline.log"
  [ $rc = 0 ] || die "Baseline build failed, see work/baseline.log"
  if [ -f "$BASE_ROM" ]; then cmp "$ROOT/builds/baseline-firered-rev1.gba" "$BASE_ROM" && echo "Baseline is byte-identical to original-rom/firered-rev1.gba"; fi
  exit 0
fi

[ "$(git rev-parse --abbrev-ref HEAD)" = "$BRANCH" ] || die "game/ is not on $BRANCH (run scripts/apply-patches.sh)"
if [ "${1:-}" = "clean" ]; then say "Cleaning"; make tidy >/dev/null 2>&1 || true; fi
dirty=""; [ -z "$(git status --porcelain --untracked-files=no)" ] || dirty="+uncommitted"
say "Building Little Trainers v$VERSION$dirty"
make "$BUILD_TARGET" -j"$JOBS" >"$WORK/build.log" 2>&1 || { grep -nE "error|Error" "$WORK/build.log" | head -n 30; die "Build failed, full log in work/build.log"; }
if grep -E "warning:" "$WORK/build.log" | grep -v "RWX permissions" | head -n 20 | grep . ; then warn "compiler warnings above (see work/build.log)"; fi

rom="$ROOT/builds/$ROM_NAME.gba"
cp "poke$BUILD_TARGET.gba" "$rom"
arm-none-eabi-nm -n "poke$BUILD_TARGET.elf" > "$ROOT/builds/$ROM_NAME.sym"   # symbol addresses for the emulator tests
cp "poke$BUILD_TARGET.map" "$ROOT/builds/$ROM_NAME.map" 2>/dev/null || true
size=$(wc -c < "$rom" | tr -d ' ')
[ "$size" -le 33554432 ] || die "ROM is $size bytes, over the 32 MiB GBA limit"
say "ROM: builds/$ROM_NAME.gba ($size bytes, sha1 $(sha1 "$rom"))"

if [ -f "$BASE_ROM" ]; then
  "$ROOT/scripts/verify-rom.sh" >/dev/null
  bps="$ROOT/builds/$ROM_NAME.bps"
  verify="$WORK/bps-verification.gba"
  rm -f "$bps" "$verify"
  if [ -x "$WORK/flips/flips" ]; then
    # Create with Floating IPS (the established tool), then verify with our independent decoder.
    "$WORK/flips/flips" --create --bps "$BASE_ROM" "$rom" "$bps" >/dev/null || die "Flips could not create the patch"
    python3 "$ROOT/tools/bps.py" apply "$BASE_ROM" "$bps" "$verify" >/dev/null || die "independent BPS apply failed"
    tool="created by Floating IPS, applied by tools/bps.py"
  else
    python3 "$ROOT/tools/bps.py" create "$BASE_ROM" "$rom" "$bps" >/dev/null
    python3 "$ROOT/tools/bps.py" apply "$BASE_ROM" "$bps" "$verify" >/dev/null
    tool="tools/bps.py only (run scripts/build-flips.sh for a cross-check with Floating IPS)"
  fi
  [ "$(sha256 "$verify")" = "$(sha256 "$rom")" ] || die "BPS verification failed: patched ROM differs from the compiled ROM"
  rm -f "$verify"
  [ "$(sha1 "$BASE_ROM")" = "$BASE_ROM_SHA1" ] || die "the original ROM changed during the build"
  say "Patch: builds/$ROM_NAME.bps ($(wc -c < "$bps" | tr -d ' ') bytes; $tool; patched SHA-256 matches the compiled ROM)"
else
  warn "No base ROM in original-rom/, so no BPS patch was made"
fi
