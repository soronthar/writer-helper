#!/usr/bin/env python3
"""new_story.py — Create a new story from an approved concept

Usage:
  python "<WR>/scripts/new_story.py" --world "<World>" --story "<Story Name>" \\
    [--hook "<Hook Title>"]... [--position N] [--concept <file>] [--dry-run]

Does the story-ideator's bookkeeping in one step, so no table is edited by hand:
  1. Copies the approved concept to stories/<Story>/CONCEPT.md, with its title line
     set to the story name. The concept is read from --concept, by default
     .writing-room-work/worlds/<World>/CONCEPT.md (where the ideator saves it on
     approval). The draft is deleted once it has been copied.
  2. Creates chapters/, current_chapter/ and state/, and writes state/Timeline.md,
     ACTIVE_SCHEMES.md and STORY_FACTS.md from the story templates.
  3. Adds the story's row to worlds/<World>/WORLD_ORDER.md through world_order.py
     (replacing the `—` placeholder row, kept in position order) and updates its Last synchronized
     line. The Unit comes from the concept's **Format:** line: Full Story for a
     Short Story or Novelette, TBD for a Book or Book Series. Without --position,
     the story goes after the last entry.
  4. Sets the Status of each --hook in worlds/<World>/HOOKS.md to `In Use (<Story>)`.

Everything is checked before anything is written. It refuses, and changes
nothing, when the story folder already exists, the concept is missing, still
marked as an unapproved draft or still has <placeholder> text, its Format is not one of the four, a hook is not in
HOOKS.md, or the story is already in WORLD_ORDER.md. Fix what it names and run
it again. --dry-run prints what it would do.

Paths are relative to the project root (found via --root, WRITING_ROOM_ROOT,
a writing-room.toml marker, or the legacy worlds/ + stories/ layout).
"""

import datetime
import re
import sys
from pathlib import Path

from common import WORK_DIR, lookup, make_parser, read_exact, setup
from world_order import Table

FORMATS = {"short story": "Full Story", "novelette": "Full Story", "book": "TBD", "book series": "TBD"}
STATE_FILES = (("timeline.md", "Timeline.md"), ("active_schemes.md", "ACTIVE_SCHEMES.md"),
               ("story_facts.md", "STORY_FACTS.md"))
PLACEHOLDER = re.compile(r"<[A-Z][^<>\n]*>")
DRAFT = "<!-- draft: not yet approved -->"


def _newline(text):
    return "\r\n" if "\r\n" in text else "\n"


def _field(text, name):
    m = re.search(rf"\*\*{name}:\*\*\s*`?([^`\n]+?)`?\s*$", text, flags=re.M)
    return m.group(1).strip() if m else ""


def prepare_concept(text, story):
    """Return (concept text with the story's title, unit, errors)."""
    errors = []
    if DRAFT in text:
        errors.append(f"the concept is still marked as a draft ({DRAFT}); delete that line once the user approves it")
    lines = text.splitlines(keepends=True)
    title = next((n for n, line in enumerate(lines) if line.startswith("# ")), None)
    if title is None:
        errors.append("the concept has no '# ' title line")
    else:
        lines[title] = f"# {story}{_newline(text)}"
    text = "".join(lines)
    left = sorted({m if len(m) <= 40 else m[:37] + "…>" for m in PLACEHOLDER.findall(text)})
    if left:
        errors.append("the concept still has placeholder text: " + ", ".join(left[:8])
                      + (" …" if len(left) > 8 else ""))
    fmt = _field(text, "Format")
    unit = FORMATS.get(fmt.lower())
    if not unit:
        errors.append(f"the concept's **Format:** is {fmt!r}; use Short Story, Novelette, Book or Book Series")
    return text, unit, errors


def add_order_row(text, story, unit, position, today):
    """Return (new WORLD_ORDER.md text, position used, note) or raise ValueError."""
    table = Table(text)
    if table.find(story):
        raise ValueError(f"[[{story}]] is already in WORLD_ORDER.md")
    notes = "" if unit == "Full Story" else "Placeholder — expand after Outliner"
    row, note = table.add(story, unit, position, notes=notes)
    return table.render(today, f"[[{story}]] added at position {row['pos']}"), row["pos"], note


def mark_hooks(text, titles, story):
    """Return (new HOOKS.md text, [(title, previous status)]) or raise ValueError naming missing hooks."""
    nl = _newline(text)
    lines = text.split(nl)
    done, missing = [], []
    for title in titles:
        want = title.strip().lower()
        start = next((n for n, line in enumerate(lines)
                      if line.startswith("### ") and line[4:].strip().lower() == want), None)
        if start is None:
            missing.append(title)
            continue
        n = start + 1
        while n < len(lines) and not lines[n].startswith("#"):
            if lines[n].lstrip().startswith("- **Status:**"):
                done.append((lines[start][4:].strip(), lines[n].split("**Status:**", 1)[1].strip()))
                lines[n] = f"- **Status:** `In Use ({story})`"
                break
            n += 1
        else:
            missing.append(f"{title} (no Status line)")
    if missing:
        raise ValueError("not found in HOOKS.md: " + "; ".join(missing))
    return nl.join(lines), done


def main():
    setup()
    p = make_parser("Create a new story from an approved concept")
    p.add_argument("--world", required=True, help='the world, e.g. "worlds/<World>" or just "<World>"')
    p.add_argument("--story", required=True, help="the story name (the folder created under stories/)")
    p.add_argument("--concept", default="", help=f"the approved concept (default: {WORK_DIR}/worlds/<World>/CONCEPT.md)")
    p.add_argument("--position", type=int, default=None, help="WORLD_ORDER.md position (default: after the last)")
    p.add_argument("--hook", action="append", default=[], help="a HOOKS.md hook title to mark In Use (repeatable)")
    p.add_argument("--dry-run", action="store_true", help="print the plan and change nothing")
    a = p.parse_args()

    world = a.world.strip().rstrip("/\\")
    if not Path(world).is_dir() and Path("worlds", world).is_dir():
        world = f"worlds/{world}"
    if not Path(world).is_dir():
        sys.exit(f'Error: no world folder at "{world}". Pass --world "worlds/<World>".')
    story = a.story.strip()
    if story.startswith("stories/"):
        story = story[len("stories/"):]
    story_dir = Path("stories", story)
    concept_path = Path(a.concept) if a.concept else Path(WORK_DIR, world, "CONCEPT.md")

    errors = []
    if story_dir.exists():
        errors.append(f"{story_dir.as_posix()} already exists; pick another name or remove it first")
    if a.position is not None and a.position < 1:
        errors.append("--position must be 1 or more")
    concept, unit = "", None
    if concept_path.is_file():
        concept, unit, found = prepare_concept(read_exact(concept_path), story)
        errors += found
        named = _field(concept, "World")
        if named and named != Path(world).name:
            errors.append(f"the concept's **World:** is {named!r}, not {Path(world).name!r}")
    else:
        errors.append(f"no concept at {concept_path.as_posix()}; save the approved concept there first (or pass --concept)")
    today = datetime.date.today().isoformat()
    order_file, order, order_note = Path(world, "WORLD_ORDER.md"), None, ""
    position = a.position
    if order_file.is_file() and unit:
        try:
            order, position, order_note = add_order_row(read_exact(order_file), story, unit, a.position, today)
        except ValueError as e:
            errors.append(str(e))
    hooks_file, hooks, marked = Path(world, "HOOKS.md"), None, []
    if a.hook:
        if not hooks_file.is_file():
            errors.append(f"--hook given but {hooks_file.as_posix()} does not exist")
        else:
            try:
                hooks, marked = mark_hooks(read_exact(hooks_file), a.hook, story)
            except ValueError as e:
                errors.append(str(e))
    templates = {}
    for src, dest in STATE_FILES:
        path = Path(lookup(f"templates/story/{src}"))
        if path.is_file():
            templates[dest] = read_exact(path).replace("<Story Name>", story)
        else:
            errors.append(f"template templates/story/{src} not found")
    if errors:
        print("Nothing was changed:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    plan = [f"stories/{story}/CONCEPT.md  (from {concept_path.as_posix()})",
            f"stories/{story}/chapters/, current_chapter/  (empty)"]
    plan += [f"stories/{story}/state/{dest}  (skeleton)" for dest in templates]
    if order is not None:
        plan.append(f"{order_file.as_posix()}: row at position {position} — [[{story}]] | {unit} | Not Started"
                    + (f" ({order_note})" if order_note else ""))
    else:
        plan.append(f"{order_file.as_posix()} not found — run the world-archivist skill to initialize it")
    plan += [f"{hooks_file.as_posix()}: {title} → `In Use ({story})` (was {before})" for title, before in marked]
    if a.dry_run:
        print("Dry run — would write:")
        print("\n".join(f"  {line}" for line in plan))
        return 0

    for sub in ("chapters", "current_chapter", "state"):
        (story_dir / sub).mkdir(parents=True, exist_ok=True)
    for dest, text in templates.items():
        (story_dir / "state" / dest).write_bytes(text.encode("utf-8"))
    (story_dir / "CONCEPT.md").write_bytes(concept.encode("utf-8"))
    if order is not None:
        order_file.write_bytes(order.encode("utf-8"))
    if hooks is not None:
        hooks_file.write_bytes(hooks.encode("utf-8"))
    if not a.concept:
        concept_path.unlink()
    print(f"Created [[{story}]] in {world}:")
    print("\n".join(f"  {line}" for line in plan))
    return 0


if __name__ == "__main__":
    sys.exit(main())
