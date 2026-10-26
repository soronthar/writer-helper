#!/usr/bin/env python3
"""wr_update.py — Update installed Writing Room skills to a newer build

Usage:
  python "<WR>/scripts/wr_update.py" [--project DIR] [--user] [--target DIR ...] [--source SKILLS_DIR]
                                     [--check] [--dry-run] [--force] [--no-backup] [--guidance]
                                     [--allow-downgrade]

Run it from the NEW build (a fresh checkout or release): the skills next to this script are the new
version. It finds the installs that wr_install.py made (each has a .writing-room-install.json),
compares them with this build, and brings them up to date:

  - skills whose content changed are replaced; skills new in this build are added; skills this build
    no longer has are removed (only ones the installer put there)
  - a skill you edited locally is saved first to <skills folder's parent>/.writing-room-backups/<time>/
    (and so is anything replaced when the install is old enough not to record hashes)
  - skill folders that are not ours are never touched; a new skill whose name collides with one of
    yours is skipped and reported (--force replaces it)
  - worlds, stories, styles and templates are never touched
  - the CHANGELOG entries since the installed version are shown when the build has a CHANGELOG.md
  - AGENTS.md and CLAUDE.md in the project are compared with the shipped versions and reported if they
    differ; --guidance replaces them (the old file is kept as <name>.bak)

Where it looks: the project's skill folders (--project DIR, default the project you are in), and with
--user also the user-level folders; --target DIR names a skills folder directly (repeatable).
--source SKILLS_DIR updates from another build's skills/ folder, for example to update using an
already-installed older copy of this script.

--check changes nothing and exits 1 if any install is out of date (0 if all are current, 2 if none were
found). --dry-run prints what would happen. A build with an older version, or a project whose layout
is newer than this build understands, is refused (--allow-downgrade overrides the first only).
"""

import argparse
import re
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import MARKER, ProjectNotFound, find_root, read_marker  # noqa: E402
from wr_install import (HARNESSES, MANIFEST, PROJECT_DIRS, Source, copy_skill, folder_hash,  # noqa: E402
                        read_manifest, user_dir, write_manifest)

BACKUPS = ".writing-room-backups"


def parse_version(v):
    """(major, minor, patch, is_release, suffix) or None. A pre-release sorts before its release."""
    m = re.match(r"^v?(\d+)\.(\d+)\.(\d+)(?:[-+](.+))?$", str(v).strip())
    if not m:
        return None
    return (int(m[1]), int(m[2]), int(m[3]), 0 if m[4] else 1, m[4] or "")


def project_of(directory):
    """The project folder a project-level skills folder belongs to, or None (user-level or custom)."""
    posix = Path(directory).as_posix()
    for rel in PROJECT_DIRS:
        if posix.endswith("/" + rel):
            return Path(posix[: -len(rel) - 1])
    return None


def find_instances(project=None, user=False, targets=(), env=None):
    """[(directory, label)] of skills folders with an install manifest."""
    found, seen = [], set()

    def add(d, label):
        d = Path(d)
        key = str(d.resolve()) if d.exists() else str(d)
        if key not in seen and (d / MANIFEST).is_file():
            seen.add(key)
            found.append((d, label))

    if project:
        for rel in PROJECT_DIRS:
            add(Path(project) / rel, "project")
    if user:
        for h in HARNESSES:
            add(user_dir(h, env), "user")
    for t in targets:
        add(t, "target")
    return found


def changelog_since(src, installed):
    """Sections of the build's CHANGELOG.md newer than `installed` (empty if there is none or no version)."""
    path = src.root.parent / "CHANGELOG.md"
    have = parse_version(installed)
    if not path.is_file() or have is None:
        return []
    sections = re.split(r"(?m)^(?=## )", path.read_text(encoding="utf-8"))
    out = []
    for s in sections:
        m = re.match(r"## (\S+)", s)
        v = parse_version(m[1]) if m else None
        if v is not None and v > have:
            out.append(s.strip())
    return out


def plan_instance(directory, src):
    """Work out what an update would do to one install. Pure: touches nothing."""
    manifest = read_manifest(directory)
    ours = set(manifest.get("skills", []))
    recorded = manifest.get("hashes") or {}
    new_names = src.names()
    src_hashes = src.hashes()
    plan = {"directory": directory, "installed_version": manifest.get("version", "unknown"),
            "new_version": src.version(), "add": [], "update": [], "remove": [], "conflicts": [],
            "backup": [], "unchanged": [], "history_known": bool(recorded)}
    for n in new_names:
        dest = Path(directory) / n
        if n not in ours:
            (plan["conflicts"] if dest.exists() else plan["add"]).append(n)
            continue
        if not dest.is_dir():
            plan["update"].append(n)                      # ours, but the folder is gone: put it back
        elif folder_hash(dest) != src_hashes[n]:
            plan["update"].append(n)
            modified = recorded.get(n) is not None and folder_hash(dest) != recorded[n]
            if modified or not recorded:
                plan["backup"].append(n)
        else:
            plan["unchanged"].append(n)
    for n in sorted(ours - set(new_names)):
        if (Path(directory) / n).is_dir():
            plan["remove"].append(n)
            if recorded.get(n) is None or folder_hash(Path(directory) / n) != recorded[n]:
                plan["backup"].append(n)
    plan["needs_update"] = bool(plan["add"] or plan["update"] or plan["remove"]
                                or plan["installed_version"] != plan["new_version"])
    return plan


def apply_plan(plan, src, backup=True, force=False, log=print):
    directory = Path(plan["directory"])
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup_dir = directory.parent / BACKUPS / stamp / directory.name
    saved = []
    if backup:
        for n in plan["backup"]:
            if (directory / n).is_dir():
                backup_dir.mkdir(parents=True, exist_ok=True)
                shutil.copytree(directory / n, backup_dir / n, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
                saved.append(n)
        if saved:
            log(f"    saved a copy of {', '.join(saved)} to {backup_dir}")
    for n in plan["add"] + plan["update"]:
        copy_skill(src.root / n, directory / n, directory, n)
    for n in plan["remove"]:
        shutil.rmtree(directory / n)
    if force:
        for n in plan["conflicts"]:
            copy_skill(src.root / n, directory / n, directory, n)
    ours_after = (set(plan["add"]) | set(plan["update"]) | set(plan["unchanged"])
                  | (set(plan["conflicts"]) if force else set()))
    write_manifest(directory, ours_after, src.version())
    return saved


def guidance_report(project, src, replace, dry_run, log=print):
    """Compare AGENTS.md / CLAUDE.md with the shipped versions. Returns the names that differ."""
    differ = []
    for name in ("AGENTS.md", "CLAUDE.md"):
        shipped = src.wr / "shared" / "project" / name
        mine = Path(project) / name
        if not shipped.is_file() or not mine.is_file():
            continue
        if mine.read_bytes() == shipped.read_bytes():
            continue
        differ.append(name)
        if replace:
            log(f"    {'would replace' if dry_run else 'replacing'} {name} (the old one is kept as {name}.bak)")
            if not dry_run:
                shutil.copy2(mine, mine.with_name(name + ".bak"))
                shutil.copy2(shipped, mine)
        else:
            log(f"    {name} differs from the shipped version (yours may be customised); "
                "run with --guidance to replace it, keeping a .bak")
    return differ


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", newline="\n")
    ap = argparse.ArgumentParser(description="Update installed Writing Room skills", allow_abbrev=False)
    ap.add_argument("--project", help="project whose skill folders to update (default: the project you are in)")
    ap.add_argument("--user", action="store_true", help="also update user-level installs")
    ap.add_argument("--target", action="append", default=[], help="a skills folder to update (repeatable)")
    ap.add_argument("--source", help="skills/ folder of the build to update from (default: the one next to this script)")
    ap.add_argument("--check", action="store_true", help="report only; exit 1 if anything is out of date")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="also replace a same-named folder this tool did not install")
    ap.add_argument("--no-backup", action="store_true", help="do not save locally edited skills before replacing them")
    ap.add_argument("--guidance", action="store_true", help="replace AGENTS.md and CLAUDE.md with the shipped ones (.bak kept)")
    ap.add_argument("--allow-downgrade", action="store_true", help="allow installing an older build over a newer one")
    a = ap.parse_args(argv)

    src = Source(a.source)
    try:
        src.check()
    except SystemExit as e:
        print(e, file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError):
        print(f"Error: {src.root} does not look like a Writing Room build (no writing-room/shared/skills.json).",
              file=sys.stderr)
        return 2

    project = None
    if not a.user and not a.target or a.project:
        try:
            project = Path(a.project).resolve() if a.project else find_root()[0]
        except ProjectNotFound:
            if not a.user and not a.target:
                print("Error: no project found. Run inside a project, pass --project DIR, --user, or --target DIR.",
                      file=sys.stderr)
                return 2
    instances = find_instances(project, a.user, [Path(t) for t in a.target])
    if not instances:
        where = f"project {project}" if project else "the places searched"
        print(f"No Writing Room install (a folder with {MANIFEST}) found for {where}. Use wr_install.py first.",
              file=sys.stderr)
        return 2

    new_layout = src.layout()
    print(f"Writing Room build {src.version()} ({src.root})")
    outdated = problems = 0
    for directory, label in instances:
        print(f"\n{directory}  [{label}]")
        if Path(directory).resolve() == src.root:
            print("    this is the build being installed from; nothing to update")
            continue
        proj = project_of(directory)
        marker = (proj / MARKER) if proj else None
        if marker and marker.is_file() and new_layout is not None:
            layout = read_marker(marker).get("layout")
            if isinstance(layout, int) and layout > new_layout:
                print(f"    REFUSED: the project's layout is {layout}, newer than the {new_layout} this build understands")
                problems += 1
                continue
        plan = plan_instance(directory, src)
        have, new = parse_version(plan["installed_version"]), parse_version(plan["new_version"])
        if have and new and new < have and not a.allow_downgrade:
            print(f"    REFUSED: installed {plan['installed_version']} is newer than this build "
                  f"{plan['new_version']} (--allow-downgrade to go back)")
            problems += 1
            continue
        if plan["installed_version"] != plan["new_version"]:
            print(f"    version {plan['installed_version']} -> {plan['new_version']}")
        elif plan["needs_update"]:
            print(f"    version {plan['installed_version']} (content differs from this build)")
        for key, word in (("add", "add"), ("update", "update"), ("remove", "remove")):
            if plan[key]:
                print(f"    {word}: {', '.join(plan[key])}")
        if plan["conflicts"]:
            print(f"    SKIP {', '.join(plan['conflicts'])}: a folder with that name exists and was not installed "
                  f"by this tool" + (" (replacing: --force)" if a.force else " (use --force to replace)"))
            if not a.force:
                problems += 1
        if plan["backup"] and not a.no_backup:
            print(f"    will save before replacing: {', '.join(plan['backup'])}"
                  + ("" if plan["history_known"] else "  (this install predates edit tracking)"))
        if not plan["needs_update"] and not (plan["conflicts"] and a.force):
            print("    up to date")
        else:
            outdated += 1
            for section in changelog_since(src, plan["installed_version"]):
                print("    " + section.replace("\n", "\n    "))
            if not a.check and not a.dry_run:
                apply_plan(plan, src, backup=not a.no_backup, force=a.force, log=print)
                print("    updated")
        if proj and (a.guidance or not a.check):
            guidance_report(proj, src, a.guidance, a.dry_run or a.check)

    print()
    if a.check:
        print(f"{outdated} install(s) out of date." if outdated else "All installs are up to date.")
        return 1 if outdated or problems else 0
    if a.dry_run:
        print("Dry run: nothing changed.")
    elif outdated:
        print("Done. Check the result with wr_doctor.py; start a fresh agent session so it reloads the skills.")
    if problems:
        print(f"{problems} install(s) could not be fully updated; see above.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
