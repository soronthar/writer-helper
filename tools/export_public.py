"""Publish the current tree of this repository without its history.

    python tools/export_public.py --dest DIR [--source "<author's own project>"] [--names-file F] [--allow-dirty] [--tag vX.Y.Z]
    python tools/export_public.py --update --dest CLONE [--source ...] [--names-file F] [--allow-dirty] --tag vX.Y.Z

Both modes copy every file git knows about or would add (tracked, plus untracked files that are not ignored).
Nothing is pushed and the working repository is not changed.

First release: DIR is initialised as a new repository on `main` with a single initial commit.

Later releases (--update): CLONE is the public repository (the first export, or a clone of what was pushed).
Its files are replaced with this tree, files that are no longer in this tree are removed, and the change is
one new commit ("Release vX.Y.Z") with the tag, on top of the public history. Pushing it needs no force.

Safety:
  - First release: DIR must not exist or must be empty.
  - --update: CLONE must be a git repository on `main` with no uncommitted changes, the tag must not exist
    there yet, and the tree must differ from what CLONE already has.
  - With --source or --names-file the tree is checked for those names (see check_public_clean.py) and the
    export stops if any is found: a first export leaves DIR uncommitted, an update leaves CLONE untouched.
  - Uncommitted changes in the working repository are refused unless --allow-dirty is given, so what you
    publish is what you committed.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_public_clean as cpc  # noqa: E402


def git(cwd, *args, check=True):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout


def identity(cwd):
    """-c options giving git a committer when none is configured (CI machines, fresh installs)."""
    have = git(cwd, "config", "user.name", check=False).strip() and git(cwd, "config", "user.email", check=False).strip()
    return [] if have else ["-c", "user.name=Writing Room export", "-c", "user.email=noreply@invalid"]


def export(repo, dest, names=None, allow_dirty=False, message="Initial commit", tag=None):
    repo, dest = Path(repo), Path(dest)
    if dest.exists() and any(dest.iterdir()):
        raise SystemExit(f"{dest} exists and is not empty.")
    if not allow_dirty and git(repo, "status", "--porcelain").strip():
        raise SystemExit("The working repository has uncommitted changes; commit them or use --allow-dirty.")
    files = cpc.tracked_files(repo)
    dest.mkdir(parents=True, exist_ok=True)
    for rel in files:
        src = repo / rel
        if not src.is_file():
            continue
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
    if names:
        hits = cpc.scan_tree(dest, names, files=files)
        if hits:
            for f, found in sorted(hits.items()):
                print(f"FOUND  {f}: {', '.join(found)}", file=sys.stderr)
            raise SystemExit(f"Export stopped: {len(hits)} file(s) contain private names. {dest} was left without a repository.")
    git(dest, "init", "-q", "-b", "main")
    git(dest, "add", "-A")
    git(dest, *identity(dest), "commit", "-q", "-m", message)
    if tag:
        git(dest, *identity(dest), "tag", "-a", tag, "-m", tag)
    return len(files)


def update(repo, dest, names=None, allow_dirty=False, tag=None, message=None):
    """Replace the public clone's tree with this one and commit it as one release. Returns (copied, removed)."""
    repo, dest = Path(repo), Path(dest)
    if not (dest / ".git").exists():
        raise SystemExit(f"{dest} is not a git repository; --update needs the public repository (the first export or a clone of it).")
    if git(dest, "rev-parse", "--abbrev-ref", "HEAD").strip() != "main":
        raise SystemExit(f"{dest} is not on main.")
    if git(dest, "status", "--porcelain").strip():
        raise SystemExit(f"{dest} has uncommitted changes; commit or discard them first.")
    if tag and git(dest, "tag", "--list", tag).strip():
        raise SystemExit(f"{dest} already has the tag {tag}.")
    if not allow_dirty and git(repo, "status", "--porcelain").strip():
        raise SystemExit("The working repository has uncommitted changes; commit them or use --allow-dirty.")
    files = [rel for rel in cpc.tracked_files(repo) if (repo / rel).is_file()]
    if names:
        hits = cpc.scan_tree(repo, names, files=files)   # before touching the clone, so a hit leaves it as it was
        if hits:
            for f, found in sorted(hits.items()):
                print(f"FOUND  {f}: {', '.join(found)}", file=sys.stderr)
            raise SystemExit(f"Export stopped: {len(hits)} file(s) contain private names. {dest} was not changed.")
    keep = set(files)
    removed = 0
    for rel in git(dest, "ls-files", "-z").split("\0"):
        if rel and rel not in keep:
            (dest / rel).unlink()
            removed += 1
            parent = (dest / rel).parent
            while parent != dest and parent.is_dir() and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent
    for rel in files:
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repo / rel, target)
    git(dest, "add", "-A")
    if not git(dest, "status", "--porcelain").strip():
        raise SystemExit(f"Nothing to release: {dest} already has this tree.")
    git(dest, *identity(dest), "commit", "-q", "-m", message or (f"Release {tag}" if tag else "Update"))
    if tag:
        git(dest, *identity(dest), "tag", "-a", tag, "-m", tag)
    return len(files), removed


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dest", required=True)
    ap.add_argument("--source", help="the author's own project; its names must not appear in the export")
    ap.add_argument("--names-file", help="file with one private name per line")
    ap.add_argument("--allow-dirty", action="store_true")
    ap.add_argument("--tag", help="also create this annotated tag on the new commit, e.g. v0.1.0")
    ap.add_argument("--update", action="store_true",
                    help="--dest is the existing public repository: add this tree to it as one release commit")
    a = ap.parse_args()
    if a.update and not a.tag:
        ap.error("--update needs --tag (each release is tagged)")
    names = set()
    if a.source:
        names |= cpc.names_from_source(a.source)
    if a.names_file:
        names |= cpc.names_from_file(a.names_file)
    if a.update:
        n, removed = update(REPO, a.dest, names or None, a.allow_dirty, tag=a.tag)
        print(f"updated {a.dest}: {n} files, {removed} removed, one commit 'Release {a.tag}' tagged {a.tag}")
    else:
        n = export(REPO, a.dest, names or None, a.allow_dirty, tag=a.tag)
        print(f"exported {n} files to {a.dest} as a new repository with one commit")
    if names:
        print(f"checked against {len(names)} private names: none found")
    else:
        print("note: no --source or --names-file given, so no check for private names was made")


if __name__ == "__main__":
    main()
