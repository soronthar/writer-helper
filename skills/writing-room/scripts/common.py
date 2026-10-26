"""Shared helpers for the Writing Room scripts.

Every script imports this module and calls setup() first. setup() finds the
project root and makes it the working directory, so all paths handled by the
scripts are relative to the project root regardless of where they are invoked.

Project root discovery, first match wins:
  1. --root <dir> on the command line
  2. WRITING_ROOM_ROOT environment variable
  3. nearest ancestor of the working directory that has a writing-room.toml
     marker, or (legacy layout v1) both worlds/ and stories/
  4. the directory above scripts/ if it has worlds/ and stories/ (legacy projects
     that keep the scripts inside the project)

Craft reference and templates fall back to the framework's shared/ directory
when the project does not provide its own copy (see lookup()).
"""

import argparse
import contextlib
import os
import re
import sys
from pathlib import Path

DIV = "═" * 60

MARKER = "writing-room.toml"
SUPPORTED_LAYOUT = 1
FRAMEWORK_DIR = Path(__file__).resolve().parent.parent

# Logical project paths that fall back to the framework's shared/ directory.
# Styles are deliberately absent: a style is the author's choice and is never defaulted.
_FALLBACKS = (
    ("writing_concepts/story_structure", "craft/story_structure"),
    ("writing_concepts/archetypes", "craft/archetypes"),
    ("writing_concepts/tropes", "craft/tropes"),
    ("templates", "templates"),
)


class ProjectNotFound(Exception):
    pass


def read_marker(path):
    """Parse the tiny `key = value` subset of TOML used by writing-room.toml."""
    data = {}
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        m = re.fullmatch(r'([A-Za-z0-9_.-]+)\s*=\s*(.+)', line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if re.fullmatch(r"-?\d+", val):
            data[key] = int(val)
        elif val in ("true", "false"):
            data[key] = val == "true"
        else:
            data[key] = val.strip('"').strip("'")
    return data


def is_legacy_root(d):
    return (d / "worlds").is_dir() and (d / "stories").is_dir()


def is_root(d):
    return (d / MARKER).is_file() or is_legacy_root(d)


def find_root(start=None, explicit=None):
    """Return (root, how). Raises ProjectNotFound with a message for the user."""
    explicit = explicit or None
    if explicit:
        d = Path(explicit).resolve()
        if not d.is_dir():
            raise ProjectNotFound(f"--root {explicit}: not a directory")
        return d, "--root"
    env = os.environ.get("WRITING_ROOM_ROOT")
    if env:
        d = Path(env).resolve()
        if not d.is_dir():
            raise ProjectNotFound(f"WRITING_ROOM_ROOT={env}: not a directory")
        return d, "WRITING_ROOM_ROOT"
    here = Path(start or Path.cwd()).resolve()
    for d in (here, *here.parents):
        if (d / MARKER).is_file():
            return d, "marker"
        if is_legacy_root(d):
            return d, "legacy layout (worlds/ + stories/)"
    legacy = FRAMEWORK_DIR
    if is_legacy_root(legacy):
        return legacy, "legacy (scripts inside project)"
    raise ProjectNotFound(
        "No Writing Room project found. Run from inside a project, pass --root <dir>, "
        "set WRITING_ROOM_ROOT, or create one with wr_init.py."
    )


def check_layout(root):
    """Refuse projects written by a newer framework than this one understands."""
    marker = root / MARKER
    if marker.is_file():
        layout = read_marker(marker).get("layout", SUPPORTED_LAYOUT)
        if not isinstance(layout, int) or layout > SUPPORTED_LAYOUT:
            raise ProjectNotFound(
                f"{marker} declares layout {layout}; this framework understands layout "
                f"{SUPPORTED_LAYOUT}. Upgrade the Writing Room framework."
            )


def _scan_root_arg(argv):
    for i, a in enumerate(argv):
        if a == "--root" and i + 1 < len(argv):
            return argv[i + 1]
        if a.startswith("--root="):
            return a.split("=", 1)[1]
    return None


def setup(argv=None):
    """Force UTF-8/LF output (Windows defaults to cp1252/CRLF), locate the project, cd into it."""
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", newline="\n")
    try:
        root, _how = find_root(explicit=_scan_root_arg(sys.argv[1:] if argv is None else argv))
        check_layout(root)
    except ProjectNotFound as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    os.chdir(root)
    return root


def make_parser(description):
    p = argparse.ArgumentParser(description=description, allow_abbrev=False)
    p.add_argument("--root", default=None, help="project root (default: auto-discovered)")
    return p


def lookup(path):
    """Resolve a logical project path to a real one: project copy first, then framework shared/."""
    p = str(path).replace("\\", "/")
    if Path(p).exists():
        return p
    for prefix, shared in _FALLBACKS:
        if p == prefix or p.startswith(prefix + "/"):
            alt = FRAMEWORK_DIR / "shared" / shared / p[len(prefix):].lstrip("/")
            if alt.exists():
                return str(alt)
    return p


def out(text=""):
    print(text)


def cat(path):
    """Write a file's contents to stdout unchanged (like `cat`)."""
    with open(lookup(path), encoding="utf-8", newline="") as fh:
        sys.stdout.write(fh.read())


def is_file(path):
    return Path(lookup(path)).is_file()


def md_files(directory):
    """Files named *.md directly inside directory, as 'dir/name.md' strings, sorted case-insensitively
    (so the order is the same on Windows, macOS and Linux).

    For directories with a framework fallback, the project's files and the
    framework's are merged by file name (project wins).
    """
    d = str(directory).replace("\\", "/")
    names = set()
    candidates = [Path(d)]
    for prefix, shared in _FALLBACKS:
        if d == prefix or d.startswith(prefix + "/"):
            candidates.append(FRAMEWORK_DIR / "shared" / shared / d[len(prefix):].lstrip("/"))
    for c in candidates:
        if c.is_dir():
            names.update(p.name for p in c.glob("*.md") if p.is_file())
    return [f"{d}/{n}" for n in sorted(names, key=str.lower)]


def stem(path):
    return Path(path).stem


def print_file(label, path):
    """Print a file under a labelled header; emit a NOT FOUND warning if missing."""
    out()
    out(DIV)
    if is_file(path):
        out(f"FILE: {label}")
        out(DIV)
        cat(path)
    else:
        out(f"FILE: {label}  ⚠ NOT FOUND — {path}")
        out(DIV)


def read_exact(path):
    """Return a file's contents unchanged (no newline translation), like cat() but as a string."""
    with open(lookup(path), encoding="utf-8", newline="") as fh:
        return fh.read()


@contextlib.contextmanager
def in_project(root):
    """Run a block with `root` as the working directory (scripts' paths are relative to the root)."""
    previous = os.getcwd()
    os.chdir(root)
    try:
        yield
    finally:
        os.chdir(previous)


def snapshot_lookup(world, position):
    """Return (dir, warning). dir is '' when there is no position or no snapshot; warning is a
    one-line message when a position was asked for but its snapshot is missing, else ''."""
    if not position:
        return "", ""
    candidate = f"{world}/snapshots/{position}"
    if Path(candidate).is_dir():
        return candidate, ""
    return "", f"POSITION {position}: ⚠ No snapshot found at {candidate} — falling back to current world"


def resolve_snapshot(world, position):
    """Return the snapshots/<position> dir, or '' (after printing a warning) if absent."""
    found, warning = snapshot_lookup(world, position)
    if warning:
        out()
        out(DIV)
        out(warning)
        out(DIV)
    return found


def strip_wikilink(name):
    return name.replace("[[", "").replace("]]", "").strip()
