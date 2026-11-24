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
- [x] Guaranteed catching of wild Pokémon; trainer Pokémon never catchable
- [x] Unlimited Poké Balls (catch works with an empty bag)
- [x] Automatic full heal after every battle
- [x] Experience ×2.5 and party-wide experience
- [x] Simplified player attacks: no PP limits, player moves do not miss
- [x] Gentler opponents: damage scaling (150% dealt / 60% taken), no enemy critical hits
- [x] Automatic move learning in battle (no "forget a move?" prompts)
- [x] No loss penalties: no money lost, friendly "need a little rest" message
- [ ] Automatic move learning outside battle (evolution scene, Rare Candy)
- [ ] Softer status conditions (sleep, paralysis, confusion, poison) and no recoil for the player
- [ ] Lower wild encounter rate; trainer party trims for the early routes
- [ ] Junior and Classic presets exercised by tests (needs a way to switch preset)
- [ ] Manual play session by a person, then tag v0.1.0

## Milestone 2 — Child-friendly battle interface (v0.2.0)
- [ ] Three big icons: Attack / Special Attack / Catch (wild) or Change (trainer); B to run
- [ ] Automatic choice of basic and special attack per Pokémon, with safe fallbacks
- [ ] Recommended action highlight
- [ ] Five-heart health display
- [ ] Simplified switching and fleeing

## Milestone 3 — First gym vertical slice (v0.3.0) — most important early milestone
- [ ] Shortened intro, safe default names, fast text
- [ ] Starter selection with large previews
- [ ] Simplified dialogue Pallet → Pewter
- [ ] Navigation assistance (story-aware objective arrow)
- [ ] Easier Viridian Forest trainers; Brock tuned so every starter can win
- [ ] Badge celebration and autosave at safe checkpoints
- [ ] Scripted emulator play-through Pallet → Boulder Badge; parent playtest checklist run

## Milestone 4 — Graphical remaster (v0.4.0, runs alongside)
- [ ] Our own UI art (icons, hearts, cursor, title branding)
- [ ] Palette pass, then tiles for the vertical-slice areas, then the rest of Kanto
- [ ] Battle backgrounds, fonts, text boxes
- [ ] Comparison screenshots for the 15 reference scenes

## Milestone 5 — Complete Kanto progression (v0.5.0)
- [ ] All gyms, Rocket events, Pokémon Tower, Safari Zone, Seafoam, Cinnabar, Victory Road, League
- [ ] HM-free field moves; puzzle simplification; trade/version exclusives obtainable

## Milestone 6 — Collection and interface (v0.9.0)
- [ ] Simplified party and storage, sticker-book Pokédex, collection celebrations
- [ ] Parent settings screen (difficulty change without restarting), custom title screen

## Milestone 7 — Optional polish (v1.0.0)
- [ ] Following Pokémon, extra navigation aids, visual rewards, post-game, device compatibility pass
