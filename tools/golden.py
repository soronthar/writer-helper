"""Pin legacy script behaviour against the layout-v1 fixture.

    python tools/golden.py capture [--scripts DIR]   # (re)write fixtures/golden/*.out
    python tools/golden.py check   [--scripts DIR] [--project DIR]

--scripts defaults to the fixture's own legacy scripts; pass `skills/writing-room/scripts` to test
the new ones. --project defaults to the legacy fixture; pass another layout-v1
project (e.g. examples/sample-project) to prove the same output from it. The
scripts must produce byte-identical normalised output. `capture` always uses
the legacy fixture.

A golden file records: exit code, stdout, stderr, and (for mutating cases) a
digest of the files created. Dates and absolute paths are normalised.
"""

import argparse
import difflib
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "fixtures" / "legacy-v1"
GOLDEN = REPO / "fixtures" / "golden"


def normalise(text, root):
    text = text.replace("\r\n", "\n")
    for variant in {str(root), str(root).replace("\\", "/"), root.as_posix()}:
        text = text.replace(variant, "<ROOT>")
    text = text.replace(date.today().isoformat(), "<DATE>")
    return text


def digest(root, rels):
    lines = []
    for rel in rels:
        base = root / rel
        for p in sorted((x for x in base.rglob("*") if x.is_file()), key=lambda x: x.as_posix().lower()):
            body = normalise(p.read_text(encoding="utf-8"), root)
            lines.append(f"{p.relative_to(root).as_posix()} {hashlib.sha256(body.encode()).hexdigest()[:16]}")
    return "\n".join(lines)


def run_case(case, scripts_dir, project=None):
    project = Path(project).resolve() if project else FIXTURE
    work = None
    root = project
    if case.get("mutating"):
        work = Path(tempfile.mkdtemp(prefix="wr-golden-"))
        root = work / "project"
        shutil.copytree(project, root)
        # legacy scripts chdir to their own project folder, so run the copy inside the throwaway project
        scripts = root / "scripts" if scripts_dir is None else Path(scripts_dir)
    else:
        scripts = FIXTURE / "scripts" if scripts_dir is None else Path(scripts_dir)
    try:
        proc = subprocess.run(
            [sys.executable, str(scripts / f"{case['script']}.py"), *case["args"]],
            cwd=root, capture_output=True, text=True, encoding="utf-8",
        )
        parts = [f"exit: {proc.returncode}",
                 "--- stdout ---", normalise(proc.stdout, root),
                 "--- stderr ---", normalise(proc.stderr, root)]
        if case.get("digest"):
            parts += ["--- files ---", digest(root, case["digest"])]
        return proc.returncode, "\n".join(parts)
    finally:
        if work:
            shutil.rmtree(work, ignore_errors=True)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", choices=["capture", "check"])
    ap.add_argument("--scripts", help="directory holding the scripts under test")
    ap.add_argument("--project", help="layout-v1 project to run against (default: legacy fixture)")
    args = ap.parse_args()

    if args.scripts:
        args.scripts = str(Path(args.scripts).resolve())
    cases = json.loads((GOLDEN / "cases.json").read_text(encoding="utf-8"))["cases"]
    failed = 0
    for case in cases:
        code, text = run_case(case, args.scripts, None if args.mode == "capture" else args.project)
        if code != 0 and not case.get("allow_nonzero"):
            print(f"ERROR  {case['name']}: exit {code}\n{text}")
            failed += 1
            continue
        target = GOLDEN / f"{case['name']}.out"
        if args.mode == "capture":
            target.write_bytes((text).encode("utf-8"))
            print(f"wrote  {case['name']}")
        elif not target.exists():
            print(f"MISSING {case['name']}")
            failed += 1
        else:
            want = target.read_text(encoding="utf-8")
            if want == text:
                print(f"ok     {case['name']}")
            else:
                failed += 1
                print(f"DIFF   {case['name']}")
                print("".join(list(difflib.unified_diff(
                    want.splitlines(True), text.splitlines(True), "golden", "actual"))[:40]))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
