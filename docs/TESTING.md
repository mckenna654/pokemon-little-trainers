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

## Not yet tested (be honest about it)
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
