# Changelog

Versions follow [Semantic Versioning](https://semver.org/); dates are AEST/AEDT.

## [Unreleased] (0.1.0-dev)
### Added
- **Little Trainer rules (Milestone 1)**, all switchable per preset in `src/little_trainers.c`:
  every Poké Ball catches wild Pokémon; a Poké Ball is always in the bag and is never used up;
  the party is fully healed after every battle; experience ×2.5 with half shared to Pokémon that
  did not battle; moves use no PP; the player's attacks never miss; opponents never land critical
  hits; the player deals 150% damage and takes 60%; a full move list swaps in stronger attacks
  automatically; losing a battle costs no money.
- **Simple battle menu (first part of Milestone 2):** ATTACK / CATCH / SPECIAL / RUN, one press
  each. No move list and no bag: the game picks a basic and a special attack for each Pokémon
  (borrowing Tackle for Pokémon with no attacks), CATCH throws a ball directly, B does nothing,
  and running from wild Pokémon always works. Against trainers the menu is ATTACK / CHANGE / SPECIAL.
- Gentle wording: Pokémon are "tired", not fainted; losing says "Your POKéMON need a little rest!".
- Difficulty presets Little / Junior / Classic stored in save variable `0x4029` (no way to change
  it in-game yet; Little Trainer is the default).
- Project foundation on pret/pokefirered `ce6406d8` (2026-10-20) and agbcc `da598c1d`, base ROM
  FireRed (USA, Europe) v1.1. The unmodified source rebuilds byte-identical to the original ROM.
- Patch-based repository: `scripts/setup.sh`, `build.sh` (ROM + BPS), `release.sh`,
  `apply-patches.sh`, `export-patches.sh`, `verify-rom.sh`, `check-forbidden.sh`, `test.sh`.
- BPS patches created with Floating IPS and independently verified with `tools/bps.py`.
- Headless emulator testing: `tools/gbarun.c` (mGBA 0.10.5 core) and `tests/emu/` drive the real
  ROM with button presses, path-find on the game's own collision maps, and read game state.
- Emulator test covering power-on → starter → rival battle → Route 1 wild battle.
- Emulator tests for the Milestone 1 rules (confirmed to fail on unmodified FireRed) and for the
  simple battle menu.
- Graphical remaster strategy and asset attribution register (`docs/GRAPHICS.md`).
