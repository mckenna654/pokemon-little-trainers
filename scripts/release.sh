#!/usr/bin/env bash
# Package a release into builds/release/v<VERSION>/ (local only, never committed):
# playable ROM, verified BPS patch, checksums and release notes.
. "$(dirname "$0")/lib.sh"
"$ROOT/scripts/verify-rom.sh"
[ -z "$(git -C "$GAME" status --porcelain --untracked-files=no)" ] || die "game/ has uncommitted changes; commit and export them before a release"
"$ROOT/scripts/build.sh" clean
"$ROOT/scripts/test.sh"
out="$ROOT/builds/release/v$VERSION"
mkdir -p "$out"
cp "$ROOT/builds/$ROM_NAME.gba" "$ROOT/builds/$ROM_NAME.bps" "$out/"
rom="$out/$ROM_NAME.gba"; bps="$out/$ROM_NAME.bps"
{
  echo "# Pokémon: Little Trainers v$VERSION"
  echo
  echo "Built $(date '+%Y-%m-%d %H:%M %Z') from upstream pret/pokefirered \`$UPSTREAM_COMMIT\`"
  echo "with $(find "$ROOT/patches" -name '*.patch' | wc -l | tr -d ' ') Little Trainers patches (repo commit \`$(git -C "$ROOT" rev-parse --short HEAD)\`)."
  echo
  echo "## Files"
  echo "| File | Size | SHA-1 | SHA-256 |"
  echo "| --- | --- | --- | --- |"
  for f in "$rom" "$bps"; do echo "| $(basename "$f") | $(wc -c < "$f" | tr -d ' ') | \`$(sha1 "$f")\` | \`$(sha256 "$f")\` |"; done
  echo
  echo "## Required original ROM (not included)"
  echo "Pokémon FireRed (USA, Europe) v1.1 (Rev 1), 16,777,216 bytes"
  echo "- SHA-1 \`$BASE_ROM_SHA1\`"
  echo "- SHA-256 \`$BASE_ROM_SHA256\`"
  echo "- CRC32 \`$BASE_ROM_CRC32\`"
  echo
  echo "## How to play"
  echo "- Open \`$ROM_NAME.gba\` directly in mGBA, RetroArch (mGBA core), Delta or another GBA emulator, **or**"
  echo "- apply \`$ROM_NAME.bps\` to your own FireRed v1.1 ROM with Floating IPS / Rom Patcher JS."
  echo "- Save type: Flash 128K (auto-detected by emulators). Use a fresh save file, not a vanilla FireRed save."
  echo
  echo "## Changes, testing and known issues"
  echo "See CHANGELOG.md, docs/TESTING.md and docs/KNOWN_ISSUES.md at this commit."
} > "$out/RELEASE.md"
(cd "$out" && { shasum -a 256 "$ROM_NAME.gba" "$ROM_NAME.bps" 2>/dev/null || sha256sum "$ROM_NAME.gba" "$ROM_NAME.bps"; } > SHA256SUMS.txt)
say "Release packaged in builds/release/v$VERSION/"
ls -1 "$out"
