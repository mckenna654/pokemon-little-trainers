# Pokémon: Little Trainers — agent instructions

A graphically remastered, preschool-friendly modification of Pokémon FireRed (GBA), built from the
pret decompilation. Target player: a 3–6 year old who cannot read. Owner: Jake (mckenna654), who is
not technical: explain outcomes in plain English and do the git work yourself. Use Australian
English in docs and in-game text. The full product specification is summarised in `ROADMAP.md` and
`docs/ACCESSIBILITY.md`; this file is how to work on it.

## Start of every session
1. `git status` here **and** in `game/`. Never discard uncommitted work.
2. `git fetch --all --prune`; check divergence from `origin/<branch>`; `git pull --ff-only`.
3. New machine or new patches: `scripts/setup.sh` (then `scripts/build-emu.sh` for emulator tests).
4. Read `docs/PROGRESS.md` (state, unverified items, next action), then `ROADMAP.md`.
5. Continue the current milestone. Do not restart working systems.

## Architecture decisions (do not change without a strong reason)
- **Base ROM:** FireRed (USA, Europe) **v1.1 / Rev 1**, SHA-1 `dd5945db9b930750cb39d00c84da8571feebf417`.
  One revision only. Build target `firered_rev1`. Jake's copy lives in `original-rom/` (git-ignored).
- **Foundation:** `pret/pokefirered` at the commit in `upstream.lock`, compiled with agbcc. No CFRU,
  no expansion frameworks, no binary patches from other hacks.
- **Modification-only repo:** this repository does **not** contain the FireRed source or assets
  (pret has no licence; the source and graphics are Nintendo-derived). It holds:
  - `patches/*.patch`: our commits, exported from `game/` (the only copy of game changes on GitHub)
  - `scripts/`, `tools/`, `tests/`, `docs/`, `assets/` (our own source art and attribution)
- **`game/`** (git-ignored): pret checkout; our work is its local branch `little-trainers`; its
  remote `upstream` has pushing disabled.
- **Feature switches:** all gameplay rules go through `include/little_trainers.h` /
  `src/little_trainers.c` in `game/` (difficulty presets, `LT_*` constants). No magic numbers
  scattered through the engine. Little Trainer preset is the default and the development target.
- **Graphics:** source-level, incremental remaster on the same foundation; Aesthetic Red is a visual
  reference only. Every third-party asset needs established reuse terms and a row in
  `docs/GRAPHICS.md` before it is committed. See `docs/GRAPHICS.md`.
- **Saves:** do not change save-block layouts casually. Custom state uses game vars/flags or
  versioned fields documented in `docs/ARCHITECTURE.md`.
- **Hardware:** stock GBA limits (240×160, 32 MiB max ROM, palette/sprite/VRAM limits). Nothing
  emulator-specific.

## Change loop
1. Edit in `game/`; one commit per coherent change (`git -C game commit`).
2. `scripts/build.sh` → `builds/Pokemon - Little Trainers.gba` + verified `.bps`.
3. `scripts/test.sh` (hygiene, unit tests, emulator tests). Add an emulator test for each gameplay
   feature in `tests/emu/`. Then **playtest**: passing tests are not enough, the screens must be
   looked at (`.claude/skills/playtest/SKILL.md`).
4. `scripts/export-patches.sh`; commit `patches/` + docs here; push.
Never leave changes only in `game/`: it is not backed up. `scripts/apply-patches.sh` rebuilds
`game/` from `patches/` and refuses to overwrite unexported work.

Other commands: `scripts/build.sh baseline` (must byte-match v1.1), `scripts/build.sh clean`,
`scripts/release.sh` (ROM + BPS + checksums + release notes in `builds/release/`),
`scripts/verify-rom.sh`, `scripts/check-forbidden.sh [--staged|--history]`.

## Hard rules
- Never commit or upload ROMs (original or modified), BIOS, saves, save states, `.bps` files or
  credentials: not to this private repo, CI, artifacts or releases (BPS only in a release, only if
  Jake asks). `.githooks/pre-commit` and CI run `scripts/check-forbidden.sh`; never bypass it.
  Run `scripts/check-forbidden.sh --history` before the first push of any new branch.
- Never push the decomp source. Never push to pret. The repo must stay **private**.
- Never modify or delete anything in `~/Downloads` or Jake's own save files.
- No force-push, history rewrite, or deleting unmerged branches without asking Jake.
- Honest reporting: say whether a feature is *compiled*, *emulator-tested (automated)*,
  *manually played*, or *source-reviewed only*. Never claim device compatibility that was not tested.
- Do not publish releases or tags unless Jake asks.

## Branches and commits
- `main`: stable, CI green, emulator tests passed. `develop`: integration. `feature/<name>` and
  `fix/<name>` for larger work; small docs fixes may go straight to `develop`.
- Conventional prefixes: `feat:`, `fix:`, `docs:`, `build:`, `test:`, `chore:`, `ci:`.
- Version bumps change `VERSION` and `CHANGELOG.md` together; tags are `vX.Y.Z`.
- Delete a branch after its PR merges.

## Accessibility principles (apply to every change)
Assume the player cannot read, mashes A, and gives up when punished. Prefer icons over words,
never punish mistakes, never allow permanent loss (Pokémon, items, progress), keep battles short,
always show where to go, keep the child's choices meaningful (do not auto-play the game).
Details and the review checklist: `docs/ACCESSIBILITY.md`.

## End of every session
Update `docs/PROGRESS.md`, `CHANGELOG.md` (Unreleased), `docs/TESTING.md` (actual results),
`docs/KNOWN_ISSUES.md`, and `ROADMAP.md` checkboxes. Commit and push. Report: local path, ROM
location/revision/validation, repo URL + visibility, branch, latest commit, sync status,
milestone, features done/remaining, graphics status, actual test results, known issues, version,
exact `.gba` and `.bps` paths, and how to resume.

## Agent skills

### Issue tracker

Issues live in this repo's GitHub Issues, managed with the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human` and `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` and `docs/adr/` at the repo root, created when first needed. See `docs/agents/domain.md`.
