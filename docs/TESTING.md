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
