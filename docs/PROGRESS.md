# Progress and handoff

_Last updated: 2026-11-24 (session 1)_

## Where things stand
- **Milestone 0 (environment and baseline): complete.** CI green.
- **Milestone 1 (simplified gameplay): core rules done and emulator-tested** (patches 0001–0003).
- **Milestone 2 (battle interface): mechanics done and emulator-tested** (patch 0004): one-press
  ATTACK / CATCH / SPECIAL / RUN with automatic move choice. Still text labels; icons, hearts and
  the recommended-action highlight are not started.
- **Milestone 3+ : not started.**
- Graphics: strategy decided (source-level, incremental; `docs/GRAPHICS.md`); no art changed yet.
- Remaining items for each milestone are the unchecked boxes in `ROADMAP.md`.

## Verified
`docs/TESTING.md` has the full tables. In short: byte-exact baseline; BPS round trip with two
independent tools; automated emulator play from power-on to Route 1; nine automated emulator tests
of the Little Trainer rules, each proven to fail on unmodified FireRed.

## Unverified / open
- No person has played the build yet. Only the mGBA 0.10.5 core has run it.
- Junior/Classic presets are untested.
- PokeCommunity threads unread (HTTP 403): third-party asset terms unknown. Needs Jake (connect the
  Chrome extension, or paste the first post of each thread).

## Next actions (in order)
1. Milestone 3 groundwork, because it unlocks testing of everything else: extend
   `tests/emu/story.py` from Route 1 to Viridian City, the parcel errand, Viridian Forest and
   Brock, so trainer battles (and the ATTACK / CHANGE / SPECIAL layout) run under automation.
2. Use the simple menu in the first rival battle (`src/battle_controllers.c` assigns
   `SetControllerToOakOrOldMan` for `BATTLE_TYPE_FIRST_BATTLE`; check what the Oak controller
   prints at the end of that battle before bypassing it).
3. Finish Milestone 1 leftovers: auto-learn in `src/evolution_scene.c` and the Rare Candy path
   (`src/party_menu.c`); softer status conditions; lower wild encounter rate
   (`src/wild_encounter.c`).
4. Milestone 2 art: draw our own icons (attack star, type symbols, Poké Ball, arrows, shoe) and
   hearts in `assets/`, then swap the text labels in `PlayerHandleChooseAction` for tiles and add
   hearts in `src/battle_interface.c`.
5. Navigation arrow and intro trim for the Pallet → Brock slice.

## How to resume
```bash
cd "~/Documents/Claude Code/pokemon-little-trainers"
git status && git -C game status && git fetch --all --prune && git pull --ff-only
scripts/setup.sh --no-deps     # only if game/ or work/ is missing
scripts/build.sh && scripts/test.sh
```
