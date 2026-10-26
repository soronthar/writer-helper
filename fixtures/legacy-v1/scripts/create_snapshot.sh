#!/usr/bin/env bash
#
# create_snapshot.sh — Capture world state snapshot after a story completes
#
# Usage:
#   bash "Writing_Room/scripts/create_snapshot.sh" \
#     --world   "worlds/<World Name>"  \
#     --position <N>                    \
#     --story   "<Story Name>"          \
#     --unit    "<Full Story|Ch. N|...>"
#
# Creates:
#   worlds/<World>/snapshots/<position>/
#     characters/        — copy of all character files
#     factions/          — copy of all faction files
#     points_of_interest/— copy of all location files
#     mythology/         — copy of all mythology files
#     DESCRIPTION.md     — copy of world description
#     manifest.md        — metadata about this snapshot
#
# HOOKS.md is intentionally excluded — it is a forward-looking list of
# narrative seeds that always lives in the base world bible only. Snapshots
# capture historical entity state; hooks are never frozen in time.
#
#   worlds/<World>/snapshots/manifest.md (index, created or updated)
#
# The snapshot captures the world state AFTER the story at <position> completed.
# Story at position N+1 should load from snapshot N as its baseline.
#
# If the consolidated world bible exists (state/bible/ has been merged into worlds/),
# the snapshot reflects the merged state. If not, it reflects the pre-story world.
# In practice: invoke after World Archivist Consolidate, before planning next story.
#
# Run from the project root (Writer Helper/).

set -uo pipefail
shopt -s nullglob

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

# ── Argument parsing ──────────────────────────────────────────────────────────

WORLD=""
POSITION=""
STORY=""
UNIT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --world)    WORLD="$2";    shift 2 ;;
    --position) POSITION="$2"; shift 2 ;;
    --story)    STORY="$2";    shift 2 ;;
    --unit)     UNIT="$2";     shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$WORLD" || -z "$POSITION" || -z "$STORY" || -z "$UNIT" ]]; then
  echo "Error: --world, --position, --story, and --unit are required." >&2
  echo "Usage: create_snapshot.sh --world <path> --position <N> --story <name> --unit <type>" >&2
  exit 1
fi

# Validate position is a positive integer
if ! [[ "$POSITION" =~ ^[0-9]+$ ]]; then
  echo "Error: --position must be a positive integer." >&2
  exit 1
fi

TODAY=$(date +%Y-%m-%d)
SNAPSHOT_DIR="$WORLD/snapshots/$POSITION"
SNAPSHOTS_INDEX="$WORLD/snapshots/manifest.md"

DIV="════════════════════════════════════════════════════════════"

# ── Check if snapshot already exists ─────────────────────────────────────────

if [[ -d "$SNAPSHOT_DIR" ]]; then
  echo ""
  echo "$DIV"
  echo "⚠ Snapshot already exists at $SNAPSHOT_DIR"
  echo "  Overwriting existing snapshot for position $POSITION."
  echo "$DIV"
  rm -rf "$SNAPSHOT_DIR"
fi

# ── Create snapshot directory structure ──────────────────────────────────────

mkdir -p "$SNAPSHOT_DIR/characters"
mkdir -p "$SNAPSHOT_DIR/factions"
mkdir -p "$SNAPSHOT_DIR/points_of_interest"
mkdir -p "$SNAPSHOT_DIR/mythology"

echo ""
echo "$DIV"
echo "Creating snapshot — Position $POSITION — [[${STORY}]] | $UNIT"
echo "$DIV"

# ── Copy entity files ─────────────────────────────────────────────────────────

copy_dir() {
  local src="$WORLD/$1"
  local dst="$SNAPSHOT_DIR/$1"
  local count=0

  if [[ -d "$src" ]]; then
    for f in "$src"/*.md; do
      [[ -f "$f" ]] || continue
      cp "$f" "$dst/"
      count=$((count + 1))
    done
  fi
  echo "$count"
}

CHAR_COUNT=$(copy_dir "characters")
FACTION_COUNT=$(copy_dir "factions")
LOC_COUNT=$(copy_dir "points_of_interest")
MYTH_COUNT=$(copy_dir "mythology")

echo "  characters/         — $CHAR_COUNT file(s)"
echo "  factions/           — $FACTION_COUNT file(s)"
echo "  points_of_interest/ — $LOC_COUNT file(s)"
echo "  mythology/          — $MYTH_COUNT file(s)"

# ── Copy world-level files ────────────────────────────────────────────────────

for f in DESCRIPTION.md; do
  if [[ -f "$WORLD/$f" ]]; then
    cp "$WORLD/$f" "$SNAPSHOT_DIR/$f"
    echo "  $f — copied"
  else
    echo "  $f — ⚠ not found, skipped"
  fi
done

# ── Write snapshot manifest.md ────────────────────────────────────────────────

TOTAL=$((CHAR_COUNT + FACTION_COUNT + LOC_COUNT + MYTH_COUNT))

cat > "$SNAPSHOT_DIR/manifest.md" <<EOF
# Snapshot Manifest — Position $POSITION

> **Created:** $TODAY
> **Captures world state AFTER this story completed.**
> Stories at position $((POSITION + 1)) and beyond should use this as their baseline.

## Story
- **Story:** [[$STORY]]
- **Unit:** $UNIT
- **Position:** $POSITION

## Contents
- **Characters:** $CHAR_COUNT file(s)
- **Factions:** $FACTION_COUNT file(s)
- **Locations (Points of Interest):** $LOC_COUNT file(s)
- **Mythology:** $MYTH_COUNT file(s)
- **Total entities:** $TOTAL

## Notes

This snapshot was created automatically by the Story Analyzer after chapter completion.
World consolidation (merging state/bible/ into worlds/) should occur before this snapshot
is taken so that the snapshot reflects all story-driven world changes.

If consolidation has not yet occurred, this snapshot reflects the pre-story world state only.
Invoke the World Archivist → Consolidate, then re-run create_snapshot.sh to update.
EOF

echo "  manifest.md — written"

# ── Update or create snapshots/manifest.md (index) ───────────────────────────

SNAPSHOTS_DIR="$WORLD/snapshots"

if [[ ! -f "$SNAPSHOTS_INDEX" ]]; then
  # Create the index from scratch
  cat > "$SNAPSHOTS_INDEX" <<EOF
# World Snapshots — Index

> Maintained by create_snapshot.sh. Do not edit manually.
> Each entry records the world state AFTER the story at that position completed.
> The story at position N+1 uses snapshot N as its world baseline.

| Position | Story | Unit | Date Created | Notes |
|----------|-------|------|--------------|-------|
| $POSITION | [[$STORY]] | $UNIT | $TODAY | Auto-created by Story Analyzer |
EOF
  echo "  snapshots/manifest.md — created"
else
  # Check if this position already has an entry
  if grep -qE "^\|\s*$POSITION\s*\|" "$SNAPSHOTS_INDEX"; then
    # Update existing row
    # Use awk to replace the matching row
    awk -F'|' -v pos="$POSITION" -v story="$STORY" -v unit="$UNIT" -v today="$TODAY" '
      /^\|/ && NF >= 5 {
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2)
        if ($2 == pos) {
          printf "| %s | [[%s]] | %s | %s | Auto-created by Story Analyzer |\n", pos, story, unit, today
          next
        }
      }
      { print }
    ' "$SNAPSHOTS_INDEX" > "${SNAPSHOTS_INDEX}.tmp" && mv "${SNAPSHOTS_INDEX}.tmp" "$SNAPSHOTS_INDEX"
    echo "  snapshots/manifest.md — updated (position $POSITION)"
  else
    # Append new row before the end of file
    # Insert in sorted position order — find the right place
    INSERTED=false
    NEWROW="| $POSITION | [[$STORY]] | $UNIT | $TODAY | Auto-created by Story Analyzer |"
    while IFS= read -r line; do
      # If this is a table data row and its position > TARGET, insert before it
      if [[ "$INSERTED" == false ]] && echo "$line" | grep -qE '^\|\s*[0-9]'; then
        row_pos=$(echo "$line" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2); print $2}')
        if [[ -n "$row_pos" ]] && [[ "$row_pos" -gt "$POSITION" ]]; then
          echo "$NEWROW"
          INSERTED=true
        fi
      fi
      echo "$line"
    done < "$SNAPSHOTS_INDEX" > "${SNAPSHOTS_INDEX}.tmp"

    if [[ "$INSERTED" == false ]]; then
      echo "$NEWROW" >> "${SNAPSHOTS_INDEX}.tmp"
    fi
    mv "${SNAPSHOTS_INDEX}.tmp" "$SNAPSHOTS_INDEX"
    echo "  snapshots/manifest.md — appended (position $POSITION)"
  fi
fi

# ── Summary ───────────────────────────────────────────────────────────────────

echo ""
echo "$DIV"
echo "Snapshot complete"
echo "  Location  : $SNAPSHOT_DIR"
echo "  Position  : $POSITION"
echo "  Story     : [[$STORY]] | $UNIT"
echo "  Entities  : $TOTAL total"
echo "$DIV"
echo ""
echo "Stories at position $((POSITION + 1))+ can now load baseline from:"
echo "  $SNAPSHOT_DIR"
