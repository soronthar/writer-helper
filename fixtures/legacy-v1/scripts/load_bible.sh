#!/usr/bin/env bash
#
# load_bible.sh — Story context loader
#
# Used by the Draft Writer, Planner, Reviewer, and Draft Fixer to load
# story-level reference files in a single Bash call.
#
# ═════════════════��═══════════════════════════════════��══════════
# Core flags (always available)
# ════════════════════════════════════════════════════════════════
#
#   --story   <path>   Story root relative to Writing_Room/.
#                      Book series: "stories/<Series>/Book 01 - <Title>"
#   --world   <path>   World bible root. e.g. "worlds/Harrowmere"
#
# ═════════════════════════���══════════════════════════════════════
# Output control flags (suppress sections that the agent doesn't need)
# ═════════════════════════��═══════════════════════���══════════════
#
#   --no-style         Skip the style file. Use for Reviewer passes.
#   --no-last-chapter  Skip the most recent completed chapter.
#                      Use for Planner (Timeline is sufficient) and
#                      Reviewer (chapter is already read in Step 3).
#   --no-timeline      Skip state/Timeline.md. Use for the Reviewer's
#                      character pass (Timeline already in context from
#                      the consistency pass).
#   --no-schemes       Skip state/ACTIVE_SCHEMES.md. Default is to load
#                      it (story-local registry of in-flight deceptions,
#                      concealments, and unresolved promises that
#                      downstream agents must respect).
#   --no-facts         Skip state/STORY_FACTS.md. Default is to load it
#                      (story-local ledger of plot-consequential facts —
#                      quantities, fingerprints, logistics, commitments —
#                      that downstream agents must not contradict).
#
# ═══════════════════════���════════════════════════════════════════
# Optional content flags (add sections the agent needs)
# ══════════════════════════════════════���═════════════════════════
#
#   --structure <Name> Add GUIDE.md, Format Reference.md, and the named
#                      structure file. Use for Planner. Name is the
#                      filename stem (no .md extension).
#
#   --description      Add DESCRIPTION.md with source-priority:
#                      state/bible/DESCRIPTION.md → worlds/<World>/DESCRIPTION.md.
#                      Use for Reviewer consistency pass.
#
#   --reviews-dir <path>  Add all Reviewer-*.md files from a directory.
#                         Path relative to Writing_Room/. Use for Draft Fixer.
#
#   --hooks            Add worlds/<World>/HOOKS.md for deduplication checks.
#                      Use for Story Analyzer.
#
# ═══════════════════════════════════════════════════════���════════
# Entity flags (source-priority: state/bible/ → worlds/)
# ════════════════════════════════════════════════════════════════
#
#   --char    "Name"   Load characters/<Name>.md
#   --loc     "Name"   Load points_of_interest/<Name>.md
#   --faction "Name"   Load factions/<Name>.md
#   --myth    "Name"   Load mythology/<Name>.md
#
#   Repeat any entity flag for multiple names. Use the exact filename
#   stem (no .md extension) as it appears in the world bible directory.
#
# ════════════════════════════��═══════════════════════════════════
# Style hint
# ══════════════════════════════════════════════���═════════════════
#
#   --style   "Name"   Partial name matched against style filenames.
#                      Used when multiple style files exist. Ignored
#                      when only one file is present.
#
# ════════════════════════════════���══════════════════════════════��
# Output order
# ═══════════════════════════════════════════════���════════════════
#
#   0. Review reports    (--reviews-dir)
#   1. Structure files   (--structure)
#   2. DESCRIPTION.md    (--description)
#   3. Style file        (default; suppressed by --no-style)
#   4. Most recent chapter (default; suppressed by --no-last-chapter)
#   5. state/Timeline.md   (default; suppressed by --no-timeline)
#   5a. state/ACTIVE_SCHEMES.md (default; suppressed by --no-schemes)
#   5b. state/STORY_FACTS.md   (default; suppressed by --no-facts)
#   5c. HOOKS.md               (--hooks)
#   6. Entity files      (--char / --loc / --faction / --myth)
#
# ═════════════════════���════════════════════���═════════════════════
# Usage examples
# ════════════════════════════════════════════════���═══════════════
#
#   Draft Writer:
#     bash "Writing_Room/scripts/load_bible.sh" \
#       --story "stories/The Tallow Ledger" --world "worlds/Harrowmere" \
#       --char "Mara Quill" --loc "The Ashwood"
#
#   Planner:
#     bash "Writing_Room/scripts/load_bible.sh" \
#       --story "stories/The Tallow Ledger" --world "worlds/Harrowmere" \
#       --structure "Three-Act Structure" --no-last-chapter \
#       --char "Mara Quill" --loc "The Ashwood"
#
#   Reviewer — consistency pass:
#     bash "Writing_Room/scripts/load_bible.sh" \
#       --story "stories/The Tallow Ledger" --world "worlds/Harrowmere" \
#       --no-style --no-last-chapter --description \
#       --loc "The Ashwood" --faction "Harbor Guild" --myth "The Pale Covenant"
#
#   Reviewer — character pass:
#     bash "Writing_Room/scripts/load_bible.sh" \
#       --story "stories/The Tallow Ledger" --world "worlds/Harrowmere" \
#       --no-style --no-last-chapter --no-timeline \
#       --char "Mara Quill" --char "Daren Cole"
#
#   Draft Fixer:
#     bash "Writing_Room/scripts/load_bible.sh" \
#       --story "stories/The Tallow Ledger" --world "worlds/Harrowmere" \
#       --reviews-dir "stories/The Tallow Ledger/current_chapter/current_reviews" \
#       --no-last-chapter --no-timeline
#
#   Story Analyzer:
#     bash "Writing_Room/scripts/load_bible.sh" \
#       --story "stories/The Tallow Ledger" --world "worlds/Harrowmere" \
#       --no-style --no-last-chapter --hooks \
#       --char "Mara Quill" --char "Daren Cole" \
#       --loc "The Ashwood" --faction "Harbor Guild"
#
# ════════════════════════════════════════════════════════════════
# Notes
# ════════════════════════════════════════════════════════════════
#
#   - Run from the project root (Writer Helper/).
#   - All paths are relative to Writing_Room/. The script cd's there automatically.
#   - Missing files emit a ⚠ warning line rather than crashing.
#
# ════════════════════════════════════════════════════════════════
# Position-aware loading (--position <N>)
# ════════════════════════════════════════════════════════════════
#
#   --position <N>  When set, entity reads apply a three-tier priority:
#     1. state/bible/<type>/<Name>.md      (story-local changes — highest)
#     2. worlds/<World>/snapshots/<N>/...  (world state as of position N)
#     3. worlds/<World>/<type>/<Name>.md   (current world — fallback)
#
#   Use this when writing a story that sits at a known chronological position.
#   Pass the PREVIOUS story's position as N (so N is the snapshot baseline
#   from before this story's events occurred).
#
#   If no snapshot exists for position N, tier 2 is skipped silently.

set -uo pipefail
shopt -s nullglob

# ── Move to Writing_Room/ ─────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

# ── Argument parsing ──────────────────────────────────────────────────────────

STORY=""
WORLD=""
STYLE_HINT=""
STRUCTURE=""
REVIEWS_DIR=""
POSITION=""
NO_STYLE=false
NO_LAST_CHAPTER=false
NO_TIMELINE=false
NO_SCHEMES=false
NO_FACTS=false
DESCRIPTION=false
HOOKS=false
declare -a CHARS=()
declare -a LOCS=()
declare -a FACTIONS=()
declare -a MYTHS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --story)           STORY="$2";           shift 2 ;;
    --world)           WORLD="$2";           shift 2 ;;
    --style)           STYLE_HINT="$2";      shift 2 ;;
    --structure)       STRUCTURE="$2";       shift 2 ;;
    --reviews-dir)     REVIEWS_DIR="$2";     shift 2 ;;
    --position)        POSITION="$2";        shift 2 ;;
    --no-style)        NO_STYLE=true;        shift 1 ;;
    --no-last-chapter) NO_LAST_CHAPTER=true; shift 1 ;;
    --no-timeline)     NO_TIMELINE=true;     shift 1 ;;
    --no-schemes)      NO_SCHEMES=true;      shift 1 ;;
    --no-facts)        NO_FACTS=true;        shift 1 ;;
    --description)     DESCRIPTION=true;     shift 1 ;;
    --hooks)           HOOKS=true;           shift 1 ;;
    --char)            CHARS+=("$2");        shift 2 ;;
    --loc)             LOCS+=("$2");         shift 2 ;;
    --faction)         FACTIONS+=("$2");     shift 2 ;;
    --myth)            MYTHS+=("$2");        shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$STORY" || -z "$WORLD" ]]; then
  echo "Error: --story and --world are required." >&2
  echo "Usage: load_bible.sh --story <path> --world <path> [flags] [--char Name] ..." >&2
  exit 1
fi

# Resolve snapshot directory for position-aware loading
SNAPSHOT_DIR=""
if [[ -n "$POSITION" ]]; then
  CANDIDATE="$WORLD/snapshots/$POSITION"
  if [[ -d "$CANDIDATE" ]]; then
    SNAPSHOT_DIR="$CANDIDATE"
  else
    echo ""
    echo "$DIV"
    echo "POSITION $POSITION: ⚠ No snapshot found at $CANDIDATE — using current world as baseline"
    echo "$DIV"
  fi
fi

# ── Helpers ──────────────────────────────────────────────────────────���────────

DIV="═══════════════════════════════════��════════════════════════"

# Print a file with a labelled header. Emits a NOT FOUND warning if missing.
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

# Load one world bible entity with source-priority:
#   state/bible/<type>/<Name>.md              (story-local — highest)
#   worlds/<World>/snapshots/<N>/<type>/...   (snapshot — if --position set)
#   worlds/<World>/<type>/<Name>.md           (current world — fallback)
print_entity() {
  local type="$1"
  local name="$2"
  local primary="$STORY/state/bible/${type}/${name}.md"
  local snapshot_file=""
  local fallback="$WORLD/${type}/${name}.md"

  if [[ -n "$SNAPSHOT_DIR" ]]; then
    snapshot_file="$SNAPSHOT_DIR/${type}/${name}.md"
  fi

  echo ""
  echo "$DIV"
  if [[ -f "$primary" ]]; then
    echo "FILE: ${type}/${name}  [story-local]"
    echo "$DIV"
    cat "$primary"
  elif [[ -n "$snapshot_file" && -f "$snapshot_file" ]]; then
    echo "FILE: ${type}/${name}  [snapshot pos $POSITION]"
    echo "$DIV"
    cat "$snapshot_file"
  elif [[ -f "$fallback" ]]; then
    echo "FILE: ${type}/${name}  [world bible]"
    echo "$DIV"
    cat "$fallback"
  else
    echo "FILE: ${type}/${name}  ⚠ NOT FOUND in state/bible/, snapshot, or world bible"
    echo "$DIV"
  fi
}

# ── 0. Review reports (--reviews-dir) ─────────────────────────────��──────────

if [[ -n "$REVIEWS_DIR" ]]; then
  REVIEW_FILES=("$REVIEWS_DIR"/Reviewer-*.md)
  if [[ ${#REVIEW_FILES[@]} -eq 0 ]]; then
    echo ""
    echo "$DIV"
    echo "REVIEWS: ⚠ No Reviewer-*.md files found in $REVIEWS_DIR"
    echo "$DIV"
  else
    for f in "${REVIEW_FILES[@]}"; do
      print_file "$(basename "$f")" "$f"
    done
  fi
fi

# ── 1. Structure files (--structure) ─────────────────────────────────────────
# GUIDE.md + Format Reference.md + named structure file. Matches Planner's
# reading order (structure context before style).

if [[ -n "$STRUCTURE" ]]; then
  print_file "story_structure/GUIDE.md"            "writing_concepts/story_structure/GUIDE.md"
  print_file "story_structure/Format Reference.md" "writing_concepts/story_structure/Format Reference.md"
  print_file "story_structure/$STRUCTURE"          "writing_concepts/story_structure/${STRUCTURE}.md"
fi

# ── 2. DESCRIPTION.md (--description) ────────────────────────────────────────
# Source-priority: state/bible/DESCRIPTION.md → worlds/<World>/DESCRIPTION.md.

if [[ "$DESCRIPTION" == true ]]; then
  primary="$STORY/state/bible/DESCRIPTION.md"
  fallback="$WORLD/DESCRIPTION.md"
  echo ""
  echo "$DIV"
  if [[ -f "$primary" ]]; then
    echo "FILE: DESCRIPTION.md  [story-local]"
    echo "$DIV"
    cat "$primary"
  elif [[ -f "$fallback" ]]; then
    echo "FILE: DESCRIPTION.md  [world bible]"
    echo "$DIV"
    cat "$fallback"
  else
    echo "FILE: DESCRIPTION.md  ⚠ NOT FOUND in state/bible/ or world bible"
    echo "$DIV"
  fi
fi

# ── 3. Style file (suppressed by --no-style) ──────────────────────────────────

if [[ "$NO_STYLE" != true ]]; then
  STYLE_FILES=(writing_concepts/styles/*.md)

  if [[ ${#STYLE_FILES[@]} -eq 0 ]]; then
    echo ""
    echo "$DIV"
    echo "STYLE FILE: ⚠ None found in writing_concepts/styles/ — agent uses own judgment"
    echo "$DIV"

  elif [[ ${#STYLE_FILES[@]} -eq 1 ]]; then
    print_file "Style: ${STYLE_FILES[0]}" "${STYLE_FILES[0]}"

  else
    if [[ -n "$STYLE_HINT" ]]; then
      MATCHED=""
      for f in "${STYLE_FILES[@]}"; do
        if [[ "$f" == *"$STYLE_HINT"* ]]; then
          MATCHED="$f"
          break
        fi
      done

      if [[ -n "$MATCHED" ]]; then
        print_file "Style: $MATCHED  [matched hint: \"$STYLE_HINT\"]" "$MATCHED"
      else
        echo ""
        echo "$DIV"
        echo "STYLE FILE: ⚠ Multiple files found; hint \"$STYLE_HINT\" matched nothing."
        echo "Agent must select one and read it separately. Available files:"
        for f in "${STYLE_FILES[@]}"; do echo "  writing_concepts/styles/$(basename "$f")"; done
        echo "$DIV"
      fi

    else
      echo ""
      echo "$DIV"
      echo "STYLE FILE: ⚠ Multiple files found — agent must select (check CONCEPT.md Notes):"
      for f in "${STYLE_FILES[@]}"; do echo "  writing_concepts/styles/$(basename "$f")"; done
      echo "$DIV"
    fi
  fi
fi

# ── 4. Most recent completed chapter (suppressed by --no-last-chapter) ────────
# Glob expansion in bash is alphabetical, so the last element = highest chapter
# number given the Chapter_01.md … Chapter_NN.md naming convention.

if [[ "$NO_LAST_CHAPTER" != true ]]; then
  CHAPTER_FILES=("$STORY/chapters/"*.md)

  if [[ ${#CHAPTER_FILES[@]} -eq 0 ]]; then
    echo ""
    echo "$DIV"
    echo "MOST RECENT CHAPTER: chapters/ is empty or absent — this is the first chapter"
    echo "$DIV"
  else
    LAST_CHAPTER="${CHAPTER_FILES[${#CHAPTER_FILES[@]}-1]}"
    print_file "Most recent chapter: $LAST_CHAPTER" "$LAST_CHAPTER"
  fi
fi

# ── 5. Timeline (suppressed by --no-timeline) ─────────────────────────────────

if [[ "$NO_TIMELINE" != true ]]; then
  print_file "state/Timeline.md" "$STORY/state/Timeline.md"
fi

# ── 5a. ACTIVE_SCHEMES.md (suppressed by --no-schemes) ────────────────────────
# Story-local registry of in-flight deceptions, concealments, and unresolved
# operational commitments. Loaded by default — downstream agents must respect
# Active entries (no character accidentally exposing their own lie in prose).

if [[ "$NO_SCHEMES" != true ]]; then
  print_file "state/ACTIVE_SCHEMES.md" "$STORY/state/ACTIVE_SCHEMES.md"
fi

# ── 5b. STORY_FACTS.md (suppressed by --no-facts) ────────────────────────────
# Story-local ledger of plot-consequential facts — quantities, forensic
# fingerprints, logistical specifics, and in-force commitments. Loaded by
# default — downstream agents must not contradict Current entries.

if [[ "$NO_FACTS" != true ]]; then
  print_file "state/STORY_FACTS.md" "$STORY/state/STORY_FACTS.md"
fi

# ── 5c. HOOKS.md (--hooks) ────────────────────────────────────────────────────

if [[ "$HOOKS" == true ]]; then
  print_file "HOOKS.md" "$WORLD/HOOKS.md"
fi

# ── 6. World bible entities ───────────────────────────────────────────────────

for name in "${CHARS[@]}";    do print_entity "characters"         "$name"; done
for name in "${LOCS[@]}";     do print_entity "points_of_interest" "$name"; done
for name in "${FACTIONS[@]}"; do print_entity "factions"           "$name"; done
for name in "${MYTHS[@]}";    do print_entity "mythology"          "$name"; done
