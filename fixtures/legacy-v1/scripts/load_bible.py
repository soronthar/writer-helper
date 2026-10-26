#!/usr/bin/env python3
"""load_bible.py — Story context loader

Used by the Draft Writer, Planner, Reviewer, Draft Fixer and Story Analyzer to
load story-level reference files in a single call.

Core flags (always available)
  --story <path>   Story root relative to Writing_Room/.
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
                        to Writing_Room/). For Draft Fixer.
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
  python "Writing_Room/scripts/load_bible.py" \\
    --story "stories/The Tallow Ledger" --world "worlds/Harrowmere" \\
    --char "Mara Quill" --loc "The Ashwood"

  python "Writing_Room/scripts/load_bible.py" \\
    --story "stories/The Tallow Ledger" --world "worlds/Harrowmere" \\
    --no-style --no-last-chapter --hooks --char "Mara Quill"

Notes
  - Run from anywhere; paths are relative to Writing_Room/ (the script cd's there).
  - Missing files emit a ⚠ warning line rather than crashing.
"""

from pathlib import Path

from common import DIV, cat, md_files, make_parser, out, print_file, resolve_snapshot, setup


def print_entity(story, world, snapshot_dir, position, type_, name):
    """Load one entity with priority: story-local -> snapshot -> world bible."""
    primary = f"{story}/state/bible/{type_}/{name}.md"
    snapshot_file = f"{snapshot_dir}/{type_}/{name}.md" if snapshot_dir else ""
    fallback = f"{world}/{type_}/{name}.md"

    out()
    out(DIV)
    if Path(primary).is_file():
        out(f"FILE: {type_}/{name}  [story-local]")
        path = primary
    elif snapshot_file and Path(snapshot_file).is_file():
        out(f"FILE: {type_}/{name}  [snapshot pos {position}]")
        path = snapshot_file
    elif Path(fallback).is_file():
        out(f"FILE: {type_}/{name}  [world bible]")
        path = fallback
    else:
        out(f"FILE: {type_}/{name}  ⚠ NOT FOUND in state/bible/, snapshot, or world bible")
        out(DIV)
        return
    out(DIV)
    cat(path)


def print_description(story, world):
    primary = f"{story}/state/bible/DESCRIPTION.md"
    fallback = f"{world}/DESCRIPTION.md"
    out()
    out(DIV)
    if Path(primary).is_file():
        out("FILE: DESCRIPTION.md  [story-local]")
        out(DIV)
        cat(primary)
    elif Path(fallback).is_file():
        out("FILE: DESCRIPTION.md  [world bible]")
        out(DIV)
        cat(fallback)
    else:
        out("FILE: DESCRIPTION.md  ⚠ NOT FOUND in state/bible/ or world bible")
        out(DIV)


def print_style(style_hint):
    style_files = md_files("writing_concepts/styles")

    if not style_files:
        out()
        out(DIV)
        out("STYLE FILE: ⚠ None found in writing_concepts/styles/ — agent uses own judgment")
        out(DIV)
    elif len(style_files) == 1:
        print_file(f"Style: {style_files[0]}", style_files[0])
    elif style_hint:
        matched = next((f for f in style_files if style_hint in f), "")
        if matched:
            print_file(f'Style: {matched}  [matched hint: "{style_hint}"]', matched)
        else:
            out()
            out(DIV)
            out(f'STYLE FILE: ⚠ Multiple files found; hint "{style_hint}" matched nothing.')
            out("Agent must select one and read it separately. Available files:")
            for f in style_files:
                out(f"  writing_concepts/styles/{Path(f).name}")
            out(DIV)
    else:
        out()
        out(DIV)
        out("STYLE FILE: ⚠ Multiple files found — agent must select (check CONCEPT.md Notes):")
        for f in style_files:
            out(f"  writing_concepts/styles/{Path(f).name}")
        out(DIV)


def print_last_chapter(story):
    # Chapter_01.md … Chapter_NN.md sort alphabetically, so last = most recent.
    chapters = md_files(f"{story}/chapters")
    if not chapters:
        out()
        out(DIV)
        out("MOST RECENT CHAPTER: chapters/ is empty or absent — this is the first chapter")
        out(DIV)
    else:
        print_file(f"Most recent chapter: {chapters[-1]}", chapters[-1])


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

    snapshot_dir = resolve_snapshot(a.world, a.position)

    # 0. Review reports
    if a.reviews_dir:
        reviews = sorted(f"{a.reviews_dir}/{r.name}" for r in Path(a.reviews_dir).glob("Reviewer-*.md")) \
            if Path(a.reviews_dir).is_dir() else []
        if not reviews:
            out()
            out(DIV)
            out(f"REVIEWS: ⚠ No Reviewer-*.md files found in {a.reviews_dir}")
            out(DIV)
        for f in reviews:
            print_file(Path(f).name, f)

    # 1. Structure files
    if a.structure:
        print_file("story_structure/GUIDE.md", "writing_concepts/story_structure/GUIDE.md")
        print_file("story_structure/Format Reference.md", "writing_concepts/story_structure/Format Reference.md")
        print_file(f"story_structure/{a.structure}", f"writing_concepts/story_structure/{a.structure}.md")

    # 2. DESCRIPTION.md
    if a.description:
        print_description(a.story, a.world)

    # 3. Style
    if not a.no_style:
        print_style(a.style)

    # 4. Most recent chapter
    if not a.no_last_chapter:
        print_last_chapter(a.story)

    # 5. Story-local state
    if not a.no_timeline:
        print_file("state/Timeline.md", f"{a.story}/state/Timeline.md")
    if not a.no_schemes:
        print_file("state/ACTIVE_SCHEMES.md", f"{a.story}/state/ACTIVE_SCHEMES.md")
    if not a.no_facts:
        print_file("state/STORY_FACTS.md", f"{a.story}/state/STORY_FACTS.md")
    if a.hooks:
        print_file("HOOKS.md", f"{a.world}/HOOKS.md")

    # 6. Entities
    for type_, names in (
        ("characters", a.char),
        ("points_of_interest", a.loc),
        ("factions", a.faction),
        ("mythology", a.myth),
    ):
        for name in names:
            print_entity(a.story, a.world, snapshot_dir, a.position, type_, name)


if __name__ == "__main__":
    main()
