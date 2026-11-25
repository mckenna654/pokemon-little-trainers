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

### Illustrated UI pack (in the game since patch 0034, 2026-11-25)

`assets/generated/v1/source/`: 27 transparent illustrations generated for Jake with OpenAI's
built-in image generation tool (through ChatGPT/Codex): 21 battle buttons, five Start menu
pictures and the title plaque. Exact prompts and provenance are in
`assets/generated/v1/prompts.json` and the pack's README. No external sprite pack or
ROM-extracted art was used. The capture ball refers to Pokémon's existing design; underlying
Pokémon names and designs remain with their owners. AI generation does not establish exclusive
copyright or clear third-party rights, so this stays inside the project's private,
non-commercial scope.

`assets/generated/v1/gba/` holds the three sheets as the game uses them (same sizes, frame order
and palettes as the drawings they replaced). `assets/ui/make_battle_icons.py` copies them into
`game/graphics/little_trainers/` and draws only the small control symbols itself. The pack's
two `.pal` files are not copied: they hold the same colours as the palettes the generator already
writes (only the line endings differ), so the palettes in the game did not change.

| Asset (path in `game/`) | Source | Author(s) | Stated terms | Verified how | Date |
| --- | --- | --- | --- | --- | --- |
| `graphics/little_trainers/battle_icons.png` (21 buttons), `start_menu_icons.png` (Pokédex, Pokémon, bag, card, save, option), `title_banner.png` | `assets/generated/v1/` (OpenAI image generation; shrunk to game size by `assets/generated/build_pack.py` and `shrink.py`) | Generated for Jake through ChatGPT/Codex; shrunk by this project | None claimed: AI-generated, private non-commercial use | Hashes in `manifest.json` (checked by `tests/test_art.py`); the built game is checked against the pack by `tests/emu/emu_art.py` | 2026-11-25 |
| `battle_ring.png`, `battle_marker.png` (star), `hearts.png`, `nav_arrow.png`, `confetti.png`, `yes_no_icons.png`, the cream button behind each battle picture, CLOSE and RETIRE in `start_menu_icons.png`, both palettes | Original, drawn from shapes by `assets/ui/make_battle_icons.py` | This project | Ours | n/a | 2026-11-24/25 |

The shape drawings of the battle buttons, Start menu pictures and title plaque (2026-11-24/25)
are no longer in the game. Their code stays in the generator because the pack's converter uses
it for the button frame, the icon order and its before/after previews (`--drawn` writes them).

No third-party sprite pack is in the build. Everything else is original FireRed graphics from the decompilation.

### Brighter colours without new tiles
`LT_VividPalette()` (in `src/little_trainers.c`, called from `LoadTilesetPalette` in `fieldmap.c`)
raises the saturation of every map palette by 30% and lifts mid and bright colours slightly as
the palette is loaded. It changes no tiles, no collision and no palette layout, so it cannot break
maps; it is the first, cheap step of the remaster and works with any future tileset. Tunable with
`LT_VIVID_SATURATION_PERCENT` and `LT_VIVID_LIFT`.

## Logo
`docs/logo.png` (README and share pictures) is the title plaque illustration from
`assets/generated/v1/source/title/title.png`, reduced to a third of its size with its three
colours flattened (which removes a dark smudge the generator left on the plaque).

## Screenshots
- **For the README** (`docs/screenshots/`, six pictures, committed at Jake's request on
  2026-11-25): Little Trainers screens taken from the screen tour of the released build. They
  necessarily show original FireRed artwork (maps, Pokémon, fonts) around our own interface. They
  are pictures of the game running, not extracted graphics, and the repository is private.
- **Everything else** stays in `builds/screenshots/` (git-ignored, not uploaded): the screen tours,
  test screenshots and original / Little Trainers comparison pairs. Screenshots of the unmodified
  game are generated locally from the baseline build and are never committed.
