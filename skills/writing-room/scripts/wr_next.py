#!/usr/bin/env python3
"""wr_next.py — Work out where each story is and which skill to run next

Usage:
  python "<WR>/scripts/wr_next.py" [--root DIR] [--story "stories/<Story>"] [--json]

Read-only. Looks at the project's files and reports, for every story (or every book of
a Book Series), its state and the next skill in the pipeline:

  no world                      -> create-world
  world, no story               -> story-ideator
  concept, no outline           -> outliner
  next chapter not planned      -> planner
  planned, not drafted          -> draft-writer
  drafted, no reviews           -> reviewer
  reviewed, no fix log          -> draft-fixer
  fixed, no Timeline entry      -> story-analyzer
  analyzed                      -> promote-chapter
  all chapters promoted         -> world-archivist (consolidate); the story's Status is
                                   then set to Complete (see the writing-room skill)

With --json the output is machine-readable. "recommended" names the single unit to work
on when exactly one is in progress, otherwise it is null and the user should choose.
Paths are relative to the project root (found via --root, WRITING_ROOM_ROOT, a
writing-room.toml marker, or the legacy worlds/ + stories/ layout).
"""

import json
import re
import sys
from pathlib import Path

from common import make_parser, setup

CHAPTER_FILE = re.compile(r"Chapter_(\d{2,})\.md")
FINISHED = {"Complete", "Archived"}


def read(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        return ""


def field(text, name):
    m = re.search(rf"\*\*{name}:\*\*\s*`?([^`\n]+?)`?\s*(?:\n|$)", text)
    return m.group(1).strip() if m else None


def unit_state(path, concept_text, series=None):
    """Describe one story or book folder and decide its next skill."""
    path = Path(path)
    name = path.name if series is None else f"{series.name} / {path.name}"
    status = field(concept_text, "Status") or "Unknown"
    world = field(concept_text, "World")
    st = {"name": name, "path": path.as_posix(), "kind": "book" if series else "story",
          "world": world, "status": status}

    outline = read(path / "OUTLINE.md")
    st["has_outline"] = bool(outline)
    st["consolidated"] = bool(world) and f"[[{path.name if series is None else series.name}]]" in read(Path("worlds") / world / "TIMELINE.md")
    total = re.search(r"\*\*Total chapters:\*\*\s*(\d+)", outline)
    st["total_chapters"] = int(total.group(1)) if total else None

    chapters = sorted(f.name for f in (path / "chapters").glob("*.md") if CHAPTER_FILE.fullmatch(f.name)) \
        if (path / "chapters").is_dir() else []
    st["chapters_done"] = len(chapters)

    cur = path / "current_chapter"
    plan, content = read(cur / "CHAPTER_PLAN.md"), (cur / "CONTENT.md").is_file()
    reviews = sorted(f.name for f in (cur / "current_reviews").glob("Reviewer-*.md")) \
        if (cur / "current_reviews").is_dir() else []
    fixed = (cur / "current_reviews" / "Draft-Fixer-Log.md").is_file()
    m = re.search(r"\*\*Chapter:\*\*\s*(\d+)", plan)
    number = int(m.group(1)) if m else len(chapters) + 1
    timeline = read(path / "state" / "Timeline.md")
    analyzed = bool(re.search(rf"\[(?:Book \d+\W+)?Chapter {number}\b", timeline))
    st["current"] = {"chapter": number, "planned": bool(plan), "drafted": content,
                     "reviews": reviews, "fixed": fixed, "analyzed": analyzed}

    skill, reason = decide(st, plan, content, reviews, fixed, analyzed, number, series)
    st["next_skill"], st["reason"] = skill, reason
    return st


def decide(st, plan, content, reviews, fixed, analyzed, number, series):
    if st["status"] == "Archived":
        return None, "Story is archived."
    if not st["has_outline"]:
        what = "Book 01 of the series" if series is None and (Path(st["path"]) / "SERIES_OUTLINE.md").exists() else "the story"
        return "outliner", f"No OUTLINE.md yet for {what}."
    if content and not plan:
        return "story-status", "A draft exists without CHAPTER_PLAN.md; inspect it before continuing."
    if plan and not content:
        return "draft-writer", f"Chapter {number} is planned but not drafted."
    if content:
        if not reviews:
            return "reviewer", f"Chapter {number} is drafted and has no review reports."
        if not fixed:
            return "draft-fixer", f"Chapter {number} has review reports but no Draft-Fixer-Log.md."
        if not analyzed:
            return "story-analyzer", f"Chapter {number} is fixed but the Timeline has no entry for it."
        return "promote-chapter", f"Chapter {number} is analyzed and ready to promote."
    total = st["total_chapters"]
    if total is not None and st["chapters_done"] >= total:
        if st["consolidated"]:
            if st["status"] in FINISHED:
                return None, "All chapters are promoted, the story is complete and already consolidated."
            return "writing-room", ("All chapters are promoted and the story is consolidated, but its Status is not "
                                    "Complete: set Status to Complete in CONCEPT.md (confirm with the user).")
        if st["status"] in FINISHED:
            return "world-archivist", "All chapters are promoted and the story is marked complete: consolidate it."
        return "world-archivist", ("All chapters are promoted: set Status to Complete in CONCEPT.md (confirm with the "
                                   "user), then consolidate the story.")
    return "planner", f"Chapter {st['chapters_done'] + 1} is next and not yet planned."


def project_state():
    """Scan the project; the working directory is the project root, so paths stay root-relative."""
    base = Path(".")
    worlds = sorted(p.name for p in (base / "worlds").iterdir() if p.is_dir()) if (base / "worlds").is_dir() else []
    units = []
    stories = base / "stories"
    for s in sorted(p for p in stories.iterdir() if p.is_dir()) if stories.is_dir() else []:
        concept = read(s / "CONCEPT.md")
        books = sorted(s.glob("Book *"))
        if books:
            series_unit = {"series": s.name, "path": s.as_posix(), "world": field(concept, "World"),
                           "status": field(concept, "Status") or "Unknown", "books": []}
            for b in books:
                units.append(unit_state(b, concept, series=s))
            if not (s / "SERIES_OUTLINE.md").exists():
                units.append({"name": s.name, "path": s.as_posix(), "kind": "series", "world": series_unit["world"],
                              "status": series_unit["status"], "has_outline": False,
                              "next_skill": "outliner", "reason": "Series has no SERIES_OUTLINE.md."})
        elif concept:
            units.append(unit_state(s, concept))
        else:
            units.append({"name": s.name, "path": s.as_posix(), "kind": "story", "world": None, "status": "Unknown",
                          "has_outline": False, "next_skill": "story-status",
                          "reason": "Folder has no CONCEPT.md."})
    return worlds, units


def main():
    root = setup()
    p = make_parser("Work out the next skill for each story")
    p.add_argument("--story", help="limit to one story or book folder, relative to the project root")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()

    worlds, units = project_state()
    if a.story:
        want = Path(a.story).as_posix().rstrip("/")
        units = [u for u in units if u["path"] == want]
        if not units:
            print(f"Error: no story or book at {a.story}.", file=sys.stderr)
            return 1

    if not worlds:
        project = {"next_skill": "create-world", "reason": "The project has no world yet."}
    elif not units:
        project = {"next_skill": "story-ideator", "reason": "There is a world but no story yet."}
    else:
        project = None

    active = [u for u in units if u.get("next_skill") and u["status"] not in FINISHED]
    recommended = active[0]["path"] if len(active) == 1 else None
    if project is None and not active:
        project = {"next_skill": "story-ideator",
                   "reason": "Every story is finished or archived; start a new one."}

    result = {"root": str(root), "worlds": worlds, "project": project, "units": units, "recommended": recommended}
    if a.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    print(f"Project: {root}")
    print(f"Worlds:  {', '.join(worlds) if worlds else '(none)'}")
    if project:
        print(f"\nNext skill: {project['next_skill']} — {project['reason']}")
    for u in units:
        print(f"\n{u['name']}  [{u['status']}]")
        if u.get("kind") != "series" and "chapters_done" in u:
            total = u["total_chapters"] if u["total_chapters"] is not None else "?"
            print(f"  chapters promoted: {u['chapters_done']} of {total}")
        print(f"  next skill: {u['next_skill'] or '—'} — {u['reason']}")
    if recommended:
        print(f"\nRecommended: {recommended}")
    elif len(active) > 1:
        print("\nSeveral stories are in progress; ask the user which to work on.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
