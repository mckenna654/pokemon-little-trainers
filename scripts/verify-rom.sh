#!/usr/bin/env bash
# Check that the base ROM in original-rom/ is the supported FireRed v1.1 (Rev 1) dump.
. "$(dirname "$0")/lib.sh"
[ -f "$BASE_ROM" ] || die "No ROM at original-rom/firered-rev1.gba (see original-rom/README.md)"
actual="$(sha1 "$BASE_ROM")"
if [ "$actual" != "$BASE_ROM_SHA1" ]; then
  case "$actual" in
    41cb23d8dccc8ebd7c649cd8fbb58eeace6e2fdc) hint="This is FireRed v1.0. The project targets v1.1 (Rev 1)." ;;
    baa452d0b24629dd7782cfc07a8984085dde1311) hint="This is the Nintendo Switch re-release dump. The project targets GBA v1.1 (Rev 1)." ;;
    *) hint="Unknown ROM: it may be modified, trimmed, a different language, or corrupted." ;;
  esac
  die "original-rom/firered-rev1.gba has SHA-1 $actual, expected $BASE_ROM_SHA1. $hint"
fi
[ "$(sha256 "$BASE_ROM")" = "$BASE_ROM_SHA256" ] || die "SHA-256 mismatch on base ROM"
echo "Base ROM OK: FireRed (USA, Europe) v1.1, sha1 $actual"
