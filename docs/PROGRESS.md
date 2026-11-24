# Progress and handoff

_Last updated: 2026-11-24 (session 1)_

## Where things stand
- **Milestone 0 (environment and baseline): complete.** CI green.
- **Milestone 1 (simplified gameplay): core rules done and emulator-tested** (patches 0001–0003).
  Remaining M1 items are listed in `ROADMAP.md` (move prompts outside battle, softer status
  conditions, encounter rate, trainer trims, preset switching, a manual play session).
- **Milestones 2+: not started.** Battle menus are still the original ones.
- Graphics: strategy decided (source-level, incremental; `docs/GRAPHICS.md`); no art changed yet.

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
1. Finish Milestone 1: auto-learn in `src/evolution_scene.c` and the Rare Candy path
   (`src/party_menu.c`); softer status conditions; halve wild encounter rate
   (`src/wild_encounter.c`); emulator tests for each.
2. Milestone 2, battle interface: Attack / Special / Catch icons replacing the action menu in
   `src/battle_controller_player.c` (`HandleInputChooseAction`, `PlayerHandleChooseAction`);
   `LT_MoveScore()` already ranks moves for choosing the two attacks; Catch should set
   `gLastUsedItem = ITEM_POKE_BALL` and skip the bag; hearts in `src/battle_interface.c`.
3. Milestone 3: the Pallet → Brock slice (intro trim, objective arrow, Brock tuning, autosave).

## How to resume
```bash
cd "~/Documents/Claude Code/pokemon-little-trainers"
git status && git -C game status && git fetch --all --prune && git pull --ff-only
scripts/setup.sh --no-deps     # only if game/ or work/ is missing
scripts/build.sh && scripts/test.sh
```
