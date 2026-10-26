#!/usr/bin/env python3
"""query_position.py — Query WORLD_ORDER.md for story positioning information

Usage:
  python "Writing_Room/scripts/query_position.py" \\
    --world "worlds/<World Name>" --story "<Story Name>" [--format json|text]

Returns the story's position, unit, status and in-world date, the previous
(position N-1) and next (position N+1) entries, and all concurrent stories
(same position).

Formats:
  text (default)  Human-readable summary
  json            Machine-readable JSON for agent parsing

WORLD_ORDER.md rows look like:
  | Position | [[Story Name]] | Unit | In-World Date | Status | Notes |
Paths are relative to Writing_Room/ (the script cd's there automatically).
"""

import json
import re
import sys
from pathlib import Path

from common import DIV, make_parser, out, setup, strip_wikilink

ROW_RE = re.compile(r"^\|\s*[0-9]")


def fail(fmt, message):
    """Report an error in the requested format and exit 1."""
    if fmt == "json":
        out(json.dumps({"error": message, "found": False}, ensure_ascii=False))
    else:
        print(f"⚠ {message}", file=sys.stderr)
    sys.exit(1)


def parse_rows(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not ROW_RE.match(line):
            continue
        # "| 1 | [[A]] | Unit | Date | Status | Notes |" -> ['', '1', '[[A]]', ...]
        f = [c.strip() for c in line.split("|")]
        f += [""] * (6 - len(f))
        pos, story = f[1], strip_wikilink(f[2])
        if pos and story:
            rows.append({"pos": pos, "story": story, "unit": f[3], "date": f[4], "status": f[5]})
    return rows


def pos_key(pos):
    try:
        return (0, float(pos), pos)
    except ValueError:
        return (1, 0.0, pos)


def pos_value(pos):
    return int(pos) if pos.isdigit() else pos


def neighbour(rows, pos):
    """First row at the given position, as the before/after summary (None if no pos)."""
    if pos is None:
        return None
    row = next(r for r in rows if r["pos"] == pos)
    return {"position": pos_value(pos), "story": row["story"], "unit": row["unit"], "status": row["status"]}


def main():
    setup()
    p = make_parser("Query WORLD_ORDER.md for story positioning information")
    p.add_argument("--world", required=True)
    p.add_argument("--story", required=True)
    p.add_argument("--format", choices=("json", "text"), default="text")
    a = p.parse_args()
    fmt = a.format

    order_file = f"{a.world}/WORLD_ORDER.md"
    if not Path(order_file).is_file():
        fail(fmt, f"WORLD_ORDER.md not found at {order_file}" if fmt == "text" else "WORLD_ORDER.md not found")

    rows = parse_rows(order_file)
    if not rows:
        fail(fmt, "No story entries found in WORLD_ORDER.md")

    story = strip_wikilink(a.story)
    target = next((r for r in rows if r["story"] == story), None)
    if target is None:
        fail(fmt, f"Story '{story}' not found in WORLD_ORDER.md")

    unique = sorted({r["pos"] for r in rows}, key=pos_key)
    idx = unique.index(target["pos"])
    before = neighbour(rows, unique[idx - 1] if idx > 0 else None)
    after = neighbour(rows, unique[idx + 1] if idx < len(unique) - 1 else None)
    concurrent = [
        {"story": r["story"], "unit": r["unit"]}
        for r in rows
        if r["pos"] == target["pos"] and r["story"] != story
    ]

    if fmt == "json":
        out(json.dumps({
            "found": True,
            "world": a.world,
            "story": story,
            "position": pos_value(target["pos"]),
            "unit": target["unit"],
            "status": target["status"],
            "in_world_date": target["date"],
            "before": before,
            "after": after,
            "concurrent": concurrent,
        }, indent=2, ensure_ascii=False))
        return

    dash = "─" * 40
    out(dash)
    out(f"World Order Position — {story}")
    out(dash)
    out(f"Position : {target['pos']}")
    out(f"Unit     : {target['unit']}")
    out(f"Status   : {target['status']}")
    out(f"Date     : {target['date']}")
    out()
    if before:
        out(f"Before (Position {before['position']}): [[{before['story']}]] | {before['unit']} | {before['status']}")
    else:
        out("Before   : (none — this is the first entry)")
    if after:
        out(f"After  (Position {after['position']}): [[{after['story']}]] | {after['unit']} | {after['status']}")
    else:
        out("After    : (none — this is the last entry)")
    if concurrent:
        out()
        out(f"Concurrent at position {target['pos']}:")
        for c in concurrent:
            out(f"  • [[{c['story']}]] | {c['unit']}")
    out(dash)


if __name__ == "__main__":
    main()
