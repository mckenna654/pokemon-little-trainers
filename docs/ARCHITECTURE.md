# Architecture

## 1. Repository design: modifications only
```
pokemon-little-trainers/
├── patches/         our game changes as numbered git patches (the ONLY game code on GitHub)
├── scripts/         setup, build, release, patch export/apply, ROM check, guards, tests
├── tools/           bps.py (BPS create/apply), gbarun.c (headless emulator runner)
├── tests/           unit tests (test_*.py) and emulator tests (emu/emu_*.py)
├── assets/          our own source art and working files (see docs/GRAPHICS.md)
├── docs/            documentation
├── upstream.lock    pinned pret/pokefirered + agbcc commits, base-ROM checksums
├── VERSION
├── game/            (ignored) pret/pokefirered checkout, branch little-trainers = pin + patches
├── work/            (ignored) agbcc, mGBA core, Flips, logs, emulator caches
├── original-rom/    (ignored except README) your FireRed v1.1 ROM
└── builds/          (ignored) ROM, BPS, symbols, screenshots, release packages
```
`game/` is a normal git clone of pret's repository. Our work is commits on its local branch
`little-trainers`. `scripts/export-patches.sh` writes those commits to `patches/` with
`git format-patch`; `scripts/apply-patches.sh` rebuilds the branch from the pinned commit plus
`patches/`. A fresh clone of this repo therefore reproduces the exact game source with
`scripts/setup.sh`, without this repo ever containing it.

### Licensing
- `pret/pokefirered` has **no licence file** (GitHub reports none). The C source is a
  reverse-engineered reconstruction of Game Freak's code, and the repository contains the game's
  graphics, maps, text and music data. None of it is ours to redistribute, so none of it is
  committed here, private or not. Patches necessarily quote a few lines of surrounding source as
  context; that is the minimum needed to describe a change.
- Our own code inside the patches, and everything else in this repo, is original work.
- A BPS patch contains only the bytes that differ from the original ROM, but those bytes include
  recompiled game code. Sharing BPS patches is the long-standing norm for ROM hacks, yet it is not a
  licence: patches are generated locally, git-ignored, and only attached to a private release if
  Jake asks.
- ROMs (original and modified), BIOS, saves and save states never enter Git. Enforced by
  `.gitignore`, the pre-commit hook and CI (`scripts/check-forbidden.sh`, including a history scan
  and GBA-header content detection so a renamed ROM is still caught).
- Third-party art: see the register in `docs/GRAPHICS.md`.
- mGBA (MPL-2.0) and Floating IPS (GPL-3.0) are fetched and built locally as tools; not vendored.

## 2. Base ROM and build target
FireRed (USA, Europe) v1.1 ("Rev 1"), game code `BPRE`, version byte 1, 16 MiB,
SHA-1 `dd5945db9b930750cb39d00c84da8571feebf417`. Upstream target `firered_rev1`
(`GAME_REVISION=1`), compiled with agbcc. v1.0 was the specification's first preference; v1.1 is
used because it is the ROM Jake owns, upstream supports it with a byte-exact build, and the
project builds from source so binary-hack tool compatibility (the usual reason to prefer v1.0) does
not matter. One revision only.

## 3. Source map (verified in `game/` at the pinned commit)
| System | Where |
| --- | --- |
| Battle flow, end of battle | `src/battle_main.c` (`BattleMainCB2`, `ReturnFromBattleToOverworld` ~3915, `CreateNPCTrainerParty` ~1539) |
| Battle script commands | `src/battle_script_commands.c`: `Cmd_accuracycheck` ~1003, `Cmd_critcalc` ~1170, `Cmd_typecalc` ~1274, `Cmd_getexp` ~3113, `Cmd_handlelearnnewmove` ~5102, `Cmd_handleballthrow` ~9463 |
| Battle scripts (text flow) | `data/battle_scripts_1.s`, `data/battle_scripts_2.s` |
| Player battle menus | `src/battle_controller_player.c`: `PlayerHandleChooseAction` ~2412, `HandleInputChooseMove` ~437, `MoveSelectionDisplayMoveNames` ~1370 |
| Health boxes / HP bars | `src/battle_interface.c` (`UpdateHealthboxAttribute` ~1772) |
| Damage formula | `src/pokemon.c` `CalculateBaseDamage` ~2385 |
| Battle start/end glue, whiteout | `src/battle_setup.c` (`CB2_EndWildBattle` ~422, `CB2_EndTrainerBattle` ~906), `src/overworld.c` `CB2_WhiteOut` ~1545 |
| Party healing | `src/script_pokemon_util.c` `HealPlayerParty` |
| Moves and learning | `src/pokemon.c` `GiveMoveToMon` ~2208, `MonTryLearningNewMove` ~2288; learnsets `src/data/pokemon/level_up_learnsets.h` |
| Evolution | `src/pokemon.c` `GetEvolutionTargetSpecies` ~5025; table `src/data/pokemon/evolution.h`; scene `src/evolution_scene.c` |
| Giving/storing Pokémon | `src/pokemon.c` `GiveMonToPlayer` ~3686; PC `src/pokemon_storage_system*.c` |
| Wild encounters | `src/wild_encounter.c` `StandardWildEncounter` ~355; tables `src/data/wild_encounters.json` |
| Trainers | `src/data/trainers.h`, `src/data/trainer_parties.h` |
| Maps, warps, NPCs, scripts | `data/maps/<Map>/map.json` + `scripts.inc`; layouts `data/layouts/` |
| Flags and vars | `include/constants/flags.h`, `include/constants/vars.h` (stored in SaveBlock1) |
| Save system | `src/save.c` (`TrySavingData` ~701), `src/load_save.c`; layout `include/global.h` |
| Bag, shops, items | `src/item.c`, `src/item_menu.c`, `src/shop.c`, `src/item_use.c` |
| Title screen | `src/title_screen.c` (`CB2_InitTitleScreen` ~342), `graphics/title_screen/` |
| Tilesets | `data/tilesets/`, headers `src/data/tilesets/` (640 primary + 384 secondary tiles; 7 + 6 palettes) |
| Text | `charmap.txt`, strings in `src/strings.c` and `data/text/` |
| Music | `sound/songs/`, `sound/song_table.inc` |
Line numbers drift as patches land; search by function name.

## 4. Little Trainers code (kept current as features land)
All rules flow through one module so engine edits stay small and reversible:
- `include/little_trainers.h`: preset enum, tunable constants (`LT_*`), rule query functions.
- `src/little_trainers.c`: `LT_GetDifficulty()` and helpers.
Engine files ask the rules (for example `LT_Rules()->healAfterBattle`) instead of hard-coding behaviour.

`LT_Rules()` returns the active preset's `struct LtRules`; `LT_BattleRulesActive()` is false in
link, Battle Tower, Trainer Tower and e-Reader battles, so those are never altered.

| Patch | Change | Engine hook (file → function) | Rule field |
| --- | --- | --- | --- |
| 0001 | Rules module, presets, move scoring | new `src/little_trainers.c`, `include/little_trainers.h`, `ld_script.ld` | — |
| 0002, 0035 | Easier catching: the original odds times a factor (Little 5, Junior 2.5), never a certainty | `battle_script_commands.c` → `Cmd_handleballthrow` (after the odds are computed; trainer, ghost and tutorial branches untouched) | `catchRatePercent` |
| 0002 | Free Poké Balls | `battle_main.c` → `CB2_InitBattle` calls `LT_OnBattleStart()` (adds one ball if the bag has none, wild battles only); `item_use.c` → `BattleUseFunc_PokeBallEtc` does not remove the ball | `freeBalls` |
| 0002 | Heal after battle | `battle_main.c` → `ReturnFromBattleToOverworld` (runs after experience, evolution and catching) | `healAfterBattle` |
| 0002 | Boosted and party-wide experience | `battle_script_commands.c` → `Cmd_getexp` cases 1–2 (bench share reuses the Exp. Share path; bench message suppressed) | `expPercent`, `benchExpPercent` |
| 0002 | No PP use | `battle_script_commands.c` → `Cmd_ppreduce` | `infinitePP` |
| 0002 | Player attacks never miss | `battle_script_commands.c` → `Cmd_accuracycheck` (after Protect and semi-invulnerable checks) | `playerNeverMisses` |
| 0002 | No enemy critical hits | `battle_script_commands.c` → `Cmd_critcalc` | `enemyNoCrits` |
| 0002 | Damage scaling | `battle_script_commands.c` → `Cmd_damagecalc` via `LT_ScaleDamage()` (fixed-damage moves are not scaled) | `playerDamagePercent`, `enemyDamagePercent` |
| 0002 | Automatic move replacement | `battle_script_commands.c` → `Cmd_handlelearnnewmove` via `LT_ChooseMoveSlotToReplace()` / `LT_MoveScore()` | `autoLearnMoves` |
| 0002 | No money lost on defeat | `overworld.c` → `ComputeWhiteOutMoneyLoss` returns 0 | `noLossPenalty` |
| 0003 | Gentle wording ("tired", "need a little rest") | `battle_message.c`, `strings.c`, `data/text/white_out.inc` | all presets |
| 0004 | Simple battle menu: ATTACK / CATCH or CHANGE / SPECIAL / RUN | `battle_controller_player.c` → `LtHandleInputSimpleMenu` (called from `HandleInputChooseAction`), `PlayerHandleChooseAction` (labels), `PlayerHandleChooseMove` (answers with the chosen slot, no move list), `PlayerHandleChooseItem` (answers `ITEM_POKE_BALL`, no bag); labels in `battle_message.c` | `simpleBattleMenu` |
| 0004 | Attack selection and Tackle fallback | `little_trainers.c` → `LT_ChooseAttackSlots()`; the borrowed move is flagged in `gDisableStructs[].mimickedMoves` so it is never written to the party | `simpleBattleMenu` |
| 0004 | Running always succeeds | `battle_main.c` → `TryRunFromBattle` | `alwaysRunAway` |

| 0005 | Picture battle menu (buttons, ring, recommended star, word label) | new `src/little_trainers_battle_ui.c`; `battle_controller_player.c` calls `LT_BattleMenu_Show/MoveCursor/Tick/Hide`; art in `graphics/little_trainers/` | `simpleBattleMenu` |
| 0005 | Attacks that cannot affect the opponent are never offered; Struggle (typeless) is the last resort | `little_trainers.c` → `EffectiveScore()`, `LT_ChooseAttackSlots()`, `LT_RecommendedAttack()` | `simpleBattleMenu` |
| 0005 | No recoil for the player | `battle_script_commands.c` → `SetMoveEffect` (`MOVE_EFFECT_RECOIL_25/33`) | `noPlayerRecoil` |
| 0006, 0028 | Picture menu in the first rival battle, no Oak lecture | `battle_controllers.c` (player controller instead of Oak's), `battle_controller_opponent.c` (lecture lines after the first hit and after a loss), `party_menu.c` (lecture on the party screen), all via `LT_OakBattleLectureActive()` | `simpleBattleMenu` |
| 0007 | Fewer wild encounters | `wild_encounter.c` → `DoWildEncounterRateTest` | `encounterRatePercent` |
| 0007 | Status protection (permanent Safeguard on the player's side) | `battle_main.c` → `BattleStartClearSetData` calls `LT_OnBattleDataCleared()` | `playerStatusShield` |
| 0007 | No move questions during evolution; B cannot cancel evolution | `evolution_scene.c` (both evolution tasks, `tCanStop`) | `autoLearnMoves`, `noEvolutionCancel` |
| 0008 | Heart health display | `battle_interface.c` → `MoveBattleBarGraphically` uses `LT_HeartTile()` | `heartHealth` |
| 0009 | Start menu pictures; trainer card entry dropped | `start_menu.c` → `PrintStartMenuItems`, `SetUpStartMenu_NormalField/SafariZone`; `new_menu_helpers.c` → `CreateStartMenuWindow` (8 tiles wide instead of 7; the menu owns 91 tiles from `0x13D`, so at most six entries) | `menuIcons` |

| 0010 | Fast text by default | `new_game.c` | all presets |
| 0011 | Opponent team caps | `battle_main.c` → `CreateNPCTrainerParty` via `LT_TrainerPartyCap()` | `trainerPartyCap`, `leaderPartyCap`, `bossPartyCap` |
| 0012 | Field moves without teaching HMs; lit caves | `scrcmd.c` → `ScrCmd_checkpartymove`, `field_player_avatar.c` → `PartyHasMonWithSurf`, `overworld.c` → `SetDefaultFlashLevel`, via `LT_CanUseFieldMove()` | `hmFree` |
| 0013 | Trade evolutions by level, easier friendship evolutions | `pokemon.c` → `GetEvolutionTargetSpecies` | `tradeEvoLevel`, `friendshipEvoThreshold` |
| 0014–0015, 0033 | Navigation arrow | new `src/little_trainers_nav.c`, generated `src/data/little_trainers_nav.h`; hooks in `overworld.c` (`CB1_Overworld`) and `malloc.c` (`InitHeap`) | `navArrow` |
| 0016 | Simple puzzles | `little_trainers.c` → `LT_OpenPuzzleGates()` (called before map transition scripts in `overworld.c`), `field_player_avatar.c` (spin tiles), `safari_zone.c` (step limit), `little_trainers_nav.c` (lifts) | `simplePuzzles` |

| 0017 | MODE option (parent control) | `option_menu.c` (BATTLE STYLE row repurposed), strings | all presets |
| 0017 | Respawn at the last town visited | `heal_location.c` → `LT_SetRespawnForCurrentMap()`, called from `LT_OnMapTransition()` | `autoRespawn` |
| 0018 | Autosave when a story goal is completed | `start_menu.c` → `LT_AutoSave()` (reuses the save dialog from the "SAVING..." step), triggered in `little_trainers_nav.c` | `autoSave` |

### Navigation arrow
- **Goals:** `tools/nav/objectives.json` lists the story goals in order; each has a "done"
  condition (flag set, variable reached, item owned) and a target (a person, a sign, a tile or
  just a map). The current goal is the first one not done.
- **Routes (offline):** `tools/gen_nav.py` reads every map's collision, warps and connections and
  models the world as areas joined by doors, map edges, one-way ledges and lifts. Trees, boulders
  and water only count as passable once the goal says the player has Cut, Strength or Surf, and
  each goal can list maps to avoid (Saffron's gates before the Tea, Snorlax routes before the
  Flute, Cycling Road). For each goal it writes, per map, up to two exits to head for, and it
  fails loudly if a goal cannot be reached from the one before. Warp events on tiles that can
  never trigger are ignored.
- **Path (in game):** `BuildField()` flood-fills outwards over the live map (`VMap`) from the
  target and from the exit listed for each separate area of the map, storing for each tile the
  direction to walk. Ledges are followed one way. Obstacles: people who stand still, trees and
  boulders the player cannot clear yet (taken from the map's object list, because distant objects
  are not spawned; an object the game has on the map is blocked where it is now, since a wandering
  trainer stops for good where they were beaten and a boulder stays where it was pushed), and
  every door or ladder that is not being aimed for. Three passes are tried:
  around standing people; around everyone (when the arrow ran into a walker); and, if there is no
  way round, straight up to whoever or whatever blocks the way, so the player talks to it, fights
  it or picks it up. People already dealt with are then routed around. The path is rebuilt after
  every conversation, battle or menu. The field lives on the heap and is forgotten when the heap
  is reset.
- **Diagonal arrows (patch 0036):** the player can only step up, down, left or right, so a
  diagonal arrow is a promise that either of its two directions is a good step. `SecondDirection()`
  follows the path up to seven steps ahead (about what is on screen); if it turns a corner, and
  the path from the tile beside the player in the corner's direction joins that same path without
  costing a step, the arrow points between the two. Otherwise it stays straight. `sShownDir` is
  always the path's own next step and `sShownDir2` the other direction (0 for a straight arrow).
  `nav_arrow.png` has three frames stacked (up, right, up-and-right); the other five directions
  are flips.
- **Route data format:** `sLtNavExits` is a pool of exit lists (count, then exit/from/to triples;
  an exit is a map edge with the stretch of tiles to use, or a warp number); each route has one
  `u16` offset per map. About 1 KB of lists plus 850 bytes per route.
- **Arrow:** a 16×16 sprite beside the player (above, below, left or right), drawn with the
  player's own palette. Hidden during conversations, cut-scenes and menus. On stairs and exit
  mats it shows which way to push.
- **Lifts:** with simple puzzles on, stepping into a lift sets its destination to the floor the
  current goal needs (`sLtNavLifts`), so no floor menu is involved.
- Re-run `python3 tools/gen_nav.py` after changing goals or maps (`--check --why` explains failures).

The simple menu is off in the old man's catching lesson, the Poké Dude lessons and the Safari Zone,
which run on their own battle controllers.

### How the picture menu is drawn
- It is drawn into the message window itself (`B_WIN_MSG`, 224×32), and
  `PutWindowRectTilemapOverridePalette` shows that window's tiles with background palette 7 while
  the menu is up. No extra window, so no extra memory. (It first borrowed `B_WIN_OAK_OLD_MAN`,
  which is two tiles narrower and shares the message window's tile memory: the box's end columns
  then showed scraps of the menu's pixels.)
- Palette 7 is the one the original game only uses for Professor Oak's tutorial text.
  `LT_OakBattleLectureActive()` is the one rule that keeps the two apart: with the picture menu
  on, none of the lecture runs (Oak's own controller, the opponent controller's lines after the
  first hit and after a loss, and the party screen's explanation of the list).
- A button has a **slot** (`LT_MENU_*`: what it does, and the value the cursor holds) and a
  **position** (where it is drawn). A button is only shown when it does something of its own
  (`SlotShown`): SPECIAL is left out when it would be the same move as ATTACK, and CHANGE when no
  other Pokémon can come in. The rest close up to the left (`SlotPosition`).
- `graphics/little_trainers/battle_icons.png` is a strip of 32×32 buttons;
  `BlitBitmapToWindow` copies one per slot (palette index 0 is transparent). The selection ring is
  a second blit on top; `LT_BattleMenu_Tick()` pulses palette index 14 between yellow and white.
- The background does not scroll to the original menu page (`gBattle_BG0_Y` stays 0).
  `LT_BattleMenu_Hide()` redraws the empty message window, which clears the buttons and puts the
  window's own palette back on its tiles.
- **Nothing is sent to the screen until the menu is fully drawn.** Drawing the buttons takes
  several frames of the console's time, and copies to video memory are carried out at the next
  frame from whatever the window holds then. `LT_BattleMenu_Show()` therefore asks for one copy,
  at the very end (it stops the message printer with `B_TEXT_FLAG_WINDOW_CLEAR`, which despite
  its name means "leave the window alone"). Asking earlier showed the half-drawn box for up to six
  frames, in the message box's colours.
- `gActionSelectionCursor[battler]` holds the selected button's slot (`LT_MENU_*`).
- Sprite sheets with more than one frame (`nav_arrow.png`, `title_banner.png`) stack their frames
  **vertically**. The game reads a sheet one frame's worth of tiles at a time in image rows, so
  frames placed side by side come out as a mix of each other's halves.
- `assets/ui/make_battle_icons.py` writes every sheet into `game/graphics/little_trainers/`. It
  draws the control symbols from shapes (ring, star, hearts, arrow, confetti, tick and cross) and
  copies the three illustrated sheets (battle buttons, Start menu pictures, title plaque) from
  `assets/generated/v1/gba/`. To change an illustration, change the pack
  (`python3 assets/generated/build_pack.py`: plain Python, about a minute), then re-run the generator. `--drawn` writes
  the old shape drawings instead, for comparison only.
- Hearts are 9 tiles (`hearts.png`) indexed with the health box's own palette; the engine still
  computes the bar exactly as before and asks for a tile per 8-pixel slice.

Preset values (Little / Junior / Classic) are the table at the top of `src/little_trainers.c`.

## 5. Save data
The save layout is unchanged. Custom state lives in script variables FireRed leaves unused (they
are inside SaveBlock1 and covered by the normal checksums):

| Variable | Name | Meaning | Default |
| --- | --- | --- | --- |
| `0x4029` | `VAR_LT_DIFFICULTY` | 0 Little Trainer, 1 Junior, 2 Classic; unknown values are treated as 0 | 0 (new game) |
 Vanilla FireRed saves are **not** supported input: use a fresh save.

## 6. Testing architecture
`tools/gbarun.c` wraps mGBA's core (no window or audio) behind a line protocol; `tests/emu/gba.py`
drives it; `tests/emu/firered.py` reads game state from RAM using symbol addresses from the build
(`builds/*.sym`), decodes `struct Pokemon`, and walks using the game's own collision data
(`tests/emu/maps.py`). `tests/emu/story.py` scripts real button presses through the story.
Details and results: `docs/TESTING.md`.

## 7. Hardware limits we respect
ARM7TDMI, 240×160, 256 KiB EWRAM / 32 KiB IWRAM, 96 KiB VRAM, 128 sprites, 16-colour palettes,
32 MiB maximum ROM (currently 16 MiB, checked by `scripts/build.sh`), Flash 128K save.
