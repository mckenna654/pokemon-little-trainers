# Testing

Compiling is not testing. Each result below says **how** it was verified:
- **Emulator (automated)**: the compiled ROM was played by script in a headless mGBA core and the
  game's memory was checked.
- **Manual**: a person played it. **Source review**: read only. **Compiled**: builds, nothing more.

## How to run
```bash
scripts/test.sh          # everything
scripts/test.sh quick    # hygiene + unit tests (no ROM needed)
python3 -m unittest tests.emu.emu_story -v     # one emulator test file
```
Screenshots from emulator tests land in `builds/screenshots/` (local only).

## How the emulator tests work
- `scripts/build-emu.sh` builds mGBA 0.10.5's core from source and `tools/gbarun.c` on top of it.
- Tests press real buttons. Nothing is patched into the ROM for testing, and no cheats are used.
- The ROM is deterministic under scripted input, so a test either always passes or always fails.
- `tests/emu/checkpoints.py` caches save states per ROM build in `work/emu-cache/` to skip replaying
  the intro; a new build invalidates the cache automatically.
- Speed: roughly 2,000 game frames per second (about 30× real time) on an M-series Mac.

## Results log
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
| Title banner, brighter map colours, solid arrow | Screenshots checked by eye | Pass |
| Long arrow-only run past Brock: Mt. Moon (correct ladders, fossil pick-up), Misty, Nugget Bridge, Bill's three steps, S.S. Ticket | Emulator (scratch script, not a committed test) | Reached; see `docs/PROGRESS.md` for how far the latest run got |

Problems that run exposed and that are now fixed: paths crossing the wrong ladder, exits covering a
whole map edge instead of one area's stretch, no path when a person or item blocks a corridor,
goals aimed at people who are moved by scripts, losing to Brock by only ever pressing the basic
attack (the test player now presses A like a child would, which uses the recommended attack), and
returning all the way home after a loss.

Not covered by automation: play beyond Brock as a continuous *committed* test; Snorlax with the Flute; Safari
Zone step limit; Silph Co. doors; Cinnabar Gym door; Strength; Sabrina, Koga and Blaine's gyms.

GitHub Actions (Ubuntu): baseline checksum match, patch build and the opening play-through passed
on the foundation commit.

## Not yet tested (be honest about it)
- Junior and Classic presets (source review only; nothing can switch preset in-game yet).
- Trainer-battle variants of the rules beyond the scripted rival fight; double battles; Safari Zone.
- Move learning during evolution or from Rare Candy still shows the original prompts.
- No manual play by a person yet. No testing on Delta, RetroArch, Pizza Boy, Steam Deck or real
  hardware. Only the mGBA 0.10.5 core has run the ROM.
- Save/load across emulator restarts, long sessions, and everything past Route 1.

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
