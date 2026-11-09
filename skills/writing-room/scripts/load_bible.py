#!/usr/bin/env python3
"""load_bible.py — Story context loader

Used by the Draft Writer, Planner, Reviewer, Draft Fixer and Story Analyzer to
load story-level reference files in a single call.

Core flags (always available)
  --story <path>   Story root relative to the project root.
                   Book series: "stories/<Series>/Book 01 - <Title>"
  --world <path>   World bible root, e.g. "worlds/Harrowmere". Optional with --for.

Presets (the short form skills use)
  --for <preset>   Sets the flags one skill step needs: planner, draft-writer,
                   reviewer-consistency, reviewer-character, draft-fixer,
                   story-analyzer. Add --char/--loc/--faction/--myth, --style
                   and --output as usual. --recipes prints each preset with the
                   flags it stands for.
  With --for, or without --world, the script works out what it can:
    --world      from CONCEPT.md's World line (the series CONCEPT.md for a Book)
    --position   the world baseline: the story before this one in WORLD_ORDER.md
                 (its first row); none for the first story. --position none
                 turns it off; an explicit --position N wins.
    --structure  (planner) from CONCEPT.md's Structure line
    --story      "The Story" is read as "stories/The Story" when only that exists
  A CONTEXT block at the top of the output says what was used and where from.
  The long form (--world given, no --for) behaves exactly as before.

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
  --style "Name"  Partial name matched against style filenames. A hint that
                  matches nothing loads no style (even if only one file exists).

Saving the output
  --output         Write the context to the project's working-files folder,
                   .writing-room-work/<story path>/load_bible.md (UTF-8), and
                   print only a receipt: the file's absolute path, then one line
                   per item with its kind, source, path and line range.
  --output <file>  The same, to <file> (relative to the project root).

Misplaced story-local files
  An entity file directly in <story>/state/bible/ (not in its type folder) is
  never loaded; a ⚠ notice names it before the entity that was loaded instead.

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
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from common import (DIV, add_output_arg, in_project, is_file, lookup, make_parser, md_files, output_path,
                    read_exact, receipt_header, save_output, setup, snapshot_lookup, strip_wikilink)
from query_position import baseline


@dataclass
class Piece:
    """One loaded item: the file content plus where it came from.

    text is exactly what the command line prints for this item (header + content);
    body is the file content alone. Library callers (the harness) use body and the
    metadata; the CLI prints text.
    """
    kind: str            # context | review | structure | description | style | chapter | timeline | schemes | facts | hooks | entity | notice
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


def _misplaced(story, type_, name):
    """A notice when <story>/state/bible/<Name>.md sits outside its type folder (never loaded), else None."""
    flat = f"{story}/state/bible/{name}.md"
    if not Path(flat).is_file():
        return None
    return _notice(f"ENTITY {type_}/{name}: ⚠ {flat} is outside state/bible/{type_}/ and was NOT loaded.",
                   "The file loaded below may be older. Ask the author to move it into the type folder;",
                   "do not merge or move it yourself.")


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
    if style_hint:
        matched = next((f for f in style_files if style_hint in f), "")
        if matched and len(style_files) == 1:
            return [_file("style", f"Style: {matched}", matched)]
        if matched:
            return [_file("style", f'Style: {matched}  [matched hint: "{style_hint}"]', matched)]
        return [_notice(f'STYLE FILE: ⚠ No style file matches "{style_hint}"; nothing was loaded.',
                        "Do not substitute another style. Ask the author which to use. Available files:",
                        *listing)]
    if len(style_files) == 1:
        return [_file("style", f"Style: {style_files[0]}", style_files[0])]
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
                misplaced = _misplaced(story, type_, name)
                if misplaced:
                    pieces.append(misplaced)
                pieces.append(_entity(story, world, snapshot_dir, position, type_, name))
        return pieces


# --for presets: the flags each skill step passes. "<story>" in a value is replaced by the story path.
PRESETS = {
    "planner": ({"no_last_chapter": True},
                "planner, Step 4b: structure files, style, Timeline, registries and the chapter's entities"),
    "draft-writer": ({},
                     "draft-writer, Step 4c: style, most recent chapter, Timeline, registries and entities"),
    "reviewer-consistency": ({"no_style": True, "no_last_chapter": True, "description": True},
                             "reviewer, Step 4: DESCRIPTION.md, Timeline, registries, locations, factions, myths"),
    "reviewer-character": ({"no_style": True, "no_last_chapter": True, "no_timeline": True},
                           "reviewer, Step 6: registries and character files"),
    "draft-fixer": ({"no_last_chapter": True, "no_timeline": True,
                     "reviews_dir": "<story>/current_chapter/current_reviews"},
                    "draft-fixer, Step 4a: review reports, style and registries"),
    "story-analyzer": ({"no_style": True, "no_last_chapter": True, "hooks": True},
                       "story-analyzer, Step 4b: Timeline, registries, HOOKS.md and the chapter's entities"),
}
ENTITY_ARGS = {
    "planner": '--char "Name" --loc "Name" [--faction "Name"] [--style "hint"]',
    "draft-writer": '--char "Name" --loc "Name" [--faction "Name"] [--style "hint"]',
    "reviewer-consistency": '--loc "Name" [--faction "Name"] [--myth "Name"]',
    "reviewer-character": '--char "Name"',
    "draft-fixer": '[--style "hint"]',
    "story-analyzer": '--char "Name" --loc "Name" [--faction "Name"]',
}


def recipes():
    """The --recipes text: one entry per preset, with the long-form flags it stands for."""
    lines = ["load_bible.py presets. Run from anywhere inside the project, as one line (no line breaks).",
             "Repeat --char/--loc/--faction/--myth once per name. [Square brackets] mark optional flags:",
             "leave out the ones you do not need, and never type the brackets.",
             "The world, the baseline position (and the planner's structure) are worked out from the story;",
             "the CONTEXT block at the top of the output says which were used.", ""]
    for name, (flags, when) in PRESETS.items():
        long_form = " ".join(f"--{k.replace('_', '-')}" + (f' "{v}"' if isinstance(v, str) else "")
                             for k, v in flags.items())
        if name == "planner":
            long_form += ' --structure "<from CONCEPT.md>"'
        lines += [f"{name} — {when}",
                  f'  python "<WR>/scripts/load_bible.py" --for {name} --story "stories/<Story>" {ENTITY_ARGS[name]} --output',
                  f"  stands for: --world <from CONCEPT.md> --position <baseline> {long_form}".rstrip(), ""]
    lines += ["Without --output the context is printed instead of saved; with it, read the file at the",
              "path the receipt prints, range by range."]
    return "\n".join(lines) + "\n"


def _concept(story):
    """(CONCEPT.md path, story name in WORLD_ORDER.md) for a story or a Book of a series, or (None, None)."""
    for d in (Path(story), Path(story).parent):
        if (d / "CONCEPT.md").is_file():
            return d / "CONCEPT.md", d.name
    return None, None


def _concept_field(text, field):
    m = re.search(rf"\*\*{field}:\*\*\s*(.+)", text)
    return strip_wikilink(m.group(1).strip().strip("`")) if m else ""


def resolve(story, world, position, structure, preset):
    """Fill in what the short form leaves out. Returns (story, world, position, structure, pieces), where
    pieces are the CONTEXT block and any warnings, printed first. Exits with a message when the story or
    its world cannot be found."""
    story = story.strip().rstrip("/\\")
    if not Path(story).is_dir() and Path("stories", story).is_dir():
        story = f"stories/{story}"
    if not Path(story).is_dir():
        sys.exit(f'Error: no story folder at "{story}". Pass the path from the project root, e.g. "stories/<Story>".')
    concept, name = _concept(story)
    text = read_exact(concept) if concept else ""
    where = concept.as_posix() if concept else ""
    lines, notices = [f"CONTEXT for {preset or 'custom flags'} — story: {story}"], []

    if world:
        lines.append(f"  World: {world}  (given)")
    else:
        found = _concept_field(text, "World")
        if not found:
            sys.exit(f"Error: cannot tell the world: {where or story + '/CONCEPT.md'} has no **World:** line. "
                     'Pass --world "worlds/<World>".')
        world = f"worlds/{found}"
        if not Path(world).is_dir():
            sys.exit(f'Error: CONCEPT.md names the world "{found}" but there is no folder {world}/. '
                     'Pass --world "worlds/<World>".')
        lines.append(f"  World: {world}  (from {where})")

    if position.lower() == "none":
        position = ""
        lines.append("  Baseline: none  (--position none)")
    elif position:
        lines.append(f"  Baseline: snapshot position {position}  (given)")
    else:
        position, error = baseline(world, name or Path(story).name)
        position = position or ""
        if error:
            lines.append("  Baseline: none — see the warning below")
            notices.append(_notice(f"BASELINE: ⚠ {error}. Loading the current world, not a snapshot."))
        elif position:
            lines.append(f"  Baseline: snapshot position {position}  (from {world}/WORLD_ORDER.md: the story before this one)")
        else:
            lines.append(f"  Baseline: none  (first story in {world}/WORLD_ORDER.md)")

    if preset == "planner":
        if structure:
            lines.append(f"  Structure: {structure}  (given)")
        else:
            structure = _concept_field(text, "Structure")
            if structure:
                lines.append(f"  Structure: {structure}  (from {where})")
            else:
                notices.append(_notice("STRUCTURE: ⚠ CONCEPT.md has no **Structure:** line and no --structure "
                                       "was given; no structure files were loaded."))

    context = Piece("context", lines[0], _block(*lines), "\n".join(lines[1:]) + "\n")
    return story, world, position, structure, [context] + notices


def render(pieces):
    """The exact text the command line prints for these items."""
    return "".join(p.text for p in pieces)


def receipt(pieces, output):
    """What --output prints instead of the context: one line per item with its source and line range."""
    warnings = sum(1 for p in pieces if not p.found)
    lines = receipt_header(output, render(pieces), len(pieces), warnings)
    before = 0  # newlines written before this item
    for p in pieces:
        start = before + 1
        before += p.text.count("\n")
        end = before if p.text.endswith("\n") else before + 1
        where = f"lines {start}-{end}"
        if p.kind in ("notice", "context"):
            lines.append(f"  {where}  {p.label.strip()}")
        elif p.found:
            source = f" [{p.source}]" if p.source else ""
            lines.append(f"  {where}  {p.kind}: {p.label}{source} — {p.path}")
        else:
            lines.append(f"  {where}  ⚠ {p.kind}: {p.label} — NOT FOUND")
    return "\n".join(lines) + "\n"


def main():
    if "--recipes" in sys.argv[1:]:
        sys.stdout.reconfigure(encoding="utf-8", newline="\n")
        sys.stdout.write(recipes())
        return
    setup()
    p = make_parser("Story context loader")
    p.add_argument("--for", dest="preset", choices=tuple(PRESETS), default="",
                   help="the flags one skill step needs; see --recipes")
    p.add_argument("--recipes", action="store_true", help="print each preset with the flags it stands for")
    p.add_argument("--story", required=True)
    p.add_argument("--world", default="")
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
    add_output_arg(p)
    a = p.parse_args()

    first = []
    if a.preset or not a.world:
        a.story, a.world, a.position, a.structure, first = resolve(a.story, a.world, a.position, a.structure, a.preset)
        for key, value in (PRESETS[a.preset][0].items() if a.preset else ()):
            if value is True:
                setattr(a, key, True)
            elif not getattr(a, key):
                setattr(a, key, value.replace("<story>", a.story))
    elif a.position.lower() == "none":
        a.position = ""

    pieces = first + collect(
        a.story, a.world, style=a.style, structure=a.structure, reviews_dir=a.reviews_dir,
        position=a.position, no_style=a.no_style, no_last_chapter=a.no_last_chapter,
        no_timeline=a.no_timeline, no_schemes=a.no_schemes, no_facts=a.no_facts,
        description=a.description, hooks=a.hooks,
        chars=a.char, locs=a.loc, factions=a.faction, myths=a.myth,
    )
    if a.output:
        out_path = output_path(a.output, a.story, "load_bible.md")
        save_output(render(pieces), out_path)
        sys.stdout.write(receipt(pieces, out_path))
    else:
        sys.stdout.write(render(pieces))


if __name__ == "__main__":
    main()
