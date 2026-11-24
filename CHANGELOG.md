# Changelog

Versions follow [Semantic Versioning](https://semver.org/); dates are AEST/AEDT.

## [Unreleased] (0.1.0-dev)
### Added
- Project foundation on pret/pokefirered `ce6406d8` (2026-10-20) and agbcc `da598c1d`, base ROM
  FireRed (USA, Europe) v1.1. The unmodified source rebuilds byte-identical to the original ROM.
- Patch-based repository: `scripts/setup.sh`, `build.sh` (ROM + BPS), `release.sh`,
  `apply-patches.sh`, `export-patches.sh`, `verify-rom.sh`, `check-forbidden.sh`, `test.sh`.
- BPS patches created with Floating IPS and independently verified with `tools/bps.py`.
- Headless emulator testing: `tools/gbarun.c` (mGBA 0.10.5 core) and `tests/emu/` drive the real
  ROM with button presses, path-find on the game's own collision maps, and read game state.
- Emulator test covering power-on → starter → rival battle → Route 1 wild battle.
- Graphical remaster strategy and asset attribution register (`docs/GRAPHICS.md`).
