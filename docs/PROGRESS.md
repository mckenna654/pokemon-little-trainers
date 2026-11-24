# Progress and handoff

_Last updated: 2026-11-24 (session 1)_

## Where things stand
- **Milestone 0 (environment and baseline): complete** except the first green CI run.
- **Milestone 1 (simplified gameplay): not started.** No gameplay patches exist yet; the built ROM
  is currently identical to original FireRed v1.1.
- Graphics: strategy decided (source-level, incremental; see `docs/GRAPHICS.md`); no art changed.

## Verified this session
See `docs/TESTING.md` (2026-11-24 table): ROM validation, byte-exact baseline, BPS round trip with
two independent tools, and an automated emulator play-through from power-on to a Route 1 battle.

## Unverified / open
- PokeCommunity threads unread (403): third-party asset terms unknown. Needs Jake (Chrome extension
  or pasted thread text).
- No manual play, no other emulators or devices.

## Next actions (in order)
1. `feature/core-config`: add `include/little_trainers.h` + `src/little_trainers.c` with the
   three presets and `LT_GetDifficulty()` (default Little Trainer; storage in an unused save var).
2. Guaranteed catch + catch with an empty bag; emulator test on Route 1 (`tests/emu/checkpoints.py`
   gives a ready "route1" state).
3. Auto-heal after battle; experience multiplier + party-wide experience; no-PP/no-miss; gentler
   opponents; auto move learning; no loss penalty. One commit and one emulator test each.
4. Then Milestone 2 (battle interface).

## How to resume
```bash
cd "~/Documents/Claude Code/pokemon-little-trainers"
git status && git -C game status && git fetch --all --prune && git pull --ff-only
scripts/setup.sh --no-deps     # only if game/ or work/ is missing
scripts/build.sh && scripts/test.sh
```
