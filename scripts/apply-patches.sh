#!/usr/bin/env bash
# Rebuild game/'s "little-trainers" branch = pinned upstream commit + patches/*.patch.
# Refuses to run if game/ has uncommitted edits or commits not yet exported to patches/.
. "$(dirname "$0")/lib.sh"
cd "$GAME" || exit 1

if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  die "game/ has uncommitted changes. Commit them and run scripts/export-patches.sh first."
fi
if git rev-parse --verify --quiet "$BRANCH" >/dev/null; then
  tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
  git "${FORMAT_PATCH[@]}" -o "$tmp" "$UPSTREAM_COMMIT..$BRANCH"
  strip() { cat "$@" 2>/dev/null | grep -vE '^(index |From [0-9a-f]+ )' || true; }
  shopt -s nullglob
  if ! diff -q <(strip "$tmp"/*.patch) <(strip "$ROOT"/patches/*.patch) >/dev/null; then
    if [ "${FORCE:-0}" != 1 ]; then
      die "game/'s $BRANCH branch differs from patches/. Run scripts/export-patches.sh to keep your work, or FORCE=1 to replace it (a backup branch is kept)."
    fi
    git branch -f "backup/little-trainers-$(date +%Y%m%d-%H%M%S)" "$BRANCH"
    warn "FORCE=1: previous branch kept as a backup/ branch in game/"
  fi
fi

say "Resetting $BRANCH to upstream $UPSTREAM_COMMIT"
git -c advice.detachedHead=false checkout --quiet --detach "$UPSTREAM_COMMIT"
git branch -f "$BRANCH" "$UPSTREAM_COMMIT"
git checkout --quiet "$BRANCH"
shopt -s nullglob
patches=("$ROOT"/patches/*.patch)
if [ ${#patches[@]} -gt 0 ]; then
  say "Applying ${#patches[@]} patch(es)"
  git -c user.name="Little Trainers" -c user.email="noreply@localhost" am --quiet --keep --committer-date-is-author-date "${patches[@]}" \
    || die "A patch failed to apply. Run 'git -C game am --abort' and fix the patch."
fi
git log --oneline "$UPSTREAM_COMMIT..HEAD" | head -n 40
