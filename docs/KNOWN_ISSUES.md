# Known issues and limitations

## Open
- **Move prompts outside battle:** learning a move during evolution or by Rare Candy with a full
  move list still asks which move to forget (only in-battle level-ups are automatic so far).
- **Preset cannot be changed in-game yet:** the game always runs as Little Trainer.
- **Battle menu uses words, not icons yet:** ATTACK / CATCH / SPECIAL / RUN are text until our own
  icon art is drawn.
- **First rival battle still shows the original FIGHT/BAG menu** (it runs on Oak's tutorial
  controller). Pressing A twice still attacks.
- **Trainer-battle menu (ATTACK / CHANGE / SPECIAL) is untested** by automation.
- **No bag or switching in wild battles** on the Little Trainer preset (by design; healing is
  automatic). If party and PC storage are both full, CATCH only plays an error sound.
- **Type immunities:** a Pokémon whose only attacks cannot affect the opponent (Normal moves
  against a Ghost) can still only run or, against trainers, change Pokémon.
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
