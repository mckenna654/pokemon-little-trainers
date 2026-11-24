# Known issues and limitations

## Open
- **MODE replaces BATTLE STYLE** in the OPTION menu; battle style stays on SHIFT. A child who
  opens OPTION could change MODE: it is not locked.
- **Normal-type special attacks use the generic sparkle symbol.**
- **Hearts are the same red whatever the health** (the original bar's green/yellow/red is not used).
- **Some menus are still words only:** the boy/girl choice, the bag, the party screen opened by
  CHANGE, shop lists and the "use next Pokémon?" question in battle. Yes/No boxes on the field have
  a tick and a cross.
- **The Sevii Islands trip is switched off on the Little Trainer preset.** Bill waits in Cinnabar's
  Pokémon Centre and says only that he will wait. To take the trip, switch MODE to Junior or
  Classic first. On those presets the arrow does not guide the island quest.
- **Names:** the player and rival get the game's default names unless a grown-up changes them on
  the name screen (B rubs out). Caught Pokémon keep their species names; the Name Rater in
  Lavender Town can still rename them. The Start menu has pictures but no trainer card entry on the Little and
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
