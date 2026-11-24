# Graphics: strategy, findings and asset attribution

## Decision (2026-11-24)
**Stay on `pret/pokefirered` and remaster the graphics at source level, incrementally.**
Pokémon Aesthetic Red is the visual *reference* (bright Gen IV/V-style tiles, cleaner UI), not a
code or patch dependency. Gameplay milestones are not blocked on graphics: the first-gym slice ships
on vanilla art if the remastered tiles are not ready, and areas are upgraded one tileset at a time.

Order of work (each step is a self-contained, testable change):
1. UI we draw ourselves: battle action icons and HP hearts (**done**), then icons for the other
   menus and title-screen branding.
2. A brighter, consistent palette pass on the general outdoor tileset (cheap, low risk, no collision
   change because metatile behaviours are untouched).
3. Replacement tiles for the vertical-slice areas (Pallet, Route 1, Viridian, Forest, Pewter), then
   buildings/interiors, then the rest of Kanto.
4. Battle backgrounds, fonts/text boxes, then optional extras (following Pokémon, music).

## Why not the alternatives
| Option | Finding | Verdict |
| --- | --- | --- |
| Apply Aesthetic Red (any edition) as a patch | A binary patch for **FireRed v1.0** ("Squirrels" 1636) built on the **CFRU + DPE** engine and Leon's ROM base. Our ROM is v1.1 and compiled from source; every offset differs, and CFRU replaces the battle engine our accessibility work modifies. No source code found. | Not possible. Reference only. |
| Port Aesthetic Red's assets | Assets are not offered as a separately licensed pack that we could confirm; reuse terms unverified (see "Unverified" below). | Only individual assets whose terms are established. |
| FireRed Extended | Binary hack with large gameplay expansion (new regions, later-generation Pokémon). Opposite of our scope. | Rejected. |
| LibertyTwins "Patches Pack" (fonts, HP bars, menus, text boxes) | Binary patches for a clean FireRed v1.0 at fixed offsets. Cannot be applied to a source build; the *ideas* (cleaner font, B/W-style boxes) can be re-implemented in source. | Re-implement, do not apply. |
| LibertyTwins "Sprites Pack" / `Shiny-Miner/GBA-Binary-hacking-assets` | Raw image assets (tilesets, battle backgrounds, overworlds, trainer sprites) prepared for binary hacking; the repo README describes them as "free to use assets and resources (with credits)", with artist names in file names, but there is **no licence file**. Images need converting to the decomp's 16-colour indexed tiles and metatiles. | Candidate source, per-asset check + credit. |
| An existing graphically enhanced *decomp* base for FireRed | None found that is maintained, documented and graphics-only. pokeemerald-expansion is Emerald-based and brings a new battle engine. | Rejected. |
| Original pixel art by us | Always permitted; slowest. Used for all UI and wherever terms cannot be established. | Default for UI. |

## Technical notes for integration
- Tilesets live in `game/data/tilesets/` (4bpp indexed PNG + `.pal` + metatiles + metatile attributes).
  **Replacing tile pixels or palettes does not change collision**; collision and behaviour live in the
  map's collision layer and the metatile attributes. Changing metatile *composition* or behaviours
  needs Porymap and a collision re-test of every map using that tileset.
- GBA limits per map: primary + secondary tileset share 640 + 384 tiles and 13 background palettes
  (7 primary, 6 secondary in FRLG), 16 colours each. Gen IV/V art must be colour-reduced to fit.
- Tools: Porymap (map/tileset editor), porytiles (tileset compiler), the decomp's own `gbagfx`.
- Battle sprites are 64×64, 16 colours: DS-era sprites fit the size but need palette reduction.
- Following Pokémon needs an overworld sprite for every species (151+) and object-event engine
  work; no ready FireRed-decomp implementation was found. Scheduled as optional (Milestone 7).
- Music: FRLG's sound engine supports the existing instrument set only; "remastered" music means
  new sequenced tracks. Not started; lowest priority.

## Unverified (needs Jake's help)
The four PokeCommunity threads named in the specification could not be read directly: the site
returns HTTP 403 to automated access, and the Chrome extension was not connected. The findings
above come from search-engine summaries of those threads, the projects' listings on other sites,
and the public GitHub asset repository. **Exact reuse terms and credit requirements stated in the
threads are not confirmed.** Until they are, no third-party asset is committed. To unblock: connect
the Claude Chrome extension (or paste the first post of each thread).

## Asset attribution register
Every non-original asset must be listed here *before* it is committed.

| Asset (path in `game/`) | Source | Author(s) | Stated terms | Verified how | Date |
| --- | --- | --- | --- | --- | --- |
| `graphics/little_trainers/battle_icons.png`, `battle_ring.png`, `battle_marker.png`, `hearts.png`, `battle_icons.pal` | Original, generated by `assets/ui/make_battle_icons.py` | This project | Ours | n/a | 2026-11-24 |
| `graphics/little_trainers/start_menu_icons.png`, `nav_arrow.png`, `title_banner.png`, `title_banner.pal` | Original, same generator | This project | Ours | n/a | 2026-11-24 |
| `graphics/little_trainers/yes_no_icons.png`, `confetti.png`, nine more type symbols in `battle_icons.png` | Original, same generator | This project | Ours | n/a | 2026-11-24 |
| CHANGE button (a made-up creature's head, in `battle_icons.png`), redrawn `nav_arrow.png` and `title_banner.png` | Original, same generator (`creature_head`, `nav_arrow_sheet`, `title_banner`); the head is two circles for ears on an oval, not based on any Pokémon | This project | Ours | n/a | 2026-11-25 |

No third-party art is in the build. Everything else is original FireRed graphics from the decompilation.

### Brighter colours without new tiles
`LT_VividPalette()` (in `src/little_trainers.c`, called from `LoadTilesetPalette` in `fieldmap.c`)
raises the saturation of every map palette by 30% and lifts mid and bright colours slightly as
the palette is loaded. It changes no tiles, no collision and no palette layout, so it cannot break
maps; it is the first, cheap step of the remaster and works with any future tileset. Tunable with
`LT_VIVID_SATURATION_PERCENT` and `LT_VIVID_LIFT`.

## Comparison screenshots
Kept locally in `builds/screenshots/` (git-ignored, not uploaded) as original / Little Trainers pairs, produced by
`tests/emu/` runs. Screenshots of the original game are generated locally from the baseline build.
