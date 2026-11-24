---
name: playtest
description: Playtest Pokémon Little Trainers by looking at its screens the way a player does. Use after any change to the game (graphics, menus, battle, text, navigation), before saying a build is ready, and when a person reports something that looks wrong.
---

# Playtest

The automated tests read the game's memory. A player reads the **screen**. Jake's first five
minutes of play found four defects that 80 passing tests had missed, and every one of them was
plainly visible in screenshots already on disk that nobody had examined. A playtest is the act of
examining them.

## Steps

1. **Build and run the tests**: `scripts/build.sh && scripts/test.sh`. Done when both pass.
2. **Take the screen tour**: `python3 -m tests.emu.screen_tour`. It plays the opening, the first
   rival battle, a wild battle and catch, the field menus, a gym leader battle with a beaten
   Pokémon, and a badge, and writes contact sheets plus `INDEX.txt` (which scene each tile is) to
   `builds/screenshots/tour/`. If the change added a kind of screen the tour does not reach, add
   a scene to `tests/emu/screen_tour.py` first. Done when the tour covers every screen the change
   can affect.
3. **Examine every sheet** with the Read tool, tile by tile, against the defect list below. For
   anything doubtful, open that tile's own `shot-NNN.png`. Done when every sheet has been opened
   and every tile judged clean or defective: a sheet not opened is a sheet not tested.
4. **Play as the child** when navigation, battles or story flow changed: `scripts/test.sh full`
   (new game to Hall of Fame by arrow and A only). Done when it passes, or its stopping place is
   understood.
5. **Report** to the user: the defects found, each with its sheet and tile; the scenes examined;
   and by name anything not examined. File defects in GitHub Issues (`docs/agents/issue-tracker.md`)
   unless fixing them now.

## Defect list

Judge each tile as a four-year-old's parent would, looking for:

- **Rubbish**: garbled or stray tiles, most often at the edges of windows and panels, and
  leftovers where something was removed (a lone "/", half a frame).
- **Wrong colours**: a rainbow or red box, text that is hard to read on its background, a sprite
  in another sprite's colours. Shared palettes and windows are the usual cause: two features
  using the same one.
- **Repeats**: two buttons or lines showing the same thing.
- **Words where a picture was promised**, and pictures a small child could not name.
- **Clipping and overlap**: text running out of its box, art drawn over other art (check the
  title screen), sprites cut off.
- **The arrow**: one clean arrow, visible wherever the player is free to walk, pointing somewhere
  sensible.
- **Dead ends for an A-masher**: any screen in the tour's "gave up here" tiles.

Compare with the previous tour when one exists: a tile that changed without a reason is a defect
until explained.

## Limits

The tour runs in the headless mGBA core. It proves nothing about other emulators or devices, and
nothing about sound, speed or feel. Say so in the report.
