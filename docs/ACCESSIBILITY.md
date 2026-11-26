# Accessibility: designing for a four-year-old

## Who we are building for
A child of three to six who: cannot read sentences; recognises colours, shapes, pictures and
favourite Pokémon; understands simple cause and effect; presses A a lot; opens menus by accident;
has little patience for repetition; does not understand type charts, inventories or statistics.
**Goal:** they can start the game, choose a Pokémon, explore, catch, win battles, watch evolutions
and earn badges with very little adult help.

## Rules every feature must pass
1. **No reading required** for anything on the critical path, **but the words stay.** A picture
   comes first and its word sits beside it. The pictures are there to help a child learn the
   words, not to replace reading (Jake, 2026-11-25): do not remove a word because a picture now
   says the same thing, and give a new picture its word.
2. **Mashing A is safe.** It must never discard a Pokémon or item, overwrite a save, or pick a
   harmful option. The default option is always the kind one.
3. **Nothing is lost for good.** No money loss, no permanently missed Pokémon, no released Pokémon,
   no dead ends. Losing a battle means "your Pokémon need a little rest", then try again.
4. **Short and rewarding.** Wild battles 1–3 hits, trainers 2–4, gym leaders 3–5. No grinding.
5. **Always know where to go.** A visible hint towards the next goal, without blocking free roaming.
6. **The child still plays.** Choices stay meaningful (which Pokémon, which attack, whether to
   catch). We remove friction, not agency. Not every battle is a one-hit win.
7. **Colour is never the only signal.** Shape, position or animation backs it up.
8. **Calm visuals.** No rapid flashing, no cluttered backgrounds behind important things.
9. **No engagement tricks.** No timers, streaks, daily rewards or pressure to keep playing.
10. **Still Pokémon.** Kanto, the gyms, the characters and the sense of adventure stay.

## Difficulty presets
| | Little Trainer (3–4, default) | Junior Trainer (5–6) | Classic Trainer (7+) |
| --- | --- | --- | --- |
| Catching | 5× the original odds, no balls needed, a miss costs nothing | 2.5× the original odds | Original |
| Damage dealt / taken | 150% / 50% | 120% / 80% | Original |
| Type matchups | Resisted hits by the player do ¾ (not ½); super-effective hits on the player do 1.5× (not 2×); mixed matchups unchanged | Original | Original |
| Rival, Elite Four, Champion bring | At most 3 Pokémon | At most 5 | Original teams |
| Healing | Automatic after every battle | Automatic | Pokémon Centres |
| Experience | ×2.5, whole party | ×1.5, whole party | Original |
| Battle menu | Picture buttons (ATTACK / SPECIAL / CATCH or CHANGE / RUN) | Picture buttons | Original |
| Attacks | 2 chosen for you, no PP, never miss | 2 chosen for you, PP used, can miss | Original |
| Losing | No penalty, friendly message | No money loss | Original |
| Throwing items away, releasing Pokémon | Not offered | Not offered | Original |
| Running from wild Pokémon | Always works | Always works | Original |
| Navigation help | On | On | Off |
| Typing and nicknames | Never asked | Never asked | Original |
| Learning a new move | Automatic | Automatic | Original |
| Written instructions at the start | Skipped | Skipped | Original |
| Sevii Islands side trip | Not offered | Offered | Original |
| Badge confetti | On | On | Off |
**The ladder (Jake, 2026-11-25):** Classic is the original game, Junior is 2.5 times easier, and
Little Trainer is twice as easy as Junior. Nothing on Little Trainer is a certainty that was a
matter of odds in the original: common Pokémon are caught almost every time, rare ones usually
break free, and weakening one first helps. Experience is the one number left where Jake set it
(×2.5; twice Junior would be ×3).

**Menus are the same on Little and Junior (Jake, 2026-11-26):** "junior is just more easier from a
numbers standpoint instead of menus". Junior has the picture battle menu, the Start menu pictures,
no typing and automatic move learning; only the numbers above (and the original puzzles and the
Sevii Islands trip) set it apart.

A parent can change the preset at any time in OPTION → MODE. (It is not locked: a child who opens
the options could change it.) The exact numbers for every preset are in `src/little_trainers.c`.

## Wording
Pokémon get **tired**, not fainted. Losing is "Your Pokémon need a little rest!". Sentences are
three to five words: "Go through the forest!", "Find Brock!", "Win a badge!".

## Review checklist (copy into each feature's PR)
- [ ] Works without reading  - [ ] Safe under A/B mashing  - [ ] Cannot lose anything permanently
- [ ] Does not lengthen battles or add menus  - [ ] Clear next step afterwards
- [ ] Scoped to the right preset(s) through `little_trainers.h`  - [ ] Emulator test added
