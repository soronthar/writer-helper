"""Tests for wr_update.py: updating installed skills when a new build exists.

Run with:  python -m unittest discover -s tests -v
A "new build" is made by copying skills/ to a temporary folder and changing it (bumped VERSION, an edited
skill, a new skill, a removed skill, a CHANGELOG), so the real repository is never modified. HOME,
USERPROFILE, APPDATA and XDG_CONFIG_HOME are redirected, so nothing outside the temp folder is touched.
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
sys.path.insert(0, str(WR / "scripts"))

import wr_update  # noqa: E402
from wr_install import folder_hash  # noqa: E402

CHANGELOG = """# Changelog

## 0.2.0 (unreleased)

- planner now asks one more question.
- new-skill added; story-status folded into the router.

## 0.1.0

First build.
"""


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="wr-upd-")
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self.tmp = Path(self._tmp).resolve()
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.proj = self.tmp / "proj"
        shutil.copytree(EXAMPLE, self.proj)
        (self.proj / ".git").mkdir()
        self.env = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home),
                        APPDATA=str(self.home / "AppData" / "Roaming"), XDG_CONFIG_HOME=str(self.home / ".config"))
        self.env.pop("WRITING_ROOM_ROOT", None)
        self.skills = self.proj / ".claude" / "skills"

    # --- builds and commands
    def make_build(self, name="new", version="0.2.0", edit=True, add=True, remove=True):
        root = self.tmp / name
        shutil.copytree(REPO / "skills", root / "skills", ignore=shutil.ignore_patterns("__pycache__"))
        (root / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
        skills = root / "skills"
        (skills / "writing-room" / "VERSION").write_text(version + "\n", encoding="utf-8")
        names = json.loads((skills / "writing-room" / "shared" / "skills.json").read_text(encoding="utf-8"))["skills"]
        if edit:
            for n in ("planner", "reviewer"):
                f = skills / n / "SKILL.md"
                f.write_text(f.read_text(encoding="utf-8") + f"\nNew in {version}.\n", encoding="utf-8")
        if add:
            (skills / "new-skill").mkdir()
            (skills / "new-skill" / "SKILL.md").write_text('---\nname: new-skill\ndescription: "A new skill."\n---\nBody.\n', encoding="utf-8")
            names.append("new-skill")
        if remove:
            shutil.rmtree(skills / "story-status")
            names.remove("story-status")
        (skills / "writing-room" / "shared" / "skills.json").write_text(json.dumps({"skills": sorted(names)}), encoding="utf-8")
        return skills

    def run_script(self, script, *args, cwd=None):
        return subprocess.run([sys.executable, str(script), *map(str, args)], env=self.env, cwd=cwd or self.tmp,
                              capture_output=True, text=True, encoding="utf-8")

    def install_old(self, *extra, harness="claude"):
        r = self.run_script(WR / "scripts" / "wr_install.py", "--harness", harness, "--project", self.proj, *extra)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def update(self, build, *args, script=None):
        return self.run_script(script or WR / "scripts" / "wr_update.py", "--source", build, "--project", self.proj, *args)

    def manifest(self, directory=None):
        return json.loads(((directory or self.skills) / ".writing-room-install.json").read_text(encoding="utf-8"))


class Versions(unittest.TestCase):
    def test_parse_and_order(self):
        p = wr_update.parse_version
        self.assertLess(p("0.1.0"), p("0.2.0"))
        self.assertLess(p("0.9.9"), p("0.10.0"))
        self.assertLess(p("1.0.0-rc1"), p("1.0.0"))
        self.assertEqual(p("v1.2.3"), p("1.2.3"))
        self.assertIsNone(p("unknown"))

    def test_folder_hash_ignores_bytecode_but_not_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "s"
            (d / "references").mkdir(parents=True)
            (d / "SKILL.md").write_text("a", encoding="utf-8")
            (d / "references" / "x.md").write_text("b", encoding="utf-8")
            h = folder_hash(d)
            (d / "__pycache__").mkdir()
            (d / "__pycache__" / "m.pyc").write_bytes(b"junk")
            self.assertEqual(folder_hash(d), h)
            (d / "references" / "x.md").write_text("c", encoding="utf-8")
            self.assertNotEqual(folder_hash(d), h)
            (d / "references" / "x.md").write_text("b", encoding="utf-8")
            self.assertEqual(folder_hash(d), h)


class UpdateProject(Base):
    def test_update_applies_everything_and_is_then_idempotent(self):
        self.install_old()
        other = self.skills / "my-own-skill"
        other.mkdir()
        (other / "SKILL.md").write_text("mine", encoding="utf-8")
        before = self.manifest()
        self.assertIn("hashes", before)
        self.assertEqual(before["version"], (WR / "VERSION").read_text(encoding="utf-8").strip())
        new = self.make_build()
        r = self.update(new)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("version 0.1.0 -> 0.2.0", r.stdout)
        self.assertIn("planner", r.stdout)
        # content of the new build is installed
        self.assertIn("New in 0.2.0", (self.skills / "planner" / "SKILL.md").read_text(encoding="utf-8"))
        self.assertTrue((self.skills / "new-skill" / "SKILL.md").is_file())
        self.assertFalse((self.skills / "story-status").exists())
        self.assertEqual((other / "SKILL.md").read_text(encoding="utf-8"), "mine")  # not ours: untouched
        m = self.manifest()
        self.assertEqual(m["version"], "0.2.0")
        self.assertIn("new-skill", m["skills"])
        self.assertNotIn("story-status", m["skills"])
        self.assertEqual(m["hashes"]["planner"], folder_hash(self.skills / "planner"))
        # nothing is left half-installed
        self.assertFalse([p for p in self.skills.iterdir() if p.name.startswith(".wr-tmp")])
        # second run: nothing to do
        r2 = self.update(new)
        self.assertEqual(r2.returncode, 0)
        self.assertIn("up to date", r2.stdout)
        self.assertEqual(self.update(new, "--check").returncode, 0)

    def test_check_and_dry_run_change_nothing(self):
        self.install_old()
        new = self.make_build()
        before = {p.relative_to(self.proj).as_posix(): p.read_bytes() for p in self.proj.rglob("*") if p.is_file()}
        r = self.update(new, "--check")
        self.assertEqual(r.returncode, 1)
        self.assertIn("1 install(s) out of date", r.stdout)
        r = self.update(new, "--dry-run")
        self.assertEqual(r.returncode, 0)
        self.assertIn("Dry run", r.stdout)
        after = {p.relative_to(self.proj).as_posix(): p.read_bytes() for p in self.proj.rglob("*") if p.is_file()}
        self.assertEqual(after, before)

    def test_changelog_since_the_installed_version_is_shown(self):
        self.install_old()
        r = self.update(self.make_build(), "--dry-run")
        self.assertIn("planner now asks one more question", r.stdout)
        self.assertNotIn("First build", r.stdout)  # 0.1.0 is already installed

    def test_project_content_is_never_touched(self):
        def tree():
            return {p.relative_to(self.proj).as_posix(): p.read_bytes() for p in self.proj.rglob("*")
                    if p.is_file() and ".claude" not in p.parts and p.name not in ("AGENTS.md", "CLAUDE.md")}
        self.install_old()
        before = tree()
        self.assertEqual(self.update(self.make_build()).returncode, 0)
        self.assertEqual(tree(), before)

    def test_same_version_but_changed_content_still_updates(self):
        self.install_old()
        new = self.make_build(version=(WR / "VERSION").read_text(encoding="utf-8").strip(), add=False, remove=False)
        r = self.update(new)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("content differs", r.stdout)
        self.assertIn("New in 0.1.0", (self.skills / "planner" / "SKILL.md").read_text(encoding="utf-8"))


class LocalEdits(Base):
    def test_locally_edited_skill_is_saved_before_it_is_replaced(self):
        self.install_old()
        edited = self.skills / "reviewer" / "SKILL.md"
        edited.write_text(edited.read_text(encoding="utf-8") + "\nMY LOCAL RULE\n", encoding="utf-8")
        r = self.update(self.make_build())
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        backups = list((self.skills.parent / ".writing-room-backups").rglob("SKILL.md"))
        self.assertEqual([b.parent.name for b in backups], ["reviewer"])  # planner was changed but not edited
        self.assertIn("MY LOCAL RULE", backups[0].read_text(encoding="utf-8"))
        self.assertNotIn("MY LOCAL RULE", edited.read_text(encoding="utf-8"))

    def test_no_backup_flag(self):
        self.install_old()
        edited = self.skills / "reviewer" / "SKILL.md"
        edited.write_text("edited", encoding="utf-8")
        self.assertEqual(self.update(self.make_build(), "--no-backup").returncode, 0)
        self.assertFalse((self.skills.parent / ".writing-room-backups").exists())

    def test_install_that_predates_edit_tracking_backs_up_what_it_replaces(self):
        self.install_old()
        m = self.manifest()
        del m["hashes"]
        (self.skills / ".writing-room-install.json").write_text(json.dumps(m), encoding="utf-8")
        r = self.update(self.make_build())
        self.assertIn("predates edit tracking", r.stdout)
        saved = {b.parent.name for b in (self.skills.parent / ".writing-room-backups").rglob("SKILL.md")}
        # everything replaced or removed is saved, since edits cannot be told apart: the two edited skills,
        # the runtime (its VERSION and skills list changed) and the skill the new build drops
        self.assertEqual(saved, {"planner", "reviewer", "writing-room", "story-status"})
        self.assertIn("hashes", self.manifest())  # now tracked

    def test_removed_skill_that_was_edited_is_saved_then_removed(self):
        self.install_old()
        gone = self.skills / "story-status" / "SKILL.md"
        gone.write_text("my version of story-status", encoding="utf-8")
        self.assertEqual(self.update(self.make_build()).returncode, 0)
        self.assertFalse((self.skills / "story-status").exists())
        saved = list((self.skills.parent / ".writing-room-backups").rglob("story-status/SKILL.md"))
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0].read_text(encoding="utf-8"), "my version of story-status")


class Safety(Base):
    def test_a_foreign_folder_with_a_new_skills_name_is_skipped_unless_forced(self):
        self.install_old()
        foreign = self.skills / "new-skill"
        foreign.mkdir()
        (foreign / "SKILL.md").write_text("someone else's", encoding="utf-8")
        new = self.make_build()
        r = self.update(new)
        self.assertEqual(r.returncode, 1)
        self.assertIn("SKIP new-skill", r.stdout)
        self.assertEqual((foreign / "SKILL.md").read_text(encoding="utf-8"), "someone else's")
        self.assertIn("New in 0.2.0", (self.skills / "planner" / "SKILL.md").read_text(encoding="utf-8"))  # the rest updated
        r = self.update(new, "--force")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("A new skill", (foreign / "SKILL.md").read_text(encoding="utf-8"))

    def test_downgrade_is_refused_unless_allowed(self):
        self.install_old()
        old_build = self.make_build(version="0.0.9", edit=False, add=False, remove=False)
        r = self.update(old_build)
        self.assertEqual(r.returncode, 1)
        self.assertIn("REFUSED", r.stdout)
        self.assertEqual(self.manifest()["version"], "0.1.0")
        self.assertEqual(self.update(old_build, "--allow-downgrade").returncode, 0)
        self.assertEqual(self.manifest()["version"], "0.0.9")

    def test_project_with_a_newer_layout_is_refused(self):
        self.install_old()
        (self.proj / "writing-room.toml").write_text("layout = 2\n", encoding="utf-8")
        r = self.update(self.make_build())
        self.assertEqual(r.returncode, 1)
        self.assertIn("layout is 2", r.stdout)
        self.assertNotIn("New in 0.2.0", (self.skills / "planner" / "SKILL.md").read_text(encoding="utf-8"))

    def test_a_skill_folder_deleted_by_hand_is_restored(self):
        self.install_old()
        shutil.rmtree(self.skills / "outliner")
        r = self.update(self.make_build(edit=False, add=False, remove=False, version="0.1.0"))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertTrue((self.skills / "outliner" / "SKILL.md").is_file())

    def test_nothing_installed_is_a_clear_error(self):
        r = self.update(self.make_build())
        self.assertEqual(r.returncode, 2)
        self.assertIn("wr_install.py first", r.stderr)

    def test_no_project_and_no_flags_is_a_clear_error(self):
        r = self.run_script(WR / "scripts" / "wr_update.py", "--source", self.make_build())  # cwd is not a project
        self.assertEqual(r.returncode, 2)
        self.assertIn("--user", r.stderr)

    def test_bad_source(self):
        self.install_old()
        r = self.update(self.tmp)
        self.assertEqual(r.returncode, 2)


class Guidance(Base):
    def test_customised_guidance_is_reported_and_replaced_only_on_request(self):
        self.install_old("--guidance")
        agents = self.proj / "AGENTS.md"
        original = agents.read_text(encoding="utf-8")
        new = self.make_build()
        self.assertNotIn("differs", self.update(new, "--dry-run").stdout)  # identical to the shipped copy
        agents.write_text(original + "\nMy own rules.\n", encoding="utf-8")
        r = self.update(new)
        self.assertIn("AGENTS.md differs", r.stdout)
        self.assertIn("My own rules.", agents.read_text(encoding="utf-8"))  # report only
        r = self.update(new, "--guidance")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(agents.read_text(encoding="utf-8"), original)
        self.assertIn("My own rules.", (self.proj / "AGENTS.md.bak").read_text(encoding="utf-8"))


class OtherScopes(Base):
    def test_user_level_install_is_found_and_updated(self):
        r = self.run_script(WR / "scripts" / "wr_install.py", "--harness", "claude", "--user")
        self.assertEqual(r.returncode, 0, r.stderr)
        user_skills = self.home / ".claude" / "skills"
        new = self.make_build()
        r = self.run_script(WR / "scripts" / "wr_update.py", "--source", new, "--user")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("[user]", r.stdout)
        self.assertIn("New in 0.2.0", (user_skills / "planner" / "SKILL.md").read_text(encoding="utf-8"))

    def test_project_and_user_installs_can_be_updated_together(self):
        self.install_old()
        self.run_script(WR / "scripts" / "wr_install.py", "--harness", "claude", "--user")
        r = self.update(self.make_build(), "--user")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.manifest()["version"], "0.2.0")
        self.assertEqual(self.manifest(self.home / ".claude" / "skills")["version"], "0.2.0")

    def test_target_folder(self):
        dest = self.tmp / "anywhere"
        r = self.run_script(WR / "scripts" / "wr_install.py", "--harness", "hermes", "--target", dest)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.run_script(WR / "scripts" / "wr_update.py", "--source", self.make_build(), "--target", dest)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.manifest(dest)["version"], "0.2.0")

    def test_two_harness_folders_in_one_project_are_both_updated(self):
        self.install_old(harness="all")  # .claude/skills and .hermes/skills
        r = self.update(self.make_build())
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for d in (".claude", ".hermes"):
            self.assertEqual(self.manifest(self.proj / d / "skills")["version"], "0.2.0")


class FromAnInstalledCopy(Base):
    def test_an_installed_copy_can_update_itself_from_a_new_build(self):
        self.install_old()
        installed_script = self.skills / "writing-room" / "scripts" / "wr_update.py"
        new = self.make_build()
        r = self.update(new, script=installed_script)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.manifest()["version"], "0.2.0")
        # and the updated copy still works
        d = self.run_script(self.skills / "writing-room" / "scripts" / "wr_doctor.py", "--root", self.proj)
        self.assertNotIn("skills missing", d.stdout)
        self.assertEqual(d.returncode, 0, d.stdout)

    def test_running_the_installed_copy_without_a_source_has_nothing_to_do(self):
        self.install_old()
        installed_script = self.skills / "writing-room" / "scripts" / "wr_update.py"
        r = self.run_script(installed_script, "--project", self.proj)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("nothing to update", r.stdout)


if __name__ == "__main__":
    unittest.main()
