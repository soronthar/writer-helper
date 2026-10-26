"""Lint the skills in skills/ for portability across Claude Code, Devin, Hermes Agent and OpenCode.

    python tools/lint_skills.py [SKILLS_DIR]        # default: skills/

Checks (errors fail the run, warnings do not):
  - every skill folder has SKILL.md with YAML frontmatter
  - frontmatter keys limited to name, description, license, compatibility, metadata
  - name matches ^[a-z0-9]+(-[a-z0-9]+)*$, is 1-64 chars, and equals the folder name
  - description present, single paragraph, at most 1024 characters
  - body has no harness-specific wording: tool names (Glob, Grep, "Bash", "Write tool", ...),
    subagent delegation ("invoke the X agent", "Task tool"), slash-command syntax for skills,
    pinned model ids, or the legacy "Writing_Room/" root
  - wiki-links that point at paths ([[dir/file]]) are errors; entity links like [[Name]] are data and allowed
  - `references/...` and `../<skill>/...` paths named in SKILL.md exist
  - SKILL.md longer than 500 lines is a warning (split into references/)
"""

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ALLOWED_KEYS = {"name", "description", "license", "compatibility", "metadata"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

BANNED = [
    (re.compile(r"\b(Glob|Grep)\b"), "tool name '{0}' (say 'list files matching' / 'search for')"),
    (re.compile(r"\bBash\b"), "tool name 'Bash' (say 'run the command'; shell may be unavailable)"),
    (re.compile(r"\b(Write|Read|Edit) tool\b|\b(using|Use) (the )?(Write|Read|Edit)\b"), "tool name '{0}'"),
    (re.compile(r"\bTask tool\b|\bsubagent\b", re.I), "subagent wording '{0}'"),
    (re.compile(r"\b[Ii]nvoke (the )?\*{0,2}[A-Z][\w -]*\*{0,2} agent\b"), "agent delegation '{0}' (say 'follow the <name> skill')"),
    (re.compile(r"(?<![\w`])/(story-status|promote-chapter|create-world|create-style)\b"), "slash command '{0}' (refer to the skill by name)"),
    (re.compile(r"claude-(opus|sonnet|haiku)-[\w.-]+"), "pinned model id '{0}'"),
    (re.compile(r"Writing_Room/"), "legacy root path 'Writing_Room/'"),
    (re.compile(r"\[\[[^\]]*/[^\]]*\]\]"), "wiki-link to a path '{0}'"),
]


def parse_frontmatter(text):
    m = re.match(r"---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    if not m:
        return None, text
    fm, key = {}, None
    for line in m.group(1).splitlines():
        if re.match(r"^[A-Za-z_][\w-]*:", line):
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()
        elif key and line.startswith((" ", "\t")):
            fm[key] = (fm[key] + " " + line.strip()).strip()
    return fm, text[m.end():]


def strip_code_fences(body):
    """Banned-wording checks apply to instructions, not to fenced output templates."""
    return re.sub(r"```.*?```", "", body, flags=re.S)


def lint(skills_dir):
    errors, warnings = [], []
    for d in sorted(p for p in Path(skills_dir).iterdir() if p.is_dir()):
        def err(msg, d=d):
            errors.append(f"{d.name}: {msg}")

        def warn(msg, d=d):
            warnings.append(f"{d.name}: {msg}")

        skill = d / "SKILL.md"
        if not skill.is_file():
            err("missing SKILL.md")
            continue
        text = skill.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        if fm is None:
            err("no YAML frontmatter")
            continue
        for k in fm:
            if k not in ALLOWED_KEYS:
                err(f"frontmatter key '{k}' not allowed (allowed: {sorted(ALLOWED_KEYS)})")
        name = fm.get("name", "").strip("\"'")
        if not name:
            err("frontmatter has no name")
        else:
            if not NAME_RE.match(name) or not 1 <= len(name) <= 64:
                err(f"name '{name}' must match {NAME_RE.pattern} and be 1-64 chars")
            if name != d.name:
                err(f"name '{name}' does not match folder '{d.name}'")
        raw = fm.get("description", "")
        desc = raw
        if raw:
            # Unquoted YAML breaks on ': ' or ' #' inside the text, and harnesses then silently drop all
            # frontmatter. Require a JSON-style double-quoted string, which is always valid YAML.
            try:
                if not raw.startswith('"'):
                    raise ValueError("not quoted")
                desc = json.loads(raw)
            except ValueError:
                err("description must be a double-quoted string (unquoted text with ': ' is invalid YAML)")
                desc = raw.strip("\"'")
        if not desc:
            err("frontmatter has no description")
        elif len(desc) > 1024:
            err(f"description is {len(desc)} chars (max 1024)")

        sources = [("body", body)] + [
            (f"references/{r.name}", r.read_text(encoding="utf-8")) for r in sorted((d / "references").glob("*.md"))
        ]
        for label, src in sources:
            prose = strip_code_fences(src)
            for rx, msg in BANNED:
                for m in rx.finditer(prose):
                    line = prose[: m.start()].count("\n") + 1
                    err(f"{msg.format(m.group(0))} ({label}, ~line {line})")
        for ref in sorted(set(re.findall(r"`(references/[^`\s]+)`", body))):
            if not (d / ref).is_file():
                err(f"referenced file '{ref}' does not exist")
        for rel in sorted(set(re.findall(r"`(\.\./[\w-]+/[^`\s]+)`", body))):
            if not (d / rel).exists():
                err(f"referenced path '{rel}' does not exist")
        if text.count("\n") > 500:
            warn(f"SKILL.md has {text.count(chr(10))} lines; move detail into references/")
    return errors, warnings


def main():
    skills = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "skills"
    errors, warnings = lint(skills)
    for w in warnings:
        print(f"warn   {w}")
    for e in errors:
        print(f"ERROR  {e}")
    n = len([p for p in skills.iterdir() if p.is_dir()])
    print(f"{n} skill(s): {len(errors)} error(s), {len(warnings)} warning(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
