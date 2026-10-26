"""First-pass converter: legacy Claude Code agent/command markdown -> portable SKILL.md.

    python tools/convert_legacy.py <legacy .md file> [--out skills]

Mechanical only: swaps the frontmatter for name/description, drops model/tools, removes the
legacy Writing_Room/ prefix, and rewrites the most common tool-name phrases. The output
is a starting point; run tools/lint_skills.py and finish by hand. Never overwrites an
existing SKILL.md.
"""

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

REWRITES = [
    (r"Writing_Room/", ""),
    (r"\bGlob\b `", "List files matching `"),
    (r"\bGlob to\b", "List the files to"),
    (r"\bGlob\b", "List files"),
    (r"\bGrep\b", "Search"),
    (r"Use Bash `cp` to copy", "Copy"),
    (r"^(#\s+)/", r"\1"),
    (r"(?<![\w`])/(story-status|promote-chapter|create-world|create-style)\b", r"`\1`"),
    (r"\*\*(Story Analyzer|Draft Writer|Draft Fixer|Story Ideator|Writing Assistant|World Archivist|Outliner|Planner|Reviewer)\*\*", r"\1"),
    (r"\bReviewer agents\b", "Reviewer"),
    (r"\bStory Analyzer\b", "`story-analyzer`"),
    (r"(?<!for )(?<!for the )\bDraft Writer\b", "`draft-writer`"),  # keep template headings such as "Notes for the Draft Writer"
    (r"\bDraft Fixer\b", "`draft-fixer`"),
    (r"\bStory Ideator\b", "`story-ideator`"),
    (r"\bWriting Assistant\b", "`writing-assistant`"),
    (r"\bWorld Archivist\b", "`world-archivist`"),
    (r"(?<!expand after )\bOutliner\b", "`outliner`"),  # data text written into WORLD_ORDER rows
    (r"(?<!for the )\bPlanner\b", "`planner`"),  # output label "Flags for the Planner"
    (r"(?<![\w`-])Reviewer(?![\w`-])(?! Notes)", "`reviewer`"),  # keep the template heading "Reviewer Notes"
]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = REPO / "skills"
    if "--out" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--out") + 1])
        args = [a for a in args if a != str(out)]
    src = Path(args[0])
    text = src.read_text(encoding="utf-8")
    m = re.match(r"---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    fm, body = (m.group(1), text[m.end():]) if m else ("", text)
    desc = re.search(r"^description:\s*(.+)$", fm, re.M)
    desc = (desc.group(1).strip() if desc else "TODO").strip("\"'")
    name = src.stem.lower().replace("_", "-")
    for rx, rep in REWRITES:
        body = re.sub(rx, rep, body, flags=re.M)
    dst = out / name / "SKILL.md"
    if dst.exists():
        sys.exit(f"{dst} exists; not overwriting")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes((f"---\nname: {name}\ndescription: {json.dumps(desc, ensure_ascii=False)}\n---\n{body}").encode("utf-8"))
    print(dst)


if __name__ == "__main__":
    main()
