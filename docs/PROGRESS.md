# Progress and handoff

_Last updated: 2026-11-25 (session 6: easier-not-certain rules, diagonal arrow)_

## Session 6 — twice as easy as Junior, diagonal arrow, README (patches 0035–0038)

Jake's instructions: "if classic is normal, junior is 2.5xs easier, make little trainers twice as
easy as junior across all aspects of the game. also add diagonal directions to the arrow. build on
github once finished", then screenshots and a simpler install guide in the README.

- **Catching is no longer guaranteed on Little Trainer** (0035): five times the original odds
  (Junior 2.5). Common Pokémon are caught practically every time, a healthy Onix about one throw
  in three, legendaries a few in a hundred; weakening helps a lot. A miss costs nothing.
- **Other dials set to twice Junior** (0035): opposing Pokémon deal 50% damage (was 60%); the rival,
  Elite Four and Champion bring three Pokémon (was four). How "twice as easy" was read for each
  dial is in `docs/ACCESSIBILITY.md`. **Experience was left at ×2.5** because Jake asked earlier for
  it to be left alone (twice Junior would be ×3). Wild encounter rate (50%, Junior 75%) was left
  as pacing rather than difficulty. Both are one number each if Jake wants them changed.
- **Diagonal arrow** (0036): shown when the path turns a corner within seven steps and either
  direction is an equally good first step. See `docs/ARCHITECTURE.md`.
- **Found on the way and fixed** (0037): the battle box flashed white for up to six frames every
  time the buttons came back. It had been there since patch 0032, so it is in `v0.1.0-dev.2`.
  Also (0038) the up arrow sat further from the player than the others.
- **README**: six screenshots (committed in `docs/screenshots/` at Jake's request, a change from
  the earlier "screenshots stay local" rule: see `docs/GRAPHICS.md`), a simple "download the patch
  and add it" guide, and the build guide kept.
- **Checked on the final build** (ROM SHA-1 `7d7e33b779032bddfe3cdcaceb6a9c3b96b18314`): 34 unit
  tests, 81 emulator tests, and the whole game by arrow and A (Hall of Fame at 206 minutes of
  play). An independent reviewer examined all 26 sheets of the screen tour; its real findings were
  the white flash and a tour scene that no longer showed a beaten Pokémon, both fixed, and the
  changed scenes were looked at again afterwards.
- **Not checked:** nobody has played this build by hand; no child has tried catching with misses;
  the left, down-left and down-right arrows were not seen in the tour (they are flips of pictures
  that were); headless mGBA 0.10.5 only.
- **Open question put to Jake:** he asked for the repository to be made public. That reverses the
  project's standing rule, so it waits for his explicit confirmation after being told what it
  exposes (Nintendo-derived patch fragments and screenshots, his name and email in the history,
  session links in commit messages, issue #1). Until he confirms, the repo stays private.

## Session 5 — Jake's ChatGPT artwork is in the game (patch 0034)

Jake had ChatGPT/Codex generate the artwork (`assets/generated/v1/`, PR #2) and asked for it to
replace the drawings and be merged.

- **In the game now:** all 21 battle buttons, the Start menu pictures (Pokédex, Pokémon, bag, card,
  save, option) and the "LITTLE TRAINERS" title plaque are the generated illustrations. The ring,
  suggested-attack star, hearts, arrow, confetti, tick/cross, CLOSE and RETIRE stay pixel art (the
  pack kept them on purpose). No code or rule changed: the new build differs from the previous one
  only inside those three pictures (checked byte by byte).
- **The pack's first exports were re-done.** On the compiled title screen they read "UTTLE
  TRAINERS" and the bag was a grey lump; the source illustrations were fine, the shrinking was
  not. `assets/generated/shrink.py` (plain Python, no image library) now shrinks by vote, and
  `assets/generated/build_pack.py` uses it for every picture.
- **Pipeline:** `build_pack.py` makes `assets/generated/v1/gba/`; `assets/ui/make_battle_icons.py`
  copies those three sheets into `game/` and draws only the control symbols, so re-running it no
  longer puts the old drawings back.
- **Checked:** 32 unit tests and 74 emulator tests pass (new: `tests/emu/emu_art.py`, more in
  `tests/test_art.py`). Screen tour on the old and new builds: 216 screens each, 197 identical,
  19 different, every difference inside the title plaque, the button row or the Start menu
  pictures. A reviewer who had not seen the change examined all 19 sheets of the first export;
  its two real findings (title, bag) are what the re-export fixed. The whole-game run was not
  repeated locally (no code changed); GitHub ran it on `main` at `c18e329` and it passed.
- **Not checked:** nobody has played this build by hand; no child has been asked to name the
  pictures; 16 type symbols and the Pokédex/card pictures were seen only as enlarged previews;
  headless mGBA 0.10.5 only.
- [Codex's source and design review](REVIEW-2026-11-25.md) came with the pack. Its gameplay
  findings are **not** addressed yet: Pokémon release and item toss are unguarded, party/bag/
  storage screens still need reading, Pokémon Tower and Game Corner themes are untouched.

## Where things stand
- **The main story is playable from start to finish without reading.** An automated player that
  only walks where the arrow points and presses A completed the whole game: new game, all eight
  badges, Victory Road, the Elite Four and Champion, Hall of Fame (207 minutes of game time). It is
  a committed test: `tests/emu/emu_full_game.py`, run with `scripts/test.sh full` (about 12 minutes).
- **Milestones 0–3 and 5: done** apart from the items that need a person (manual play, parent
  playtest) and a few leftovers listed in `ROADMAP.md`.
- **Milestone 4 (graphical remaster): interface art only so far**: picture battle menu with 21
  illustrated buttons, illustrated Start menu pictures and title plaque (generated for Jake),
  plus our own hearts, Yes/No tick and cross, navigation arrow, confetti, and brighter map colours
  (`LT_VividPalette`). Tiles, sprites, battle backgrounds and fonts are original FireRed.
- **Milestones 6–7: mostly not started** (party/storage/Pokédex simplification, following Pokémon).
- All game changes are in `patches/` (38 files).
- **Pre-release `v0.1.0-dev`** (2026-11-24, at Jake's request): the BPS patch and its checksum on
  the private repo's Releases page, built from commit `a749e31`. No ROM is attached, and none ever
  should be. It does not contain the session 4 fixes or the illustrated pictures.
- **Pre-release `v0.1.0-dev.2`** (2026-11-25, at Jake's request): patch and checksum only, built
  from `main` at `c18e329` (patched ROM SHA-1 `3074c0e690ce1502423ca873a24029f83a984d7f`). It has
  the session 4 fixes and the illustrated pictures. A clean rebuild reproduced the tested build
  exactly. Further pre-releases still need Jake's say-so each time.
- **Jake's first playtest (2026-11-24)** of that build found four visible defects in the first
  five minutes (GitHub issue #1). Session 4 fixed them and four more found while looking.

## What changed in session 4 (2026-11-25)
Fixes for issue #1, each with a test that failed first: the navigation arrow's picture (its sprite
sheet was laid out the wrong way, so every arrow was two half-arrows); one attack button when
ATTACK and SPECIAL would be the same move; a new CHANGE picture (a made-up creature's head);
no Professor Oak lecture anywhere in the first rival battle on Little Trainer; no scraps at the
ends of the picture menu (it is now drawn into the message window itself); a solid plaque behind
the title words. Found on the way and also fixed: CHANGE is hidden when no other Pokémon can come
in (it led to a screen where A goes round in circles); the Professor's first Yes/No box had no
tick and cross; and the arrow walked into beaten trainers who used to wander (the whole-game run
got stuck on Route 13 because of it: see `docs/TESTING.md`). **Experience rates were not changed**
(Jake withdrew that request).

New ways of checking, because memory-reading tests had passed all of the above:
`tests/emu/emu_playtest1.py` reads screen pixels and the arrow's sprite tiles; `GBA.pixels()`
gives any test the screen; `tests/test_art.py` checks generated art; the screen tour
(`python3 -m tests.emu.screen_tour`) has honest scene labels; the `playtest` skill says to hand the
sheets to a reviewer who has not seen the change. The Superpowers plugin (systematic debugging,
test first, verify before claiming, code review) was used throughout.

## What changed in session 3
No typing or nickname questions; pre-filled name screens; shorter start; Yes/No pictures; nine
more attack symbols; HP numbers hidden; badge confetti; Rare Candy auto-learn; no "will you
switch?"; party cursor starts on a Pokémon that can battle; absorbed attack types never
recommended; Blaine's quiz doors open; Bill's island trip not started on Little Trainer;
LeafGreen exclusives in the wild; and a long list of navigation fixes found by the whole-game run
(listed in `docs/TESTING.md`).

## Verified
`docs/TESTING.md` has the tables. In short: byte-exact baseline; BPS round trip with two
independent tools; 23 unit tests; 72 regular emulator tests; the whole-game run; the screen tour
examined sheet by sheet. CI (Ubuntu) repeats the build and the regular tests on every push, and
the whole-game run on `main`.

## Unverified / open
- **The fixed build has not been played by a person.** Jake played the opening of `v0.1.0-dev`
  only. Feel, pacing and whether a child notices the arrow are unknown.
- The picture for CHANGE and the title plaque are our own first attempts: Jake has not seen them.
- **Only the mGBA 0.10.5 core has run it.** No Delta, RetroArch, handheld or real hardware check.
- A child who leaves the arrow's route is much less tested than one who follows it.
- Junior and Classic presets: menu and rule checks only, no long play.
- **Graphics (Jake's decision, 2026-11-25):** artwork comes from Jake's ChatGPT/Codex sessions;
  this project integrates it and does not draw a competing set. The first pack (interface
  pictures) is in. Further packs should arrive the same way: sources plus prompts in
  `assets/generated/`, registered in `docs/GRAPHICS.md`, shrunk with `shrink.py`, then looked at on
  compiled screens. The four PokeCommunity threads are still unreadable (HTTP 403); no outside
  sprite pack is used.

## Next actions (in order)
1. **Jake's answers wanted:** whether to make the repository public (see session 6 above); whether
   rare Pokémon are now too hard to catch on Little Trainer (a floor would be one rule); and what
   he thinks of the pictures (small Start menu pictures; CHANGE has no "swap" cue).
2. **Jake keeps playing** (and, if possible, a child will). New findings go in GitHub Issues; fix
   them the way issue #1 was fixed: reproduce, failing test, fix, playtest skill, code review.
   The parent checklist is at the end of `docs/TESTING.md`.
3. The gameplay gaps in `docs/REVIEW-2026-11-25.md`, most important first: guard Pokémon release
   and item toss on Little Trainer, then the party screen that CHANGE opens.
4. Leftovers in `ROADMAP.md`: pictures for the boy/girl choice, bag and party screens; Fly without
   a menu; missable Pokémon; storage-full handling; simpler dialogue; Milestone 6.

## How to work on it
- When goals or maps change: `python3 tools/gen_nav.py --check --why`, then `python3 tools/gen_nav.py`,
  rebuild, `scripts/export-patches.sh`. When UI art changes: `python3 assets/generated/build_pack.py` (illustrations) and/or
  `python3 assets/ui/make_battle_icons.py` (control symbols; also copies the illustrations in).
- When the arrow misbehaves somewhere: play to that place with `FireRed.follow_arrow`, saving an
  emulator state on each map change, then replay from the last state with a trace of position,
  arrow and `sPathMode`. Save states only work with the exact ROM build that made them. To keep
  building while a long run is going, point it at a copy with `LT_TEST_ROM` / `LT_TEST_SYM`.
- The whole-game run is one sample of a game with random events: any change to the ROM shifts
  the timing and so the whole history. A failure may be an old bug that this timeline happened to
  meet. Replaying from a save state changes the timing too, so reproduce from the start with a
  logging copy of the run (frame limit just past the stall, save a state there), then inspect.
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
