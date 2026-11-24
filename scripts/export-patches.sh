#!/usr/bin/env bash
# Save the commits on game/'s little-trainers branch into patches/ (the only copy of our game
# changes that reaches GitHub). Run after committing a change in game/.
. "$(dirname "$0")/lib.sh"
cd "$GAME" || exit 1
[ "$(git rev-parse --abbrev-ref HEAD)" = "$BRANCH" ] || die "game/ is not on the $BRANCH branch"
[ -z "$(git status --porcelain --untracked-files=no)" ] || die "Commit your changes in game/ first."
untracked="$(git status --porcelain | grep '^??' || true)"
[ -z "$untracked" ] || warn "Untracked files in game/ are NOT exported:"$'\n'"$untracked"
rm -f "$ROOT"/patches/*.patch
git "${FORMAT_PATCH[@]}" -o "$ROOT/patches" "$UPSTREAM_COMMIT..$BRANCH"
find "$ROOT/patches" -name '*.patch' -size +1024k -exec sh -c 'echo "warning: large patch (check it only adds our own/permitted assets): $1" >&2' _ {} \;
echo "$(find "$ROOT/patches" -name '*.patch' | wc -l | tr -d ' ') patch(es) in patches/"
