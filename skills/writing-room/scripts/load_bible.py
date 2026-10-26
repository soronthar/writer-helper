#!/usr/bin/env python3
"""load_bible.py — Story context loader

Used by the Draft Writer, Planner, Reviewer, Draft Fixer and Story Analyzer to
load story-level reference files in a single call.

Core flags (always available)
  --story <path>   Story root relative to the project root.
                   Book series: "stories/<Series>/Book 01 - <Title>"
  --world <path>   World bible root, e.g. "worlds/Harrowmere"

Output control flags (suppress sections the agent doesn't need)
  --no-style         Skip the style file (Reviewer passes).
  --no-last-chapter  Skip the most recent completed chapter.
  --no-timeline      Skip state/Timeline.md.
  --no-schemes       Skip state/ACTIVE_SCHEMES.md (loaded by default).
  --no-facts         Skip state/STORY_FACTS.md (loaded by default).

Optional content flags
  --structure <Name>    Add GUIDE.md, Format Reference.md and the named
                        structure file (filename stem, no .md). For Planner.
  --description         Add DESCRIPTION.md (state/bible/ -> worlds/<World>/).
  --reviews-dir <path>  Add all Reviewer-*.md files from a directory (relative
                        to the project root). For Draft Fixer.
  --hooks               Add worlds/<World>/HOOKS.md. For Story Analyzer.

Entity flags (priority: state/bible/ -> snapshot (if --position) -> worlds/)
  --char "Name"  --loc "Name"  --faction "Name"  --myth "Name"
  Repeatable. Use the exact filename stem (no .md extension).

Style hint
  --style "Name"  Partial name matched against style filenames; used when
                  multiple style files exist, ignored when only one is present.

Position-aware loading
  --position <N>  Entity reads gain a snapshot tier:
                    1. <story>/state/bible/<type>/<Name>.md
                    2. <world>/snapshots/<N>/<type>/<Name>.md
                    3. <world>/<type>/<Name>.md
                  Pass the PREVIOUS story's position as N. If no snapshot
                  exists, a warning is printed and tier 2 is skipped.

Output order
  0. Review reports  1. Structure files  2. DESCRIPTION.md  3. Style file
  4. Most recent chapter  5. Timeline  5a. ACTIVE_SCHEMES  5b. STORY_FACTS
  5c. HOOKS  6. Entity files

Examples
  python "scripts/load_bible.py" \\
    --story "stories/The Tallow Ledger" --world "worlds/Harrowmere" \\
    --char "Mara Quill" --loc "The Ashwood"

  python "scripts/load_bible.py" \\
    --story "stories/The Tallow Ledger" --world "worlds/Harrowmere" \\
    --no-style --no-last-chapter --hooks --char "Mara Quill"

Library use
  collect(story, world, ..., root=<project root>) returns the same items as a list of
  Piece (label, body, path, source, found, ...); render(pieces) gives the text this
  command prints. The Writing Room harness builds its context from collect().

Notes
  - Run from anywhere; paths are relative to the project root
    (auto-discovered; override with --root).
  - Missing files emit a ⚠ warning line rather than crashing.
"""

import contextlib
import sys
from dataclasses import dataclass
from pathlib import Path

from common import (DIV, in_project, is_file, lookup, make_parser, md_files, read_exact,
                    setup, snapshot_lookup)


@dataclass
class Piece:
    """One loaded item: the file content plus where it came from.

    text is exactly what the command line prints for this item (header + content);
    body is the file content alone. Library callers (the harness) use body and the
    metadata; the CLI prints text.
    """
    kind: str            # review | structure | description | style | chapter | timeline | schemes | facts | hooks | entity | notice
    label: str
    text: str
    body: str = ""
    path: str = ""       # the file actually read ('' when nothing was found)
    source: str = ""     # story-local | snapshot | world bible ('' when not applicable)
    found: bool = True


def _block(*lines):
    """A ═-delimited block of lines, preceded by a blank line (the CLI's header shape)."""
    return "\n" + DIV + "\n" + "".join(line + "\n" for line in lines) + DIV + "\n"


def _notice(*lines):
    return Piece("notice", lines[0], _block(*lines), found=False)


def _file(kind, label, path, source=""):
    """Load a file under a labelled header; a NOT FOUND notice if missing."""
    if is_file(path):
        body = read_exact(path)
        return Piece(kind, label, _block(f"FILE: {label}") + body, body, lookup(path), source)
    return Piece(kind, label, _block(f"FILE: {label}  ⚠ NOT FOUND — {path}"), found=False)


def _entity(story, world, snapshot_dir, position, type_, name):
    """Load one entity with priority: story-local -> snapshot -> world bible."""
    primary = f"{story}/state/bible/{type_}/{name}.md"
    snapshot_file = f"{snapshot_dir}/{type_}/{name}.md" if snapshot_dir else ""
    fallback = f"{world}/{type_}/{name}.md"
    label = f"{type_}/{name}"

    if Path(primary).is_file():
        path, source, tag = primary, "story-local", "story-local"
    elif snapshot_file and Path(snapshot_file).is_file():
        path, source, tag = snapshot_file, "snapshot", f"snapshot pos {position}"
    elif Path(fallback).is_file():
        path, source, tag = fallback, "world bible", "world bible"
    else:
        return Piece("entity", label,
                     _block(f"FILE: {label}  ⚠ NOT FOUND in state/bible/, snapshot, or world bible"),
                     found=False)
    body = read_exact(path)
    return Piece("entity", label, _block(f"FILE: {label}  [{tag}]") + body, body, lookup(path), source)


def _description(story, world):
    primary = f"{story}/state/bible/DESCRIPTION.md"
    fallback = f"{world}/DESCRIPTION.md"
    if Path(primary).is_file():
        path, source = primary, "story-local"
    elif Path(fallback).is_file():
        path, source = fallback, "world bible"
    else:
        return Piece("description", "DESCRIPTION.md",
                     _block("FILE: DESCRIPTION.md  ⚠ NOT FOUND in state/bible/ or world bible"),
                     found=False)
    body = read_exact(path)
    return Piece("description", "DESCRIPTION.md",
                 _block(f"FILE: DESCRIPTION.md  [{source}]") + body, body, lookup(path), source)


def _style(style_hint):
    style_files = md_files("writing_concepts/styles")
    listing = [f"  writing_concepts/styles/{Path(f).name}" for f in style_files]

    if not style_files:
        return [_notice("STYLE FILE: ⚠ None found in writing_concepts/styles/ — agent uses own judgment")]
    if len(style_files) == 1:
        return [_file("style", f"Style: {style_files[0]}", style_files[0])]
    if style_hint:
        matched = next((f for f in style_files if style_hint in f), "")
        if matched:
            return [_file("style", f'Style: {matched}  [matched hint: "{style_hint}"]', matched)]
        return [_notice(f'STYLE FILE: ⚠ Multiple files found; hint "{style_hint}" matched nothing.',
                        "Agent must select one and read it separately. Available files:", *listing)]
    return [_notice("STYLE FILE: ⚠ Multiple files found — agent must select (check CONCEPT.md Notes):",
                    *listing)]


def _last_chapter(story):
    # Chapter_01.md … Chapter_NN.md sort alphabetically, so last = most recent.
    chapters = md_files(f"{story}/chapters")
    if not chapters:
        return _notice("MOST RECENT CHAPTER: chapters/ is empty or absent — this is the first chapter")
    return _file("chapter", f"Most recent chapter: {chapters[-1]}", chapters[-1])


def collect(story, world, *, style="", structure="", reviews_dir="", position="",
            no_style=False, no_last_chapter=False, no_timeline=False, no_schemes=False,
            no_facts=False, description=False, hooks=False,
            chars=(), locs=(), factions=(), myths=(), root=None):
    """Return the context items for a story as a list of Piece, in output order.

    Paths (story, world, reviews_dir) are relative to the project root. Pass `root`
    to have the call run from there; otherwise the working directory must already be
    the project root (as it is after common.setup()).
    """
    with (in_project(root) if root else contextlib.nullcontext()):
        pieces = []
        snapshot_dir, warning = snapshot_lookup(world, position)
        if warning:
            pieces.append(_notice(warning))

        # 0. Review reports
        if reviews_dir:
            reviews = sorted(f"{reviews_dir}/{r.name}" for r in Path(reviews_dir).glob("Reviewer-*.md")) \
                if Path(reviews_dir).is_dir() else []
            if not reviews:
                pieces.append(_notice(f"REVIEWS: ⚠ No Reviewer-*.md files found in {reviews_dir}"))
            for f in reviews:
                pieces.append(_file("review", Path(f).name, f))

        # 1. Structure files
        if structure:
            pieces.append(_file("structure", "story_structure/GUIDE.md",
                                "writing_concepts/story_structure/GUIDE.md"))
            pieces.append(_file("structure", "story_structure/Format Reference.md",
                                "writing_concepts/story_structure/Format Reference.md"))
            pieces.append(_file("structure", f"story_structure/{structure}",
                                f"writing_concepts/story_structure/{structure}.md"))

        # 2. DESCRIPTION.md
        if description:
            pieces.append(_description(story, world))

        # 3. Style
        if not no_style:
            pieces.extend(_style(style))

        # 4. Most recent chapter
        if not no_last_chapter:
            pieces.append(_last_chapter(story))

        # 5. Story-local state
        if not no_timeline:
            pieces.append(_file("timeline", "state/Timeline.md", f"{story}/state/Timeline.md"))
        if not no_schemes:
            pieces.append(_file("schemes", "state/ACTIVE_SCHEMES.md", f"{story}/state/ACTIVE_SCHEMES.md"))
        if not no_facts:
            pieces.append(_file("facts", "state/STORY_FACTS.md", f"{story}/state/STORY_FACTS.md"))
        if hooks:
            pieces.append(_file("hooks", "HOOKS.md", f"{world}/HOOKS.md"))

        # 6. Entities
        for type_, names in (
            ("characters", chars),
            ("points_of_interest", locs),
            ("factions", factions),
            ("mythology", myths),
        ):
            for name in names:
                pieces.append(_entity(story, world, snapshot_dir, position, type_, name))
        return pieces


def render(pieces):
    """The exact text the command line prints for these items."""
    return "".join(p.text for p in pieces)


def main():
    setup()
    p = make_parser("Story context loader")
    p.add_argument("--story", required=True)
    p.add_argument("--world", required=True)
    p.add_argument("--style", default="")
    p.add_argument("--structure", default="")
    p.add_argument("--reviews-dir", default="")
    p.add_argument("--position", default="")
    p.add_argument("--no-style", action="store_true")
    p.add_argument("--no-last-chapter", action="store_true")
    p.add_argument("--no-timeline", action="store_true")
    p.add_argument("--no-schemes", action="store_true")
    p.add_argument("--no-facts", action="store_true")
    p.add_argument("--description", action="store_true")
    p.add_argument("--hooks", action="store_true")
    p.add_argument("--char", action="append", default=[])
    p.add_argument("--loc", action="append", default=[])
    p.add_argument("--faction", action="append", default=[])
    p.add_argument("--myth", action="append", default=[])
    a = p.parse_args()

    pieces = collect(
        a.story, a.world, style=a.style, structure=a.structure, reviews_dir=a.reviews_dir,
        position=a.position, no_style=a.no_style, no_last_chapter=a.no_last_chapter,
        no_timeline=a.no_timeline, no_schemes=a.no_schemes, no_facts=a.no_facts,
        description=a.description, hooks=a.hooks,
        chars=a.char, locs=a.loc, factions=a.faction, myths=a.myth,
    )
    sys.stdout.write(render(pieces))


if __name__ == "__main__":
    main()
