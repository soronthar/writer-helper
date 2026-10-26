"""Shared helpers for the Writing Room scripts.

Every script imports this module and calls setup() first. All paths handled by
the scripts are relative to Writing_Room/, which setup() makes the working
directory regardless of where the script is invoked from.
"""

import argparse
import os
import sys
from pathlib import Path

DIV = "═" * 60


def setup():
    """Force UTF-8/LF output (Windows defaults to cp1252/CRLF) and cd to Writing_Room/."""
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", newline="\n")
    os.chdir(Path(__file__).resolve().parent.parent)


def make_parser(description):
    return argparse.ArgumentParser(description=description, allow_abbrev=False)


def out(text=""):
    print(text)


def cat(path):
    """Write a file's contents to stdout unchanged (like `cat`)."""
    with open(path, encoding="utf-8", newline="") as fh:
        sys.stdout.write(fh.read())


def md_files(directory):
    """Sorted *.md files directly inside directory, as 'dir/name.md' strings."""
    d = Path(directory)
    if not d.is_dir():
        return []
    return [f"{directory}/{p.name}" for p in sorted(d.glob("*.md")) if p.is_file()]


def stem(path):
    return Path(path).stem


def print_file(label, path):
    """Print a file under a labelled header; emit a NOT FOUND warning if missing."""
    out()
    out(DIV)
    if Path(path).is_file():
        out(f"FILE: {label}")
        out(DIV)
        cat(path)
    else:
        out(f"FILE: {label}  ⚠ NOT FOUND — {path}")
        out(DIV)


def resolve_snapshot(world, position):
    """Return the snapshots/<position> dir, or '' (after printing a warning) if absent."""
    if not position:
        return ""
    candidate = f"{world}/snapshots/{position}"
    if Path(candidate).is_dir():
        return candidate
    out()
    out(DIV)
    out(f"POSITION {position}: ⚠ No snapshot found at {candidate} — falling back to current world")
    out(DIV)
    return ""


def strip_wikilink(name):
    return name.replace("[[", "").replace("]]", "").strip()
