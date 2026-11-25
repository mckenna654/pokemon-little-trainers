# Roadmap

Rules: Little Trainer preset first; every feature is built, emulator-tested and documented before
the next; a milestone is tagged only when CI is green and its emulator tests pass.
Legend: [x] done and emulator-tested · [~] built, test incomplete · [ ] not started.

## Milestone 0 — Environment and baseline (→ foundation)
- [x] Original ROM located, validated (FireRed USA/Europe v1.1) and stored outside Git
- [x] pret/pokefirered + agbcc pinned; unmodified build byte-identical to the original ROM
- [x] Patch-based private repo, setup/build/release scripts, BPS creation + independent verification
- [x] Headless emulator test harness (mGBA core) with scripted play from power-on
- [x] Graphical foundation decision (docs/GRAPHICS.md)
- [x] GitHub Actions run green on the private repo (baseline checksum + emulator tests on Linux)

## Milestone 1 — Simplified gameplay (v0.1.0)
- [x] Central difficulty configuration (`little_trainers.h/.c`): Little / Junior / Classic presets
- [x] Easy catching of wild Pokémon (five times the original odds, free balls; was guaranteed until 0.1.0-dev.3); trainer Pokémon never catchable
- [x] Unlimited Poké Balls (catch works with an empty bag)
- [x] Automatic full heal after every battle
- [x] Experience ×2.5 and party-wide experience
- [x] Simplified player attacks: no PP limits, player moves do not miss, no recoil
- [x] Gentler opponents: damage scaling (150% dealt / 50% taken), no enemy critical hits
- [x] No status conditions on the player's Pokémon
- [x] Automatic move learning in battle and during evolution; evolution cannot be cancelled
- [x] No loss penalties: no money lost, friendly "need a little rest" message
- [~] Wild encounters halved (built; checked in source only, no statistical test)
- [x] Automatic move learning from Rare Candy
- [ ] Trainer party trims for the early routes
- [x] Junior and Classic presets exercised by tests (through OPTION → MODE)
- [~] Manual play session by a person, then tag v0.1.0 (Jake played the opening on 2026-11-24; his findings, issue #1, are fixed; more play needed)

## Milestone 2 — Child-friendly battle interface (v0.2.0)
- [x] One-press ATTACK / SPECIAL / CATCH (wild) or CHANGE (trainer) / RUN
- [x] Large pixel-art buttons instead of words; special-attack symbol follows the move's type
- [x] Automatic choice of basic and special attack per Pokémon, with fallbacks (Tackle, Struggle)
- [x] Recommended attack marked with a star and selected by default
- [x] Direct catch with no bag; B does nothing; running always works
- [x] Six-heart health display
- [x] Picture menu in the first rival battle (trainer layout tested there)
- [x] A symbol for every attack type except Normal (which keeps the sparkle)
- [ ] Friendly handling when party and storage are both full (currently just an error sound)
- [x] Start menu: a picture beside each entry
- [x] HP numbers hidden under the hearts; tick and cross on Yes/No boxes
- [x] No typing: no nickname questions, name screens pre-filled; trainers never ask about switching
- [ ] Pictures for the new-game boy/girl choice, the bag and the party screen

## Milestone 3 — First gym vertical slice (v0.3.0)
- [x] Navigation arrow, story-aware, from the bedroom to the Boulder Badge (points diagonally when either of two directions is right, since 0.1.0-dev.3)
- [x] An arrow-following test player completes new game → Brock using only the arrow, A and ATTACK
- [x] Fast text by default; the rival battle uses the picture menu
- [x] Brock within reach of every starter (team of 2, damage scaling, type-safe attack choice)
- [x] Shorter intro (straight to the Professor; A alone starts a game)
- [ ] Simpler dialogue on the Pallet → Pewter path
- [x] Autosave whenever a story goal is completed; respawn at the last town after losing
- [x] Badge celebration (confetti)
- [ ] Parent playtest checklist run with a real child

## Milestone 4 — Graphical remaster (v0.4.0, runs alongside)
- [ ] Our own UI art (icons, hearts, cursor, title branding)
  - 2026-11-25: battle buttons, Start menu pictures and title plaque are now the illustrations
    generated for Jake (`assets/generated/v1/`, patch 0034), checked on compiled screens. Still
    open: 16 of the type symbols and the Pokédex/card pictures have not been seen in the game, the
    Start menu pictures are small (see `docs/KNOWN_ISSUES.md`), and no child has been asked to
    name the pictures.
- [ ] Palette pass, then tiles for the vertical-slice areas, then the rest of Kanto
- [ ] Battle backgrounds, fonts, text boxes
- [ ] Comparison screenshots for the 15 reference scenes

## Milestone 5 — Complete Kanto progression (v0.5.0)
- [x] Story goals and arrow routes for all eight gyms, Rocket Hideout, Pokémon Tower, Silph Co.,
      Safari Zone and the Pokémon League (generator-validated; arrow shown at every goal in the emulator)
- [x] HM-free field moves (Cut and Surf emulator-tested), lit caves
- [x] Simple puzzles: spin tiles, Surge's gates, Cinnabar Gym lock, Victory Road barriers, Silph
      doors, Safari step limit, automatic lifts
- [x] Opponent team caps for trainers, leaders, rival and Elite Four; trade evolutions by level
- [x] The whole game played by the arrow-following test player: new game to Hall of Fame
- [x] Sabrina's teleport maze, Koga's invisible walls, Blaine's quiz, Pokémon Tower, Silph Co. and
      Victory Road passed in that play-through
- [x] LeafGreen-only Pokémon appear in the wild
- [ ] Missable Pokémon made obtainable; Fly without a menu

## Milestone 6 — Collection and interface (v0.9.0)
- [x] Parent control: OPTION → MODE (Little / Junior / Classic), saved with the game
- [x] Title screen banner
- [ ] Simplified party and storage, sticker-book Pokédex, collection celebrations

## Milestone 7 — Optional polish (v1.0.0)
- [ ] Following Pokémon, extra navigation aids, visual rewards, post-game, device compatibility pass
