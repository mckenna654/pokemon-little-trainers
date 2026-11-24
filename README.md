<div align="center">

# Pokémon: Little Trainers

**A graphically remastered, preschool-friendly Pokémon FireRed modification: simplified combat,
accessible exploration, visual navigation, easier catching and child-friendly progression.**

![status](https://img.shields.io/badge/status-early%20development-orange)
![base](https://img.shields.io/badge/base-FireRed%20v1.1-red)
![platform](https://img.shields.io/badge/platform-GBA-blue)
![repo](https://img.shields.io/badge/repo-private-lightgrey)

</div>

Little Trainers adapts Pokémon FireRed for children aged three to six: a child who cannot read
should be able to choose a Pokémon, explore, catch, battle, evolve and earn badges with very little
adult help. It is a real GBA ROM hack built from the
[pret/pokefirered](https://github.com/pret/pokefirered) decompilation, and it runs on any standard
GBA emulator.

**This repository contains no ROMs and no game source.** It holds only our changes (as patches),
build scripts, tests and documentation. You supply your own FireRed ROM.

## Status
See [docs/PROGRESS.md](docs/PROGRESS.md) for exactly what is built and how it was tested, and
[ROADMAP.md](ROADMAP.md) for what is next.

## Quick start (macOS, Linux, Windows via WSL)
```bash
git clone https://github.com/mckenna654/pokemon-little-trainers.git
cd pokemon-little-trainers
scripts/setup.sh            # tools, pinned decomp source into game/, our patches applied
cp /path/to/your/firered.gba original-rom/firered-rev1.gba
scripts/verify-rom.sh       # must be FireRed (USA, Europe) v1.1
scripts/build.sh            # -> builds/Pokemon - Little Trainers.gba  and  .bps
scripts/test.sh             # unit tests + automated play-through in a headless emulator
```
Play `builds/Pokemon - Little Trainers.gba` in mGBA, RetroArch, Delta or another GBA emulator, or
apply `builds/Pokemon - Little Trainers.bps` to your own FireRed v1.1 ROM with any BPS patcher.

More: [docs/BUILD.md](docs/BUILD.md) · [docs/TESTING.md](docs/TESTING.md)

## Documents
| File | Purpose |
| --- | --- |
| [ROADMAP.md](ROADMAP.md) · [CHANGELOG.md](CHANGELOG.md) | Milestones and history |
| [docs/PROGRESS.md](docs/PROGRESS.md) | Current status, unverified items, next action |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Repo design, source map, every change, licensing |
| [docs/ACCESSIBILITY.md](docs/ACCESSIBILITY.md) | Design rules for preschool players, parent checklist |
| [docs/GRAPHICS.md](docs/GRAPHICS.md) | Remaster strategy and asset attribution |
| [docs/BUILD.md](docs/BUILD.md) · [docs/TESTING.md](docs/TESTING.md) · [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md) | Building, testing, limitations |
| [AGENTS.md](AGENTS.md) / [CLAUDE.md](CLAUDE.md) | Instructions for Claude sessions |

## Credits and legal
Pokémon and Pokémon FireRed are © Nintendo, Creatures Inc. and GAME FREAK inc. This is an unofficial,
non-commercial fan project with no affiliation. The decompilation is the work of the
[pret](https://pret.github.io/) contributors; mGBA (MPL-2.0) and Floating IPS (GPL-3.0) are used as
local build/test tools and are not redistributed. Never share ROM files.
