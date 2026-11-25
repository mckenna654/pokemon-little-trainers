# Testing

Compiling is not testing. Each result below says **how** it was verified:
- **Emulator (automated)**: the compiled ROM was played by script in a headless mGBA core and the
  game's memory was checked.
- **Emulator (automated, screen)**: the same, but the test reads what is drawn: the pixels of the
  screen, or a sprite's picture as the console holds it.
- **Screen tour**: every sheet of `python3 -m tests.emu.screen_tour` examined tile by tile.
- **Manual**: a person played it. **Source review**: read only. **Compiled**: builds, nothing more.

## How to run
```bash
scripts/test.sh          # everything except the whole-game run
scripts/test.sh quick    # hygiene + unit tests (no ROM needed)
scripts/test.sh full     # everything, plus the whole game played by following the arrow (several minutes)
python3 -m unittest tests.emu.emu_story -v     # one emulator test file
```
Screenshots from emulator tests land in `builds/screenshots/` (local only).

**Looking at the screens** is a separate step from the tests: `python3 -m tests.emu.screen_tour`
plays through the screens a child sees and writes contact sheets to `builds/screenshots/tour/` for
a reviewer to inspect one by one. The procedure is the `playtest` skill
(`.claude/skills/playtest/SKILL.md`).

## How the emulator tests work
- `scripts/build-emu.sh` builds mGBA 0.10.5's core from source and `tools/gbarun.c` on top of it.
- Tests press real buttons. Nothing is patched into the ROM for testing, and no cheats are used.
- The ROM is deterministic under scripted input, so a test either always passes or always fails.
- `tests/emu/checkpoints.py` caches save states per ROM build in `work/emu-cache/` to skip replaying
  the intro; a new build invalidates the cache automatically.
- Speed: roughly 2,000 game frames per second (about 30× real time) on an M-series Mac.

## Results log
### 2026-11-25 — Illustrated artwork integrated (patch 0034)

Build: ROM SHA-1 `3074c0e690ce1502423ca873a24029f83a984d7f`. Emulator: headless mGBA 0.10.5 only.

| Check | Method | Result |
| --- | --- | --- |
| The game contains the pack's three pictures and none of the old drawings | `tests/emu/emu_art.py` (looks for each picture's bytes in the ROM); failed before the change | Pass |
| Nothing else in the ROM changed | Byte comparison with the previous build (rebuilt from its patch): 4,416 bytes differ, all inside the battle buttons, Start menu pictures and title plaque | Pass |
| Title letters are separate; plaque is solid | `tests/test_art.py`; the letter test failed on the first export (LITTLE came out as four shapes) | Pass |
| The bag is a green bag | `tests/test_art.py`; failed on the first export (13 green pixels, 85 grey) | Pass |
| Pictures fit the game's limits (sizes, menu rows, ring colour, palettes), generator copies the pack | `tests/test_art.py` | Pass |
| Regular suite | `scripts/test.sh`: 32 unit tests (34 after two colour-matching tests were added), 75 emulator tests (1 skipped: the opt-in whole-game run) | Pass |
| Screens, old build against new | Screen tour of each (216 screens each, checkpoints warm): 197 identical; 19 differ, every differing pixel inside the title plaque, the battle button row or the Start menu picture column | Pass |
| Changed screens looked at | Title, wild battle menu, trainer battle menu (with CHANGE), Start menu, enlarged, by Claude; all 21 buttons and 9 menu pictures as enlarged previews | No defects seen; doubts in `docs/KNOWN_ISSUES.md` |
| Independent look at every sheet | A reviewer with no knowledge of the change examined all 19 sheets of the **first export** | Found the title ("UTTLE TRAINERS", stray pixels) and the bag (unnameable); both fixed by re-exporting. Its other points were present before the change (see below) |
| Whole game by arrow and A | Not repeated locally: no code changed. GitHub ran it on `main` at `c18e329` (run 45528579646) | Pass (CI) |
| Release build | `scripts/release.sh`: clean rebuild, then the suite again (34 unit tests, 75 emulator tests, 1 skipped). Same ROM and patch hashes as the build tested above; the published patch applied to the original ROM gives SHA-1 `3074c0e6…` | Pass |

The reviewer's other points, each checked against the old build's tour, where the same pixels
appear: hearts jumping in the forced leader fight (the tour writes HP to memory, as its labels
say); the player's pixels at the edge of the save box; the small suggested-attack mark that reads
as a dot; uneven confetti pieces; the player's name differing between the tour's first part and
the rest (two separate runs). They are recorded in `docs/KNOWN_ISSUES.md` where they matter.

A lesson for comparing tours: the first comparison showed whole battles differing, which was not
the artwork. A tour that has to create its checkpoints plays out differently from one that loads
them. Compare tours taken the same way (see the playtest skill).

**Not tested:** play by a person or a child; any other emulator or device; 16 of the type
symbols and the Pokédex and card pictures on a compiled screen; Junior and Classic screens (they
share the same pictures; only their existing automated checks ran).

### 2026-11-25 — Codex artwork pack and source review (before integration; Codex's own record)

- All 33 existing patches replayed cleanly on pinned upstream; local `game/` remains clean.
- 23 existing unit tests passed (`python3 -m unittest discover -s tests -p 'test_*.py' -t . -v`).
- Navigation check passed: 30 goals, 25 route tables, 425 maps. Expected notes: Surge/Blaine
  routes do not solve Junior's original barriers.
- `assets/generated/build_pack.py` validated 27 transparent source PNGs and nine four-bit
  graphics sheets: dimensions, palette range, reserved ring colour, menu row spacing, solid title
  interior, per-source size limit and hashes. Six optional larger menu icons also exported.
- Visually examined: every old/new battle pair (21), every Start-menu position (nine), and the
  reduced/reassembled title plaque. Corrected a transparent hole in the title export.
- **Not performed:** new ROM compilation, baseline comparison, emulator tests, screen tour,
  whole-game play-through, audio checks or device/child play. This is an asset handoff for
  Claude to integrate and verify; earlier game results below were not rerun in this session.

### 2026-11-24 — foundation (baseline build, no gameplay patches)
| Check | Method | Result |
| --- | --- | --- |
| Original ROM is FireRed (USA, Europe) v1.1 | SHA-1, SHA-256, CRC32, header fields | Pass |
| Unmodified source rebuilds byte-identical to the original ROM | `scripts/build.sh baseline` + `cmp` | Pass |
| BPS created by Floating IPS, applied by `tools/bps.py`, SHA-256 equals compiled ROM | `scripts/build.sh` | Pass |
| Guard blocks ROMs (by name and by content), saves, states, patches, keys, history leftovers | 6 unit tests | Pass |
| BPS encoder/decoder | 8 unit tests | Pass |
| Power-on → new game → bedroom | Emulator (automated) | Pass |
| Leave house, Oak cut-scene, choose Charmander | Emulator (automated) | Pass |
| Rival battle won by pressing only A | Emulator (automated) | Pass |
| Walk to Route 1, wild battle starts | Emulator (automated) | Pass |

### 2026-11-24 — Milestone 1 rules, Little Trainer preset (patches 0001–0003)
All **Emulator (automated)**, `tests/emu/emu_milestone1.py`, starting on Route 1 with Charmander.
Control run: the same nine tests were run against unmodified FireRed
(`LT_TEST_BASELINE=1`) and the eight that existed at the time all failed there, as they should.

| Rule | What the test does | Result |
| --- | --- | --- |
| Catch with an empty bag, at full health; ball not used up | Two wild Pokémon caught in a row through BAG → POKé BALLS → USE; party grows to 3; ball count stays 1 | Pass |
| Heal after battle | Takes damage for three turns, wins; HP full and status clear afterwards | Pass |
| No PP use | PP identical after using two moves | Pass |
| Attacks never miss | Accuracy forced to −6 in RAM; every Scratch over four battles still hits | Pass |
| Damage scaling, no enemy criticals | Damage taken and dealt compared with every value the Gen 3 formula allows at 60% / 150%; ranges do not overlap the original's | Pass |
| Experience ×2.5 and bench share | Exact experience gained by the battler and by a benched Pokémon | Pass |
| Auto-learn: better attack | Full move list of status moves + Scratch; level 13 swaps Growl for Metal Claw, no prompt | Pass |
| Auto-learn: skip useless move | Level 19 Smokescreen is not learned over existing attacks | Pass |
| Losing | Faints to a wild Pokémon: no money lost, sent home, party restored | Pass |

Also checked by eye from emulator screenshots: the new "is tired!" / "need a little rest!" text
fits its boxes.

### 2026-11-24 — Simple battle menu (patch 0004)
All **Emulator (automated)**, `tests/emu/emu_milestone2.py`. The Milestone 1 tests were rewritten
to play through the new menu and still pass.

| Check | Result |
| --- | --- |
| ATTACK is one press, never opens the move list, uses the basic move (Scratch) | Pass |
| SPECIAL uses the Pokémon's own-type move (Ember) | Pass |
| With one attack only, both buttons use it | Pass |
| A Pokémon with only Growl and Leer borrows Tackle; its real moves are unchanged afterwards | Pass |
| CATCH is one press with an empty bag, at full health, twice in a row; the bag never opens | Pass |
| RUN works three times in a row with speed forced to 1 | Pass |
| Pressing B ten times in the menu does nothing | Pass |
| Menu shows the four actions (screenshot checked by eye; later replaced by pictures) | Pass |

### 2026-11-25 — Picture menu, hearts and remaining rules (patches 0005–0008)
All **Emulator (automated)** unless marked. 30 emulator tests in total now pass.

| Check | Result |
| --- | --- |
| Picture menu appears; ring moves with LEFT/RIGHT and stops at both ends; UP/DOWN/B do nothing | Pass |
| Cursor starts on the recommended attack (Ember over Scratch), then stays where the player left it | Pass |
| With one attack only, the cursor starts on the first button | Pass |
| Opponent turned into a Ghost in RAM: Scratch is not offered, a typeless attack is borrowed, it does damage, and there is no recoil | Pass |
| First rival battle uses the picture menu in trainer layout (ATTACK, SPECIAL, CHANGE; no RUN) and is won by pressing A | Pass |
| Opponent that only knows Thunder Wave: the player's Pokémon is never paralysed over four turns | Pass |
| Benched Pokémon evolves (Caterpie → Metapod) while the test taps B throughout: evolution is not cancelled, Harden is skipped with no question, moves unchanged | Pass |
| Buttons, ring, recommended star, label text, hearts (full / half / empty) | Screenshots checked by eye |
| Wild encounter rate halved | Source review only |
| Start menu opens with pictures, has no trainer card entry, closes with EXIT and with B | Pass |
| SAVE from the new Start menu, then power cycle and CONTINUE: same map, position, Pokémon, level and money | Pass |
| Start menu and save dialog drawn cleanly | Screenshots checked by eye |

Patches containing the new art were re-applied from scratch and rebuilt to the identical ROM.

### 2026-11-25 — Navigation, HM-free moves, team caps, simple puzzles (patches 0011–0016)
All **Emulator (automated)**. 48 emulator tests in total.

| Check | Result |
| --- | --- |
| **Arrow-only play-through:** a test player that only walks where the arrow points, presses A when there is no arrow or something is in the way, and presses ATTACK in battle goes from a new game to the Boulder Badge (starter, rival, parcel, Pokédex, Viridian Forest, Brock) | Pass (about 43 minutes of game time, 63 s to run) |
| Story goals file is consistent with the maps: all 28 goals reachable in order | Pass (`gen_nav.py --check`) |
| At every goal from Misty to the Pokémon League, with the story state recreated by script, the game picks that goal and shows an arrow | Pass |
| Ordinary trainer with three Pokémon brings two; Lt. Surge brings two with no badges and three with three; Lorelei brings four including Lapras | Pass |
| Cut a tree and Surf with a Charmander that knows neither move, once the HM and badge are held; refused before | Pass |
| Rock Tunnel is lit | Pass |
| Kadabra evolves into Alakazam at level 36 with no trade | Pass |
| Lift in the Rocket Hideout opens on B4F when Giovanni is the goal, with no floor menu | Pass |
| Spin tile does not carry the player away | Pass |
| Lt. Surge's gates are open and the arrow leads to him | Pass |
| Victory Road's first rock barrier is walkable | Pass |

### 2026-11-25 — Autosave, presets, banner, colours, long arrow-only run (patches 0017–0019)
| Check | Method | Result |
| --- | --- | --- |
| OPTION → MODE changes Little → Junior and the value is kept | Emulator (automated) | Pass |
| Classic preset shows the original FIGHT menu and move list | Emulator (automated) | Pass |
| Junior preset keeps the arrow but shows the move list | Emulator (automated) | Pass |
| Autosave fires when a goal is completed and the game carries on | Emulator (automated), as part of the arrow play-through | Pass |
| Title banner, brighter map colours, solid arrow | Screenshots checked by eye | Pass, **wrongly**: the arrow was in fact drawn from the wrong pieces and the banner was hard to read (see the playtest section below). A glance at a small screenshot is not a check |
| **The whole game by arrow** (`tests/emu/emu_full_game.py`): one continuous play from a new game, pressing only the arrow's direction and A, nothing set up behind the game's back: all eight badges, Victory Road, the Elite Four and Champion, into the Hall of Fame | Emulator (automated, opt-in: `scripts/test.sh full`) | **Pass**: Hall of Fame after 207 minutes of game time (12 minutes to run). Badges at 17, 33, 60, 88, 123, 140, 171 and 180 minutes; the starter was Lv 68 at the eighth badge |
| No typing: A alone starts a new game with real names; catching and gift Pokémon ask for no nickname | Emulator (automated) | Pass |
| Tick and cross on Yes/No boxes (pixel colours read from the window) and A still answers yes | Emulator (automated) | Pass |
| Trainers never ask about switching; a beaten Pokémon is replaced by pressing A | Emulator (automated) | Pass |
| Rare Candy teaches the new move without the "forget a move" screen | Emulator (automated) | Pass |
| Confetti appears when a badge is earned and stops by itself | Emulator (automated) | Pass |
| The arrow leads through all five League rooms (trainer first, then the door) to the credits | Emulator (automated; set-up jumps the story forward and makes the test Pokémon sturdy) | Pass |
| LeafGreen-only Bellsprout turns up beside Oddish on Route 6 (40 wild meetings) | Emulator (automated) | Pass |
| Hearts without numbers, new type symbols, shorter intro | Screenshots checked by eye | Pass |

Problems the whole-game run exposed, all fixed: ground heights ignored (Safari Zone plateaus,
where surfing can start and stop); the arrow planning without Surf while the game allowed it (an
hour lost circling the Safari Zone); a town's other areas pulling the path over a one-way ledge;
locked doors with guards (the arrow now leads to people nearby when there is no way onward);
standing on a tile that was occupied when the path was made; Blaine's quiz doors; being carried off
to the Sevii Islands by pressing A at Bill; a Strength boulder pushed into a dead end in Victory
Road (the arrow now walks around boulders); the League rooms' shut doors; a Water attack
recommended against a Lapras that absorbs water; and the party screen that could not be passed
with A after a Pokémon was beaten. Earlier ones: wrong ladders, exits covering a whole map edge,
people or items blocking corridors, people moved by scripts, and returning home after a loss.

Still not covered by automation: the Junior preset's unsimplified puzzles; optional areas; what
happens when the player wanders off the arrow's route for a long time.

GitHub Actions (Ubuntu): baseline checksum match, patch build and the regular emulator tests pass
on every push; the whole-game run is an extra step for `main`.

### 2026-11-25 — Jake's first playtest and the fixes (issue #1, patches 0027–0033)
**Manual (Jake, 2026-11-24):** `v0.1.0-dev` in mGBA 0.10.5 on Windows, from a new game into the
first rival battle. He reported: the arrow "bugged"; the same word on both attack buttons; swap
arrows on CHANGE that say nothing about Pokémon; "wrong colour in text during fight". Every one
was plainly visible in screenshots the tests had already saved, and no test had looked.

| Check | Method | Result |
| --- | --- | --- |
| Each defect reproduced on the released build before any change | Screenshots, tile-map dump, enlarged crops | Reproduced: all four, plus scraps of tiles at both ends of the picture menu and a hard-to-read title banner |
| The arrow is one whole arrow (two sides match, a point at the front, one tail), read from the sprite's tiles and flip bits, pointing up or down and sideways | Emulator (automated, screen) | Pass (failed on the old build) |
| The picture menu fills the box: both end columns are plain panel | Emulator (automated, screen) | Pass (failed on the old build) |
| One attack → one attack button; RIGHT from ATTACK lands on CATCH; two attacks → two buttons | Emulator (automated, screen) | Pass (failed on the old build) |
| When the second attack goes away mid-battle the ring returns to ATTACK and each picture stays on the button that does what it shows | Emulator (automated, screen; set-up edits the move list) | Pass |
| First rival battle, won and lost: Oak's lecture window is never written in | Emulator (automated) | Pass (failed on the old build) |
| Classic preset still gets Oak's lecture (also proves the check above looks in the right place) | Emulator (automated) | Pass |
| First rival battle with one Pokémon: ATTACK is the only button | Emulator (automated, screen) | Pass (failed before the fix) |
| First rival battle with a second Pokémon (set-up: gift by script): CHANGE then A alone sends it out, and nobody explains the party screen | Emulator (automated) | Pass (failed before the fix) |
| The Professor's "So your name is…?" box has the tick and the cross | Emulator (automated) | Pass (failed before the fix) |
| Title words sit on a solid plaque (no see-through pixels except the rounded corners) | Unit test on the generated art | Pass (failed on the old art) |
| New CHANGE picture, title plaque clear of the logo, PRESS START and Charizard | Screen tour and enlarged crops, by eye | Pass |
| A beaten wandering trainer standing north of the boardwalk corner on Route 13 (set-up: story flags by script; the battle itself is real): the arrow leads round him on foot | Emulator (automated) | Pass (failed before the fix: the arrow looped into the water and back) |
| Regular suite | `scripts/test.sh` | 23 unit tests and 72 emulator tests pass |
| The whole game by arrow, on the build with all these fixes | `scripts/test.sh full` equivalent on a copy of the ROM | **Pass** on the final build (ROM SHA-1 `1c3dbcc5…`): Hall of Fame after 206 minutes of game time; badges at 17, 34, 60, 86, 122, 140, 168 and 177 minutes. The build just before it **failed** (see below) |
| Screen tour, all 19 sheets, on the build with every screen change (the one before the arrow's people fix, which draws nothing new); two sheets looked at again on the final build | An agent that had not seen the changes, given the defect list; key sheets also by the author | No defects on any of the 19 sheets (225 screens). One doubt noted: the wing picture for Flying attacks is hard to name. Not shown by the tour: a left-pointing arrow, the party screen opened by CHANGE, a real badge award in a gym |

How the work was checked: the screen tour was examined before the fixes by an agent given only the
defect list (it found Jake's four problems unprompted, and the title banner), again after the
fixes, and once more on the finished build. A separate code review of the changes found that Oak
still lectured on the party screen if CHANGE was pressed in the first battle, and that CHANGE with
a single Pokémon led to a list where pressing A goes round in circles; both are fixed and tested
above.

**The whole-game run failed once on the way.** The build with every battle fix stopped after the
sixth badge: an hour of play going in and out of the water at one corner of Route 13. The cause
was older than this session and had nothing to do with battles: the arrow's map of people used
where each person started, not where they are, and a beaten wandering trainer no longer moves.
The run before it had passed only because its trainer happened to be beaten on a harmless tile.
One passing whole-game run is one sample of a game with random events, not proof. The tour tool itself had mislabelled scenes (Start menu entries that showed no menu, a
"winning" battle that was lost); it is corrected.

Not covered: nobody has played the fixed build by hand; the left-pointing arrow was not seen in
the tour (it is the right arrow flipped, and the test honours the flip); CHANGE while held in
place by Mean Look or Arena Trap.

## Not yet tested (be honest about it)
- **Very little manual play.** Jake played the opening and first battle of `v0.1.0-dev`; nobody
  has played the build with the fixes. Nearly everything above is automated. How the game *feels* to a
  child (pace, clarity of the pictures, whether the arrow is noticed) is untested.
- **No device testing.** Only the mGBA 0.10.5 core has run the ROM: not Delta, RetroArch, Pizza
  Boy, a Steam Deck or real hardware.
- Double battles, link features, the Trainer Tower and the Sevii Islands under the new rules.
- Junior preset beyond its menu and move-list checks (its puzzles are not simplified, so the arrow
  can stop at gym barriers).
- Storage filling up (party and all PC boxes full).
- Loading a save made by an older Little Trainers build after an update.

## Parent playtest checklist (first-gym demo; to be used at Milestone 3)
Sit beside the child, do not help unless they ask, and note:
1. Could they start a new game and get out of the house alone?
2. Did they understand how to pick a starter? Which one, and why?
3. In battle, did they find Attack without reading? Did they find Catch?
4. Did they ever look lost? Where? For how long before they asked for help?
5. Did any battle feel too long, or any moment upset them?
6. Did they notice the Pokémon being healed / getting stronger / evolving?
7. Could they get through Viridian Forest? Did they find Brock?
8. What made them smile? What did they ask to do again?
9. How long did they play before stopping on their own?
Record answers in this file under a dated heading.
