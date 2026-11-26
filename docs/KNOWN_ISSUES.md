# Known issues and limitations

## Open
_The QA play-through of 2026-11-26 (`docs/QA-2026-11-26.md`) is the full list with reproduction
steps; the items below are its confirmed bugs and main points._
- **QA play-through fixes (v0.1.0-dev.4):** tossing items, releasing Pokémon, CHANGE while trapped,
  the evolution that always stopped, Arena Trap stopping RUN and CATCH where it can't work are
  fixed (#3–#6, patches 0039–0042). Still open from that report: the items below.
- **Selling in shops** turns items into money, with YES already chosen (D-02: Jake to decide). The
  question now shows the tick and cross.
- **Some rarer Yes/No boxes are still words only:** the Day Care, the Move Relearner, trade
  evolutions and the new-game "delete the save?" screen draw their own boxes.
- **Pacing depends on the starter:** with Bulbasaur the Champion won twice and the Elite Four had
  to be beaten three times; Erika and Blaine took 13 and 15 turns.
- **After the Hall of Fame there is nothing for the arrow to point at**, and the post-game
  (Sevii Islands, Cerulean Cave, National Pokédex) cannot be reached on Little Trainer.
- **Rare Pokémon are now hard to catch on Little Trainer.** Five times the original odds is still
  small for the rarest: a healthy Snorlax about one ball in six, a healthy legendary bird or Mewtwo
  about two in a hundred (about four in a hundred when nearly beaten). Balls are free, so a child
  can keep pressing CATCH, but each miss gives the wild Pokémon a turn, and a non-reader will not
  know that weakening it first helps. None of these are needed to finish the game. A floor (say,
  never worse than one in three) would be a one-line rule if Jake wants it.
- **A miss is told in words** ("Oh, no! The POKéMON broke free!"), like the rest of the original
  battle messages.
- **Diagonal arrows only appear near a corner** (within seven steps of it) and only when both
  directions are equally good; on a long straight stretch the arrow stays straight even if the
  goal is off to one side. The four straight arrows and the up-and-right family have been seen on
  screen; not every diagonal has been looked at in every kind of place (caves, water, indoors).
- **Confetti can cover the arrow** for a moment while it falls after a badge.
- **Battles on Little Trainer are easier again** (50% damage taken, three-Pokémon bosses). With an
  A-masher winning the whole game before this change, it may now be too easy for an older child:
  Junior is the step up.
- **Start menu pictures are only 14 pixels.** The illustrated bag, save disk and cog are
  recognisable but coarse; the larger versions in `assets/generated/v1/menu-32/` need a bigger
  menu (a code change) before they can be used. The Pokédex and trainer card pictures have not
  been seen in the game yet (the screen tour stops before the Pokédex is given).
- **CHANGE is a friendly green face**, which says "a Pokémon" more than "swap". The earlier
  drawing had a second head and an arrow. No child has been asked what any of the pictures mean.
- **Only the attack burst, fire, CATCH, RUN and CHANGE buttons have been seen on compiled
  screens**; the other 16 type symbols were checked only as enlarged previews.
- **The small yellow mark on the suggested attack** (a star, 8 pixels) reads as a dot. A reviewer
  who had not been told could not say what it was for.
- **Save box and the player:** when the save box is open it covers the player except a sliver, so
  a couple of the player's pixels show at its edge. Same before and after the new pictures; not
  yet compared with unmodified FireRed.
- **Preschool content pass remains:** Pokémon Tower death/ghost text and Game Corner coin/slot
  interactions are retained. Jake should choose whether to soften them; easier battles and
  friendly fainting text do not change those scenes.
- **MODE replaces BATTLE STYLE** in the OPTION menu; battle style stays on SHIFT. A child who
  opens OPTION could change MODE: it is not locked.
- **Normal-type special attacks use the generic sparkle symbol.**
- **The wing picture for Flying attacks is hard to name** (a reviewer could not tell what it was).
- **Hearts are the same red whatever the health** (the original bar's green/yellow/red is not used).
- **Some menus are still words only:** the boy/girl choice, the bag, the party screen opened by
  CHANGE, shop lists and the "use next Pokémon?" question in battle. Yes/No boxes on the field have
  a tick and a cross.
- **The Sevii Islands trip is switched off on the Little Trainer preset.** Bill waits in Cinnabar's
  Pokémon Centre and says only that he will wait. To take the trip, switch MODE to Junior or
  Classic first. On those presets the arrow does not guide the island quest.
- **Names:** the player and rival get the game's default names unless a grown-up changes them on
  the name screen (B rubs out). Caught Pokémon keep their species names; the Name Rater in
  Lavender Town can still rename them. The Start menu has pictures but no trainer card entry on the Little and
  Junior presets.
- **No bag or switching in wild battles** on the Little and Junior presets (by design; healing is
  automatic after each battle). On Junior this also means no potions during a battle, and Junior's
  opponents hit harder; it has not been played through the whole game on Junior yet. If party and
  PC storage are both full, CATCH only plays an error sound.
- **Status protection is shown as SAFEGUARD:** when an opponent tries a status move the game says
  the party is protected by Safeguard. Opponents' AI therefore avoids status moves.
- **Oak's battle lecture is skipped** in the first rival battle on the Little and Junior presets (it
  is all text, and explains a menu the picture menu replaces). Classic keeps it.
- **Buttons come and go.** A Pokémon with one attacking move has one attack button; SPECIAL
  appears when there is a second attack to offer. CHANGE appears only when another Pokémon can
  come in. So the first rival battle has a single button, and the same picture can sit in a
  different place from one battle to the next.
- **CHANGE when the Pokémon is held in place** (Mean Look, Arena Trap and the like) still opens
  the party screen and the game then says it cannot switch. Not yet simplified.
- **The whole game has been finished by an automated player, not yet by a person.** It follows
  the arrow exactly; a child will wander, and places off the route are much less tested.
- **A person who walks about and stops in a narrow place** can make the arrow suggest the water
  (the Surf question) and then the land again until they move on. People who never move again
  (beaten trainers) are now gone round properly.
- **The arrow follows the main story only.** It does not guide to Pokémon Centres, shops or
  optional areas, and Fly still needs the party menu.
- **Junior preset and puzzles:** Junior keeps the original gym puzzles, so its arrow can stop at a
  barrier (Surge's gates, Blaine's quiz, spin tiles). Little Trainer has no such stops.
- **Boulders:** the arrow walks around Strength boulders and never asks for one to be pushed. A
  child can still push one into a corridor; leaving the cave floor and coming back resets them.
- **The Pokémon Mansion is skipped** on the Little Trainer preset (Cinnabar Gym is already
  unlocked), so its items and Pokémon are optional.
- **Opponent levels are unchanged**; only team sizes and damage are reduced.
- **Graphics research incomplete:** the four PokeCommunity threads in the specification could not
  be read (HTTP 403 to automated access). Asset reuse terms are unconfirmed, so no third-party art
  is included yet. See `docs/GRAPHICS.md`.
- **Only one emulator core tested:** mGBA 0.10.5 (headless). No device compatibility is claimed.
- **Manual play so far:** Jake, the opening and first rival battle of `v0.1.0-dev` in mGBA 0.10.5
  on Windows (2026-11-24). What he found is GitHub issue #1 and is fixed from `v0.1.0-dev.2` on; neither that
  build nor `v0.1.0-dev.3` has been played by a person yet.
- **Slow moments:** the arrow's path is worked out in one go when the map or goal changes, which
  can take longer than one frame on big maps (a brief hitch, not measured on real hardware).
- **Vanilla saves unsupported:** start a fresh save with Little Trainers.

## Build environment
- agbcc cannot be built in a path containing spaces; `scripts/setup.sh` works around it by building
  in a temporary directory.
- Homebrew's `mgba` formula is broken/deprecated on current macOS; the tests build mGBA's core from
  source instead. To *play* the ROM yourself, install the mGBA app from https://mgba.io/ or use any
  other GBA emulator.
- Linker warning `LOAD segment with RWX permissions` is expected and harmless.
