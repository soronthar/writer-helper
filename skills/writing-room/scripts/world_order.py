#!/usr/bin/env python3
"""world_order.py — Change rows of a world's WORLD_ORDER.md without hand-editing the table

Usage:
  python "<WR>/scripts/world_order.py" add      --world "<World>" --story "<Story>" --unit "<Unit>" \\
                                                [--position N] [--shift] [--status S] [--date D] [--notes T]
  python "<WR>/scripts/world_order.py" status   --world "<World>" --story "<Story>" [--unit U] --to "<Status>"
  python "<WR>/scripts/world_order.py" move     --world "<World>" --story "<Story>" [--unit U] --to N [--shift]
  python "<WR>/scripts/world_order.py" chapter  --world "<World>" --story "<Story>" --chapter N [--book B]
  python "<WR>/scripts/world_order.py" renumber --world "<World>"

Every command also takes --dry-run (print the change, write nothing) and --reason
(the text of the Last synchronized line; each command has a default).

  add       Adds a row. Without --position it goes after the last entry. A taken
            position makes the row concurrent, unless --shift moves every row at that
            position and later down by one.
  status    Sets a row's Status: Not Started, In Progress or Complete.
  move      Gives a row a new position (concurrent, or --shift as for add).
  chapter   The story-analyzer's update after analyzing a chapter. The unit comes
            from the story's CONCEPT.md **Format:** — Full Story for a Short Story or
            Novelette, Ch. N for a Book, Bk. B Ch. N for a Book Series (--book). It
            fills a TBD row, completes the chapter's row, or adds it after the
            previous chapter's row (shifting later rows). A Full Story row is Complete
            only once the last chapter (OUTLINE.md **Total chapters:**) is analyzed;
            before that it is In Progress. It ends with "Story complete: yes|no".
  renumber  Renumbers positions 1, 2, 3… in order, keeping concurrent rows together.

A story with several rows (a Book) is named with --unit where a command needs one row.
The table is kept sorted by position; rows that do not change keep their exact text,
and so do the file's line endings. On an error nothing is written: the reason goes
to stderr after "Nothing was changed:" and the exit code is 1.

Paths are relative to the project root (found via --root, WRITING_ROOM_ROOT,
a writing-room.toml marker, or the legacy worlds/ + stories/ layout).
"""

import argparse
import datetime
import re
import sys
from pathlib import Path

from common import read_exact, setup, strip_wikilink

STATUSES = ("Not Started", "In Progress", "Complete")
SHORT = ("short story", "novelette")


def _cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _field(text, name):
    m = re.search(rf"\*\*{name}:\*\*\s*`?([^`\n]+?)`?\s*$", text, flags=re.M)
    return m.group(1).strip() if m else ""


class Table:
    """The Story Order table of a WORLD_ORDER.md, parsed into rows that render back unchanged unless edited."""

    def __init__(self, text):
        self.nl = "\r\n" if "\r\n" in text else "\n"
        self.lines = text.split(self.nl)
        try:
            self.head = next(n for n, line in enumerate(self.lines) if line.startswith("| Position"))
        except StopIteration:
            raise ValueError("WORLD_ORDER.md has no Story Order table (a '| Position |' header)")
        self.end = self.head + 2
        while self.end < len(self.lines) and self.lines[self.end].startswith("|"):
            self.end += 1
        self.rows = []
        for line in self.lines[self.head + 2:self.end]:
            c = _cells(line) + [""] * 6
            if all(x in ("", "—", "-") for x in c[:6]):
                continue  # the template's placeholder row
            if not c[0].isdigit():
                raise ValueError(f"the row {line.strip()!r} has position {c[0]!r}; positions must be whole numbers")
            self.rows.append({"pos": int(c[0]), "story": strip_wikilink(c[1]), "unit": c[2], "date": c[3],
                              "status": c[4], "notes": c[5], "line": line})
        self.dropped_placeholder = len(self.rows) < self.end - self.head - 2

    def find(self, story, unit=None):
        return [r for r in self.rows if r["story"] == story and (unit is None or r["unit"] == unit)]

    def one(self, story, unit=None):
        found = self.find(story, unit)
        if not found:
            raise ValueError(f"no row for [[{story}]]" + (f" with unit {unit!r}" if unit else "") + " in WORLD_ORDER.md")
        if len(found) > 1:
            raise ValueError(f"[[{story}]] has {len(found)} rows ({', '.join(r['unit'] for r in found)}); "
                             "name one with --unit")
        return found[0]

    def last(self):
        return max((r["pos"] for r in self.rows), default=0)

    def at(self, pos, besides=None):
        return [r for r in self.rows if r is not besides and r["pos"] == pos]

    def shift_from(self, pos, besides=None):
        for r in self.rows:
            if r is not besides and r["pos"] >= pos:
                self.set(r, pos=r["pos"] + 1)

    def set(self, row, **values):
        row.update(values)
        row["line"] = None

    def place(self, row, pos, shift):
        """Put a row at a position; return a note on what else is there."""
        others = self.at(pos, besides=row)
        if others and shift:
            self.shift_from(pos, besides=row)
            note = f"rows from position {pos} on moved down by one"
        elif others:
            note = "concurrent with " + ", ".join(f"[[{r['story']}]]" for r in others)
        else:
            note = ""
        self.set(row, pos=pos)
        self.rows.remove(row)
        self.rows.append(row)  # after the rows already at its position once sorted
        return note

    def add(self, story, unit, position=None, shift=False, status="Not Started", date="—", notes=""):
        """Add a row; return (row, note)."""
        if self.find(story, unit):
            raise ValueError(f"[[{story}]] already has a {unit} row in WORLD_ORDER.md")
        pos = position or self.last() + 1
        row = {"pos": pos, "story": story, "unit": unit, "date": date or "—", "status": status, "notes": notes}
        self.rows.append(row)
        return row, self.place(row, pos, shift)

    def renumber(self):
        self.rows.sort(key=lambda r: r["pos"])
        new, prev = 0, None
        for r in self.rows:
            if r["pos"] != prev:
                new, prev = new + 1, r["pos"]
            if r["pos"] != new:
                r["new"] = new
        for r in self.rows:
            if "new" in r:
                self.set(r, pos=r.pop("new"))

    def render(self, today, reason):
        self.rows.sort(key=lambda r: r["pos"])
        body = []
        for r in self.rows:
            if r["line"] is None:
                notes = f" {r['notes']} " if r["notes"] else " "
                r["line"] = f"| {r['pos']} | [[{r['story']}]] | {r['unit']} | {r['date']} | {r['status']} |{notes}|"
            body.append(r["line"])
        lines = self.lines[:self.head + 2] + body + self.lines[self.end:]
        for n, line in enumerate(lines):
            if line.startswith("> **Last synchronized:**"):
                lines[n] = f"> **Last synchronized:** {today} — {reason}"
                break
        return self.nl.join(lines)


def describe(row):
    return f"| {row['pos']} | [[{row['story']}]] | {row['unit']} | {row['status']} |"


def chapter(table, story, n, book, fmt, total):
    """The story-analyzer's WORLD_ORDER update for chapter n. Return (summary, story complete or None)."""
    fmt = fmt.lower()
    if fmt in SHORT:
        unit = "Full Story"
    elif fmt == "book":
        unit = f"Ch. {n}"
    elif fmt == "book series":
        if book is None:
            raise ValueError("the story is a Book Series; pass --book N")
        unit = f"Bk. {book} Ch. {n}"
    else:
        raise ValueError(f"the story's CONCEPT.md **Format:** is {fmt!r}; expected Short Story, Novelette, Book "
                         "or Book Series")
    if unit == "Full Story":
        if total is None:
            status = "In Progress"
        else:
            status = "Complete" if n >= total else "In Progress"
    else:
        status = "Complete"

    rows = table.find(story)
    exact = [r for r in rows if r["unit"] == unit]
    tbd = [r for r in rows if r["unit"] == "TBD"]
    if exact:
        row = exact[0]
        if row["status"] != "Complete":  # re-analyzing a chapter never reopens a finished row
            table.set(row, status=status)
        summary = f"{unit} → {row['status']}"
    elif tbd:
        row = tbd[0]
        table.set(row, unit=unit, status=status, notes="" if row["notes"].startswith("Placeholder") else row["notes"])
        summary = f"TBD → {unit}, {status}"
    else:
        prev_unit = re.sub(r"\d+$", str(n - 1), unit) if unit != "Full Story" and n > 1 else None
        prev = [r for r in rows if r["unit"] == prev_unit]
        if prev:
            pos, shift = prev[0]["pos"] + 1, True
        elif rows:
            pos, shift = max(r["pos"] for r in rows) + 1, True
        else:
            pos, shift = table.last() + 1, False
        row, note = table.add(story, unit, pos, shift=shift, status=status)
        summary = f"new {unit} row at position {pos}" + (f" ({note})" if note else "")
        if not rows:
            summary += " — the default; reposition it with the world-archivist if it is wrong"

    if fmt == "book series":
        complete = None
    elif unit == "Full Story":
        complete = row["status"] == "Complete"
    else:
        done = sum(1 for r in table.find(story) if r["unit"].startswith("Ch.") and r["status"] == "Complete")
        complete = total is not None and done >= total
    if unit == "Full Story" and total is None and row["status"] != "Complete":
        summary += " (OUTLINE.md has no **Total chapters:**, so the story is not marked Complete; " \
                   "run the status command when the last chapter is analyzed)"
    return summary, complete


def main():
    setup()
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=None, help="project root (default: auto-discovered)")
    common.add_argument("--world", required=True, help='the world, e.g. "worlds/<World>" or just "<World>"')
    common.add_argument("--dry-run", action="store_true", help="print the change and write nothing")
    common.add_argument("--reason", default="", help="text for the Last synchronized line")
    p = argparse.ArgumentParser(description="Change rows of WORLD_ORDER.md", allow_abbrev=False)
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("add", parents=[common], allow_abbrev=False, help="add a row")
    s.add_argument("--story", required=True)
    s.add_argument("--unit", required=True, help="Full Story, Ch. N, Bk. N Ch. M or TBD")
    s.add_argument("--position", type=int, default=None)
    s.add_argument("--shift", action="store_true", help="move rows at the position and later down by one")
    s.add_argument("--status", choices=STATUSES, default="Not Started")
    s.add_argument("--date", default="—", help="in-world date")
    s.add_argument("--notes", default="")
    s = sub.add_parser("status", parents=[common], allow_abbrev=False, help="set a row's status")
    s.add_argument("--story", required=True)
    s.add_argument("--unit", default=None)
    s.add_argument("--to", required=True, choices=STATUSES)
    s = sub.add_parser("move", parents=[common], allow_abbrev=False, help="give a row a new position")
    s.add_argument("--story", required=True)
    s.add_argument("--unit", default=None)
    s.add_argument("--to", required=True, type=int)
    s.add_argument("--shift", action="store_true", help="move rows at the position and later down by one")
    s = sub.add_parser("chapter", parents=[common], allow_abbrev=False, help="record an analyzed chapter")
    s.add_argument("--story", required=True)
    s.add_argument("--chapter", required=True, type=int)
    s.add_argument("--book", type=int, default=None, help="the book number, for a Book Series")
    sub.add_parser("renumber", parents=[common], allow_abbrev=False, help="renumber positions 1, 2, 3…")
    a = p.parse_args()

    world = a.world.strip().rstrip("/\\")
    if not Path(world).is_dir() and Path("worlds", world).is_dir():
        world = f"worlds/{world}"
    order_file = Path(world, "WORLD_ORDER.md")
    story = strip_wikilink(getattr(a, "story", "") or "").strip()
    if story.startswith("stories/"):
        story = story[len("stories/"):]
    today = datetime.date.today().isoformat()
    complete = None
    try:
        if not order_file.is_file():
            raise ValueError(f"no WORLD_ORDER.md at {order_file.as_posix()}; "
                             "the world-archivist's Initialize creates it")
        table = Table(read_exact(order_file))
        if a.command == "add":
            if a.position is not None and a.position < 1:
                raise ValueError("--position must be 1 or more")
            row, note = table.add(story, a.unit, a.position, a.shift, a.status, a.date, a.notes)
            summary = f"added {describe(row)}" + (f" ({note})" if note else "")
            reason = f"[[{story}]] {a.unit} added at position {row['pos']}"
        elif a.command == "status":
            row = table.one(story, a.unit)
            before = row["status"]
            table.set(row, status=a.to)
            summary = f"[[{story}]] {row['unit']}: {before} → {a.to}"
            reason = f"[[{story}]] {row['unit']} {a.to}"
        elif a.command == "move":
            if a.to < 1:
                raise ValueError("--to must be 1 or more")
            row = table.one(story, a.unit)
            before = row["pos"]
            note = table.place(row, a.to, a.shift)
            summary = f"[[{story}]] {row['unit']}: position {before} → {a.to}" + (f" ({note})" if note else "")
            reason = f"[[{story}]] {row['unit']} moved to position {a.to}"
        elif a.command == "chapter":
            if a.chapter < 1:
                raise ValueError("--chapter must be 1 or more")
            concept = Path("stories", story, "CONCEPT.md")
            if not concept.is_file():
                raise ValueError(f"no CONCEPT.md at {concept.as_posix()}")
            outline = Path("stories", story, "OUTLINE.md")
            m = re.search(r"\*\*Total chapters:\*\*\s*(\d+)", read_exact(outline)) if outline.is_file() else None
            summary, complete = chapter(table, story, a.chapter, a.book, _field(read_exact(concept), "Format"),
                                        int(m.group(1)) if m else None)
            reason = f"after [[{story}]] Chapter {a.chapter} analyzed" + (" (story complete)" if complete else "")
        else:
            table.renumber()
            moved = [r for r in table.rows if r["line"] is None]
            summary = f"renumbered {len(moved)} row(s)" if moved else "positions were already 1, 2, 3…"
            reason = "positions renumbered"
        text = table.render(today, a.reason or reason)
    except ValueError as e:
        print("Nothing was changed:", file=sys.stderr)
        print(f"  - {e}", file=sys.stderr)
        return 1

    print(("Dry run — would change " if a.dry_run else "Changed ") + f"{order_file.as_posix()}: {summary}")
    print(f"  Last synchronized: {today} — {a.reason or reason}")
    if a.command == "chapter":
        print("Story complete: " + {True: "yes", False: "no", None: "not judged (Book Series)"}[complete])
    if not a.dry_run:
        order_file.write_bytes(text.encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
