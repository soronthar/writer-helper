"""Layout v1 validation and consistency checks (docs/LAYOUT_V1.md). Imported by wr_doctor and
tools/check_layout_v1.py.

check(root) -> (errors, warnings), both lists of strings. Read-only.

Errors are structural violations. Warnings are legacy quirks, gaps and inconsistencies between files,
each saying what to run to fix it. The cross-file checks cover what the skills actually depend on:

  - a world without SUMMARY.md (skills then read every entity file) or with one that no longer matches the
    entity files (by name, not just by count)
  - a world without WORLD_ORDER.md, a story missing from it, a row naming a story that does not exist,
    a completed row with no snapshot
  - promoted chapters with no Timeline entry (the story-analyzer did not run for them)
"""

import re
from pathlib import Path

ENTITY_DIRS = ("characters", "factions", "mythology", "points_of_interest")
STATUSES = {"Concept", "In Development", "Active", "Complete", "Archived"}
# SUMMARY.md section heading -> entity directory
SUMMARY_SECTIONS = {
    "## Characters": "characters",
    "## Factions": "factions",
    "## Locations": "points_of_interest",
    "## Active Mythology": "mythology",
}
FIX_SUMMARY = "run the world-archivist skill (Regenerate SUMMARY.md) or the writing-assistant skill"
FIX_ORDER = "run the world-archivist skill (Manage story order)"
FIX_CONSOLIDATE = "run the world-archivist skill (Consolidate)"


def _norm(name):
    """Compare names the way a reader does: case-insensitively, underscores as spaces."""
    return re.sub(r"\s+", " ", name.replace("_", " ")).strip().lower()


def _summary_names(text):
    """{entity dir: [names]} from the '| [[Name]] |' rows of each SUMMARY.md section."""
    out, current = {}, None
    for line in text.splitlines():
        if line.startswith("## "):
            current = next((d for h, d in SUMMARY_SECTIONS.items() if line.startswith(h)), None)
        elif current:
            m = re.match(r"\|\s*\[\[([^\]|]+)", line)
            if m:
                out.setdefault(current, []).append(m.group(1))
    return out


def _order_rows(text):
    """[(position, story, unit, status)] from the WORLD_ORDER.md Story Order table."""
    rows = []
    for line in text.splitlines():
        m = re.match(r"\|\s*(\d+)\s*\|\s*\[\[([^\]]+)\]\]\s*\|([^|]*)\|([^|]*)\|([^|]*)\|", line)
        if m:
            rows.append((int(m.group(1)), m.group(2).strip(), m.group(3).strip(), m.group(5).strip()))
    return rows


def _story_world(concept_text):
    m = re.search(r"\*\*World:\*\*\s*(.+)", concept_text)
    return m.group(1).strip().strip("`") if m else None


def _frontmatter(text):
    """The simple `key: value` lines of a leading --- block, or {}."""
    m = re.match(r"---\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", text, re.S)
    out = {}
    for line in (m.group(1).splitlines() if m else []):
        k, sep, v = line.partition(":")
        if sep:
            out[k.strip()] = v.strip().strip("\"'")
    return out


def check(root, coverage=False):
    """Validate a project. With coverage=True also report which fixture-style cases the project lacks
    (an in-flight chapter, a Book Series); that is for the repository's own fixtures, not for users."""
    root = Path(root)
    errors, warnings = [], []
    err, warn = errors.append, warnings.append

    worlds, stories = root / "worlds", root / "stories"
    for d in (worlds, stories):
        if not d.is_dir():
            err(f"missing {d.name}/")
    if errors:
        return errors, warnings

    story_dirs = sorted(p for p in stories.iterdir() if p.is_dir())
    story_world = {}
    for s in story_dirs:
        c = s / "CONCEPT.md"
        if c.is_file():
            story_world[s.name] = _story_world(c.read_text(encoding="utf-8"))

    for w in sorted(p for p in worlds.iterdir() if p.is_dir()):
        for req in ("DESCRIPTION.md", "HOOKS.md"):
            if not (w / req).is_file():
                err(f"world '{w.name}': missing {req}")
        snaps = w / "snapshots"
        if snaps.is_dir():
            for s in sorted(p for p in snaps.iterdir() if p.is_dir()):
                if not s.name.isdigit() or int(s.name) < 1:
                    err(f"world '{w.name}': snapshot dir '{s.name}' is not a positive integer")
                elif not (s / "manifest.md").is_file():
                    err(f"world '{w.name}': snapshot {s.name} missing manifest.md")
                if (s / "HOOKS.md").exists():
                    err(f"world '{w.name}': snapshot {s.name} must not contain HOOKS.md")
            if not (snaps / "manifest.md").is_file():
                err(f"world '{w.name}': snapshots/ missing manifest.md")

        files = {d: sorted(p.stem for p in (w / d).glob("*.md")) if (w / d).is_dir() else [] for d in ENTITY_DIRS}
        n_entities = sum(len(v) for v in files.values())

        # --- SUMMARY.md: present, and matching the entity files by name
        summary = w / "SUMMARY.md"
        if not summary.is_file():
            if n_entities:
                warn(f"world '{w.name}': no SUMMARY.md, so skills read every entity file ({n_entities}) instead of "
                     f"a one-page index; {FIX_SUMMARY}")
        else:
            listed = _summary_names(summary.read_text(encoding="utf-8"))
            for d in ENTITY_DIRS:
                have = {_norm(n): n for n in files[d]}
                said = {_norm(n): n for n in listed.get(d, [])}
                missing = sorted(have[k] for k in have.keys() - said.keys())
                extra = sorted(said[k] for k in said.keys() - have.keys())
                if missing or extra:
                    parts = []
                    if missing:
                        parts.append("not listed: " + ", ".join(missing))
                    if extra:
                        parts.append("listed but no file: " + ", ".join(extra))
                    warn(f"world '{w.name}': SUMMARY.md may be stale — {d}/ {'; '.join(parts)} ({FIX_SUMMARY})")

        # --- WORLD_ORDER.md: present, and consistent with the stories
        using = sorted(s for s, world in story_world.items() if world == w.name)
        wo = w / "WORLD_ORDER.md"
        if not wo.is_file():
            if using:
                warn(f"world '{w.name}': no WORLD_ORDER.md although {len(using)} story(ies) use it "
                     f"({', '.join(using)}); position lookups find nothing and no world baseline is used; {FIX_ORDER}")
            elif n_entities:
                warn(f"world '{w.name}': no WORLD_ORDER.md; {FIX_ORDER} to initialize it before the first story")
        else:
            text = wo.read_text(encoding="utf-8")
            if "| Position |" not in text:
                err(f"world '{w.name}': WORLD_ORDER.md has no '| Position |' table header")
            else:
                rows = _order_rows(text)
                listed_stories = {name for _, name, _, _ in rows}
                for s in using:
                    if s not in listed_stories:
                        warn(f"world '{w.name}': story '{s}' is not in WORLD_ORDER.md; {FIX_ORDER} (Add Entry)")
                for _, name, _, _ in rows:
                    if name not in story_world and not (stories / name).is_dir():
                        warn(f"world '{w.name}': WORLD_ORDER.md lists '{name}', which is not in stories/")
                made = {int(s.name) for s in snaps.iterdir() if s.is_dir() and s.name.isdigit()} if snaps.is_dir() else set()
                for pos, name, _, status in rows:
                    if status == "Complete" and pos not in made and (stories / name).is_dir():
                        warn(f"world '{w.name}': '{name}' is Complete at position {pos} but there is no snapshot "
                             f"{pos}; consolidate it ({FIX_CONSOLIDATE})")

    def check_unit(d, label):
        chapters = []
        if (d / "chapters").is_dir():
            for f in (d / "chapters").iterdir():
                if f.is_file() and f.suffix == ".md":
                    m = re.fullmatch(r"Chapter_(\d{2,})\.md", f.name)
                    if m:
                        chapters.append(int(m.group(1)))
                    else:
                        warn(f"{label}: chapters/{f.name} is not Chapter_NN.md (ignored by tools)")
        timeline = d / "state" / "Timeline.md"
        if not timeline.is_file():
            warn(f"{label}: no state/Timeline.md")
        elif chapters:
            recorded = {int(n) for n in re.findall(r"\[(?:Book \d+\W+)?Chapter (\d+)\b", timeline.read_text(encoding="utf-8"))}
            missing = sorted(set(chapters) - recorded)
            if missing:
                warn(f"{label}: chapter(s) {', '.join(map(str, missing))} are promoted but have no Timeline entry "
                     "(the story-analyzer skill may not have run for them)")
        bible = d / "state" / "bible"
        if bible.is_dir():
            for sub in bible.iterdir():
                if sub.is_dir() and sub.name not in ENTITY_DIRS:
                    err(f"{label}: state/bible/{sub.name}/ is not a known entity folder")

    for s in story_dirs:
        concept = s / "CONCEPT.md"
        if not concept.is_file():
            err(f"story '{s.name}': missing CONCEPT.md")
            continue
        text = concept.read_text(encoding="utf-8")
        world = _story_world(text)
        if not world:
            err(f"story '{s.name}': CONCEPT.md has no **World:** field")
        elif not (worlds / world).is_dir():
            warn(f"story '{s.name}': world '{world}' not present in worlds/")
        m = re.search(r"\*\*Status:\*\*\s*`?([A-Za-z ]+?)`?\s*(?:$|\n|\*)", text)
        if not m:
            warn(f"story '{s.name}': CONCEPT.md has no Status field (legacy concepts may lack it)")
        elif m.group(1).strip() not in STATUSES:
            err(f"story '{s.name}': CONCEPT.md Status '{m.group(1).strip()}' is not one of {sorted(STATUSES)}")
        fm = _frontmatter(text)
        body_status = m.group(1).strip() if m else None
        for key, body in (("world", world), ("status", body_status)):
            if key in fm and body and fm[key] != body:
                warn(f"story '{s.name}': CONCEPT.md frontmatter {key} '{fm[key]}' differs from the body '{body}'; "
                     f"set the frontmatter to match (the body is the truth)")
        books = sorted(s.glob("Book *"))
        if books:
            if not (s / "SERIES_OUTLINE.md").is_file():
                err(f"series '{s.name}': missing SERIES_OUTLINE.md")
            for b in books:
                check_unit(b, f"{s.name}/{b.name}")
        else:
            check_unit(s, s.name)

    styles = root / "writing_concepts" / "styles"
    if not (styles.is_dir() and any(styles.glob("*.md"))):
        warn("no writing style in writing_concepts/styles/ (the draft-writer will use its own judgment)")
    if coverage:
        if not list(stories.glob("*/current_chapter")) and not list(stories.glob("*/Book */current_chapter")):
            warn("no story has a current_chapter/ (in-flight case not covered)")
        if not any(stories.glob("*/Book *")):
            warn("no Book Series present (series case not covered)")
    return errors, warnings
