# Progress and handoff

_Last updated: 2026-11-26 (session 11: Junior Trainer uses Little Trainer's menus, patch 0048)_

## Session 11 — Junior Trainer uses Little Trainer's menus (patch 0048)

Jake: "implement the little trainer artwork menu to junior mode as well. so junior is just more
easier from a numbers standpoint instead of menus", then "update it on the readme".
- Junior now has `simpleBattleMenu`, `noTyping` and `autoLearnMoves` on (the Start menu pictures,
  hearts and Yes/No pictures it already had). Its numbers are unchanged: PP used, attacks can miss,
  120%/80% damage, 2.5× catching, teams of 3/3/5, original puzzles, Sevii trip offered. Oak's
  text-only lecture now skips on Junior too (it is tied to the picture menu).
- When all attacks run out of PP on Junior, ATTACK borrows Tackle for that battle (the existing
  last-resort rule), so the child is never stuck.
- README, `docs/ACCESSIBILITY.md`, `docs/KNOWN_ISSUES.md`, `ROADMAP.md` and the changelog describe
  Junior this way.
- **Results on ROM SHA-1 `96e8235eafeb99425d2a0bc51e8970c16bfb4900`:** `scripts/test.sh` 55 unit and
  107 emulator tests pass; the two new Junior tests fail on dev.6. Junior battle screen looked at.
  Not played by hand; no whole-game run on Junior.
- Branch `feature/junior-picture-menus`, PR to `develop`. **Next:** Jake to merge (and say if he
  wants a dev.7 build); a whole-game run on Junior would show whether no potions mid-battle plus
  Junior's harder numbers is too tough.

## Session 10 — gentler type matchups (patch 0047)

**v0.1.0-dev.5 published** (pre-release, patch and checksum only) from `main` at `f991ca1` (PR #10),
patched ROM SHA-1 `665375d75f8d0c4ca86049d034810494ac8b284d`; CI green on `main` (whole game).
Also fixed: `apply-patches.sh` piped `git log` into `head`, which failed CI at random (exit 141)
once there were more than 40 patches.

Jake asked why Bulbasaur struggles (FireRed's own type matchups: Erika, Koga, Blaine, the rival's
Charizard), then: "dont just make special discounts for bulbasaur, maybe with little trainer only,
make type match ups a little bit easier".
- **`gentleTypes` (Little only):** applied once to the overall matchup after the type chart: the
  player's resisted hits ×1.5 (½ → ¾), the opponent's super-effective hits ×¾ (2× → 1.5×). Mixed
  matchups, immunities, messages and the Poké Dude's lessons unchanged; the suggested attack uses
  the same numbers. A first version applied it per type; code review pointed out that made mixed
  matchups 1.5× and left the suggested attack on the weaker move, so it was reworked.
- **Bulbasaur whole-game run** (`qa_journey --starter bulbasaur`), turns in the leader's battle,
  before → after: Erika 13 → 8, Koga 10 → 4, Blaine 15 → 8, Lance 15 → 10, Champion 29 → 11;
  battles lost 4 → 1; 272 → 231 minutes of play.
- **Results on ROM SHA-1 `20a1cd9ab87dd432631728cb84d403fbf279b825`:** `scripts/test.sh full` 55 unit
  and 106 emulator tests pass (whole game included). `emu_types.py` softened cases fail on dev.5.
  The Arena Trap test now gives the Diglett Arena Trap itself (its ability is random: the new
  build's random numbers gave Sand Veil). Not played by hand; mGBA core only.
- Jake: "merge all, build": **v0.1.0-dev.6 published** (pre-release, patch and checksum only) from
  `main` at `f874202` (PR #11), patched ROM SHA-1 `20a1cd9ab87dd432631728cb84d403fbf279b825`; CI green on
  `main` (whole game).
- **Next:** Jake's son playing by hand. Still waiting on Jake: D-01 to D-07, S-02 (the ring going
  back to the suggested attack), QA-09 (the arrow over people).

## Session 9 — bugs that don't change difficulty (patches 0044–0046)

Jake: "fix all bugs which dont alter gameplay difficulty anymore".
- **#8 fixed:** reproduced on the emulator first (the right-hand Pokémon in a double battle was
  offered CHANGE with nobody left), then fixed; test fails before, passes after.
- **QA-08 fixed:** the tick and cross on the shop's, bag's, Berry Pouch's, TM Case's and PC's Yes/No
  boxes (Little and Junior). Each was looked at on screen: the PC and TM Case needed another palette
  (the tick was black at first), so `YesNoPictures` now checks their colours on screen.
- **Tests:** `DoubleBattle` (#8 and a control that CHANGE still shows when the bench is free) and
  `YesNoPictures`; all fail on the dev.4 build and pass on this one. Code review: no bugs found.
- **Results on ROM SHA-1 `665375d75f8d0c4ca86049d034810494ac8b284d`:** `scripts/test.sh full` 55 unit and
  98 emulator tests pass (whole game included); the final `emu_qa_flows.py` (19 tests) passes on the
  same frozen ROM. Screen tour: 316 of 319 screens identical to the QA tour; the 3 that differ are
  the "… defeated …" line. Not played by hand.
- **Text:** "JANNE defeated …" instead of FireRed's "Player defeated …".
- **Left alone on purpose:** QA-09 (the arrow over people: cosmetic); S-01 and S-02 (they change
  battle difficulty or the moves offered); D-01 to D-07 (Jake's decisions). Version 0.1.0-dev.5:
  Jake then asked "merge and build".

## Session 8 — fixes from the QA play-through (patches 0039–0043)

**Released as pre-release `v0.1.0-dev.4`** (2026-11-26, at Jake's request): patch and checksum only,
from `main` at `e8b2d22`, patched ROM SHA-1 `ec6579987f7a43ff665e84a5eafc8d85d4d5376f`. CI green on
`develop` and `main` (whole-game run included). Issues #3–#6 closed; #8 open.

Jake: "fix all issues, build a new build for github".
- Fixed the four filed bugs and three smaller confirmed points from `docs/QA-2026-11-26.md`:
  - no TOSS and no RELEASE on Little and Junior (#3, #4; new rule `keepEverything`);
  - no evolution the game would only stop (#6);
  - no CHANGE while trapped (#5);
  - no CATCH against the Tower ghost or with a full PC;
  - RUN wins over Arena Trap and the other trapping abilities.
- **Testing:** each regression test failed on the QA build and passes on the fixed one. The screen
  tour of the fixed build matches the QA tour tile for tile (319 screens). The changed screens
  (bag menu, PC menu, trapped, ghost and full-PC battle buttons) were looked at.
- **Found by the fixes' code review:** the Berry Pouch had its own TOSS (fixed, patch 0043); a
  double-battle CHANGE case filed as #8 (not reproduced yet).
- **Left for Jake's decisions:** selling (D-02), saving after a catch (D-01), the post-game
  (D-03), MODE lock (D-04), words-only screens (D-05), story themes (D-06), and the pacing and
  attack-picture points S-01 and S-02.

## Session 7 — QA play-through and accessibility review (no gameplay changes)

Jake asked for a thorough QA pass of the current build without changing gameplay, difficulty,
experience or artwork. Report: **`docs/QA-2026-11-26.md`**.

- **Main story completed** from a fresh save with all three starters by arrow and A only (no
  memory edits). Bulbasaur is much harder late on (S-01).
- **Confirmed bugs, filed as issues:** #3 item toss (QA-01), #4 Pokémon release (QA-02), #5 CHANGE
  while trapped loops for an A-masher (QA-03), #6 Chansey/Golbat evolution that always stops
  (QA-04). Each has a regression test in `tests/emu/emu_qa_flows.py` marked as an expected failure:
  when a fix lands, remove the decorator.
- **Smaller confirmed points:** QA-05 Arena Trap still stops RUN; QA-06 CATCH offered against the
  Tower ghost; QA-07 a full PC makes CATCH only beep; QA-08 Yes/No boxes without pictures in the
  bag, shop and PC; QA-09 the arrow drawn over neighbours.
- **Decisions for Jake:** saving after catches (D-01), selling (D-02), the post-game and the end of
  the arrow (D-03), MODE not locked (D-04), words-only screens (D-05), story themes (D-06).
- **New QA tools** (not part of `scripts/test.sh`): `tests/emu/qa_journey.py` (whole game with
  pictures, a log and save states), `qa_property.py` (seeded wander / backtrack / mash / arrow
  checks with shrinking), `qa_scenarios.py` (save-reload, mode switch, shop, party, post-game from
  save states). Harness fix: `nav_arrow_shown()` checks the sprite template (QA-10).
- **Skills:** the project's playtest skill and Superpowers' systematic-debugging,
  verification-before-completion and requesting-code-review were used. Trail of Bits'
  spec-to-code-compliance and property-based-testing are not installed; their roles were covered by
  the report's spec-by-spec findings and the seeded, shrinking generated tests.

## README update — 2026-11-26

- Jake requested a more professional public README, with clear positioning for the easier
  modes, especially Little Trainer for ages 3–4. The introduction now explains that artwork
  supports written labels and shared reading; adult help may still be needed.
- Replaced the long numerical mode/catch tables with a short mode comparison linked to the
  accessibility guide. Retained screenshots, patching/build instructions, experimental Steam Deck
  guidance, contributors and actual test limitations. Removed broad assurances about independent
  play, rare catches and loss protection.
- Documentation only: no game patches, difficulty values, artwork, version, milestone status or
  known gameplay issues changed. README local links/images/anchors (28), code fences, collapsible
  section and whitespace checked. Game builds and emulator tests were not rerun for this copy edit.
- Next development actions remain those listed below; no new release was made.

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
- **The repository is public** since 2026-11-25. Jake asked for it, was told what it exposes
  (Nintendo-derived patch fragments and screenshots, his name and email in the history, session
  links in commit messages, issue #1) and confirmed. Checked beforehand: no ROMs, saves or
  credentials in the files or history, no CI artifacts, no repository secrets, and releases hold
  only patches and checksums. Checked afterwards as a signed-out visitor: the page, the README
  pictures and the patch download all open.
- **Steam Deck installer** (`steamdeck/install-little-trainers.py`): finds the player's FireRed
  v1.1, downloads the newest patch, makes the game in the GBA ROM folder and updates it when run
  again. Tested on the Mac only (see `docs/TESTING.md`): **it has not been run on a Steam Deck**.

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
  the repo's Releases page, built from commit `a749e31`. No ROM is attached, and none ever
  should be. It does not contain the session 4 fixes or the illustrated pictures.
- **Pre-release `v0.1.0-dev.2`** (2026-11-25, at Jake's request): patch and checksum only, built
  from `main` at `c18e329` (patched ROM SHA-1 `3074c0e690ce1502423ca873a24029f83a984d7f`). It has
  the session 4 fixes and the illustrated pictures. A clean rebuild reproduced the tested build
  exactly.
- **Pre-release `v0.1.0-dev.3`** (2026-11-25, at Jake's request): patch and checksum only, built
  from `main` at `1b30874` (patched ROM SHA-1 `7d7e33b779032bddfe3cdcaceb6a9c3b96b18314`). Session 6's
  changes. A clean rebuild reproduced the tested build exactly, and CI on that commit passed
  including the whole-game run. Further pre-releases still need Jake's say-so each time.
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
1. **Jake's decisions on the QA report** (D-01 to D-07), then the S-01 pacing and S-02
   attack-picture changes.
2. **Jake's answers wanted:** the QA report's decisions; whether rare Pokémon are now too hard to
   catch on Little Trainer (a floor would be one rule); how the Steam Deck installer behaves on a
   real Deck; and what he thinks of the pictures (small Start menu pictures; CHANGE has no "swap" cue).
3. **Jake keeps playing** (and, if possible, a child will). New findings go in GitHub Issues; fix
   them the way issue #1 was fixed: reproduce, failing test, fix, playtest skill, code review.
   The parent checklist is at the end of `docs/TESTING.md`.
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
