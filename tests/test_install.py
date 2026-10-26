"""Phase 4 tests: wr_install, relocatability of an installed copy, plugin manifest, skills.json.

Run with:  python -m unittest discover -s tests -v
Every test installs into throwaway folders with HOME, USERPROFILE, APPDATA and XDG_CONFIG_HOME redirected,
so nothing outside the temp folder is ever touched.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WR = REPO / "skills" / "writing-room"
EXAMPLE = REPO / "examples" / "sample-project"
SKILLS = sorted(p.name for p in (REPO / "skills").iterdir() if (p / "SKILL.md").is_file())


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="wr-inst-")
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self.tmp = Path(self._tmp).resolve()
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.proj = self.tmp / "proj"
        shutil.copytree(EXAMPLE, self.proj)
        (self.proj / ".git").mkdir()  # a repository root: Hermes and Devin look for project skills there
        self.env = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home),
                        APPDATA=str(self.home / "AppData" / "Roaming"), XDG_CONFIG_HOME=str(self.home / ".config"))
        self.env.pop("WRITING_ROOM_ROOT", None)

    def install(self, *args, script=None):
        script = script or WR / "scripts" / "wr_install.py"
        return subprocess.run([sys.executable, str(script), *map(str, args)], env=self.env,
                              capture_output=True, text=True, encoding="utf-8", cwd=self.tmp)

    def names(self, directory):
        return sorted(p.name for p in Path(directory).iterdir() if (p / "SKILL.md").is_file())


class SkillsList(unittest.TestCase):
    def test_skills_json_matches_the_skills_folder(self):
        listed = json.loads((WR / "shared" / "skills.json").read_text(encoding="utf-8"))["skills"]
        self.assertEqual(sorted(listed), SKILLS)

    def test_plugin_manifest(self):
        data = json.loads((REPO / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(data["name"], "writing-room")
        self.assertEqual(data["version"], (WR / "VERSION").read_text(encoding="utf-8").strip())
        self.assertTrue((REPO / "skills").is_dir())  # the plugin layout: skills/ beside .claude-plugin/


class ProjectScope(Base):
    def test_claude_project_install(self):
        r = self.install("--harness", "claude", "--project", self.proj)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.names(self.proj / ".claude" / "skills"), SKILLS)
        self.assertTrue((self.proj / ".claude" / "skills" / ".writing-room-install.json").is_file())
        self.assertTrue((self.proj / ".claude" / "skills" / "writing-room" / "scripts" / "wr_doctor.py").is_file())
        self.assertFalse(list((self.proj / ".claude" / "skills").rglob("__pycache__")))

    def test_devin_and_opencode_share_one_copy(self):
        r = self.install("--harness", "devin,opencode", "--project", self.proj)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.names(self.proj / ".agents" / "skills"), SKILLS)
        self.assertFalse((self.proj / ".opencode").exists())
        self.assertFalse((self.proj / ".claude").exists())

    def test_opencode_alone_uses_its_own_folder(self):
        self.assertEqual(self.install("--harness", "opencode", "--project", self.proj).returncode, 0)
        self.assertEqual(self.names(self.proj / ".opencode" / "skills"), SKILLS)

    def test_all_installs_one_shared_copy_plus_hermes(self):
        r = self.install("--harness", "all", "--project", self.proj)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.names(self.proj / ".claude" / "skills"), SKILLS)  # covers claude, devin, opencode
        self.assertFalse((self.proj / ".agents").exists())
        self.assertEqual(self.names(self.proj / ".hermes" / "skills"), SKILLS)
        self.assertIn("hermes skills trust", r.stdout)  # Hermes asks the user to approve project skills once
        self.assertNotIn("external_dirs", r.stdout)  # project-local discovery needs no config entry
        self.assertNotIn("warning", r.stdout)

    def test_project_found_from_cwd(self):
        r = subprocess.run([sys.executable, str(WR / "scripts" / "wr_install.py"), "--harness", "claude"],
                           env=self.env, capture_output=True, text=True, encoding="utf-8", cwd=self.proj / "stories")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.proj / ".claude" / "skills" / "planner" / "SKILL.md").is_file())

    def test_no_project_is_a_clear_error(self):
        r = self.install("--harness", "claude")  # cwd is the temp folder, which is not a project
        self.assertEqual(r.returncode, 2)
        self.assertIn("--scope user", r.stderr)

    def test_project_content_is_untouched(self):
        def tree():
            return {str(p.relative_to(self.proj)): p.read_bytes() for p in sorted(self.proj.rglob("*"))
                    if p.is_file() and ".claude" not in p.parts}
        before = tree()
        self.install("--harness", "claude", "--project", self.proj)
        self.assertEqual(tree(), before)

    def test_guidance_flag(self):
        r = self.install("--harness", "claude", "--project", self.proj, "--guidance")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.proj / "AGENTS.md").is_file())
        self.assertEqual((self.proj / "CLAUDE.md").read_text(encoding="utf-8").strip(), "@AGENTS.md")
        (self.proj / "AGENTS.md").write_text("MINE", encoding="utf-8")
        self.install("--harness", "claude", "--project", self.proj, "--guidance")
        self.assertEqual((self.proj / "AGENTS.md").read_text(encoding="utf-8"), "MINE")


class ProjectPlacement(Base):
    """Which folders are chosen, and the warnings about where tools look for project skills."""

    def plan(self, *harnesses):
        sys.path.insert(0, str(WR / "scripts"))
        import wr_install
        return {d.relative_to(Path("P")).as_posix(): sorted(c)
                for d, c in wr_install.plan_project_targets(set(harnesses), Path("P"))}

    def test_each_harness_alone_uses_its_own_folder(self):
        self.assertEqual(self.plan("claude"), {".claude/skills": ["claude"]})
        self.assertEqual(self.plan("devin"), {".agents/skills": ["devin"]})
        self.assertEqual(self.plan("opencode"), {".opencode/skills": ["opencode"]})
        self.assertEqual(self.plan("hermes"), {".hermes/skills": ["hermes"]})

    def test_combinations_use_the_fewest_folders_without_duplicates(self):
        self.assertEqual(self.plan("devin", "opencode"), {".agents/skills": ["devin", "opencode"]})
        self.assertEqual(self.plan("devin", "hermes"), {".agents/skills": ["devin", "hermes"]})
        self.assertEqual(self.plan("opencode", "hermes"), {".agents/skills": ["hermes", "opencode"]})
        self.assertEqual(self.plan("claude", "hermes"), {".claude/skills": ["claude"], ".hermes/skills": ["hermes"]})
        self.assertEqual(self.plan("claude", "devin", "opencode", "hermes"),
                         {".claude/skills": ["claude", "devin", "opencode"], ".hermes/skills": ["hermes"]})

    def test_no_harness_sees_two_copies(self):
        sys.path.insert(0, str(WR / "scripts"))
        import wr_install
        from itertools import combinations
        for n in range(1, 5):
            for combo in combinations(wr_install.HARNESSES, n):
                dirs = [d for d, _ in wr_install.plan_project_targets(set(combo), Path("P"))]
                for h in combo:
                    seen = [d for d in dirs if h in wr_install.PROJECT_DIRS[d.relative_to(Path("P")).as_posix()]]
                    self.assertEqual(len(seen), 1, f"{h} would read {len(seen)} copies for {combo}")

    def test_repository_root_gives_no_warning_and_no_config_snippet(self):
        r = self.install("--harness", "hermes,devin", "--project", self.proj)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("warning", r.stdout)
        self.assertNotIn("external_dirs", r.stdout)
        self.assertIn("hermes skills trust", r.stdout)

    def test_not_a_git_repository_warns_hermes_and_devin_only(self):
        shutil.rmtree(self.proj / ".git")
        r = self.install("--harness", "all", "--project", self.proj)
        self.assertEqual(r.returncode, 0, r.stderr)
        warnings = [line for line in r.stdout.splitlines() if "warning:" in line]
        self.assertEqual(sorted(w.split("warning: ")[1].split(":")[0] for w in warnings), ["devin", "hermes"])
        self.assertIn("git init", r.stdout)
        self.assertIn("external_dirs", r.stdout)  # the fallback for Hermes
        self.assertIn("skills", r.stdout)

    def test_project_inside_a_larger_repository_points_at_the_repository_root(self):
        shutil.rmtree(self.proj / ".git")
        repo = self.tmp / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        sub = repo / "novel"
        shutil.move(str(self.proj), str(sub))
        r = self.install("--harness", "hermes", "--project", sub)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("looks for project skills at the repository root", r.stdout)
        self.assertIn(str(repo), r.stdout)
        self.assertIn("--project", r.stdout)
        # claude and opencode do not need the repository root
        r = self.install("--harness", "claude,opencode", "--project", sub, "--dry-run")
        self.assertNotIn("warning", r.stdout)

    def test_installing_at_the_repository_root_works_for_a_project_in_a_subfolder(self):
        shutil.rmtree(self.proj / ".git")
        repo = self.tmp / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        sub = repo / "novel"
        shutil.move(str(self.proj), str(sub))
        r = self.install("--harness", "hermes", "--project", repo)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.names(repo / ".hermes" / "skills"), SKILLS)
        self.assertNotIn("warning", r.stdout)
        # the scripts installed at the repository root still find the writing project from where you work
        scripts = repo / ".hermes" / "skills" / "writing-room" / "scripts"
        out = subprocess.run([sys.executable, str(scripts / "wr_next.py"), "--json"], cwd=sub, env=self.env,
                             capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(json.loads(out.stdout)["worlds"], ["Harrowmere"])


class ScopeOption(Base):
    def test_default_scope_is_project_and_is_announced(self):
        r = self.install("--harness", "claude", "--project", self.proj, "--dry-run")
        self.assertIn("project scope", r.stdout)

    def test_user_shorthand_equals_scope_user(self):
        r = self.install("--harness", "claude", "--user")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("user scope", r.stdout)
        self.assertEqual(self.names(self.home / ".claude" / "skills"), SKILLS)
        self.assertFalse((self.proj / ".claude").exists())

    def test_user_and_explicit_project_scope_conflict(self):
        r = self.install("--harness", "claude", "--user", "--scope", "project", "--project", self.proj)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("conflicts", r.stderr)

    def test_project_and_user_installs_are_independent(self):
        self.assertEqual(self.install("--harness", "claude", "--project", self.proj).returncode, 0)
        self.assertEqual(self.install("--harness", "claude", "--scope", "user").returncode, 0)
        self.assertEqual(self.names(self.proj / ".claude" / "skills"), SKILLS)
        self.assertEqual(self.names(self.home / ".claude" / "skills"), SKILLS)
        self.assertEqual(self.install("--harness", "claude", "--scope", "user", "--uninstall").returncode, 0)
        self.assertEqual(self.names(self.proj / ".claude" / "skills"), SKILLS)  # project copy untouched
        self.assertFalse((self.home / ".claude" / "skills" / "planner").exists())


class UserScope(Base):
    def test_user_locations(self):
        r = self.install("--harness", "all", "--scope", "user")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.names(self.home / ".claude" / "skills"), SKILLS)
        self.assertEqual(self.names(self.home / ".hermes" / "skills"), SKILLS)
        devin = (self.home / "AppData" / "Roaming" / "devin" / "skills") if os.name == "nt" \
            else (self.home / ".config" / "devin" / "skills")
        self.assertEqual(self.names(devin), SKILLS)
        # OpenCode reads ~/.claude/skills too, so no second copy when Claude Code is also installed
        self.assertFalse((self.home / ".config" / "opencode").exists())

    def test_opencode_user_alone(self):
        self.assertEqual(self.install("--harness", "opencode", "--scope", "user").returncode, 0)
        self.assertEqual(self.names(self.home / ".config" / "opencode" / "skills"), SKILLS)

    def test_target_override(self):
        dest = self.tmp / "anywhere"
        self.assertEqual(self.install("--harness", "hermes", "--target", dest).returncode, 0)
        self.assertEqual(self.names(dest), SKILLS)


class Safety(Base):
    def test_dry_run_changes_nothing(self):
        r = self.install("--harness", "claude", "--project", self.proj, "--dry-run")
        self.assertEqual(r.returncode, 0)
        self.assertIn("Dry run", r.stdout)
        self.assertFalse((self.proj / ".claude").exists())

    def test_foreign_skill_folder_is_not_replaced_without_force(self):
        foreign = self.proj / ".claude" / "skills" / "planner"
        foreign.mkdir(parents=True)
        (foreign / "SKILL.md").write_text("someone else's planner", encoding="utf-8")
        r = self.install("--harness", "claude", "--project", self.proj)
        self.assertEqual(r.returncode, 1)
        self.assertIn("planner", r.stdout)
        self.assertEqual((foreign / "SKILL.md").read_text(encoding="utf-8"), "someone else's planner")
        self.assertTrue((self.proj / ".claude" / "skills" / "reviewer" / "SKILL.md").is_file())  # others still installed
        r = self.install("--harness", "claude", "--project", self.proj, "--force")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotEqual((foreign / "SKILL.md").read_text(encoding="utf-8"), "someone else's planner")

    def test_update_replaces_only_our_folders_and_keeps_other_skills(self):
        skills = self.proj / ".claude" / "skills"
        other = skills / "my-own-skill"
        other.mkdir(parents=True)
        (other / "SKILL.md").write_text("mine", encoding="utf-8")
        self.install("--harness", "claude", "--project", self.proj)
        stale = skills / "planner" / "SKILL.md"
        stale.write_text("stale local edit", encoding="utf-8")
        r = self.install("--harness", "claude", "--project", self.proj)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotEqual(stale.read_text(encoding="utf-8"), "stale local edit")
        self.assertEqual((other / "SKILL.md").read_text(encoding="utf-8"), "mine")

    def test_uninstall_removes_only_ours(self):
        skills = self.proj / ".claude" / "skills"
        other = skills / "my-own-skill"
        other.mkdir(parents=True)
        (other / "SKILL.md").write_text("mine", encoding="utf-8")
        self.install("--harness", "claude", "--project", self.proj)
        r = self.install("--harness", "claude", "--project", self.proj, "--uninstall")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.names(skills), ["my-own-skill"])
        self.assertFalse((skills / ".writing-room-install.json").exists())

    def test_list(self):
        self.install("--harness", "claude", "--project", self.proj)
        r = self.install("--harness", "claude", "--project", self.proj, "--list")
        self.assertIn("14 skill(s) installed", r.stdout)

    def test_unknown_harness(self):
        r = self.install("--harness", "emacs", "--project", self.proj)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("unknown harness", r.stderr + r.stdout)


class InstalledCopyWorksInPlace(Base):
    """The installed copy must be self-contained: the same scripts, templates and cross-references must work."""

    def setUp(self):
        super().setUp()
        self.assertEqual(self.install("--harness", "opencode", "--project", self.proj).returncode, 0)
        self.skills = self.proj / ".opencode" / "skills"
        self.scripts = self.skills / "writing-room" / "scripts"

    def test_installed_scripts_reproduce_the_golden_output(self):
        r = subprocess.run([sys.executable, str(REPO / "tools" / "golden.py"), "check", "--scripts", str(self.scripts),
                            "--project", str(EXAMPLE)], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stdout[-2000:] + r.stderr)

    def test_installed_doctor_is_clean_and_sees_its_siblings(self):
        r = subprocess.run([sys.executable, str(self.scripts / "wr_doctor.py"), "--root", str(self.proj), "--json"],
                           env=self.env, capture_output=True, text=True, encoding="utf-8")
        data = json.loads(r.stdout)
        self.assertEqual(data["errors"], [], data)
        self.assertEqual(Path(data["info"]["skills_dir"]).resolve(), self.skills.resolve())

    def test_doctor_reports_a_missing_sibling_skill(self):
        shutil.rmtree(self.skills / "planner")
        r = subprocess.run([sys.executable, str(self.scripts / "wr_doctor.py"), "--root", str(self.proj)],
                           env=self.env, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 1)
        self.assertIn("skills missing next to writing-room", r.stdout)
        self.assertIn("planner", r.stdout)

    def test_cross_skill_references_resolve_after_install(self):
        r = subprocess.run([sys.executable, str(REPO / "tools" / "lint_skills.py"), str(self.skills)],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_installed_scripts_use_the_installed_shared_files(self):
        r = subprocess.run([sys.executable, str(self.scripts / "wr_resolve.py"), "templates/world/character.md",
                            "--root", str(self.proj)], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(Path(r.stdout.strip()).resolve(),
                         (self.skills / "writing-room" / "shared" / "templates" / "world" / "character.md").resolve())

    def test_installed_copy_can_install_again_elsewhere(self):
        dest = self.tmp / "second"
        r = self.install("--harness", "claude", "--target", dest, script=self.scripts / "wr_install.py")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.names(dest), SKILLS)


if __name__ == "__main__":
    unittest.main()
