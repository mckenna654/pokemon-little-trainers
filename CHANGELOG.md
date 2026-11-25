# Changelog

Versions follow [Semantic Versioning](https://semver.org/); dates are AEST/AEDT.

## [Unreleased] (0.1.0-dev)
_Pre-release `v0.1.0-dev` (2026-11-24) is this list as it stood at commit `a749e31`: patch only._
### Added
- **Generated UI art handoff (not integrated):** 27 transparent AI-generated source illustrations,
  nine GBA-format graphics sheets, optional larger menu pictures, palettes, exact prompts,
  hashes and before/after previews in `assets/generated/v1/`. Claude retains gameplay/integration
  ownership; no ROM, new gameplay patch or release accompanies this pack.
- **FireRed / Little Trainers source and design review:** `docs/REVIEW-2026-11-25.md`, including
  remaining permanent-loss flows, reading requirements, retained story themes and test limits.
- **Little Trainer rules (Milestone 1)**, all switchable per preset in `src/little_trainers.c`:
  every Poké Ball catches wild Pokémon; a Poké Ball is always in the bag and is never used up;
  the party is fully healed after every battle; experience ×2.5 with half shared to Pokémon that
  did not battle; moves use no PP; the player's attacks never miss; opponents never land critical
  hits; the player deals 150% damage and takes 60%; a full move list swaps in stronger attacks
  automatically; losing a battle costs no money.
- **Picture battle menu (Milestone 2):** a row of large buttons instead of words: attack star,
  a special-attack symbol that matches the move's type (flame, drop, leaf, bolt, snowflake, rock,
  eye or sparkle), Poké Ball, and running shoe (a CHANGE picture replaces the ball against trainers).
  A pulsing ring shows the selection, a small star marks the recommended attack, the cursor starts
  on it, and the move name is shown beside the row for grown-ups. One press per action: no move
  list, no bag. Also used in the very first rival battle (Oak's battle lecture is gone on Little Trainer).
- **Hearts instead of an HP bar** (six hearts: full, half, empty) on Little and Junior presets.
- The game picks a basic and a special attack for each Pokémon. Attacks that cannot affect the
  opponent are never offered: a Pokémon with nothing usable borrows Tackle, or a typeless attack
  against Ghosts, for that battle only.
- No recoil damage for the player; the player's Pokémon cannot be put to sleep, paralysed,
  poisoned, burned, frozen or confused; running from wild Pokémon always works.
- New games start with fast text speed.
- Wild Pokémon appear half as often. Evolution never asks which move to forget and cannot be
  cancelled with B.
- **Navigation arrow:** a yellow arrow beside the player points along a walkable path to the next
  story goal, from leaving the bedroom to the Pokémon League (28 goals). It goes around people,
  knows about ledges, trees, water and lifts, and shows which way to push on stairs and door mats.
- **Title screen:** a "LITTLE TRAINERS" banner under the FireRed logo.
- **Brighter world:** every map's colours are more saturated and a little lighter.
- **Parent control:** OPTION → MODE switches between Little, Junior and Classic Trainer at any
  time (it replaces the BATTLE STYLE row). The choice is stored in the save.
- **Autosave:** the game saves by itself each time a story goal is completed (Little and Junior).
- **Losing sends you to the last town visited**, not all the way back to the last Pokémon Centre used.
- **No HM teaching:** Cut, Surf, Strength, Rock Smash and Waterfall work as soon as the HM is
  owned (the first Pokémon in the party does it); caves are never dark.
- **Simple puzzles (Little Trainer):** spin tiles do not spin, Lt. Surge's gates are off, Cinnabar
  Gym is unlocked, Victory Road's barriers are down, Silph Co.'s Card Key doors are open, the Safari
  Zone has no step limit, and lifts go straight to the floor the story needs.
- **Smaller opponent teams:** ordinary trainers bring at most 2 Pokémon, gym leaders 2 to 4
  (growing with badges), the rival, Elite Four and Champion 4; each keeps their strongest.
- **Trade evolutions** (Kadabra, Machoke, Graveler, Haunter) happen at level 36.
- **No typing (Little Trainer):** the game never asks for a nickname, and the screens for the
  player's and the rival's name open with a name already filled in and the cursor on OK, so a new
  game can be started by pressing A alone. A grown-up can press B to rub the name out and type one.
- **Shorter start:** a new game goes straight to the Professor (the six pages of written
  instructions are skipped on Little and Junior presets).
- **Pictures on Yes/No boxes:** a green tick beside YES and a red cross beside NO.
- **More attack pictures:** fist (fighting), bubbles (poison), wing (flying), hills (ground),
  ladybird (bug), ghost, blue flame (dragon), moon (dark) and cog (steel) join the first eight.
- **Hearts only:** the HP numbers under the player's hearts are gone on Little and Junior presets.
- **Badge celebration:** confetti falls for a few seconds when a Gym Badge is earned.
- **Rare Candy** teaches new moves the same automatic way as battles do (Little Trainer).
- **Trainers never stop to ask "Will you switch POKéMON?"** (Little and Junior).
- **Blaine's quiz doors are open** with the other simple puzzles.
- **No surprise island trip (Little Trainer):** after Cinnabar Gym, Bill waits in the Pokémon
  Centre instead of whisking the player off to the Sevii Islands, and does not ask there either.
  Switch MODE to Junior or Classic to take the trip.
- **LeafGreen-only Pokémon appear in the wild** (about one meeting in three where their FireRed
  counterpart lives) on Little and Junior presets.
- **The arrow now leads all the way into the Hall of Fame**, through each Elite Four room, and to a
  nearby person when the way ahead is locked. It respects ground heights (Safari Zone plateaus),
  walks around Strength boulders instead of pushing them, and keeps to the planned route's side of
  the water.
- **Next Pokémon with one button:** when the player's Pokémon gets tired in a battle, the party
  screen opens with the cursor already on one that can battle, so pressing A sends it out.
- Attacks that an ability would soak up (Water on Water Absorb, Electric on Volt Absorb, Fire on
  Flash Fire) are never offered or recommended.
- **Start menu pictures:** an icon beside each entry (Poké Ball, bag, save book, gear, exit cross,
  Pokédex, Safari flag). The trainer card entry is left out on Little and Junior presets.
- Original UI art generated by `assets/ui/make_battle_icons.py`.
- Gentle wording: Pokémon are "tired", not fainted; losing says "Your POKéMON need a little rest!".
### Fixed (after `v0.1.0-dev`, from Jake's first playtest, issue #1)
- **The arrow is one whole arrow.** Its picture was being put together from the wrong pieces (the
  top half of the up arrow over the top half of the right arrow), in every direction. It is also
  now one flat yellow with a dark outline.
- **One attack button when there is one attack.** A Pokémon with a single attacking move no longer
  gets ATTACK and SPECIAL buttons that both say the same move.
- **CHANGE has a picture of a Pokémon:** a made-up creature's head stepping in front of a greyed
  one, with an arrow, instead of two swap arrows. Our own drawing, not a copy of any Pokémon.
- **No Professor Oak lecture in the first rival battle** (Little Trainer). It was still popping up
  after the first hit and after a loss, drawn in the picture menu's colours (a rainbow frame on
  red), and again on the party screen. Junior and Classic keep the original lecture.
- **CHANGE is only offered when another Pokémon can come in.** With one Pokémon it opened a list
  where no choice worked and pressing A went round in circles.
- **Tick and cross on the Professor's "So your name is…?"** question, the one Yes/No box that
  had been missed.
- **The arrow no longer walks into a beaten trainer who used to wander.** Such a trainer stands
  still for good wherever they were beaten; the arrow was still avoiding the spot they started
  from. Once the player could Surf, this could send the arrow into the water and straight back
  out, over and over (found on Route 13 by the whole-game run).
- **Nothing left over at the ends of the picture menu.** The battle box showed scraps of tiles at
  its left and right ends whenever the buttons were up.
- **The title screen's LITTLE TRAINERS** is now on a solid plaque, so the flames and horizon behind
  it no longer run through the letters.
- Difficulty presets Little / Junior / Classic stored in save variable `0x4029` (no way to change
  it in-game yet; Little Trainer is the default).
- Project foundation on pret/pokefirered `ce6406d8` (2026-10-20) and agbcc `da598c1d`, base ROM
  FireRed (USA, Europe) v1.1. The unmodified source rebuilds byte-identical to the original ROM.
- Patch-based repository: `scripts/setup.sh`, `build.sh` (ROM + BPS), `release.sh`,
  `apply-patches.sh`, `export-patches.sh`, `verify-rom.sh`, `check-forbidden.sh`, `test.sh`.
- BPS patches created with Floating IPS and independently verified with `tools/bps.py`.
- Headless emulator testing: `tools/gbarun.c` (mGBA 0.10.5 core) and `tests/emu/` drive the real
  ROM with button presses, path-find on the game's own collision maps, and read game state.
- Emulator test covering power-on → starter → rival battle → Route 1 wild battle.
- Emulator tests for the Milestone 1 rules (confirmed to fail on unmodified FireRed) and for the
  simple battle menu.
- Graphical remaster strategy and asset attribution register (`docs/GRAPHICS.md`).
