# Known issues and limitations

## Open
- **Move prompts outside battle:** learning a move during evolution or by Rare Candy with a full
  move list still asks which move to forget (only in-battle level-ups are automatic so far).
- **Preset cannot be changed in-game yet:** the game always runs as Little Trainer.
- **Battle menus are still the original text menus** (Milestone 2 replaces them); catching goes
  through BAG → POKé BALLS → USE.
- **Trainers and gyms are not rebalanced yet** beyond the global damage scaling.
- **Graphics research incomplete:** the four PokeCommunity threads in the specification could not
  be read (HTTP 403 to automated access). Asset reuse terms are unconfirmed, so no third-party art
  is included yet. See `docs/GRAPHICS.md`.
- **Only one emulator core tested:** mGBA 0.10.5 (headless). No device compatibility is claimed.
- **No manual play yet:** all gameplay checks so far are automated.
- **Vanilla saves unsupported:** start a fresh save with Little Trainers.

## Build environment
- agbcc cannot be built in a path containing spaces; `scripts/setup.sh` works around it by building
  in a temporary directory.
- Homebrew's `mgba` formula is broken/deprecated on current macOS; the tests build mGBA's core from
  source instead. To *play* the ROM yourself, install the mGBA app from https://mgba.io/ or use any
  other GBA emulator.
- Linker warning `LOAD segment with RWX permissions` is expected and harmless.
