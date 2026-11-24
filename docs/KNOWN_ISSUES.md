# Known issues and limitations

## Open
- **Rare Candy still asks which move to forget** when the move list is full (battle level-ups and
  evolution are automatic).
- **Preset cannot be changed in-game yet:** the game always runs as Little Trainer.
- **Six move types share the generic sparkle symbol** (fighting, poison, flying, dragon, dark,
  steel); Normal-type specials also use it.
- **HP numbers still show under the player's hearts**, and the opponent's hearts are the same red
  whatever its health (the original bar's green/yellow/red is not used).
- **Some menus are still words only:** Yes/No boxes, the new-game screens, the bag, and the party
  screen opened by CHANGE. The Start menu has pictures but no trainer card entry on the Little and
  Junior presets.
- **No bag or switching in wild battles** on the Little Trainer preset (by design; healing is
  automatic). If party and PC storage are both full, CATCH only plays an error sound.
- **Status protection is shown as SAFEGUARD:** when an opponent tries a status move the game says
  the party is protected by Safeguard. Opponents' AI therefore avoids status moves.
- **Oak's battle lecture is skipped** in the first rival battle on the Little Trainer preset.
- **Beyond Brock is only checked goal by goal.** The arrow has been shown to appear at every story
  goal, but no continuous play-through past the first gym has been run. Expect rough edges in
  dungeons (Mt. Moon, Rock Tunnel, Pokémon Tower, Silph Co.).
- **The arrow follows the main story only.** It does not guide to Pokémon Centres, shops or
  optional areas, and Fly still needs the party menu.
- **Arrow and gates that the map data cannot see:** inside Sabrina's, Koga's and Blaine's gyms and
  the Pokémon Mansion the arrow may stop at a barrier or teleporter.
- **The Pokémon Mansion is skipped** on the Little Trainer preset (Cinnabar Gym is already
  unlocked), so its items and Pokémon are optional.
- **Opponent levels are unchanged**; only team sizes and damage are reduced.
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
