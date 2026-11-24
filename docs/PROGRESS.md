# Progress and handoff

_Last updated: 2026-11-25 (session 2)_

## Where things stand
- **Milestone 0 (environment and baseline): complete.** CI green.
- **Milestone 1 (simplified gameplay): done and emulator-tested**, apart from the unchecked
  boxes in `ROADMAP.md` (Rare Candy prompts, trainer trims, preset switching, a manual session).
- **Milestone 2 (battle interface): done and emulator-tested** (patches 0004–0008): picture
  buttons, automatic attack choice with fallbacks, recommended-attack star, hearts, and the picture
  menu in the first rival battle. Leftovers are small (see `ROADMAP.md`).
- **Milestone 3 (Pallet → Brock slice): not started.** This is the next big piece.
- Graphics: battle UI art is our own and in the game. No tiles, sprites or backgrounds changed yet
  (`docs/GRAPHICS.md`).

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
1. Milestone 3 groundwork: extend `tests/emu/story.py` from Route 1 to Viridian City, the parcel
   errand, Viridian Forest and Brock. It gives automated coverage of ordinary trainer battles and
   is the yardstick for everything else in the slice.
2. Pictures for the other menus Jake asked about: Start menu (icon beside each entry, drawn with
   the standard menu palette), Yes/No boxes (tick and cross), and the new-game flow. The generator
   in `assets/ui/` and the blit approach in `src/little_trainers_battle_ui.c` are the pattern.
3. Intro trim and fast text by default; navigation arrow for the Pallet → Brock objectives
   (objective table keyed on story vars/flags; see the specification notes in `ROADMAP.md`).
4. Brock and Viridian Forest trainer tuning; badge celebration; autosave at safe checkpoints.
5. Small leftovers: more type symbols, hide HP numbers, storage-full message, Rare Candy prompts,
   a parent settings screen to change preset (unlocks Junior/Classic tests).

## How to resume
```bash
cd "~/Documents/Claude Code/pokemon-little-trainers"
git status && git -C game status && git fetch --all --prune && git pull --ff-only
scripts/setup.sh --no-deps     # only if game/ or work/ is missing
scripts/build.sh && scripts/test.sh
```
