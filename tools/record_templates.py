#!/usr/bin/env python3
"""record_templates.py — Record the fingerprint of every shipped template and craft file

Usage:
  python tools/record_templates.py [--legacy-repo PATH] [--check]

Writes skills/writing-room/shared/template_history.json: for each logical project path
(templates/…, writing_concepts/story_structure/…, archetypes/…, tropes/…) the fingerprints of
every version the framework has shipped. wr_templates.py uses it to tell a project's unchanged
copy of an old template (safe to move aside) from one the author edited.

Sources, merged into what the file already holds (fingerprints are never removed):
  - the current skills/writing-room/shared/templates and shared/craft
  - fixtures/legacy-v1 (the original single-folder framework)
  - every commit of this repository that touched shared/templates or shared/craft
  - with --legacy-repo, every commit of that repository's Writing_Room/ framework files

Run it after changing any template or craft file; a test fails until you do.
--check only reports whether the current files are recorded (exit 1 if not).
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SHARED = REPO / "skills" / "writing-room" / "shared"
sys.path.insert(0, str(REPO / "skills" / "writing-room" / "scripts"))

from wr_templates import HISTORY_FILE, LOGICAL, fingerprint  # noqa: E402


def from_dir(base, mapping):
    """{logical path: fingerprint} for the files under base, with mapping [(logical prefix, dir under base)]."""
    found = {}
    for logical, sub in mapping:
        d = base / sub
        if d.is_dir():
            for f in sorted(d.rglob("*.md")):
                found.setdefault(f"{logical}/{f.relative_to(d).as_posix()}", set()).add(fingerprint(f.read_bytes()))
    return found


def from_git(repo, mapping):
    """{logical path: {fingerprints}} for every version of the mapped folders in a git repository's history."""
    dirs = [sub for _, sub in mapping]
    commits = subprocess.run(["git", "-C", str(repo), "log", "--format=%H", "--", *dirs],
                             capture_output=True, text=True, check=True).stdout.split()
    wanted = []
    for c in commits:
        names = subprocess.run(["git", "-C", str(repo), "ls-tree", "-r", "--name-only", c, "--", *dirs],
                               capture_output=True, text=True, encoding="utf-8", check=True).stdout.splitlines()
        for name in names:
            for logical, sub in mapping:
                if name.startswith(sub + "/") and name.endswith(".md"):
                    wanted.append((f"{logical}/{name[len(sub) + 1:]}", f"{c}:{name}"))
    found = {}
    if not wanted:
        return found
    batch = subprocess.run(["git", "-C", str(repo), "cat-file", "--batch"], capture_output=True, check=True,
                           input="".join(f"{spec}\n" for _, spec in wanted).encode("utf-8")).stdout
    pos = 0
    for logical, _ in wanted:
        header_end = batch.index(b"\n", pos)
        size = int(batch[pos:header_end].split()[2])
        body = batch[header_end + 1:header_end + 1 + size]
        pos = header_end + 1 + size + 1
        found.setdefault(logical, set()).add(fingerprint(body))
    return found


def merge(into, more):
    for k, v in more.items():
        into.setdefault(k, set()).update(v)


def main():
    p = argparse.ArgumentParser(description="Record shipped template and craft fingerprints")
    p.add_argument("--legacy-repo", help="a repository whose history holds the original Writing_Room/ framework")
    p.add_argument("--check", action="store_true", help="only check that the current files are recorded")
    a = p.parse_args()

    shared_map = [(logical, shared) for logical, shared in LOGICAL]
    current = from_dir(SHARED, shared_map)
    history = {}
    if HISTORY_FILE.is_file():
        history = {k: set(v) for k, v in json.loads(HISTORY_FILE.read_text(encoding="utf-8")).items()}
    if a.check:
        missing = sorted(k for k, v in current.items() if not v <= history.get(k, set()))
        for k in missing:
            print(f"not recorded: {k}")
        return 1 if missing else 0

    merge(history, current)
    merge(history, from_dir(REPO / "fixtures" / "legacy-v1", [(logical, logical) for logical, _ in LOGICAL]))
    merge(history, from_git(REPO, [(logical, f"skills/writing-room/shared/{shared}") for logical, shared in LOGICAL]))
    if a.legacy_repo:
        merge(history, from_git(Path(a.legacy_repo), [(logical, f"Writing_Room/{logical}") for logical, _ in LOGICAL]))
    data = {k: sorted(v) for k, v in sorted(history.items())}
    HISTORY_FILE.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{HISTORY_FILE.relative_to(REPO).as_posix()}: {len(data)} paths, "
          f"{sum(len(v) for v in data.values())} versions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
