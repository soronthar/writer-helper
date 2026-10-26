#!/usr/bin/env bash
#
# load_world.sh — World bible context loader
#
# Used by the Story Ideator and Outliner to load world bible and story craft
# files in a single Bash call. Three operating modes, selected automatically
# based on the flags provided.
#
# ════════════════════════════════════════════════════════════════
# MODE 1 — Overview  (Story Ideator, Pass 1)
# ════════════════════════════════════════════════════════════════
#
#   bash "Writing_Room/scripts/load_world.sh" --world "worlds/<World Name>"
#
#   Outputs: DESCRIPTION.md, SUMMARY.md, HOOKS.md, WORLD_ORDER.md,
#            ALL writing_concepts/story_structure/ files.
#
#   Use when the agent needs to choose a story structure (Ideator).
#
# ════════════════════════════════════════════════════════════════
# MODE 2 — Structure  (Outliner, Pass 1)
# ════════════════════════════════════════════════════════════════
#
#   bash "Writing_Room/scripts/load_world.sh" \
#     --world     "worlds/<World Name>"        \
#     --structure "Three-Act Structure"
#
#   Outputs: DESCRIPTION.md, SUMMARY.md,
#            story_structure/GUIDE.md, story_structure/Format Reference.md,
#            the named structure file.
#
#   Skips: HOOKS.md, WORLD_ORDER.md, all other structure files.
#   Use when the structure is already known from CONCEPT.md (Outliner).
#   The --structure value is the filename stem (no .md extension).
#
# ════════════════════════════════════════════════════════════════
# MODE 3 — Entities  (Ideator & Outliner, Pass 2)
# ════════════════════════════════════════════════════════════════
#
#   Pass 2a — selective (after identifying entities from SUMMARY.md):
#
#     bash "Writing_Room/scripts/load_world.sh" \
#       --world  "worlds/<World Name>"           \
#       --entity "characters/Mara Quill"       \
#       --entity "factions/Harbor Guild"          \
#       --entity "mythology/The Pale Covenant"
#
#   Pass 2b — staleness fallback (SUMMARY.md absent or stale):
#
#     bash "Writing_Room/scripts/load_world.sh" \
#       --world "worlds/<World Name>"            \
#       --all-entities
#
#   --entity accepts "type/Name" where type is one of:
#     characters | factions | points_of_interest | mythology
#   The name is the filename stem (no .md extension).
#
#   When --entity or --all-entities is provided, ONLY entity files are output —
#   the world overview is already in context from Pass 1.
#
# ════════════════════════════════════════════════════════════════
# Notes
# ════════════════════════════════════════════════════════════════
#
#   - Run from the project root (Writer Helper/).
#   - All paths are relative to Writing_Room/. The script cd's there automatically.
#   - Missing files emit a ⚠ warning line rather than crashing.
#   - --position <N>: when provided, entity reads prefer worlds/<World>/snapshots/<N>/
#     over the current worlds/<World>/ directory. Use to load historical world state.
#     Useful when planning/writing a story that occurs at a known chronological position.

set -uo pipefail
shopt -s nullglob

# ── Move to Writing_Room/ ─────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

# ── Argument parsing ──────────────────────────────────────────────────────────

WORLD=""
STRUCTURE=""
POSITION=""
declare -a ENTITIES=()
ALL_ENTITIES=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --world)        WORLD="$2";         shift 2 ;;
    --structure)    STRUCTURE="$2";     shift 2 ;;
    --position)     POSITION="$2";      shift 2 ;;
    --entity)       ENTITIES+=("$2");   shift 2 ;;
    --all-entities) ALL_ENTITIES=true;  shift 1 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$WORLD" ]]; then
  echo "Error: --world is required." >&2
  echo "Usage: load_world.sh --world <path> [--position N] [--structure Name] [--entity type/Name | --all-entities]" >&2
  exit 1
fi

# Resolve snapshot directory if --position is set
SNAPSHOT_DIR=""
if [[ -n "$POSITION" ]]; then
  CANDIDATE="$WORLD/snapshots/$POSITION"
  if [[ -d "$CANDIDATE" ]]; then
    SNAPSHOT_DIR="$CANDIDATE"
  else
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "POSITION $POSITION: ⚠ No snapshot found at $CANDIDATE — falling back to current world"
    echo "════════════════════════════════════════════════════════════"
  fi
fi

# ── Helpers ───────────────────────────────────────────────────────────────────

DIV="════════════════════════════════════════════════════════════"

print_file() {
  local label="$1"
  local path="$2"
  echo ""
  echo "$DIV"
  if [[ -f "$path" ]]; then
    echo "FILE: $label"
    echo "$DIV"
    cat "$path"
  else
    echo "FILE: $label  ⚠ NOT FOUND — $path"
    echo "$DIV"
  fi
}

# ── Mode 3 — Entities ─────────────────────────────────────────────────────────
# --entity or --all-entities provided. Output only entity files — the world
# overview is already in context from Pass 1.
#
# Source priority when --position is set:
#   worlds/<World>/snapshots/<N>/<type>/<Name>.md  →  worlds/<World>/<type>/<Name>.md

# Helper: resolve entity file with snapshot priority
resolve_entity_file() {
  local entry="$1"   # e.g. "characters/Mara Quill"
  if [[ -n "$SNAPSHOT_DIR" && -f "$SNAPSHOT_DIR/${entry}.md" ]]; then
    echo "$SNAPSHOT_DIR/${entry}.md"
  else
    echo "$WORLD/${entry}.md"
  fi
}

if [[ ${#ENTITIES[@]} -gt 0 || "$ALL_ENTITIES" == true ]]; then

  if [[ "$ALL_ENTITIES" == true ]]; then
    for dir in characters factions points_of_interest mythology; do
      # Prefer snapshot dir if available, merge with world dir (world = fallback for missing)
      declare -A SEEN_FILES=()

      # First: files from snapshot (if present)
      if [[ -n "$SNAPSHOT_DIR" ]]; then
        SNAP_FILES=("$SNAPSHOT_DIR/$dir/"*.md)
        for f in "${SNAP_FILES[@]}"; do
          [[ -f "$f" ]] || continue
          name=$(basename "${f%.md}")
          SEEN_FILES["$name"]=1
          print_file "$dir/$name  [snapshot pos $POSITION]" "$f"
        done
      fi

      # Then: world files not already covered by snapshot
      WORLD_FILES=("$WORLD/$dir/"*.md)
      for f in "${WORLD_FILES[@]}"; do
        [[ -f "$f" ]] || continue
        name=$(basename "${f%.md}")
        if [[ -z "${SEEN_FILES[$name]+x}" ]]; then
          print_file "$dir/$name  [world bible]" "$f"
        fi
      done

      if [[ ${#SEEN_FILES[@]} -eq 0 && ${#WORLD_FILES[@]} -eq 0 ]]; then
        echo ""
        echo "$DIV"
        echo "DIRECTORY: $WORLD/$dir/  (empty or not found)"
        echo "$DIV"
      fi
      unset SEEN_FILES
    done

  else
    # Selective: --entity "type/Name" (no .md extension)
    for entry in "${ENTITIES[@]}"; do
      resolved=$(resolve_entity_file "$entry")
      if [[ -n "$SNAPSHOT_DIR" && -f "$SNAPSHOT_DIR/${entry}.md" ]]; then
        print_file "$entry  [snapshot pos $POSITION]" "$resolved"
      else
        print_file "$entry" "$resolved"
      fi
    done
  fi

# ── Mode 2 — Structure ────────────────────────────────────────────────────────
# --structure provided. Output world overview + the specific structure files.
# Skips HOOKS.md, WORLD_ORDER.md, and all other structure files.

elif [[ -n "$STRUCTURE" ]]; then

  print_file "DESCRIPTION.md"  "$WORLD/DESCRIPTION.md"
  print_file "SUMMARY.md"      "$WORLD/SUMMARY.md"
  print_file "story_structure/GUIDE.md"            "writing_concepts/story_structure/GUIDE.md"
  print_file "story_structure/Format Reference.md" "writing_concepts/story_structure/Format Reference.md"
  print_file "story_structure/$STRUCTURE"          "writing_concepts/story_structure/${STRUCTURE}.md"

# ── Mode 1 — Overview ─────────────────────────────────────────────────────────
# No entity or structure flags. Output full world overview + all structure files.

else

  print_file "DESCRIPTION.md" "$WORLD/DESCRIPTION.md"
  print_file "SUMMARY.md"     "$WORLD/SUMMARY.md"
  print_file "HOOKS.md"       "$WORLD/HOOKS.md"
  print_file "WORLD_ORDER.md" "$WORLD/WORLD_ORDER.md"

  STRUCTURE_FILES=(writing_concepts/story_structure/*.md)
  if [[ ${#STRUCTURE_FILES[@]} -eq 0 ]]; then
    echo ""
    echo "$DIV"
    echo "STORY STRUCTURE: ⚠ No files found in writing_concepts/story_structure/"
    echo "$DIV"
  else
    for f in "${STRUCTURE_FILES[@]}"; do
      print_file "story_structure/$(basename "$f")" "$f"
    done
  fi

fi
