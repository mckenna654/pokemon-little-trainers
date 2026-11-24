#!/usr/bin/env bash
# Refuse ROMs, BIOS, saves, emulator states, binary patches and credentials in Git.
#   check-forbidden.sh            check every tracked file (CI)
#   check-forbidden.sh --staged   check what is about to be committed (pre-commit hook)
#   check-forbidden.sh --history  check every blob ever committed on any branch
set -euo pipefail
cd "$(dirname "$0")/.."
name_re='\.(gba|gb|gbc|nds|rom|sav|srm|ss[0-9]|state[^/]*|sgm|bps|ips|ups|pem|key|p12)$|(^|/)\.env($|\.)|(^|/)(gba_bios\.bin|baserom[^/]*)$|^(original-rom|builds|saves|savestates|bios|work|game)/'
secret_re='(ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|AKIA[0-9A-Z]{16}|xox[bap]-[A-Za-z0-9-]{10,}|sk-[A-Za-z0-9]{32,})'
bad=0

check_name() { # path
  case "$1" in original-rom/README.md|.env.example) return 0 ;; esac
  if printf '%s\n' "$1" | grep -qiE "$name_re"; then echo "forbidden file: $1"; bad=1; fi
}

if [ "${1:-}" = "--history" ]; then
  while IFS=' ' read -r sha path; do
    [ -z "$path" ] && continue
    check_name "$path"
    size=$(git cat-file -s "$sha")
    if [ "$size" -gt 4194304 ]; then echo "blob over 4 MiB in history: $path ($sha)"; bad=1; fi
    if [ "$(git cat-file -p "$sha" | head -c 8 | tail -c 4 | od -An -tx1 | tr -d ' \n')" = "24ffae51" ]; then echo "GBA ROM in history: $path ($sha)"; bad=1; fi
  done < <(git rev-list --objects --all | awk 'NF>1')
  if [ $bad = 1 ]; then echo "Blocked: forbidden content exists in Git history. Do not push; fix history first." >&2; exit 1; fi
  echo "history check: OK"; exit 0
fi

if [ "${1:-}" = "--staged" ]; then
  files="$(git diff --cached --name-only --diff-filter=ACMR)"
else
  files="$(git ls-files)"
fi
while IFS= read -r f; do
  [ -z "$f" ] && continue
  check_name "$f"
  [ -f "$f" ] || continue
  # GBA ROM header: Nintendo logo starts at offset 4 with 24 FF AE 51
  if [ "$(head -c 8 "$f" 2>/dev/null | tail -c 4 | od -An -tx1 | tr -d ' \n')" = "24ffae51" ]; then
    echo "file looks like a GBA ROM: $f"; bad=1; continue
  fi
  size=$(wc -c < "$f")
  if [ "$size" -gt 4194304 ]; then echo "file over 4 MiB (ROM-sized?): $f"; bad=1; fi
  case "$f" in scripts/check-forbidden.sh|tests/test_guard.py) continue ;; esac
  if grep -IqE "$secret_re" "$f" 2>/dev/null; then echo "possible credential in: $f"; bad=1; fi
done <<< "$files"
if [ $bad = 1 ]; then echo "Blocked: remove these files from Git (they must stay local)." >&2; exit 1; fi
echo "forbidden-file check: OK"
