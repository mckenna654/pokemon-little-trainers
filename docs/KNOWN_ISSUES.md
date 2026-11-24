# Known issues and limitations

## Open
- **Rare Candy still asks which move to forget** when the move list is full (battle level-ups and
  evolution are automatic).
- **Preset cannot be changed in-game yet:** the game always runs as Little Trainer.
- **Six move types share the generic sparkle symbol** (fighting, poison, flying, dragon, dark,
  steel); Normal-type specials also use it.
- **HP numbers still show under the player's hearts**, and the opponent's hearts are the same red
  whatever its health (the original bar's green/yellow/red is not used).
- **Other menus are still words:** Start menu, Yes/No boxes, the new-game screens, the party
  screen opened by CHANGE.
- **No bag or switching in wild battles** on the Little Trainer preset (by design; healing is
  automatic). If party and PC storage are both full, CATCH only plays an error sound.
- **Status protection is shown as SAFEGUARD:** when an opponent tries a status move the game says
  the party is protected by Safeguard. Opponents' AI therefore avoids status moves.
- **Oak's battle lecture is skipped** in the first rival battle on the Little Trainer preset.
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
