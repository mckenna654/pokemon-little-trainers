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
Engine files call a query (for example `LT_GuaranteedCatch()`) instead of hard-coding behaviour.

`LT_Rules()` returns the active preset's `struct LtRules`; `LT_BattleRulesActive()` is false in
link, Battle Tower, Trainer Tower and e-Reader battles, so those are never altered.

| Patch | Change | Engine hook (file → function) | Rule field |
| --- | --- | --- | --- |
| 0001 | Rules module, presets, move scoring | new `src/little_trainers.c`, `include/little_trainers.h`, `ld_script.ld` | — |
| 0002 | Guaranteed / easier catching | `battle_script_commands.c` → `Cmd_handleballthrow` (after the odds are computed; trainer, ghost and tutorial branches untouched) | `guaranteedCatch`, `catchRatePercent` |
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
