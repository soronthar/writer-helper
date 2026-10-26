"""Check that nothing of an author's private fiction is in this repository, before publishing it.

    python tools/check_public_clean.py --source "<path to the author's original Writing_Room>"
    python tools/check_public_clean.py --names-file names.txt
    python tools/check_public_clean.py --source ... --history       # also search git history

The names to look for are not stored in this repository. They are derived from the author's own
project: every world folder, story folder, and character / faction / location / myth file name under
worlds/ and stories/<story>/state/bible/. Matches are whole-word. Every tracked file (git ls-files) is
scanned. With --tokens the individual words of multi-word names (4+ letters, capitalised) are reported too,
as advisory hints for a human to review (they include ordinary words).

Exit code 0 if no name appears, 1 otherwise. History is checked with `git log --all -S<name>`; a
repository whose history contains a name must not be published as is (use tools/export_public.py).
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITY_DIRS = ("characters", "factions", "mythology", "points_of_interest")


def names_from_source(source):
    source = Path(source)
    names = set()
    for kind in ("worlds", "stories"):
        base = source / kind
        if base.is_dir():
            names.update(d.name for d in base.iterdir() if d.is_dir())
    for md in source.glob("worlds/*/*/*.md"):
        if md.parent.name in ENTITY_DIRS:
            names.add(md.stem)
    for md in source.glob("stories/**/state/bible/*/*.md"):
        if md.parent.name in ENTITY_DIRS:
            names.add(md.stem)
    return {n for n in names if len(n) >= 4}


def names_from_file(path):
    return {line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")}


def tracked_files(root):
    out = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=root, capture_output=True, text=True, encoding="utf-8")
    return [f for f in out.stdout.split("\0") if f]


def scan_tree(root, names, files=None):
    """Return {file: [names found]} for whole-word, case-sensitive matches in text files."""
    root = Path(root)
    patterns = {n: re.compile(r"(?<!\w)" + re.escape(n) + r"(?!\w)") for n in names}
    hits = {}
    for rel in (files if files is not None else tracked_files(root)):
        p = root / rel
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        found = sorted(n for n, rx in patterns.items() if rx.search(text))
        if found:
            hits[rel] = found
    return hits


def tokens_of(names):
    toks = set()
    for n in names:
        for w in re.findall(r"[A-Z][a-z']{3,}", n):
            toks.add(w)
    return toks - names


def scan_history(root, names):
    """Names that appear anywhere in git history, with the first commit that has them."""
    found = {}
    for n in sorted(names):
        r = subprocess.run(["git", "log", "--all", "--format=%h", "-S", n], cwd=root, capture_output=True,
                           text=True, encoding="utf-8")
        commits = r.stdout.split()
        if commits:
            found[n] = commits
    return found


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source", help="the author's original project folder (names are derived from it)")
    ap.add_argument("--names-file", help="a text file with one name per line")
    ap.add_argument("--history", action="store_true", help="also search git history")
    ap.add_argument("--root", default=str(REPO), help="repository to check (default: this one)")
    ap.add_argument("--tokens", action="store_true", help="also report individual words of multi-word names (advisory)")
    a = ap.parse_args()
    root = Path(a.root).resolve()

    names = set()
    if a.source:
        names |= names_from_source(a.source)
    if a.names_file:
        names |= names_from_file(a.names_file)
    if not names:
        ap.error("give --source or --names-file")
    print(f"checking {len(names)} names against {len(tracked_files(root))} tracked files")

    bad = False
    hits = scan_tree(root, names)
    for f, found in sorted(hits.items()):
        bad = True
        print(f"FOUND  {f}: {', '.join(found)}")
    if a.tokens:
        for f, found in sorted(scan_tree(root, tokens_of(names)).items()):
            print(f"token  {f}: {', '.join(found)}")
    if a.history:
        hist = scan_history(root, names)
        for n, commits in hist.items():
            bad = True
            print(f"HISTORY '{n}' appears in {len(commits)} commit(s), e.g. {commits[0]}")
    print("clean" if not bad else "NOT CLEAN")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
