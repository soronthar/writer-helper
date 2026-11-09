#!/usr/bin/env python3
"""load_world.py — World bible context loader

Used by the Story Ideator and Outliner to load world bible and story craft
files in a single call. Three operating modes, selected automatically based on
the flags provided.

MODE 1 — Overview  (Story Ideator, Pass 1)

  python "scripts/load_world.py" --world "worlds/<World Name>"

  Outputs: DESCRIPTION.md, SUMMARY.md, HOOKS.md, WORLD_ORDER.md,
           ALL writing_concepts/story_structure/ files.

MODE 2 — Structure  (Outliner, Pass 1)

  python "scripts/load_world.py" \\
    --world "worlds/<World Name>" --structure "Three-Act Structure"

  Outputs: DESCRIPTION.md, SUMMARY.md, story_structure/GUIDE.md,
           story_structure/Format Reference.md, the named structure file.
  Skips:   HOOKS.md, WORLD_ORDER.md, all other structure files.
  --structure is the filename stem (no .md extension).

MODE 3 — Entities  (Ideator & Outliner, Pass 2)

  Pass 2a — selective:
    python "scripts/load_world.py" --world "worlds/<World Name>" \\
      --entity "characters/Mara Quill" --entity "factions/Harbor Guild"

  Pass 2b — staleness fallback (SUMMARY.md absent or stale):
    python "scripts/load_world.py" --world "worlds/<World Name>" --all-entities

  --entity accepts "type/Name" where type is one of:
    characters | factions | points_of_interest | mythology
  The name is the filename stem (no .md extension).
  When --entity or --all-entities is given, ONLY entity files are output.

Craft files (any mode)
  --trope "Name"  --archetype "Name"   Repeatable. Add writing_concepts/tropes/<Name>.md
  or archetypes/<Name>.md after the rest. Given without --entity, they are loaded
  instead of the overview, like --entity. With --entity, --trope or --archetype,
  --structure "Name" adds that full structure file at the end.

PRESETS — the short form skills use

  --for story-ideator --world "<World>"
    The overview, then a SUMMARY CHECK. Story structures are short here:
    GUIDE.md and Format Reference.md in full, and only the Overview of each
    structure file. When SUMMARY.md is missing or does not match the entity
    files, every entity file is added, so no second call is needed. Add
    --entity, --trope and --archetype to load those in the same call, and
    --structure "<Name>" for the full file of the structure you choose.
  --for outliner --story "stories/<Story>"
    World and structure come from the story's CONCEPT.md (the series CONCEPT.md
    for a Book). Prints the structure mode's files, WORLD_ORDER.md and a SUMMARY
    CHECK, then every entity file if SUMMARY.md is stale, plus any --entity,
    --trope and --archetype.
  A CONTEXT block at the top says what was used. --world accepts a bare world
  name ("Harrowmere" for "worlds/Harrowmere"). Without --for, output is
  unchanged.

Notes
  - Run from anywhere; paths are relative to the project root
    (auto-discovered; override with --root).
  - Missing files emit a ⚠ warning line rather than crashing.
  - --position <N>: entity reads prefer worlds/<World>/snapshots/<N>/ over the
    current worlds/<World>/ directory (historical world state).
  - --output [<file>]: save the output instead of printing it — by default to
    .writing-room-work/<world path>/load_world.md — and print a receipt with the
    file's absolute path and each block's line range.
"""

import contextlib
import io
import sys
from pathlib import Path

from common import (DIV, add_output_arg, md_files, make_parser, out, output_path, print_file, read_exact,
                    resolve_snapshot, save_output, setup, stem, text_receipt)
from load_bible import _concept, _concept_field
from wr_layout import summary_mismatches

ENTITY_DIRS = ("characters", "factions", "points_of_interest", "mythology")


def load_all_entities(world, snapshot_dir, position):
    for d in ENTITY_DIRS:
        seen = set()

        # Snapshot files first, then world files not already covered.
        snap_files = md_files(f"{snapshot_dir}/{d}") if snapshot_dir else []
        for f in snap_files:
            seen.add(stem(f))
            print_file(f"{d}/{stem(f)}  [snapshot pos {position}]", f)

        world_files = md_files(f"{world}/{d}")
        for f in world_files:
            if stem(f) not in seen:
                print_file(f"{d}/{stem(f)}  [world bible]", f)

        if not seen and not world_files:
            out()
            out(DIV)
            out(f"DIRECTORY: {world}/{d}/  (empty or not found)")
            out(DIV)


def load_entities(world, entities, snapshot_dir, position):
    for entry in entities:
        snap = f"{snapshot_dir}/{entry}.md" if snapshot_dir else ""
        if snap and Path(snap).is_file():
            print_file(f"{entry}  [snapshot pos {position}]", snap)
        else:
            print_file(entry, f"{world}/{entry}.md")


def load_structure(world, structure):
    print_file("DESCRIPTION.md", f"{world}/DESCRIPTION.md")
    print_file("SUMMARY.md", f"{world}/SUMMARY.md")
    print_file("story_structure/GUIDE.md", "writing_concepts/story_structure/GUIDE.md")
    print_file("story_structure/Format Reference.md", "writing_concepts/story_structure/Format Reference.md")
    print_file(f"story_structure/{structure}", f"writing_concepts/story_structure/{structure}.md")


def load_overview(world):
    print_file("DESCRIPTION.md", f"{world}/DESCRIPTION.md")
    print_file("SUMMARY.md", f"{world}/SUMMARY.md")
    print_file("HOOKS.md", f"{world}/HOOKS.md")
    print_file("WORLD_ORDER.md", f"{world}/WORLD_ORDER.md")

    structure_files = md_files("writing_concepts/story_structure")
    if not structure_files:
        out()
        out(DIV)
        out("STORY STRUCTURE: ⚠ No files found in writing_concepts/story_structure/")
        out(DIV)
    else:
        for f in structure_files:
            print_file(f"story_structure/{Path(f).name}", f)


def structure_overview(path):
    """The top of a structure file: its title and Overview section, up to the next ## heading."""
    lines = read_exact(path).splitlines(keepends=True)
    headings = [n for n, line in enumerate(lines) if line.startswith("## ")]
    return "".join(lines[:headings[1]] if len(headings) > 1 else lines).rstrip("\n") + "\n"


def load_structure_overviews():
    """GUIDE.md and Format Reference.md in full; the Overview of every other structure file."""
    structure_files = md_files("writing_concepts/story_structure")
    if not structure_files:
        _block("STORY STRUCTURE: ⚠ No files found in writing_concepts/story_structure/")
        return
    for f in structure_files:
        name = Path(f).name
        if name in ("GUIDE.md", "Format Reference.md"):
            print_file(f"story_structure/{name}", f)
        else:
            _block(f"FILE: story_structure/{name}  (Overview only; the full file loads with --structure \"{stem(f)}\")")
            sys.stdout.write(structure_overview(f))


def load_craft(args):
    for kind, names in (("tropes", args.trope), ("archetypes", args.archetype)):
        for name in names:
            print_file(f"{kind}/{name}", f"writing_concepts/{kind}/{name}.md")


def _block(*lines):
    out()
    out(DIV)
    for line in lines:
        out(line)
    out(DIV)


def summary_check(world):
    """Print the SUMMARY CHECK block; True when every entity file should be loaded (SUMMARY.md missing or stale)."""
    n_entities, stale = summary_mismatches(world)
    if stale is None:
        _block(f"SUMMARY CHECK: ⚠ no SUMMARY.md — all {n_entities} entity files are loaded below.")
        return True
    if stale:
        _block("SUMMARY CHECK: ⚠ SUMMARY.md is stale — all entity files are loaded below. Tell the user:",
               "  run the writing-assistant skill after this session to regenerate SUMMARY.md.",
               *(f"  {line}" for line in stale))
        return True
    _block(f"SUMMARY CHECK: SUMMARY.md matches the {n_entities} entity files. Load the ones you need with --entity.")
    return False


def resolve(args):
    """Fill in what the short form leaves out; print the CONTEXT block. Exits with a message on failure."""
    lines = [f"CONTEXT for {args.preset}"]
    if args.preset == "outliner":
        if not args.story:
            sys.exit('Error: --for outliner needs --story "stories/<Story>".')
        story = args.story.strip().rstrip("/\\")
        if not Path(story).is_dir() and Path("stories", story).is_dir():
            story = f"stories/{story}"
        concept, _name = _concept(story)
        if not concept:
            sys.exit(f'Error: no CONCEPT.md for "{story}". Pass the path from the project root, e.g. "stories/<Story>".')
        text = concept.read_text(encoding="utf-8")
        lines[0] += f" — story: {story}"
        if not args.world:
            found = _concept_field(text, "World")
            if not found:
                sys.exit(f'Error: {concept.as_posix()} has no **World:** line. Pass --world "worlds/<World>".')
            args.world = found
            lines.append(f"  World: worlds/{found}  (from {concept.as_posix()})")
        if not args.structure:
            args.structure = _concept_field(text, "Structure")
            if args.structure:
                lines.append(f"  Structure: {args.structure}  (from {concept.as_posix()})")
            else:
                lines.append("  Structure: ⚠ CONCEPT.md has no **Structure:** line; pass --structure \"<Name>\"")
    if not args.world:
        sys.exit(f'Error: --for {args.preset} needs --world "<World>".')
    if not Path(args.world).is_dir() and Path("worlds", args.world).is_dir():
        args.world = f"worlds/{args.world}"
    if not Path(args.world).is_dir():
        sys.exit(f'Error: no world folder at "{args.world}". Pass --world "worlds/<World>".')
    if len(lines) == 1 or not lines[1].startswith("  World:"):
        lines.insert(1, f"  World: {args.world}")
    _block(*lines)


def load_preset(args):
    resolve(args)
    if args.preset == "story-ideator":
        print_file("DESCRIPTION.md", f"{args.world}/DESCRIPTION.md")
        print_file("SUMMARY.md", f"{args.world}/SUMMARY.md")
        print_file("HOOKS.md", f"{args.world}/HOOKS.md")
        print_file("WORLD_ORDER.md", f"{args.world}/WORLD_ORDER.md")
        if not args.structure:
            load_structure_overviews()
    else:
        load_structure(args.world, args.structure)
        print_file("WORLD_ORDER.md", f"{args.world}/WORLD_ORDER.md")
    snapshot_dir = resolve_snapshot(args.world, args.position)
    if summary_check(args.world):
        load_all_entities(args.world, snapshot_dir, args.position)
    elif args.entity:
        load_entities(args.world, args.entity, snapshot_dir, args.position)
    load_craft(args)
    if args.preset == "story-ideator" and args.structure:
        print_file(f"story_structure/{args.structure}", f"writing_concepts/story_structure/{args.structure}.md")


def main():
    setup()
    parser = make_parser("World bible context loader")
    parser.add_argument("--for", dest="preset", choices=("story-ideator", "outliner"), default="",
                        help="the files one skill step needs, with the SUMMARY.md check done for you")
    parser.add_argument("--world", default="")
    parser.add_argument("--story", default="")
    parser.add_argument("--structure", default="")
    parser.add_argument("--position", default="")
    parser.add_argument("--entity", action="append", default=[])
    parser.add_argument("--all-entities", action="store_true")
    parser.add_argument("--trope", action="append", default=[])
    parser.add_argument("--archetype", action="append", default=[])
    add_output_arg(parser)
    args = parser.parse_args()
    if not args.preset and not args.world:
        parser.error("--world is required (or use --for)")
    if args.world and not Path(args.world).is_dir() and Path("worlds", args.world).is_dir():
        args.world = f"worlds/{args.world}"  # a bare world name

    if not args.output:
        load(args)
        return
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        load(args)
    path = output_path(args.output, args.world, "load_world.md")
    save_output(buffer.getvalue(), path)
    sys.stdout.write(text_receipt(buffer.getvalue(), path))


def load(args):
    if args.preset:
        load_preset(args)
        return
    snapshot_dir = resolve_snapshot(args.world, args.position)

    if args.entity or args.all_entities or args.trope or args.archetype:
        if args.all_entities:
            load_all_entities(args.world, snapshot_dir, args.position)
        else:
            load_entities(args.world, args.entity, snapshot_dir, args.position)
        load_craft(args)
        if args.structure:
            print_file(f"story_structure/{args.structure}", f"writing_concepts/story_structure/{args.structure}.md")
    elif args.structure:
        load_structure(args.world, args.structure)
    else:
        load_overview(args.world)


if __name__ == "__main__":
    main()
