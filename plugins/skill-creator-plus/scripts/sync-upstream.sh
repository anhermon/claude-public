#!/usr/bin/env bash
# Resync upstream/skill-creator from the claude.ai-synced copy and carry the
# upstream delta into skills/skill-creator with a per-file 3-way merge.
# Usage: sync-upstream.sh [--dry-run] [SOURCE_DIR]
# Never commits. Exit 0 = clean or no-op, 1 = merge conflicts, 2 = usage/error.
set -euo pipefail

JUNK_NAMES=(__pycache__ .DS_Store '*.pyc')
SYNC_DATE="${SYNC_DATE:-$(date +%Y-%m-%d)}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UPSTREAM="$ROOT/upstream/skill-creator"
LOCAL="$ROOT/skills/skill-creator"
NOTES="$ROOT/upstream/UPSTREAM.md"

dry_run=0
src=""
for a in "$@"; do
  case "$a" in
    --dry-run) dry_run=1 ;;
    -h|--help) sed -n '2,5p' "${BASH_SOURCE[0]}"; exit 0 ;;
    -*) echo "unknown flag: $a" >&2; exit 2 ;;
    *) src="$a" ;;
  esac
done

if [ -z "$src" ]; then
  matches=()
  for m in "$HOME"/.claude/skills/synced/*/skill-creator; do
    [ -d "$m" ] && matches+=("$m")
  done
  if [ "${#matches[@]}" -ne 1 ]; then
    echo "expected exactly 1 match for ~/.claude/skills/synced/*/skill-creator, found ${#matches[@]}; pass SOURCE_DIR" >&2
    exit 2
  fi
  src="${matches[0]}"
fi
[ -f "$src/SKILL.md" ] || { echo "not a skill dir (no SKILL.md): $src" >&2; exit 2; }
[ -d "$UPSTREAM" ] || { echo "missing $UPSTREAM" >&2; exit 2; }
[ -d "$LOCAL" ] || { echo "missing $LOCAL" >&2; exit 2; }
src="$(cd "$src" && pwd)"

sha256() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -d' ' -f1
  else shasum -a 256 "$1" | cut -d' ' -f1; fi
}

# Print the filtered file list (relative paths, sorted) of a tree.
list_files() {
  local args=() n
  for n in "${JUNK_NAMES[@]}"; do args+=(-name "$n" -o); done
  unset 'args[${#args[@]}-1]'
  (cd "$1" && find . \( "${args[@]}" \) -prune -o -type f -print | sed 's|^\./||' | LC_ALL=C sort)
}

# Public-safe source label: never record absolute paths or account ids.
redact_src() {
  case "$src" in
    "$HOME"/.claude/skills/synced/*/skill-creator)
      echo "~/.claude/skills/synced/<id>/skill-creator" ;;
    *) echo "<custom source dir>/$(basename "$src")" ;;
  esac
}

# Write UPSTREAM.md with a sha256 manifest of $tmp/new.
write_notes() {
{
  echo "# Upstream provenance"
  echo
  echo "\`upstream/skill-creator/\` is a pristine, byte-exact copy of Anthropic's skill-creator as shipped by claude.ai. Never hand-edit it; run \`scripts/sync-upstream.sh\`."
  echo
  echo "- Source: \`$(redact_src)\`"
  echo "- Sync date: $SYNC_DATE"
  echo "- Files: $(wc -l < "$tmp/new.list" | tr -d ' ')"
  echo
  echo "## sha256 manifest"
  echo
  echo '```'
  while IFS= read -r f; do echo "$(sha256 "$tmp/new/$f")  $f"; done < "$tmp/new.list"
  echo '```'
} > "$NOTES"
}

tmp="$(mktemp -d)"
trap 'rm -rf "${tmp:?}"' EXIT

# Stage a junk-free copy of the new source.
mkdir -p "$tmp/new"
while IFS= read -r f; do
  mkdir -p "$tmp/new/$(dirname "$f")"
  cp -p "$src/$f" "$tmp/new/$f"
done < <(list_files "$src")

list_files "$UPSTREAM" > "$tmp/old.list"
list_files "$tmp/new" > "$tmp/new.list"
sort -u "$tmp/old.list" "$tmp/new.list" > "$tmp/all.list"

added=() removed=() modified=()
while IFS= read -r f; do
  if [ ! -f "$UPSTREAM/$f" ]; then added+=("$f")
  elif [ ! -f "$tmp/new/$f" ]; then removed+=("$f")
  elif ! cmp -s "$UPSTREAM/$f" "$tmp/new/$f"; then modified+=("$f")
  fi
done < "$tmp/all.list"

if [ $(( ${#added[@]} + ${#removed[@]} + ${#modified[@]} )) -eq 0 ]; then
  if [ ! -f "$NOTES" ] && [ "$dry_run" -eq 0 ]; then
    write_notes
    echo "upstream unchanged; wrote missing UPSTREAM.md"
    exit 0
  fi
  echo "upstream unchanged; nothing to do"
  exit 0
fi

echo "upstream delta (old upstream -> $src):"
for f in ${added[@]+"${added[@]}"}; do echo "  A $f"; done
for f in ${removed[@]+"${removed[@]}"}; do echo "  D $f"; done
for f in ${modified[@]+"${modified[@]}"}; do echo "  M $f"; done
if [ "$dry_run" -eq 1 ]; then
  for f in ${modified[@]+"${modified[@]}"}; do
    diff -u "$UPSTREAM/$f" "$tmp/new/$f" || true
  done
  echo "(dry run: nothing written)"
  exit 0
fi

conflicts=()

for f in ${added[@]+"${added[@]}"}; do
  if [ ! -e "$LOCAL/$f" ]; then
    mkdir -p "$LOCAL/$(dirname "$f")"; cp -p "$tmp/new/$f" "$LOCAL/$f"
  elif ! cmp -s "$LOCAL/$f" "$tmp/new/$f"; then
    conflicts+=("$f (added upstream, but a different local file exists; local kept)")
  fi
done

for f in ${removed[@]+"${removed[@]}"}; do
  if [ ! -e "$LOCAL/$f" ]; then :
  elif cmp -s "$LOCAL/$f" "$UPSTREAM/$f"; then rm -f "${LOCAL:?}/${f:?}"
  else conflicts+=("$f (deleted upstream, but modified locally; local kept)")
  fi
done

for f in ${modified[@]+"${modified[@]}"}; do
  if [ ! -e "$LOCAL/$f" ]; then
    conflicts+=("$f (modified upstream, but deleted locally; not restored)")
  elif cmp -s "$LOCAL/$f" "$UPSTREAM/$f"; then
    cp -p "$tmp/new/$f" "$LOCAL/$f"
  elif cmp -s "$LOCAL/$f" "$tmp/new/$f"; then :
  else
    # 3-way: base = old upstream, ours = local, theirs = new upstream.
    if ! git merge-file -L local -L "old-upstream" -L "new-upstream" \
        "$LOCAL/$f" "$UPSTREAM/$f" "$tmp/new/$f" 2>/dev/null; then
      conflicts+=("$f (merge conflict; markers left in file)")
    fi
  fi
done

# Replace pristine upstream with the new source.
rm -rf "${UPSTREAM:?}"
mkdir -p "$UPSTREAM"
cp -pR "$tmp/new/." "$UPSTREAM/"

write_notes

echo "upstream/skill-creator updated; UPSTREAM.md rewritten."
if [ "${#conflicts[@]}" -gt 0 ]; then
  echo "CONFLICTS (${#conflicts[@]}):" >&2
  for c in "${conflicts[@]}"; do echo "  $c" >&2; done
  echo "Resolve in skills/skill-creator (search for <<<<<<<), then review with git diff." >&2
  exit 1
fi
echo "skills/skill-creator merged cleanly. Review with git diff; nothing was committed."
