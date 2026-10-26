#!/usr/bin/env python3
"""create_snapshot.py — Capture world state snapshot after a story completes

Usage:
  python "scripts/create_snapshot.py" \\
    --world "worlds/<World Name>" --position <N> \\
    --story "<Story Name>" --unit "<Full Story|Ch. N|...>"

Creates worlds/<World>/snapshots/<position>/ containing copies of characters/,
factions/, points_of_interest/, mythology/, DESCRIPTION.md and a manifest.md,
and creates or updates worlds/<World>/snapshots/manifest.md (the index).

HOOKS.md is intentionally excluded — it is a forward-looking list of narrative
seeds that lives only in the base world bible; hooks are never frozen in time.

The snapshot captures the world state AFTER the story at <position> completed;
the story at position N+1 loads from snapshot N as its baseline. Invoke after
World Archivist Consolidate, before planning the next story. An existing
snapshot at the same position is overwritten.

Paths are relative to the project root (found via --root, WRITING_ROOM_ROOT,
a writing-room.toml marker, or the legacy worlds/ + stories/ layout).
"""

import re
import shutil
import sys
from datetime import date
from pathlib import Path

from common import DIV, make_parser, md_files, out, setup

ENTITY_DIRS = ("characters", "factions", "points_of_interest", "mythology")
NOTE = "Auto-created by Story Analyzer"

INDEX_HEADER = """# World Snapshots — Index

> Maintained by create_snapshot.py. Do not edit manually.
> Each entry records the world state AFTER the story at that position completed.
> The story at position N+1 uses snapshot N as its world baseline.

| Position | Story | Unit | Date Created | Notes |
|----------|-------|------|--------------|-------|
"""

MANIFEST = """# Snapshot Manifest — Position {position}

> **Created:** {today}
> **Captures world state AFTER this story completed.**
> Stories at position {next_position} and beyond should use this as their baseline.

## Story
- **Story:** [[{story}]]
- **Unit:** {unit}
- **Position:** {position}

## Contents
- **Characters:** {characters} file(s)
- **Factions:** {factions} file(s)
- **Locations (Points of Interest):** {points_of_interest} file(s)
- **Mythology:** {mythology} file(s)
- **Total entities:** {total}

## Notes

This snapshot was created automatically by the Story Analyzer after chapter completion.
World consolidation (merging state/bible/ into worlds/) should occur before this snapshot
is taken so that the snapshot reflects all story-driven world changes.

If consolidation has not yet occurred, this snapshot reflects the pre-story world state only.
Invoke the World Archivist → Consolidate, then re-run create_snapshot.py to update.
"""


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def row_position(line):
    """Position cell of a table data row, or None if the line isn't one."""
    if not re.match(r"^\|\s*[0-9]", line):
        return None
    cells = line.split("|")
    return int(cells[1].strip()) if len(cells) > 1 and cells[1].strip().isdigit() else None


def update_index(index_path, position, story, unit, today):
    """Create the index, or replace/insert this position's row (kept in position order)."""
    new_row = f"| {position} | [[{story}]] | {unit} | {today} | {NOTE} |"

    if not Path(index_path).is_file():
        write(index_path, INDEX_HEADER + new_row + "\n")
        out("  snapshots/manifest.md — created")
        return

    lines = Path(index_path).read_text(encoding="utf-8").splitlines()

    for i, line in enumerate(lines):
        if row_position(line) == position:
            lines[i] = new_row
            write(index_path, "\n".join(lines) + "\n")
            out(f"  snapshots/manifest.md — updated (position {position})")
            return

    insert_at = next(
        (i for i, line in enumerate(lines) if (row_position(line) or 0) > position),
        len(lines),
    )
    lines.insert(insert_at, new_row)
    write(index_path, "\n".join(lines) + "\n")
    out(f"  snapshots/manifest.md — appended (position {position})")


def main():
    setup()
    p = make_parser("Capture world state snapshot after a story completes")
    p.add_argument("--world", required=True)
    p.add_argument("--position", required=True)
    p.add_argument("--story", required=True)
    p.add_argument("--unit", required=True)
    a = p.parse_args()

    if not re.fullmatch(r"[0-9]+", a.position):
        print("Error: --position must be a positive integer.", file=sys.stderr)
        sys.exit(1)
    position = int(a.position)

    today = date.today().isoformat()
    snapshot_dir = f"{a.world}/snapshots/{position}"
    index_path = f"{a.world}/snapshots/manifest.md"

    if Path(snapshot_dir).is_dir():
        out()
        out(DIV)
        out(f"⚠ Snapshot already exists at {snapshot_dir}")
        out(f"  Overwriting existing snapshot for position {position}.")
        out(DIV)
        shutil.rmtree(snapshot_dir)

    for d in ENTITY_DIRS:
        Path(f"{snapshot_dir}/{d}").mkdir(parents=True, exist_ok=True)

    out()
    out(DIV)
    out(f"Creating snapshot — Position {position} — [[{a.story}]] | {a.unit}")
    out(DIV)

    counts = {}
    for d in ENTITY_DIRS:
        files = md_files(f"{a.world}/{d}")
        for f in files:
            shutil.copy(f, f"{snapshot_dir}/{d}/")
        counts[d] = len(files)
        out(f"  {d + '/':<20}— {len(files)} file(s)")

    description = f"{a.world}/DESCRIPTION.md"
    if Path(description).is_file():
        shutil.copy(description, f"{snapshot_dir}/DESCRIPTION.md")
        out("  DESCRIPTION.md — copied")
    else:
        out("  DESCRIPTION.md — ⚠ not found, skipped")

    total = sum(counts.values())
    write(f"{snapshot_dir}/manifest.md", MANIFEST.format(
        position=position, next_position=position + 1, today=today,
        story=a.story, unit=a.unit, total=total, **counts,
    ))
    out("  manifest.md — written")

    update_index(index_path, position, a.story, a.unit, today)

    out()
    out(DIV)
    out("Snapshot complete")
    out(f"  Location  : {snapshot_dir}")
    out(f"  Position  : {position}")
    out(f"  Story     : [[{a.story}]] | {a.unit}")
    out(f"  Entities  : {total} total")
    out(DIV)
    out()
    out(f"Stories at position {position + 1}+ can now load baseline from:")
    out(f"  {snapshot_dir}")


if __name__ == "__main__":
    main()
