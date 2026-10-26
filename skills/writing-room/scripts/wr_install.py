#!/usr/bin/env python3
"""wr_install.py — Install the Writing Room skills for a coding agent

Usage:
  python "<WR>/scripts/wr_install.py" --harness claude|devin|opencode|hermes|all[,..] \\
      [--scope project|user] [--project DIR] [--target DIR] [--guidance] \\
      [--dry-run] [--force] [--uninstall] [--list]

Copies every skill folder (the writing-room skill carries the scripts, templates and shared
references) into the place each harness reads skills from. Copies, never symlinks (symlinks are
unreliable on Windows). Project content (worlds/, stories/, ...) is never touched.

Scope: --scope project (the default) installs into one project; --scope user (or the shorthand --user)
installs for every project of that user. The output always says which scope was used.

Where skills go:

  harness   --scope project                              --scope user
  claude    <project>/.claude/skills                     ~/.claude/skills
  devin     <project>/.agents/skills                     ~/.config/devin/skills  (Windows: %APPDATA%\\devin\\skills)
  opencode  <project>/.opencode/skills                   ~/.config/opencode/skills
  hermes    <project>/.hermes/skills                     ~/.hermes/skills

Several harnesses read each other's folders: .claude/skills is read by Claude Code, Devin and OpenCode;
.agents/skills by Devin, OpenCode and Hermes. When you ask for several harnesses at project scope the
fewest folders that cover them all are used, avoiding two copies of the same skill names in folders one
tool reads (`--harness all` gives .claude/skills plus .hermes/skills).

Project-level discovery depends on where the tool thinks the project is: Hermes uses the nearest ancestor
containing .git, and Devin discovers skills in git repositories. If the project folder is not a git
repository root, the installer says so for the harnesses affected. Hermes also asks the user to approve
project skills once (`hermes skills trust`).

Safety: a skill folder that already exists and was not installed by this tool is never replaced
unless you pass --force. An install manifest (.writing-room-install.json) in each target records what
this tool installed, so updates replace only those folders and --uninstall removes only those.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import FRAMEWORK_DIR, ProjectNotFound, find_root  # noqa: E402

HARNESSES = ("claude", "devin", "opencode", "hermes")
MANIFEST = ".writing-room-install.json"
SKILLS_SRC = FRAMEWORK_DIR.parent

# project-scope folders and the harnesses that read them (each tool's own documentation, 2026-10-02)
PROJECT_DIRS = {
    ".claude/skills": {"claude", "devin", "opencode"},
    ".agents/skills": {"devin", "opencode", "hermes"},
    ".opencode/skills": {"opencode"},
    ".hermes/skills": {"hermes"},
}

# the folder each harness treats as its own; preferred when it costs nothing extra
NATIVE_DIR = {"claude": ".claude/skills", "devin": ".agents/skills", "opencode": ".opencode/skills",
              "hermes": ".hermes/skills"}

NOTES = {
    "project": {
        "claude": "Claude Code picks the skills up when it starts in this project.",
        "devin": "Commit the folder so Devin sessions that clone the repository discover the skills.",
        "opencode": "OpenCode walks up from the working directory to the git root, so any subfolder finds them.",
        "hermes": "Hermes finds <repository>/.hermes/skills. Approve project skills once: run `hermes skills trust` "
                  "in the repository.",
    },
    "user": {
        "claude": "Claude Code picks the skills up in every project.",
        "devin": "Devin picks the skills up in every project.",
        "opencode": "OpenCode picks the skills up in every project.",
        "hermes": "Hermes reads ~/.hermes/skills at start-up.",
    },
}


def folder_hash(path):
    """Content hash of a skill folder, stable between a source folder and an installed copy.

    Covers relative paths and file bytes; ignores what installing ignores (__pycache__, *.pyc), because
    running an installed script creates those and they are not part of the skill."""
    path = Path(path)
    h = hashlib.sha256()
    for f in sorted((x for x in path.rglob("*") if x.is_file() and "__pycache__" not in x.parts and x.suffix != ".pyc"),
                    key=lambda x: x.relative_to(path).as_posix()):
        h.update(f.relative_to(path).as_posix().encode("utf-8") + b"\0")
        h.update(f.read_bytes() + b"\0")
    return h.hexdigest()[:16]


class Source:
    """A build of the Writing Room: a `skills/` folder with writing-room (the runtime) beside the others."""

    def __init__(self, skills_dir=None):
        self.root = Path(skills_dir or SKILLS_SRC).resolve()
        self.wr = self.root / "writing-room"

    def names(self):
        data = json.loads((self.wr / "shared" / "skills.json").read_text(encoding="utf-8"))
        return list(data["skills"])

    def version(self):
        try:
            return (self.wr / "VERSION").read_text(encoding="utf-8").strip()
        except OSError:
            return "unknown"

    def layout(self):
        """The project layout number this build understands (read from its common.py)."""
        try:
            m = re.search(r"^SUPPORTED_LAYOUT\s*=\s*(\d+)", (self.wr / "scripts" / "common.py").read_text(encoding="utf-8"), re.M)
            return int(m.group(1)) if m else None
        except OSError:
            return None

    def check(self):
        missing = [n for n in self.names() if not (self.root / n / "SKILL.md").is_file()]
        if missing:
            raise SystemExit(f"Error: skill folder(s) missing next to writing-room in {self.root}: {', '.join(missing)}")

    def hashes(self):
        return {n: folder_hash(self.root / n) for n in self.names()}


def skill_names():
    return Source().names()


def framework_version():
    return Source().version()


def copy_skill(src_dir, dest, directory, name):
    """Copy a skill folder into place through a temporary sibling, replacing any existing folder."""
    tmp = directory / f".wr-tmp-{name}"
    if tmp.exists():
        shutil.rmtree(tmp)
    shutil.copytree(src_dir, tmp, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if dest.exists():
        shutil.rmtree(dest)
    tmp.rename(dest)


def user_dir(harness, env=None):
    env = os.environ if env is None else env
    home = Path(env.get("USERPROFILE") or env.get("HOME") or Path.home()) if os.name == "nt" else \
        Path(env.get("HOME") or Path.home())
    xdg = Path(env["XDG_CONFIG_HOME"]) if env.get("XDG_CONFIG_HOME") else home / ".config"
    if harness == "claude":
        return home / ".claude" / "skills"
    if harness == "devin":
        if os.name == "nt":
            appdata = env.get("APPDATA")
            return (Path(appdata) if appdata else home / "AppData" / "Roaming") / "devin" / "skills"
        return xdg / "devin" / "skills"
    if harness == "opencode":
        return xdg / "opencode" / "skills"
    if harness == "hermes":
        return home / ".hermes" / "skills"
    raise ValueError(harness)


def plan_targets(harnesses, scope, project=None, env=None):
    """Return a list of (directory, covered_harnesses). One copy per distinct directory."""
    want = set(harnesses)
    targets = []
    if scope == "user":
        for h in HARNESSES:
            if h not in want:
                continue
            # OpenCode also reads ~/.claude/skills, so no second copy when Claude Code is installed there
            if h == "opencode" and "claude" in want:
                continue
            d = user_dir(h, env)
            covers = {h} | ({"opencode"} if h == "claude" and "opencode" in want else set())
            targets.append((d, covers))
        return targets

    return plan_project_targets(want, Path(project))


def plan_project_targets(want, project):
    """Fewest project folders that cover every wanted harness, avoiding folders that would give a harness
    two copies of the same skills. Ties go to the order of PROJECT_DIRS."""
    from itertools import combinations
    dirs = list(PROJECT_DIRS)
    best = None
    for n in range(1, len(dirs) + 1):
        for combo in combinations(dirs, n):
            covered = set().union(*(PROJECT_DIRS[d] for d in combo))
            if not want <= covered:
                continue
            duplicates = sum(max(0, sum(1 for d in combo if h in PROJECT_DIRS[d]) - 1) for h in want)
            useful = all(PROJECT_DIRS[d] & want for d in combo)
            foreign = sum(1 for d in combo if d not in {NATIVE_DIR[h] for h in want})
            key = (not useful, n, duplicates, foreign, [dirs.index(d) for d in combo])
            if best is None or key < best[0]:
                best = (key, combo)
    combo = best[1]
    targets = []
    claimed = set()
    for d in combo:
        covers = (PROJECT_DIRS[d] & want) - claimed
        claimed |= covers
        targets.append((project / Path(d), covers or (PROJECT_DIRS[d] & want)))
    return targets


def git_root(start):
    """Nearest ancestor (or the folder itself) that contains .git (a folder, or a file for worktrees)."""
    start = Path(start).resolve()
    for d in (start, *start.parents):
        if (d / ".git").exists():
            return d
    return None


def location_warnings(project, harnesses):
    """Warnings about tools that look for project skills at the repository root."""
    project = Path(project).resolve()
    root = git_root(project)
    out = []
    needs_repo = [h for h in ("hermes", "devin") if h in harnesses]
    if root is None:
        for h in needs_repo:
            why = ("finds the project as the nearest folder containing .git" if h == "hermes"
                   else "discovers project skills in git repositories")
            out.append(f"{h}: {project} is not inside a git repository, and {h} {why}. "
                       "Run `git init`, or use --scope user.")
    elif root != project:
        for h in needs_repo:
            out.append(f"{h}: the git repository root is {root}, not {project}; {h} looks for project skills at "
                       f"the repository root. Install there with --project \"{root}\" (the scripts still find "
                       "your writing project from where you work), or use --scope user.")
    return out, root


def read_manifest(directory):
    try:
        return json.loads((directory / MANIFEST).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"skills": []}


def write_manifest(directory, names, version=None):
    """Record what this tool installed, with a content hash per skill folder as installed, so a later
    update can tell a locally edited skill from an untouched one."""
    names = sorted(names)
    data = {"tool": "wr_install", "version": version or framework_version(), "skills": names,
            "hashes": {n: folder_hash(directory / n) for n in names if (directory / n).is_dir()}}
    (directory / MANIFEST).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")


def install_into(directory, dry_run=False, force=False, log=print, src=None):
    """Install all skills into directory. Returns (installed, conflicts)."""
    src = src or Source()
    names = src.names()
    src.check()
    manifest = read_manifest(directory)
    ours = set(manifest.get("skills", []))
    installed, conflicts = [], []
    log(f"  {directory}")
    if not dry_run:
        directory.mkdir(parents=True, exist_ok=True)
    for n in names:
        dest = directory / n
        action = "install"
        if dest.exists():
            if n in ours or force:
                action = "replace" if n in ours else "replace (--force, not installed by this tool)"
            else:
                log(f"    SKIP {n}: {dest} exists and was not installed by this tool (use --force to replace it)")
                conflicts.append(n)
                continue
        log(f"    {'would ' if dry_run else ''}{action} {n}")
        if dry_run:
            installed.append(n)
            continue
        copy_skill(src.root / n, dest, directory, n)
        installed.append(n)
    if not dry_run and installed:
        write_manifest(directory, ours | set(installed), src.version())
    return installed, conflicts


def uninstall_from(directory, dry_run=False, log=print):
    manifest = read_manifest(directory)
    names = manifest.get("skills", [])
    log(f"  {directory}")
    if not names:
        log("    nothing installed by this tool")
        return []
    removed = []
    for n in names:
        dest = directory / n
        if dest.exists():
            log(f"    {'would remove' if dry_run else 'remove'} {n}")
            if not dry_run:
                shutil.rmtree(dest)
            removed.append(n)
    if not dry_run:
        try:
            (directory / MANIFEST).unlink()
        except OSError:
            pass
    return removed


def hermes_snippet(directory):
    return ("  Add this to your Hermes config.yaml:\n"
            "    skills:\n"
            "      external_dirs:\n"
            f"        - {Path(directory).as_posix()}")


def parse_harnesses(value):
    items = [x.strip().lower() for x in value.split(",") if x.strip()]
    if "all" in items:
        return list(HARNESSES)
    bad = [x for x in items if x not in HARNESSES]
    if bad:
        raise SystemExit(f"Error: unknown harness {', '.join(bad)} (choose from {', '.join(HARNESSES)}, all)")
    return items


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", newline="\n")
    ap = argparse.ArgumentParser(description="Install the Writing Room skills", allow_abbrev=False)
    ap.add_argument("--harness", required=True, help="claude, devin, opencode, hermes, all, or a comma list")
    ap.add_argument("--scope", choices=("project", "user"), default="project",
                    help="project: this project only (default); user: every project of this user")
    ap.add_argument("--user", action="store_true", help="shorthand for --scope user")
    ap.add_argument("--project", help="project folder for --scope project (default: the discovered project)")
    ap.add_argument("--target", help="install into this folder instead (one copy, whatever the harness)")
    ap.add_argument("--guidance", action="store_true",
                    help="also add AGENTS.md and CLAUDE.md to the project root if absent (project scope)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="replace skill folders this tool did not install")
    ap.add_argument("--uninstall", action="store_true", help="remove what this tool installed")
    ap.add_argument("--list", action="store_true", help="show where skills would go and what is installed")
    a = ap.parse_args(argv)
    harnesses = parse_harnesses(a.harness)
    if a.user:
        if a.scope == "project" and "--scope" in (argv if argv is not None else sys.argv):
            ap.error("--user conflicts with --scope project")
        a.scope = "user"

    project = None
    if a.target:
        targets = [(Path(a.target), set(harnesses))]
    elif a.scope == "project":
        try:
            project = Path(a.project).resolve() if a.project else find_root()[0]
        except ProjectNotFound:
            print("Error: no project found. Pass --project DIR, run inside a project, or use --scope user.",
                  file=sys.stderr)
            return 2
        targets = plan_targets(harnesses, "project", project)
    else:
        targets = plan_targets(harnesses, "user")

    if a.list:
        for d, covers in targets:
            m = read_manifest(d)
            state = f"{len(m.get('skills', []))} skill(s) installed" if (d / MANIFEST).exists() else "not installed"
            print(f"{d}  [{', '.join(sorted(covers))}]  {state}")
        return 0

    scope_label = f"custom folder (--target)" if a.target else (
        f"project scope ({project})" if a.scope == "project" and project else "user scope")
    print(f"Writing Room {framework_version()} — {'uninstalling from' if a.uninstall else 'installing into'} "
          f"{scope_label}:")
    problems = 0
    for d, covers in targets:
        if a.uninstall:
            uninstall_from(d, a.dry_run)
            continue
        _, conflicts = install_into(d, a.dry_run, a.force)
        problems += len(conflicts)
        for h in sorted(covers):
            print(f"    {h}: {NOTES['project' if (a.scope == 'project' or a.target) else 'user'][h]}")

    if not a.uninstall and project is not None and not a.target:
        warns, root = location_warnings(project, set(harnesses))
        for w in warns:
            print(f"  warning: {w}")
        hermes_dirs = [d for d, covers in targets if "hermes" in covers]
        if hermes_dirs and any(w.startswith("hermes:") for w in warns):
            print("  Alternatively, if you cannot install at the repository root, list the folder in Hermes's config:")
            print(hermes_snippet(hermes_dirs[0]))

    if a.guidance and not a.uninstall and project is not None:
        for name in ("AGENTS.md", "CLAUDE.md"):
            src, dst = FRAMEWORK_DIR / "shared" / "project" / name, project / name
            if dst.exists():
                print(f"  guidance: {name} already exists, left alone")
            else:
                print(f"  guidance: {'would add' if a.dry_run else 'add'} {name}")
                if not a.dry_run:
                    shutil.copy2(src, dst)
    elif a.guidance and project is None:
        print("  guidance: only added for --scope project", file=sys.stderr)

    if a.dry_run:
        print("\nDry run: nothing changed.")
    if problems:
        print(f"\n{problems} skill folder(s) were not installed because they already exist and are not "
              "ours. Re-run with --force to replace them.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
