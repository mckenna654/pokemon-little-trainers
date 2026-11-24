# Progress and handoff

_Last updated: 2026-11-25 (session 2)_

## Where things stand
- **Milestones 0–2: complete** (environment, simplified rules, picture battle menu, hearts).
- **Milestone 3 (Pallet → Brock): playable end to end by following the arrow**, proven by an
  automated arrow-following player (`tests/emu/emu_arrow.py`).
- **Milestone 5 (all of Kanto): systems in place.** Story goals and routes to the League, HM-free
  field moves, simple puzzles, team caps, autosave, respawn at the last town, parent MODE option.
  A long arrow-only run (scratch script, not yet a committed test) has gone New Game → Brock →
  Mt. Moon → Misty → Nugget Bridge → Bill's cottage; each stop it found was fixed in
  `src/little_trainers_nav.c` / `tools/gen_nav.py`. Beyond Bill is only checked goal by goal.
- **Milestone 4 (graphical remaster):** our own battle UI, hearts, Start menu icons and arrow; map
  colours brightened on load (`LT_VividPalette`). Tiles, sprites and backgrounds are unchanged.
- Patches 0001–0018 in `patches/`. Remaining items are the unchecked boxes in `ROADMAP.md`.

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
1. Keep pushing the arrow-only run further (S.S. Anne, Surge, Rock Tunnel, Celadon, ...). The
   method: run a follower that saves a state on every map change, and when it sticks, replay
   from the last state with a short trace. The follower is `FireRed.follow_arrow`; a per-map
   save/trace wrapper is easy to rebuild from `tests/emu/emu_arrow.py`. Save states only work
   with the exact ROM build that made them.
2. Promote the longest reliable stretch into `tests/emu/emu_arrow.py` (currently to Brock).
3. Badge celebration; shorter intro and simpler critical-path dialogue; title-screen branding.
4. Graphics: tiles and sprites (needs the PokeCommunity terms or our own art).
5. Small leftovers listed in `ROADMAP.md`.

When goals or maps change: `python3 tools/gen_nav.py --check --why`, then `python3 tools/gen_nav.py`,
rebuild, `scripts/export-patches.sh`. When UI art changes: `python3 assets/ui/make_battle_icons.py`.

## How to resume
```bash
cd "~/Documents/Claude Code/pokemon-little-trainers"
git status && git -C game status && git fetch --all --prune && git pull --ff-only
scripts/setup.sh --no-deps     # only if game/ or work/ is missing
scripts/build.sh && scripts/test.sh
```
