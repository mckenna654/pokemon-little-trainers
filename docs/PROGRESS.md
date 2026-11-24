# Progress and handoff

_Last updated: 2026-11-24 (session 3)_

## Where things stand
- **The main story is playable from start to finish without reading.** An automated player that
  only walks where the arrow points and presses A completed the whole game: new game, all eight
  badges, Victory Road, the Elite Four and Champion, Hall of Fame (207 minutes of game time). It is
  a committed test: `tests/emu/emu_full_game.py`, run with `scripts/test.sh full` (about 12 minutes).
- **Milestones 0–3 and 5: done** apart from the items that need a person (manual play, parent
  playtest) and a few leftovers listed in `ROADMAP.md`.
- **Milestone 4 (graphical remaster): only our own UI art so far**: picture battle menu, 17 attack
  symbols, hearts, Start menu icons, Yes/No tick and cross, navigation arrow, confetti, title
  banner, and brighter map colours (`LT_VividPalette`). Tiles, sprites, battle backgrounds and
  fonts are original FireRed. Blocked on art permissions (see below).
- **Milestones 6–7: mostly not started** (party/storage/Pokédex simplification, following Pokémon).
- All game changes are in `patches/`. `develop` and `main` are in step when this was written.

## What changed in session 3
No typing or nickname questions; pre-filled name screens; shorter start; Yes/No pictures; nine
more attack symbols; HP numbers hidden; badge confetti; Rare Candy auto-learn; no "will you
switch?"; party cursor starts on a Pokémon that can battle; absorbed attack types never
recommended; Blaine's quiz doors open; Bill's island trip not started on Little Trainer;
LeafGreen exclusives in the wild; and a long list of navigation fixes found by the whole-game run
(listed in `docs/TESTING.md`).

## Verified
`docs/TESTING.md` has the tables. In short: byte-exact baseline; BPS round trip with two
independent tools; 21 unit tests; 61 regular emulator tests; the whole-game run. CI (Ubuntu)
repeats the build and the regular tests on every push, and the whole-game run on `main`.

## Unverified / open
- **No person has played the build.** Feel, pacing and whether a child notices the arrow are unknown.
- **Only the mGBA 0.10.5 core has run it.** No Delta, RetroArch, handheld or real hardware check.
- A child who leaves the arrow's route is much less tested than one who follows it.
- Junior and Classic presets: menu and rule checks only, no long play.
- **Graphics permissions (needs Jake):** the four PokeCommunity threads named in the specification
  cannot be read by automated tools (HTTP 403), so third-party art terms are unknown and none is
  used. Either connect the Chrome extension, paste the first post of each thread, or decide that
  the remaster uses only art drawn for this project.

## Next actions (in order)
1. **Jake plays it** (and, if possible, a child does): `builds/Pokemon - Little Trainers.gba` in
   mGBA or Delta. Use the checklist at the end of `docs/TESTING.md`; record what happened there.
2. Fix what that shows, then tag v0.1.0 (ask Jake before tagging or releasing).
3. Graphics, once the permission question is answered.
4. Leftovers in `ROADMAP.md`: pictures for the boy/girl choice, bag and party screens; Fly without
   a menu; missable Pokémon; storage-full handling; simpler dialogue; Milestone 6.

## How to work on it
- When goals or maps change: `python3 tools/gen_nav.py --check --why`, then `python3 tools/gen_nav.py`,
  rebuild, `scripts/export-patches.sh`. When UI art changes: `python3 assets/ui/make_battle_icons.py`.
- When the arrow misbehaves somewhere: play to that place with `FireRed.follow_arrow`, saving an
  emulator state on each map change, then replay from the last state with a trace of position,
  arrow and `sPathMode`. Save states only work with the exact ROM build that made them. To keep
  building while a long run is going, point it at a copy with `LT_TEST_ROM` / `LT_TEST_SYM`.
- A value read from the emulator between frames can be mid-update when the game is running slow
  (a party member's species has shown up as nonsense in progress notes); check twice before
  believing a single odd reading.

## How to resume
```bash
cd "~/Documents/Claude Code/pokemon-little-trainers"
git status && git -C game status && git fetch --all --prune && git pull --ff-only
scripts/setup.sh --no-deps     # only if game/ or work/ is missing
scripts/build.sh && scripts/test.sh          # add "full" for the whole-game run
```
