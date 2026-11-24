# Building

## What you need
| | macOS (Apple Silicon or Intel) | Debian/Ubuntu, WSL |
| --- | --- | --- |
| Compiler tools | Xcode Command Line Tools, Homebrew | `build-essential` |
| Installed by `scripts/setup.sh` | `arm-none-eabi-binutils`, `arm-none-eabi-gcc` (for its preprocessor), `libpng`, `pkgconf`, `cmake` | `binutils-arm-none-eabi`, `libpng-dev`, `pkg-config`, `cmake`, `zlib1g-dev`, `python3`, `git` |
| Your own ROM | FireRed (USA, Europe) v1.1 at `original-rom/firered-rev1.gba` | same |

devkitPro is **not** required. Python 3.9+ is needed for the tools and tests (no packages).
Windows: use WSL (Ubuntu) and follow the Linux column. Docker: see the `Dockerfile` header.

## Commands
```bash
scripts/setup.sh            # one-off per machine; safe to re-run. --no-deps skips package installs
scripts/verify-rom.sh       # checks SHA-1 and SHA-256 of original-rom/firered-rev1.gba
scripts/build.sh baseline   # unmodified upstream; must print "pokefirered_rev1.gba: OK"
scripts/build.sh            # Little Trainers ROM + verified BPS in builds/
scripts/build.sh clean      # full rebuild
scripts/test.sh             # hygiene + unit tests + emulator tests   (quick: scripts/test.sh quick)
scripts/release.sh          # clean build, tests, then builds/release/v<version>/
```
Outputs (all local, git-ignored):
- `builds/Pokemon - Little Trainers.gba` — playable ROM
- `builds/Pokemon - Little Trainers.bps` — patch from FireRed v1.1 to that ROM
- `builds/Pokemon - Little Trainers.sym` — symbol addresses used by the emulator tests
- `builds/baseline-firered-rev1.gba` — unmodified reference build (for comparison screenshots)

## What setup does
1. Clones `pret/pokefirered` into `game/` and `pret/agbcc` into `work/agbcc`, at the commits in
   `upstream.lock`. pret's remote in `game/` is named `upstream` and its push URL is disabled.
2. Builds agbcc (the original-era GBA C compiler) **in a temporary directory** and copies it into
   `game/tools/agbcc`. agbcc's configure scripts fail when the path contains a space, and this
   project lives under `Claude Code/`.
3. Creates the `little-trainers` branch in `game/` at the pinned commit and applies `patches/`.
4. Builds Floating IPS (`work/flips`) and the headless emulator runner (`work/gbarun`); both are
   optional helpers and a failure only produces a warning.

## Versions used for the verified baseline (2026-11-24, macOS 26.4, Apple Silicon)
| Tool | Version |
| --- | --- |
| pret/pokefirered | `ce6406d8c2eaf46d543c8a2606de0c3cb1951982` |
| pret/agbcc | `da598c1d918402c42c0c0d7128ba14567f3175e9` |
| arm-none-eabi binutils | 2.47 (Homebrew) |
| arm-none-eabi-gcc (preprocessor only) | 16.2.0 (Homebrew) |
| libpng | 1.6.59 |
| mGBA core for tests | 0.10.5, built from source by `scripts/build-emu.sh` |
| Floating IPS | commit `fdd5c6e3` |

Homebrew's `mgba` formula is not used: on this machine its library was linked against an older
ffmpeg and would not load, and the formula is deprecated.

## Known build notes
- The linker prints `LOAD segment with RWX permissions`; it also appears for the unmodified build
  and is harmless (new binutils, old linker script).
- A matching build needs agbcc. `make modern` (GCC) is not used: it does not produce a matching ROM.

## Updating upstream (deliberate, rare)
1. Export current work (`scripts/export-patches.sh`) and commit.
2. Change `UPSTREAM_COMMIT` in `upstream.lock`; run `FORCE=1 scripts/apply-patches.sh`.
3. Fix any patch that no longer applies (`git -C game am --continue`), re-export.
4. `scripts/build.sh baseline` must still match; run all tests; record the new commit in the changelog.
