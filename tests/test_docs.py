"""Documentation and release-hygiene tests: links resolve, versions agree, license present, scripts named exist.

Run with:  python -m unittest discover -s tests -v
"""

import json
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "skills" / "writing-room" / "scripts"
DOCS = [REPO / "README.md", REPO / "CONTRIBUTING.md", REPO / "AGENTS.md", REPO / "CHANGELOG.md",
        *sorted((REPO / "docs").glob("*.md")), *sorted((REPO / "docs" / "development").glob("*.md"))]


class Links(unittest.TestCase):
    def test_relative_links_resolve(self):
        link = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
        problems = []
        for doc in DOCS:
            text = re.sub(r"```.*?```", "", doc.read_text(encoding="utf-8"), flags=re.S)
            for target in link.findall(text):
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                path = target.split("#", 1)[0]
                if path and not (doc.parent / path).exists():
                    problems.append(f"{doc.relative_to(REPO)}: {target}")
        self.assertEqual(problems, [])

    def test_in_page_anchors_exist_in_the_readme(self):
        text = (REPO / "README.md").read_text(encoding="utf-8")
        headings = {re.sub(r"[^a-z0-9 -]", "", h.lower()).strip().replace(" ", "-")
                    for h in re.findall(r"^#+\s+(.*)$", text, flags=re.M)}
        for anchor in re.findall(r"\]\(#([^)]+)\)", text):
            self.assertIn(anchor, headings, anchor)

    def test_scripts_named_in_docs_exist(self):
        scripts = {p.name for p in SCRIPTS.glob("*.py")}
        for doc in DOCS:
            if doc.name in ("CHANGELOG.md",) or "development" in doc.parts:
                continue
            for name in re.findall(r"\b((?:wr_\w+|load_\w+|query_position|create_snapshot|promote_chapter)\.py)\b",
                                   doc.read_text(encoding="utf-8")):
                self.assertIn(name, scripts, f"{doc.name} names {name}")

    def test_skills_named_in_the_pipeline_doc_exist(self):
        skills = {p.name for p in (REPO / "skills").iterdir() if p.is_dir()}
        text = (REPO / "docs" / "PIPELINE.md").read_text(encoding="utf-8")
        mentioned = set(re.findall(r"^\| `([a-z-]+)` \|", text, flags=re.M))
        self.assertEqual(mentioned, skills)


class Release(unittest.TestCase):
    def test_versions_agree(self):
        version = (REPO / "skills" / "writing-room" / "VERSION").read_text(encoding="utf-8").strip()
        plugin = json.loads((REPO / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(plugin["version"], version)
        changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertRegex(changelog, rf"(?m)^## {re.escape(version)}\b", "CHANGELOG must have an entry for the current version")

    def test_license(self):
        text = (REPO / "LICENSE").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("MIT License"))
        self.assertIn("Copyright (c) 2026", text)
        plugin = json.loads((REPO / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(plugin["license"], "MIT")
        self.assertIn("MIT", (REPO / "README.md").read_text(encoding="utf-8"))

    def test_ci_workflow_runs_the_same_checks(self):
        ci = (REPO / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        for cmd in ("tools/lint_skills.py", "unittest discover -s tests"):
            self.assertIn(cmd, ci)
        for py in ("3.9", "3.11", "3.13"):
            self.assertIn(f'"{py}"', ci)

    def test_no_private_working_folder_or_machine_paths_in_shipped_docs(self):
        for doc in DOCS:
            text = doc.read_text(encoding="utf-8")
            self.assertNotIn("Project_Notes", text, doc.name)
            self.assertNotRegex(text, r"[A-Za-z]:\\Users\\|/home/\w+/|D:/devtools", doc.name)


class ExportIdentity(unittest.TestCase):
    def test_export_works_without_a_configured_git_identity_and_tags(self):
        import subprocess
        import sys
        sys.path.insert(0, str(REPO / "tools"))
        import export_public as exp

        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            empty = tmp / "gitconfig"
            empty.write_text("", encoding="utf-8")
            env = {"GIT_CONFIG_GLOBAL": str(empty), "GIT_CONFIG_NOSYSTEM": "1", "HOME": str(tmp), "USERPROFILE": str(tmp)}
            repo = tmp / "repo"
            repo.mkdir()
            with mock.patch.dict(os.environ, env):
                run = lambda *a, cwd=repo: subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a],
                                                          cwd=cwd, capture_output=True, text=True, check=True)
                run("init", "-q", "-b", "main")
                (repo / "a.md").write_text("x\n", encoding="utf-8")
                run("add", "-A")
                run("commit", "-q", "-m", "first")
                exp.export(repo, tmp / "out", tag="v0.0.1")
                tags = subprocess.run(["git", "tag"], cwd=tmp / "out", capture_output=True, text=True).stdout.split()
            self.assertEqual(tags, ["v0.0.1"])


if __name__ == "__main__":
    unittest.main()
