#!/usr/bin/env bash
# Run the automated checks.
#   scripts/test.sh          hygiene + unit tests + emulator tests (if the ROM and runner exist)
#   scripts/test.sh quick    hygiene + unit tests only
. "$(dirname "$0")/lib.sh"
cd "$ROOT" || exit 1
say "Repository hygiene"; scripts/check-forbidden.sh
say "Unit tests"
python3 -m unittest discover -s tests -p 'test_*.py' -t . 2>&1 | tail -n 6
[ "${PIPESTATUS[0]}" = 0 ] || die "unit tests failed"
[ "${1:-}" = "quick" ] && exit 0
if [ -x "$WORK/gbarun" ] && [ -f "$ROOT/builds/$ROM_NAME.gba" ]; then
  say "Emulator tests (real ROM in headless mGBA)"
  python3 -m unittest discover -s tests/emu -p 'emu_*.py' -t . -v 2>&1 | tail -n 40
  [ "${PIPESTATUS[0]}" = 0 ] || die "emulator tests failed"
else
  warn "Emulator tests skipped (need scripts/build-emu.sh and scripts/build.sh)"
fi
