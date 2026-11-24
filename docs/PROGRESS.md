# Progress and handoff

_Last updated: 2026-11-25 (session 2)_

## Where things stand
- **Milestones 0–2: complete** (environment, simplified rules, picture battle menu, hearts).
- **Milestone 3 (Pallet → Brock): playable end to end by following the arrow**, proven by an
  automated arrow-following player. Intro/dialogue trimming, badge celebration and autosave remain.
- **Milestone 5 (all of Kanto): systems in place** — story goals and routes to the League,
  HM-free field moves, simple puzzles, team caps — but only checked goal by goal past Brock.
- **Milestone 4 (graphical remaster):** battle UI, Start menu and arrow art are ours and in the
  game; tiles, sprites and backgrounds are unchanged.
- Patches 0001–0016 in `patches/`. Remaining items are the unchecked boxes in `ROADMAP.md`.

## Verified
`docs/TESTING.md` has the full tables. In short: byte-exact baseline; BPS round trip with two
independent tools; automated emulator play from power-on to Route 1; nine automated emulator tests
of the Little Trainer rules, each proven to fail on unmodified FireRed.

## Unverified / open
- No person has played the build yet. Only the mGBA 0.10.5 core has run it.
- Junior/Classic presets are untested.
- PokeCommunity threads unread (HTTP 403): third-party asset terms unknown. Needs Jake (connect the
  Chrome extension, or paste the first post of each thread).

## Next actions (in order)
1. Extend the arrow-following play-through past Brock (Mt. Moon → Misty → Bill → S.S. Anne → Surge)
   in `tests/emu/emu_arrow.py`; fix whatever stops it. `FireRed.run_script` can set up later
   starting points (see `tests/emu/emu_world.py` → `story_state`).
2. Autosave at badges; a badge celebration; parent option to change preset (then test Junior and
   Classic); shorter intro and simpler critical-path dialogue.
3. Graphics: a brighter palette pass, then tiles (needs the PokeCommunity terms or our own art).
4. Small leftovers listed in `ROADMAP.md`.

When goals or maps change: `python3 tools/gen_nav.py --check --why`, then `python3 tools/gen_nav.py`,
rebuild, `scripts/export-patches.sh`. When UI art changes: `python3 assets/ui/make_battle_icons.py`.

## How to resume
```bash
cd "~/Documents/Claude Code/pokemon-little-trainers"
git status && git -C game status && git fetch --all --prune && git pull --ff-only
scripts/setup.sh --no-deps     # only if game/ or work/ is missing
scripts/build.sh && scripts/test.sh
```
