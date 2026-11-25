# Generated UI artwork — v1

Created for Jake on 2026-11-25 with the built-in OpenAI image generation tool. **In the game since patch 0034 (2026-11-25):** `assets/ui/make_battle_icons.py` copies `gba/battle_icons.png`, `gba/start_menu_icons.png` and `gba/title_banner.png` into the game. The integration steps below are kept as the record of the handoff; one note on step 3: the two `.pal` files here are not copied, because they hold the same colours as the palettes the generator already writes (only the line endings differ).

## Look at these first

- [Battle buttons: old drawing above, illustration below](preview/battle-before-after.png): all 21 in
  the order of `manifest.json` (`battle_order`), seven to a row, enlarged four times.
- [Start menu pictures: old above, new below](preview/menu-before-after.png): the nine menu positions
  (`menu_order`), enlarged six times.
- [Title plaque](preview/title.png): the 128×32 picture enlarged eight times.
- [Actual-size menu strip](preview/menu-native.png).

The "old" pictures are this project's own shape drawings, not extracted FireRed graphics. The
large illustrations are deliberately simple and friendly; the game uses the tiny indexed exports.

## Contents

| Location | Contents |
| --- | --- |
| `source/battle/` | 21 separate transparent AI-generated source PNGs, one per existing battle icon |
| `source/menu/` | Five transparent sources: collection book, backpack, trainer card, save book, settings |
| `source/title/title.png` | Transparent source for LITTLE TRAINERS subtitle plaque |
| `gba/` | Nine four-bit indexed PNGs and two JASC palettes using the current game contracts |
| `menu-32/` | Six optional 32×32 menu pictures, including the reused capture ball; use battle palette. Future UI work only |
| `prompts.json` | Exact accepted prompt for each of the 27 source images; built-in generation mode |
| `manifest.json` | Explicit icon order, dimensions, bit depth and SHA-256 hashes |
| `../build_pack.py`, `../shrink.py` | Repeatable conversion (plain Python, no image library); writes only inside this pack |

CATCH doubles as the Pokémon Start-menu picture. The card is repeated in the two slots used by the engine. CLOSE and RETIRE retain the precise existing pixel symbols. The selection ring, recommended star, hearts, arrow, confetti and Yes/No marks also retain the project's existing pixel art. No new type, battle action or gameplay ability was added.

The 14-pixel menu drawings are constrained by the existing interface and lose facial/book detail. Larger sources and `menu-32/` are provided for a future menu redesign; those larger images cannot replace a 16-pixel sheet without code changes.

## Instructions for Claude

1. Fetch `origin/feature/generated-ui-art` and merge this asset/documentation branch into your development branch after reviewing it. Read [the review](../../../docs/REVIEW-2026-11-25.md).
2. Set up `game/` using the existing project scripts. Keep all current gameplay fixes.
3. Copy **the contents of `assets/generated/v1/gba/`** to `game/graphics/little_trainers/`. Filenames, icon order and palette indices are intentionally unchanged. This replaces three illustrations sheets: battle icons, Start-menu icons and title banner. The companion sheets preserve the current art.
4. Update `assets/ui/make_battle_icons.py` or the art pipeline to preserve/prefer the new pack. **Running the old generator after copying will overwrite the replacements.** The new conversion script is separate so this handoff does not change the development pipeline without your review.
5. Build, run regular emulator tests and the screen tour. Inspect the title over its animated background; all battle types and actions; selected and recommended overlays; the first rival battle; party-change entry; six-row Start menu; Yes/No boxes; and heart/arrow integrity. Check Junior/Classic too, since they share some UI.
6. Only after inspecting the compiled screens, commit the game graphics in `game/`, export numbered patches, update the project's handoff/test results, and push. This branch deliberately contains **no new game patch and no ROM**.

Regenerate the exports from the sources (about a minute; plain Python, nothing to install), then
copy them into the game:

```sh
python3 assets/generated/build_pack.py
python3 assets/ui/make_battle_icons.py
```

### How the pictures are shrunk (changed during integration)

The first exports were resized with an image library: smoothly for the icons, by nearest pixel for
the title. On the compiled screens two things were wrong: the title's letters had run together
(it read "UTTLE TRAINERS", with stray orange pixels), and the green bag had turned into a grey
lump, because by plain RGB distance its green is "nearer" to the menu's grey than to its greens.
The sources were fine. `shrink.py` now snaps every source pixel to the nearest game colour first
(judging colour difference more heavily than brightness) and lets each game pixel take the colour
most of its source pixels voted for. The title gives the plaque and border colours extra votes so
the gaps between letters survive, and the menu pictures leave out the pale green, which vanished
on the menu's white. All 21 battle buttons were re-exported the same way; they look the same or
slightly crisper. `tests/test_art.py` holds the title-letter and green-bag checks.

## Technical contracts and validation

- Battle: 32×672, 21 vertically stacked 32×32 frames, existing 24×24 picture area and cream buttons. Index 0 transparent; 14 reserved exclusively for the engine's pulsing ring. Existing battle palette preserved.
- Start: 16×144, nine vertical 16×16 cells; drawing limited to top-left 14×14 because rows are 15 pixels apart. Only shared menu indices 1–9 used.
- Title: 32×128 packed as four vertical 32×32 frames. Reassemble left-to-right for the 128×32 wordmark; existing title palette preserved. Solid interior enforced in conversion.
- Arrow: 16×48, vertical up/right/up-and-right frames. Hearts: 72×8. Yes/No: 16×32. These layouts must not be “tidied” into horizontal sprite sheets.
- The PNG writer preserves GBA transparency as **palette index 0**, matching the existing generator. Desktop software may show this index as magenta. Source PNGs carry real alpha; the game exports use indexed transparency conventions.
- Checked by `build_pack.py`: 27 transparent sources, nine four-bit sheets, dimensions, ring reservation, menu row spacing, repository size guard and hashes. Checked by `tests/test_art.py`: the same contracts, a solid plaque, separate title letters, a green bag, palettes, and that the generator copies these sheets. Checked by `tests/emu/emu_art.py`: the built game contains exactly these pictures.
- Looked at on compiled screens (headless mGBA, 2026-11-25): the title, the wild and trainer battle menus, the first rival battle and the Start menu. Not yet seen in the game: the Pokédex and card pictures, and the type symbols other than the attack burst and fire.

## Provenance

These are newly AI-generated illustrations, not a ripped sprite pack or Aesthetic Red assets. The capture ball intentionally refers to Pokémon's familiar design; Pokémon names/designs remain associated with their respective owners. No claim of exclusive copyright or third-party licence clearance is made for generated work. Keep this fan project non-commercial. Attribution register: `docs/GRAPHICS.md`.
