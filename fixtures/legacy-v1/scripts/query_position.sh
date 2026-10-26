#!/usr/bin/env bash
#
# query_position.sh — Query WORLD_ORDER.md for story positioning information
#
# Usage:
#   bash "Writing_Room/scripts/query_position.sh" \
#     --world "worlds/<World Name>" \
#     --story "<Story Name>" \
#     [--format json|text]
#
# Returns:
#   - Position number of the story/chapter
#   - Story name, unit type, status, in-world date
#   - Previous story details (position N-1)
#   - Next story details (position N+1)
#   - All concurrent stories (same position)
#
# Output formats:
#   - text (default): Human-readable summary
#   - json: Machine-readable JSON for agent parsing
#
# Run from the project root (Writer Helper/).
# All paths are relative to Writing_Room/.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

# ── Argument parsing ──────────────────────────────────────────────────────────

WORLD=""
STORY=""
FORMAT="text"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --world)  WORLD="$2";  shift 2 ;;
    --story)  STORY="$2";  shift 2 ;;
    --format) FORMAT="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$WORLD" || -z "$STORY" ]]; then
  echo "Error: --world and --story are required." >&2
  echo "Usage: query_position.sh --world <path> --story <name>" >&2
  exit 1
fi

if [[ "$FORMAT" != "json" && "$FORMAT" != "text" ]]; then
  echo "Error: --format must be 'json' or 'text'." >&2
  exit 1
fi

WORLD_ORDER_FILE="$WORLD/WORLD_ORDER.md"

if [[ ! -f "$WORLD_ORDER_FILE" ]]; then
  if [[ "$FORMAT" == "json" ]]; then
    echo '{"error":"WORLD_ORDER.md not found","found":false}'
  else
    echo "⚠ WORLD_ORDER.md not found at $WORLD_ORDER_FILE" >&2
  fi
  exit 1
fi

# ── Parse the Story Order table ───────────────────────────────────────────────
#
# Table rows start with "| <number>" (the Position column).
# Format: | Position | [[Story Name]] | Unit | In-World Date | Status | Notes |
#
# Steps:
#   1. Extract data rows (lines matching "| <digit>")
#   2. Use awk to split on "|" and trim each field
#   3. Strip [[ ]] from story names for comparison and storage

TMPFILE=$(mktemp)
trap "rm -f $TMPFILE" EXIT

# Extract table data rows only (skip header and separator lines)
grep -E '^\|\s*[0-9]' "$WORLD_ORDER_FILE" > "$TMPFILE" || true

if [[ ! -s "$TMPFILE" ]]; then
  if [[ "$FORMAT" == "json" ]]; then
    echo '{"error":"No story entries found in WORLD_ORDER.md","found":false}'
  else
    echo "⚠ No story entries found in WORLD_ORDER.md" >&2
  fi
  exit 1
fi

# Parse each row into arrays (one entry per unique position+story pair)
declare -a ROW_POS=()
declare -a ROW_STORY=()
declare -a ROW_UNIT=()
declare -a ROW_DATE=()
declare -a ROW_STATUS=()

while IFS= read -r line; do
  # Use awk to split on "|" and trim whitespace from each field
  parsed=$(echo "$line" | awk -F'|' '{
    for(i=1; i<=NF; i++) {
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", $i)
      print $i
    }
  }')

  # Fields (0-indexed after split): empty, pos, story, unit, date, status, notes
  pos=$(echo "$parsed" | sed -n '2p')
  story_raw=$(echo "$parsed" | sed -n '3p')
  unit=$(echo "$parsed" | sed -n '4p')
  date=$(echo "$parsed" | sed -n '5p')
  status=$(echo "$parsed" | sed -n '6p')

  # Strip [[ ]] from story name
  story=$(echo "$story_raw" | sed 's/\[\[//g; s/\]\]//g' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

  [[ -z "$pos" || -z "$story" ]] && continue

  ROW_POS+=("$pos")
  ROW_STORY+=("$story")
  ROW_UNIT+=("$unit")
  ROW_DATE+=("$date")
  ROW_STATUS+=("$status")

done < "$TMPFILE"

TOTAL=${#ROW_POS[@]}

if [[ $TOTAL -eq 0 ]]; then
  if [[ "$FORMAT" == "json" ]]; then
    echo '{"error":"Failed to parse story entries","found":false}'
  else
    echo "⚠ Failed to parse story entries from WORLD_ORDER.md" >&2
  fi
  exit 1
fi

# ── Find the target story ─────────────────────────────────────────────────────

# Strip [[ ]] from requested story name for comparison
STORY_NORM=$(echo "$STORY" | sed 's/\[\[//g; s/\]\]//g' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

TARGET_IDX=-1
for i in "${!ROW_STORY[@]}"; do
  if [[ "${ROW_STORY[$i]}" == "$STORY_NORM" ]]; then
    TARGET_IDX=$i
    break
  fi
done

if [[ $TARGET_IDX -eq -1 ]]; then
  if [[ "$FORMAT" == "json" ]]; then
    echo "{\"error\":\"Story '$STORY_NORM' not found in WORLD_ORDER.md\",\"found\":false}"
  else
    echo "⚠ Story '$STORY_NORM' not found in WORLD_ORDER.md" >&2
  fi
  exit 1
fi

TARGET_POS="${ROW_POS[$TARGET_IDX]}"
TARGET_UNIT="${ROW_UNIT[$TARGET_IDX]}"
TARGET_DATE="${ROW_DATE[$TARGET_IDX]}"
TARGET_STATUS="${ROW_STATUS[$TARGET_IDX]}"

# ── Find before, after, and concurrent entries ────────────────────────────────

# Collect all unique positions (sorted numerically)
declare -a UNIQUE_POS=()
for p in "${ROW_POS[@]}"; do
  already=false
  for up in "${UNIQUE_POS[@]:-}"; do
    [[ "$up" == "$p" ]] && already=true && break
  done
  $already || UNIQUE_POS+=("$p")
done
IFS=$'\n' UNIQUE_POS=($(printf '%s\n' "${UNIQUE_POS[@]}" | sort -n))
unset IFS

# Find this position's index in the sorted unique list
THIS_POS_IDX=-1
for i in "${!UNIQUE_POS[@]}"; do
  [[ "${UNIQUE_POS[$i]}" == "$TARGET_POS" ]] && THIS_POS_IDX=$i && break
done

# Previous position
PREV_POS=""
PREV_STORY=""
PREV_UNIT=""
PREV_STATUS=""
if [[ $THIS_POS_IDX -gt 0 ]]; then
  PREV_POS="${UNIQUE_POS[$((THIS_POS_IDX - 1))]}"
  # Find first story at that position
  for i in "${!ROW_POS[@]}"; do
    if [[ "${ROW_POS[$i]}" == "$PREV_POS" ]]; then
      PREV_STORY="${ROW_STORY[$i]}"
      PREV_UNIT="${ROW_UNIT[$i]}"
      PREV_STATUS="${ROW_STATUS[$i]}"
      break
    fi
  done
fi

# Next position
NEXT_POS=""
NEXT_STORY=""
NEXT_UNIT=""
NEXT_STATUS=""
if [[ $THIS_POS_IDX -lt $((${#UNIQUE_POS[@]} - 1)) ]]; then
  NEXT_POS="${UNIQUE_POS[$((THIS_POS_IDX + 1))]}"
  for i in "${!ROW_POS[@]}"; do
    if [[ "${ROW_POS[$i]}" == "$NEXT_POS" ]]; then
      NEXT_STORY="${ROW_STORY[$i]}"
      NEXT_UNIT="${ROW_UNIT[$i]}"
      NEXT_STATUS="${ROW_STATUS[$i]}"
      break
    fi
  done
fi

# Concurrent stories (same position, different name)
declare -a CONCURRENT_STORIES=()
declare -a CONCURRENT_UNITS=()
for i in "${!ROW_POS[@]}"; do
  if [[ "${ROW_POS[$i]}" == "$TARGET_POS" && "${ROW_STORY[$i]}" != "$STORY_NORM" ]]; then
    CONCURRENT_STORIES+=("${ROW_STORY[$i]}")
    CONCURRENT_UNITS+=("${ROW_UNIT[$i]}")
  fi
done

# ── Output ────────────────────────────────────────────────────────────────────

if [[ "$FORMAT" == "json" ]]; then
  # Build concurrent array
  CONC_JSON="["
  for i in "${!CONCURRENT_STORIES[@]}"; do
    [[ $i -gt 0 ]] && CONC_JSON+=","
    CONC_JSON+="{\"story\":\"${CONCURRENT_STORIES[$i]}\",\"unit\":\"${CONCURRENT_UNITS[$i]}\"}"
  done
  CONC_JSON+="]"

  # Build before/after (null if absent)
  if [[ -n "$PREV_POS" ]]; then
    BEFORE_JSON="{\"position\":$PREV_POS,\"story\":\"$PREV_STORY\",\"unit\":\"$PREV_UNIT\",\"status\":\"$PREV_STATUS\"}"
  else
    BEFORE_JSON="null"
  fi

  if [[ -n "$NEXT_POS" ]]; then
    AFTER_JSON="{\"position\":$NEXT_POS,\"story\":\"$NEXT_STORY\",\"unit\":\"$NEXT_UNIT\",\"status\":\"$NEXT_STATUS\"}"
  else
    AFTER_JSON="null"
  fi

  cat <<EOF
{
  "found": true,
  "world": "$WORLD",
  "story": "$STORY_NORM",
  "position": $TARGET_POS,
  "unit": "$TARGET_UNIT",
  "status": "$TARGET_STATUS",
  "in_world_date": "$TARGET_DATE",
  "before": $BEFORE_JSON,
  "after": $AFTER_JSON,
  "concurrent": $CONC_JSON
}
EOF

else
  # Human-readable text output
  DIV="────────────────────────────────────────"
  echo "$DIV"
  echo "World Order Position — $STORY_NORM"
  echo "$DIV"
  echo "Position : $TARGET_POS"
  echo "Unit     : $TARGET_UNIT"
  echo "Status   : $TARGET_STATUS"
  echo "Date     : $TARGET_DATE"
  echo ""

  if [[ -n "$PREV_POS" ]]; then
    echo "Before (Position $PREV_POS): [[${PREV_STORY}]] | $PREV_UNIT | $PREV_STATUS"
  else
    echo "Before   : (none — this is the first entry)"
  fi

  if [[ -n "$NEXT_POS" ]]; then
    echo "After  (Position $NEXT_POS): [[${NEXT_STORY}]] | $NEXT_UNIT | $NEXT_STATUS"
  else
    echo "After    : (none — this is the last entry)"
  fi

  if [[ ${#CONCURRENT_STORIES[@]} -gt 0 ]]; then
    echo ""
    echo "Concurrent at position $TARGET_POS:"
    for i in "${!CONCURRENT_STORIES[@]}"; do
      echo "  • [[${CONCURRENT_STORIES[$i]}]] | ${CONCURRENT_UNITS[$i]}"
    done
  fi
  echo "$DIV"
fi
