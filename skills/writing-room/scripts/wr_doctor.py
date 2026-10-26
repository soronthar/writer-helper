#!/usr/bin/env python3
"""wr_doctor.py — Diagnose a Writing Room installation and project

Usage:
  python scripts/wr_doctor.py [--root DIR] [--json]

Reports the Python version, the framework directory and its shared files, how
the project root was found, the marker/layout, and every layout-v1 problem
(errors) or oddity (warnings, including a possibly stale SUMMARY.md).
Read-only. Exit code 0 if there are no errors, 1 if there are, 2 if no project was found.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import FRAMEWORK_DIR, MARKER, SUPPORTED_LAYOUT, ProjectNotFound, check_layout, find_root, make_parser, read_marker  # noqa: E402
from wr_layout import check  # noqa: E402

MIN_PYTHON = (3, 9)
SHARED_REQUIRED = ("templates/world/character.md", "templates/story/concept.md",
                   "craft/story_structure/GUIDE.md")


def main():
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", newline="\n")
    p = make_parser("Diagnose a Writing Room installation and project")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    a = p.parse_args()

    errors, warnings, info = [], [], {}
    info["python"] = ".".join(map(str, sys.version_info[:3]))
    if sys.version_info < MIN_PYTHON:
        errors.append(f"Python {'.'.join(map(str, MIN_PYTHON))}+ required, found {info['python']}")

    info["framework"] = str(FRAMEWORK_DIR)
    missing = [f for f in SHARED_REQUIRED if not (FRAMEWORK_DIR / "shared" / f).is_file()]
    if missing:
        errors.append("framework shared/ is incomplete, missing: " + ", ".join(missing))

    # Skills reference each other and this skill as siblings (../writing-room/, ../planner/ ...), so
    # a harness that installed only some of them breaks those references.
    try:
        expected = json.loads((FRAMEWORK_DIR / "shared" / "skills.json").read_text(encoding="utf-8"))["skills"]
        absent = [n for n in expected if not (FRAMEWORK_DIR.parent / n / "SKILL.md").is_file()]
        info["skills_dir"] = str(FRAMEWORK_DIR.parent)
        if absent:
            errors.append("skills missing next to writing-room (install them together): " + ", ".join(absent))
    except (OSError, ValueError, KeyError):
        warnings.append("shared/skills.json could not be read; skipped the installed-skills check")

    root = None
    try:
        root, how = find_root(explicit=a.root)
        check_layout(root)
        info["root"], info["found_via"] = str(root), how
    except ProjectNotFound as e:
        info["root"] = None
        errors.append(str(e))

    if root is not None:
        marker = root / MARKER
        if marker.is_file():
            info["layout"] = read_marker(marker).get("layout")
        else:
            info["layout"] = f"{SUPPORTED_LAYOUT} (legacy, no marker; wr_migrate.py adds one)"
        e, w = check(root)
        errors += e
        warnings += w
        # Old framework files inside the project sit beside the new skills and confuse an agent that sees both.
        old = [rel for rel in (".claude/agents", ".claude/commands", "room_rules") if (root / rel).exists()]
        if (root / "scripts" / "load_bible.py").exists():
            old.append("scripts")
        if old:
            warnings.append("old framework files are still in the project (" + ", ".join(old) + "); once the new "
                            "skills are installed, `wr_migrate.py --retire-legacy` moves them aside (reversible)")

    if a.json:
        print(json.dumps({"info": info, "errors": errors, "warnings": warnings}, indent=2))
    else:
        for k, v in info.items():
            print(f"{k:10}: {v}")
        for w in warnings:
            print(f"warn   {w}")
        for e in errors:
            print(f"ERROR  {e}")
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    if info["root"] is None:
        return 2
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
