#!/usr/bin/env python3
"""wr_paths.py — Write where the Writing Room framework is into the project's AGENTS.md

Usage:
  python "<WR>/scripts/wr_paths.py" [--root DIR] [--wr DIR] [--check] [--dry-run]

Skills write `<WR>` for the framework folder (the installed `writing-room` skill, with its scripts,
templates and shared references). A model cannot reliably work out that folder from the skill it is
running, so the project says it outright: AGENTS.md (which CLAUDE.md imports, and which every
supported harness loads at session start) carries a managed "Writing Room paths" block naming <WR>,
the conventions, the scripts, and where templates and craft files come from.

The path is relative to the project root when the install is inside the project (so a synced or
moved project keeps working), absolute otherwise. wr_install.py, wr_update.py and wr_init.py keep
the block current; run this script to write it by hand, or with --check to only report.

Which install is named: the one the block already names, if it still exists; otherwise the first
project install (.claude/skills, .agents/skills, .opencode/skills, .hermes/skills); otherwise a
user-level install; otherwise the framework this script belongs to. --wr names one explicitly.
Only the block is ever changed; the rest of AGENTS.md is left as it is. A project without AGENTS.md
gets none (wr_install.py --guidance or wr_init.py add one).
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import FRAMEWORK_DIR, ProjectNotFound, find_root, make_parser  # noqa: E402

BEGIN = "<!-- writing-room:paths -->"
END = "<!-- /writing-room:paths -->"
BLOCK_RE = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END) + r"[ \t]*(?:\r?\n)?", re.S)
STRIP_RE = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END) + r"[ \t]*(?:\r?\n){0,2}", re.S)
WR_LINE = re.compile(r"^- `<WR>` = `([^`]+)`", re.M)
GUIDE = "AGENTS.md"


def is_framework(path):
    """True if path is a usable writing-room skill folder."""
    path = Path(path)
    return (path / "SKILL.md").is_file() and (path / "scripts" / "common.py").is_file()


def display(project, wr):
    """<WR> as written in the block: project-relative POSIX path if inside the project, else absolute."""
    project, wr = Path(project).resolve(), Path(wr).resolve()
    try:
        return wr.relative_to(project).as_posix()
    except ValueError:
        return wr.as_posix()


def render(project, wr):
    """The block text (LF line endings), ending with a newline."""
    w = display(project, wr)
    skills = w.rsplit("/", 1)[0] if "/" in w else "."
    where = ("These paths are relative to the project root (the folder this file is in)."
             if not Path(w).is_absolute() else "These are absolute paths.")
    return "\n".join([
        BEGIN,
        "## Writing Room paths",
        "",
        "Skills write `<WR>` for the Writing Room framework folder. It is not inside the skill you are running "
        "and not a folder of the project unless the line below says so. In this project:",
        "",
        f"- `<WR>` = `{w}`",
        f"- Shared rules: `{w}/references/conventions.md`; project layout: `{w}/references/layout.md`",
        f"- Scripts: `python \"{w}/scripts/<name>.py\" ...`, run from the project root",
        f"- Templates and craft files: the project's own copy if it has one, otherwise the framework's: "
        f"`templates/…` is `{w}/shared/templates/…`; `writing_concepts/story_structure/…`, `writing_concepts/archetypes/…` "
        f"and `writing_concepts/tropes/…` are under `{w}/shared/craft/…`",
        f"- A skill's own `references/…` files: `{skills}/<skill name>/references/…`",
        "",
        f"{where} Use them exactly as written. This block is kept current by the Writing Room scripts; do not edit it.",
        END,
        "",
    ])


def read(project):
    """(<WR> as written in the block or None, AGENTS.md exists)."""
    f = Path(project) / GUIDE
    if not f.is_file():
        return None, False
    m = BLOCK_RE.search(f.read_text(encoding="utf-8"))
    if not m:
        return None, True
    w = WR_LINE.search(m.group(0))
    return (w.group(1) if w else ""), True


def resolve(project, written):
    """The folder a block's <WR> value points to."""
    p = Path(written)
    return p if p.is_absolute() else Path(project) / p


def strip(text):
    """text without the block (to compare AGENTS.md with the shipped version)."""
    return STRIP_RE.sub("", text)


def candidates(project, env=None):
    """Writing-room folders that could be <WR> for this project, in order of preference."""
    from wr_install import HARNESSES, PROJECT_DIRS, user_dir  # local import: wr_install uses this module
    found = []
    for rel in PROJECT_DIRS:
        found.append(Path(project) / rel / "writing-room")
    for h in HARNESSES:
        found.append(user_dir(h, env) / "writing-room")
    found.append(FRAMEWORK_DIR)
    return [p for p in found if is_framework(p)]


def choose(project, env=None):
    """The folder to name: the current one if still valid, else the first candidate, else None."""
    written, _ = read(project)
    if written and is_framework(resolve(project, written)):
        return resolve(project, written)
    found = candidates(project, env)
    return found[0] if found else None


def write(project, wr=None, dry_run=False, env=None):
    """Add or refresh the block in AGENTS.md. Returns (status, <WR> as written or None).

    status: "added", "updated", "unchanged", "removed" (no install left), "no AGENTS.md", "nothing found"."""
    project = Path(project)
    f = project / GUIDE
    if not f.is_file():
        return "no AGENTS.md", None
    wr = Path(wr) if wr else choose(project, env)
    raw = f.read_bytes().decode("utf-8")
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")
    has = BLOCK_RE.search(text)
    if wr is None:
        if not has:
            return "nothing found", None
        new, status, shown = BLOCK_RE.sub("", text), "removed", None
    else:
        block, shown = render(project, wr), display(project, wr)
        if has:
            new = text[:has.start()] + block + text[has.end():]
            status = "unchanged" if new == text else "updated"
        else:
            # Before the first second-level section, so it is read early; else at the end.
            m = re.search(r"^## ", text, re.M)
            if m:
                new = text[:m.start()] + block + "\n" + text[m.start():]
            else:
                new = text.rstrip("\n") + "\n\n" + block
            status = "added"
    if status != "unchanged" and not dry_run:
        f.write_bytes((new.replace("\n", "\r\n") if crlf else new).encode("utf-8"))
    return status, shown


def describe(status, shown, dry_run=False):
    """One line saying what write() did, or None when nothing changed."""
    verbs = {"added": ("added", "would add"), "updated": ("updated", "would update"),
             "removed": ("removed", "would remove")}
    if status not in verbs:
        return None
    return (f"AGENTS.md: {verbs[status][dry_run]} the Writing Room paths block"
            + (f" (<WR> = {shown})" if shown else ""))


def check(project):
    """(errors, warnings) for wr_doctor. A project without AGENTS.md is a choice (--no-guidance), not a
    problem: skills then fall back to the writing-room folder beside their own."""
    written, exists = read(project)
    if not exists:
        return [], []
    if written is None:
        return [], ["AGENTS.md has no Writing Room paths block, so skills must guess where the framework (<WR>) "
                    "is; `python \"<WR>/scripts/wr_paths.py\"` (or wr_update.py) adds it"]
    if not is_framework(resolve(project, written)):
        return [f"AGENTS.md says the framework (<WR>) is `{written}`, which is not a writing-room skill folder "
                "(moved, uninstalled, or another machine); `python \"<WR>/scripts/wr_paths.py\"` rewrites it"], []
    return [], []


def main():
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", newline="\n")
    p = make_parser("Write where the Writing Room framework is into the project's AGENTS.md")
    p.add_argument("--wr", help="the writing-room folder to name (default: see the module help)")
    p.add_argument("--check", action="store_true", help="report only; exit 1 if the block is missing or wrong")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    try:
        root, _ = find_root(explicit=a.root)
    except ProjectNotFound as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    if a.check:
        errors, warnings = check(root)
        for line in errors + warnings:
            print(line)
        if not errors and not warnings:
            print(f"AGENTS.md names <WR> = {read(root)[0]}")
        return 1 if errors or warnings else 0
    if a.wr and not is_framework(a.wr):
        print(f"Error: {a.wr} is not a writing-room skill folder (no SKILL.md and scripts/).", file=sys.stderr)
        return 2
    status, shown = write(root, a.wr, a.dry_run)
    messages = {
        "added": f"Added the Writing Room paths block to AGENTS.md: <WR> = {shown}",
        "updated": f"Updated the Writing Room paths block in AGENTS.md: <WR> = {shown}",
        "unchanged": f"AGENTS.md already names <WR> = {shown}",
        "removed": "No Writing Room install found; removed the paths block from AGENTS.md",
        "no AGENTS.md": "The project has no AGENTS.md; `wr_install.py --guidance` adds one.",
        "nothing found": "No Writing Room install found; nothing written.",
    }
    print(("Dry run: " if a.dry_run and status not in ("unchanged", "no AGENTS.md", "nothing found") else "")
          + messages[status])
    return 0 if status not in ("no AGENTS.md", "nothing found") else 1


if __name__ == "__main__":
    sys.exit(main())
