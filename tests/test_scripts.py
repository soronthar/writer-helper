"""Phase 1 tests: root discovery, compatibility with legacy output, init/migrate/doctor/resolve.

Run with:  python -m unittest discover -s tests -v     (or: pytest tests)
Stdlib only. Every test works on throwaway copies; nothing under fixtures/ or examples/ is modified.
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
SCRIPTS = WR / "scripts"
LEGACY = REPO / "fixtures" / "legacy-v1"
SYNTHETIC = REPO / "fixtures" / "synthetic-v1"
EXAMPLE = REPO / "examples" / "sample-project"
WORLD = "worlds/Harrowmere"


def run(script, *args, cwd=None, env=None):
    e = dict(os.environ)
    e.pop("WRITING_ROOM_ROOT", None)
    e.update(env or {})
    return subprocess.run([sys.executable, str(SCRIPTS / f"{script}.py"), *map(str, args)],
                          cwd=cwd, env=e, capture_output=True, text=True, encoding="utf-8")


class Tmp(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="wr-test-")
        self.tmp = Path(self._tmp).resolve()
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)

    def copy(self, src, name="project"):
        dst = self.tmp / name
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))
        return dst


class GoldenCompatibility(unittest.TestCase):
    """The new scripts must reproduce the recorded legacy output byte for byte."""

    def golden(self, *extra):
        return subprocess.run([sys.executable, str(REPO / "tools" / "golden.py"), "check",
                               "--scripts", str(SCRIPTS), *extra], capture_output=True, text=True, encoding="utf-8")

    def test_against_legacy_fixture(self):
        r = self.golden()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_against_example_project_using_framework_craft_fallback(self):
        r = self.golden("--project", str(EXAMPLE))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class RootDiscovery(Tmp):
    def test_walk_up_from_subdirectory(self):
        proj = self.copy(EXAMPLE)
        r = run("query_position", "--world", WORLD, "--story", "Salt and Signal", "--format", "json",
                cwd=proj / "stories" / "Salt and Signal" / "chapters")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["position"], 2)

    def test_explicit_root_flag_beats_cwd(self):
        proj = self.copy(EXAMPLE)
        r = run("query_position", "--root", proj, "--world", WORLD, "--story", "The Tallow Ledger",
                "--format", "json", cwd=self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["position"], 1)

    def test_root_equals_form(self):
        proj = self.copy(EXAMPLE)
        r = run("query_position", f"--root={proj}", "--world", WORLD, "--story", "The Tallow Ledger",
                "--format", "json", cwd=self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_env_var(self):
        proj = self.copy(EXAMPLE)
        r = run("query_position", "--world", WORLD, "--story", "The Tallow Ledger", "--format", "json",
                cwd=self.tmp, env={"WRITING_ROOM_ROOT": str(proj)})
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_flag_beats_env_var(self):
        good, bad = self.copy(EXAMPLE, "good"), self.tmp / "nowhere"
        r = run("query_position", "--root", good, "--world", WORLD, "--story", "The Tallow Ledger",
                "--format", "json", cwd=self.tmp, env={"WRITING_ROOM_ROOT": str(bad)})
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_legacy_project_without_marker_is_found(self):
        proj = self.copy(LEGACY)
        self.assertFalse((proj / "writing-room.toml").exists())
        r = run("query_position", "--world", WORLD, "--story", "The Tallow Ledger", "--format", "json", cwd=proj)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_no_project_gives_clear_error(self):
        empty = self.tmp / "empty"
        empty.mkdir()
        r = run("query_position", "--world", WORLD, "--story", "x", cwd=empty)
        self.assertEqual(r.returncode, 2)
        self.assertIn("No Writing Room project found", r.stderr)

    def test_newer_layout_is_refused(self):
        proj = self.copy(EXAMPLE)
        (proj / "writing-room.toml").write_text("layout = 2\n", encoding="utf-8")
        r = run("query_position", "--world", WORLD, "--story", "The Tallow Ledger", cwd=proj)
        self.assertEqual(r.returncode, 2)
        self.assertIn("layout 2", r.stderr)


class CraftFallback(Tmp):
    def test_project_copy_overrides_framework_copy(self):
        proj = self.copy(EXAMPLE)
        d = proj / "writing_concepts" / "story_structure"
        d.mkdir(parents=True)
        (d / "GUIDE.md").write_text("PROJECT GUIDE OVERRIDE\n", encoding="utf-8")
        r = run("load_world", "--world", WORLD, "--structure", "Freytag's Pyramid", cwd=proj)
        self.assertIn("PROJECT GUIDE OVERRIDE", r.stdout)
        self.assertIn("Freytag", r.stdout)  # the rest still comes from the framework

    def test_styles_are_never_defaulted(self):
        proj = self.copy(EXAMPLE)
        shutil.rmtree(proj / "writing_concepts" / "styles")
        r = run("load_bible", "--story", "stories/Salt and Signal", "--world", WORLD,
                "--no-last-chapter", "--no-timeline", cwd=proj)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("None found in writing_concepts/styles/", r.stdout)

    def test_wr_resolve_prefers_project_then_framework(self):
        proj = self.copy(EXAMPLE)
        r = run("wr_resolve", "templates/world/character.md", cwd=proj)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(Path(r.stdout.strip()), WR / "shared" / "templates" / "world" / "character.md")
        (proj / "templates" / "world").mkdir(parents=True)
        (proj / "templates" / "world" / "character.md").write_text("mine", encoding="utf-8")
        r = run("wr_resolve", "templates/world/character.md", cwd=proj)
        self.assertEqual(Path(r.stdout.strip()), proj / "templates" / "world" / "character.md")

    def test_wr_resolve_missing(self):
        r = run("wr_resolve", "templates/nope.md", cwd=self.copy(EXAMPLE))
        self.assertEqual(r.returncode, 1)


class SyntheticCoverage(unittest.TestCase):
    """Cases the public fixture lacks: in-flight chapter, reviews directory, book series."""

    def test_doctor_clean(self):
        r = run("wr_doctor", "--root", SYNTHETIC)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("0 error(s), 0 warning(s)", r.stdout)

    def test_load_bible_reviews_dir(self):
        r = run("load_bible", "--root", SYNTHETIC, "--story", "stories/Short Piece", "--world", "worlds/Test World",
                "--reviews-dir", "stories/Short Piece/current_chapter/current_reviews", "--no-style")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Consistency Review", r.stdout)
        self.assertIn("Character Review", r.stdout)
        self.assertIn("Ada found the ledger", r.stdout)  # most recent promoted chapter

    def test_load_bible_for_book_in_series(self):
        story = "stories/Test Series/Book 01 - Opening"
        r = run("load_bible", "--root", SYNTHETIC, "--story", story, "--world", "worlds/Test World", "--no-style")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("The first day.", r.stdout)

    def test_query_position_without_world_order_is_not_a_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "p"
            shutil.copytree(SYNTHETIC, proj)
            (proj / "worlds" / "Test World" / "WORLD_ORDER.md").unlink()
            r = run("query_position", "--root", proj, "--world", "worlds/Test World", "--story", "Short Piece",
                    "--format", "json")
            self.assertNotIn("Traceback", r.stderr)


class Init(Tmp):
    def test_creates_project_and_doctor_passes(self):
        d = self.tmp / "new"
        r = run("wr_init", d)
        self.assertEqual(r.returncode, 0, r.stderr)
        for rel in ("writing-room.toml", "worlds", "stories", "writing_concepts/styles/Default Style.md"):
            self.assertTrue((d / rel).exists(), rel)
        r = run("wr_doctor", "--root", d)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_dry_run_changes_nothing(self):
        d = self.tmp / "new"
        d.mkdir()
        r = run("wr_init", d, "--dry-run")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(list(d.iterdir()), [])

    def test_idempotent_and_never_overwrites(self):
        d = self.tmp / "new"
        run("wr_init", d)
        style = d / "writing_concepts" / "styles" / "Default Style.md"
        style.write_text("MY STYLE", encoding="utf-8")
        r = run("wr_init", d)
        self.assertEqual(r.returncode, 0)
        self.assertIn("already a Writing Room project", r.stdout)
        self.assertEqual(style.read_text(encoding="utf-8"), "MY STYLE")

    def test_existing_style_is_not_replaced_by_starter(self):
        d = self.tmp / "new"
        (d / "writing_concepts" / "styles").mkdir(parents=True)
        (d / "writing_concepts" / "styles" / "Mine.md").write_text("x", encoding="utf-8")
        run("wr_init", d)
        self.assertEqual([p.name for p in (d / "writing_concepts" / "styles").iterdir()], ["Mine.md"])

    def test_legacy_project_is_pointed_to_migrate(self):
        r = run("wr_init", self.copy(LEGACY))
        self.assertEqual(r.returncode, 1)
        self.assertIn("wr_migrate", r.stderr)

    def test_refuses_nested_project_without_force(self):
        outer = self.copy(EXAMPLE)
        r = run("wr_init", outer / "sub")
        self.assertEqual(r.returncode, 1)
        self.assertIn("inside an existing project", r.stderr)
        self.assertEqual(run("wr_init", outer / "sub", "--force").returncode, 0)


def snapshot_tree(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(Path(root).rglob("*")) if p.is_file()}


class Migrate(Tmp):
    def test_dry_run_changes_nothing(self):
        proj = self.copy(LEGACY)
        before = snapshot_tree(proj)
        r = run("wr_migrate", "--root", proj)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Dry run", r.stdout)
        self.assertEqual(snapshot_tree(proj), before)

    def test_apply_adds_only_the_marker(self):
        proj = self.copy(LEGACY)
        before = snapshot_tree(proj)
        r = run("wr_migrate", "--root", proj, "--apply")
        self.assertEqual(r.returncode, 0, r.stderr)
        after = snapshot_tree(proj)
        self.assertEqual(set(after) - set(before), {"writing-room.toml"})
        self.assertEqual({k: v for k, v in after.items() if k != "writing-room.toml"}, before)

    def test_idempotent(self):
        proj = self.copy(LEGACY)
        run("wr_migrate", "--root", proj, "--apply")
        r = run("wr_migrate", "--root", proj, "--apply")
        self.assertEqual(r.returncode, 0)
        self.assertIn("already declares layout 1", r.stdout)
        self.assertIn("Nothing to do", r.stdout)

    def retire_tree(self, proj):
        """Everything except the retired framework files, as {relative path: bytes}."""
        skip = (".claude/agents", ".claude/commands", "CLAUDE.md", "README.md", "room_rules", "scripts", ".writing-room-legacy",
                "AGENTS.md", "writing-room.toml")
        return {p.relative_to(proj).as_posix(): p.read_bytes() for p in sorted(proj.rglob("*"))
                if p.is_file() and not p.relative_to(proj).as_posix().startswith(skip)}

    def test_retire_legacy_dry_run_changes_nothing(self):
        proj = self.copy(LEGACY)
        before = snapshot_tree(proj)
        r = run("wr_migrate", "--root", proj, "--retire-legacy")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("move scripts -> .writing-room-legacy/scripts", r.stdout)
        self.assertIn("Dry run", r.stdout)
        self.assertEqual(snapshot_tree(proj), before)

    def test_retire_legacy_moves_framework_files_and_nothing_else(self):
        proj = self.copy(LEGACY)
        edited = proj / "templates" / "story" / "outline.md"
        edited.write_bytes(edited.read_bytes() + b"\nMy own addition.\n")
        before_content = self.retire_tree(proj)
        old_agent = (proj / ".claude" / "agents" / "planner.md").read_bytes()
        old_claude_md = (proj / "CLAUDE.md").read_bytes()
        r = run("wr_migrate", "--root", proj, "--apply", "--retire-legacy")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        arch = proj / ".writing-room-legacy"
        for rel in (".claude/agents", ".claude/commands", "CLAUDE.md", "README.md", "room_rules", "scripts"):
            self.assertFalse((proj / rel).exists() and rel not in ("CLAUDE.md",), rel)
            self.assertTrue((arch / rel).exists(), rel)
        self.assertEqual((arch / ".claude" / "agents" / "planner.md").read_bytes(), old_agent)  # moved intact
        self.assertEqual((arch / "CLAUDE.md").read_bytes(), old_claude_md)
        # user content, edited templates and the style folder are exactly as before; unedited shipped
        # templates and craft files moved intact to the archive, where they no longer hide the framework's
        after = self.retire_tree(proj)
        gone = set(before_content) - set(after)
        self.assertEqual({k: before_content[k] for k in after}, after)
        self.assertTrue(gone)
        crafts = ("templates/", "writing_concepts/story_structure/", "writing_concepts/archetypes/", "writing_concepts/tropes/")
        for rel in gone:
            self.assertTrue(rel.startswith(crafts), rel)
            self.assertEqual((arch / rel).read_bytes(), before_content[rel], rel)
        self.assertIn("templates/story/chapter_plan.md", gone)
        self.assertEqual(edited.read_text(encoding="utf-8").splitlines()[-1], "My own addition.")
        self.assertTrue((proj / "writing_concepts" / "styles").is_dir())
        # the new guidance replaced the old CLAUDE.md
        self.assertEqual((proj / "CLAUDE.md").read_text(encoding="utf-8").strip(), "@AGENTS.md")
        self.assertTrue((proj / "AGENTS.md").is_file())
        self.assertTrue((proj / "writing-room.toml").is_file())

    def test_retire_legacy_is_reversible_by_moving_back(self):
        proj = self.copy(LEGACY)
        before = snapshot_tree(proj)
        run("wr_migrate", "--root", proj, "--apply", "--retire-legacy")
        arch = proj / ".writing-room-legacy"
        for path in sorted(arch.rglob("*")):
            if path.is_file():
                target = proj / path.relative_to(arch)
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    target.unlink()
                shutil.move(str(path), str(target))
        shutil.rmtree(arch)
        (proj / "AGENTS.md").unlink()
        (proj / "writing-room.toml").unlink()
        self.assertEqual(snapshot_tree(proj), before)

    def test_retire_legacy_is_idempotent_and_skips_blocked_items(self):
        proj = self.copy(LEGACY)
        run("wr_migrate", "--root", proj, "--apply", "--retire-legacy")
        r = run("wr_migrate", "--root", proj, "--apply", "--retire-legacy")
        self.assertEqual(r.returncode, 0)
        self.assertIn("Nothing to do", r.stdout)
        # a re-created folder whose archive copy already exists is skipped, not overwritten
        (proj / "scripts").mkdir()
        (proj / "scripts" / "new.py").write_text("x", encoding="utf-8")
        r = run("wr_migrate", "--root", proj, "--apply", "--retire-legacy")
        self.assertIn("Skipping scripts", r.stdout)
        self.assertTrue((proj / "scripts" / "new.py").exists())

    def test_retired_project_still_works(self):
        proj = self.copy(LEGACY)
        run("wr_migrate", "--root", proj, "--apply", "--retire-legacy")
        self.assertEqual(run("wr_doctor", "--root", proj).returncode, 0)
        g = subprocess.run([sys.executable, str(REPO / "tools" / "golden.py"), "check",
                            "--scripts", str(SCRIPTS), "--project", str(proj)], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(g.returncode, 0, g.stdout[-1500:])

    def test_retire_legacy_respects_the_dirty_git_guard(self):
        if shutil.which("git") is None:
            self.skipTest("git not available")
        proj = self.copy(LEGACY)
        git = lambda *a: subprocess.run(["git", "-C", str(proj), "-c", "user.email=t@t", "-c", "user.name=t", *a],
                                        capture_output=True, text=True)
        git("init", "-q")
        git("add", "-A")
        git("commit", "-q", "-m", "base")
        (proj / "templates" / "extra.md").write_text("uncommitted", encoding="utf-8")
        r = run("wr_migrate", "--root", proj, "--apply", "--retire-legacy")
        self.assertEqual(r.returncode, 1)
        self.assertTrue((proj / "scripts").exists())
        self.assertEqual(run("wr_migrate", "--root", proj, "--apply", "--retire-legacy", "--force").returncode, 0)

    def test_skills_installed_first_do_not_trip_the_dirty_guard(self):
        if shutil.which("git") is None:
            self.skipTest("git not available")
        proj = self.copy(LEGACY)
        git = lambda *a: subprocess.run(["git", "-C", str(proj), "-c", "user.email=t@t", "-c", "user.name=t", *a],
                                        capture_output=True, text=True)
        git("init", "-q")
        git("add", "-A")
        git("commit", "-q", "-m", "base")
        inst = subprocess.run([sys.executable, str(SCRIPTS / "wr_install.py"), "--harness", "devin,opencode",
                               "--project", str(proj)], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(inst.returncode, 0, inst.stderr)
        self.assertTrue((proj / ".agents" / "skills" / "planner" / "SKILL.md").is_file())
        r = run("wr_migrate", "--root", proj, "--apply", "--retire-legacy")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        # but other uncommitted work still blocks it
        proj2 = self.copy(LEGACY, "project2")
        git2 = lambda *a: subprocess.run(["git", "-C", str(proj2), "-c", "user.email=t@t", "-c", "user.name=t", *a],
                                         capture_output=True, text=True)
        git2("init", "-q")
        git2("add", "-A")
        git2("commit", "-q", "-m", "base")
        (proj2 / "worlds" / "Harrowmere" / "HOOKS.md").write_text("edited", encoding="utf-8")
        self.assertEqual(run("wr_migrate", "--root", proj2, "--apply").returncode, 1)

    def test_migrated_project_still_passes_doctor_and_golden(self):
        proj = self.copy(LEGACY)
        run("wr_migrate", "--root", proj, "--apply")
        self.assertEqual(run("wr_doctor", "--root", proj).returncode, 0)
        g = subprocess.run([sys.executable, str(REPO / "tools" / "golden.py"), "check",
                            "--scripts", str(SCRIPTS), "--project", str(proj)],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(g.returncode, 0, g.stdout)

    def test_not_a_project(self):
        empty = self.tmp / "empty"
        empty.mkdir()
        self.assertNotEqual(run("wr_migrate", "--root", empty).returncode, 0)

    def test_dirty_git_tree_blocks_apply_unless_forced(self):
        if shutil.which("git") is None:
            self.skipTest("git not available")
        proj = self.copy(LEGACY)
        git = lambda *a: subprocess.run(["git", "-C", str(proj), *a], capture_output=True, text=True)
        git("init", "-q")
        git("-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
        git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "base")
        (proj / "worlds" / WORLD.split("/")[1] / "HOOKS.md").write_text("changed", encoding="utf-8")
        r = run("wr_migrate", "--root", proj, "--apply")
        self.assertEqual(r.returncode, 1)
        self.assertFalse((proj / "writing-room.toml").exists())
        r = run("wr_migrate", "--root", proj, "--apply", "--force")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((proj / "writing-room.toml").exists())


class Doctor(Tmp):
    def test_json_output(self):
        r = run("wr_doctor", "--root", EXAMPLE, "--json")
        data = json.loads(r.stdout)
        self.assertEqual(data["errors"], [])
        self.assertEqual(data["info"]["layout"], 1)

    def test_reports_structural_errors(self):
        proj = self.copy(EXAMPLE)
        (proj / "worlds" / "Harrowmere" / "HOOKS.md").unlink()
        r = run("wr_doctor", "--root", proj)
        self.assertEqual(r.returncode, 1)
        self.assertIn("missing HOOKS.md", r.stdout)

    def test_flags_stale_summary(self):
        proj = self.copy(EXAMPLE)
        (proj / "worlds" / "Harrowmere" / "characters" / "New Person.md").write_text("x", encoding="utf-8")
        r = run("wr_doctor", "--root", proj)
        self.assertIn("SUMMARY.md may be stale", r.stdout)

    # --- cross-file consistency checks
    def doctor_text(self, proj):
        return run("wr_doctor", "--root", proj).stdout

    def test_world_without_summary_or_world_order_is_reported_with_the_fix(self):
        proj = self.copy(EXAMPLE)
        world = proj / "worlds" / "Harrowmere"
        (world / "SUMMARY.md").unlink()
        (world / "WORLD_ORDER.md").unlink()
        out = self.doctor_text(proj)
        self.assertIn("world 'Harrowmere': no SUMMARY.md, so skills read every entity file", out)
        self.assertIn("run the world-archivist skill (Regenerate SUMMARY.md)", out)
        self.assertIn("no WORLD_ORDER.md although 2 story(ies) use it", out)
        self.assertIn("run the world-archivist skill (Manage story order)", out)
        self.assertEqual(run("wr_doctor", "--root", proj).returncode, 0)  # warnings, not errors

    def test_world_without_stories_or_entities_is_not_nagged(self):
        proj = self.copy(EXAMPLE)
        (proj / "worlds" / "Blank").mkdir()
        (proj / "worlds" / "Blank" / "DESCRIPTION.md").write_text("# Blank\n", encoding="utf-8")
        (proj / "worlds" / "Blank" / "HOOKS.md").write_text("# Hooks\n", encoding="utf-8")
        self.assertNotIn("'Blank'", self.doctor_text(proj))

    def test_world_order_without_the_world_but_with_entities_says_to_initialize(self):
        proj = self.copy(EXAMPLE)
        (proj / "worlds" / "Other").mkdir()
        (proj / "worlds" / "Other" / "DESCRIPTION.md").write_text("# Other\n", encoding="utf-8")
        (proj / "worlds" / "Other" / "HOOKS.md").write_text("# Hooks\n", encoding="utf-8")
        (proj / "worlds" / "Other" / "characters").mkdir()
        (proj / "worlds" / "Other" / "characters" / "Someone.md").write_text("# Someone\n", encoding="utf-8")
        out = self.doctor_text(proj)
        self.assertIn("world 'Other': no WORLD_ORDER.md; run the world-archivist skill", out)

    def test_story_missing_from_world_order_and_unknown_story_in_it(self):
        proj = self.copy(EXAMPLE)
        order = proj / "worlds" / "Harrowmere" / "WORLD_ORDER.md"
        text = order.read_text(encoding="utf-8")
        order.write_text(text.replace("[[Salt and Signal]]", "[[Vanished Story]]"), encoding="utf-8")
        out = self.doctor_text(proj)
        self.assertIn("story 'Salt and Signal' is not in WORLD_ORDER.md", out)
        self.assertIn("WORLD_ORDER.md lists 'Vanished Story', which is not in stories/", out)

    def test_completed_story_without_a_snapshot(self):
        proj = self.copy(EXAMPLE)
        shutil.rmtree(proj / "worlds" / "Harrowmere" / "snapshots" / "2")
        out = self.doctor_text(proj)
        self.assertIn("'Salt and Signal' is Complete at position 2 but there is no snapshot 2", out)
        self.assertIn("(run the world-archivist skill (Consolidate))", out)

    def test_book_in_progress_with_complete_chapter_rows_needs_no_snapshot(self):
        proj = self.copy(EXAMPLE)
        shutil.rmtree(proj / "worlds" / "Harrowmere" / "snapshots" / "2")
        order = proj / "worlds" / "Harrowmere" / "WORLD_ORDER.md"
        row = "| 2 | [[Salt and Signal]] | Full Story | Early winter, the same year | Complete | The sealed room |"
        text = order.read_text(encoding="utf-8")
        self.assertIn(row, text)

        def chapters(done):
            return "\n".join(f"| {1 + n} | [[Salt and Signal]] | Ch. {n} | Early winter | "
                             f"{'Complete' if n <= done else 'In Progress'} | |" for n in range(1, 5))
        order.write_text(text.replace(row, chapters(2)), encoding="utf-8")  # 2 of the outline's 4 chapters
        self.assertNotIn("'Salt and Signal' is Complete", self.doctor_text(proj))
        order.write_text(text.replace(row, chapters(4)), encoding="utf-8")
        self.assertIn("'Salt and Signal' is Complete at position 2 but there is no snapshot 2", self.doctor_text(proj))

    def test_summary_staleness_is_judged_by_name_not_count(self):
        proj = self.copy(EXAMPLE)
        chars = proj / "worlds" / "Harrowmere" / "characters"
        (chars / "Ilsa Brandt.md").rename(chars / "Ilsa Brandt-Renamed.md")  # same count, different name
        out = self.doctor_text(proj)
        self.assertIn("SUMMARY.md may be stale", out)
        self.assertIn("not listed: Ilsa Brandt-Renamed", out)
        self.assertIn("listed but no file: Ilsa Brandt", out)

    def test_summary_names_match_despite_case_and_underscores(self):
        proj = self.copy(EXAMPLE)
        chars = proj / "worlds" / "Harrowmere" / "characters"
        (chars / "Doran Pike.md").rename(chars / "doran_pike.md")
        self.assertNotIn("SUMMARY.md may be stale", self.doctor_text(proj))

    def test_promoted_chapter_without_a_timeline_entry(self):
        proj = self.copy(EXAMPLE)
        timeline = proj / "stories" / "Salt and Signal" / "state" / "Timeline.md"
        lines = [line for line in timeline.read_text(encoding="utf-8").splitlines() if "[Chapter 3" not in line]
        timeline.write_text("\n".join(lines) + "\n", encoding="utf-8")
        out = self.doctor_text(proj)
        self.assertIn("Salt and Signal: chapter(s) 3 are promoted but have no Timeline entry", out)

    def test_coverage_hints_are_for_the_repository_not_for_users(self):
        out = self.doctor_text(EXAMPLE)
        self.assertNotIn("not covered", out)
        dev = subprocess.run([sys.executable, str(REPO / "tools" / "check_layout_v1.py"), str(EXAMPLE)],
                             capture_output=True, text=True, encoding="utf-8").stdout
        self.assertIn("series case not covered", dev)

    def test_fixtures_are_free_of_consistency_warnings(self):
        self.assertIn("0 error(s), 1 warning(s)", self.doctor_text(EXAMPLE))  # only the stray chapter file
        self.assertIn("0 error(s), 0 warning(s)", self.doctor_text(SYNTHETIC))

    def test_flags_old_framework_files_until_they_are_retired(self):
        proj = self.copy(LEGACY)
        r = run("wr_doctor", "--root", proj)
        self.assertIn("old framework files are still in the project", r.stdout)
        self.assertIn(".claude/agents", r.stdout)
        self.assertEqual(r.returncode, 0)  # a warning, not an error
        run("wr_migrate", "--root", proj, "--apply", "--retire-legacy")
        self.assertNotIn("old framework files", run("wr_doctor", "--root", proj).stdout)

    def test_clean_project_has_no_legacy_warning(self):
        self.assertNotIn("old framework files", run("wr_doctor", "--root", EXAMPLE).stdout)

    def test_no_project_exit_code(self):
        empty = self.tmp / "empty"
        empty.mkdir()
        self.assertEqual(run("wr_doctor", cwd=empty).returncode, 2)


class CreateSnapshot(Tmp):
    def test_writes_into_the_discovered_root_not_the_cwd(self):
        proj = self.copy(EXAMPLE)
        elsewhere = self.tmp / "elsewhere"
        elsewhere.mkdir()
        r = run("create_snapshot", "--root", proj, "--world", WORLD, "--position", "3",
                "--story", "Test Story", "--unit", "Full Story", cwd=elsewhere)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((proj / WORLD / "snapshots" / "3" / "manifest.md").is_file())
        self.assertEqual(list(elsewhere.iterdir()), [])


class ScriptsInsideProject(Tmp):
    """Legacy habit: scripts live in <project>/scripts and are invoked from anywhere."""

    def test_script_relative_discovery_still_works(self):
        proj = self.copy(LEGACY)
        shutil.rmtree(proj / "scripts")
        shutil.copytree(SCRIPTS, proj / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
        elsewhere = self.tmp / "elsewhere"
        elsewhere.mkdir()
        r = subprocess.run([sys.executable, str(proj / "scripts" / "query_position.py"), "--world", WORLD,
                            "--story", "The Tallow Ledger", "--format", "json"],
                           cwd=elsewhere, capture_output=True, text=True, encoding="utf-8",
                           env={k: v for k, v in os.environ.items() if k != "WRITING_ROOM_ROOT"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["position"], 1)



class FrictionRegressions(Tmp):
    """Failure cases from a recorded local-model run (story-local files, style hints, long output)."""

    STORY = "stories/Salt and Signal"

    def bible(self, proj, *args):
        return run("load_bible", "--root", proj, "--story", self.STORY, "--world", WORLD,
                   "--no-last-chapter", "--no-timeline", "--no-schemes", "--no-facts", *args)

    def test_flat_story_local_file_is_named_not_silently_skipped(self):
        proj = self.copy(EXAMPLE)
        (proj / self.STORY / "state" / "bible" / "Doran Pike.md").write_text("# Doran Pike (flat)\n", encoding="utf-8")
        r = self.bible(proj, "--no-style", "--position", "1", "--char", "Doran Pike")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("state/bible/Doran Pike.md is outside state/bible/characters/ and was NOT loaded", r.stdout)
        self.assertIn("[snapshot pos 1]", r.stdout)
        self.assertNotIn("(flat)", r.stdout)

    def test_flat_and_typed_copies_both_exist(self):
        proj = self.copy(EXAMPLE)
        (proj / self.STORY / "state" / "bible" / "Mara Quill.md").write_text("# Mara Quill (flat)\n", encoding="utf-8")
        r = self.bible(proj, "--no-style", "--char", "Mara Quill")
        self.assertIn("Mara Quill.md is outside state/bible/characters/", r.stdout)
        self.assertIn("[story-local]", r.stdout)

    def test_doctor_reports_flat_story_local_files_but_not_description(self):
        proj = self.copy(EXAMPLE)
        bible = proj / self.STORY / "state" / "bible"
        (bible / "Doran Pike.md").write_text("x", encoding="utf-8")
        (bible / "DESCRIPTION.md").write_text("# Description\n", encoding="utf-8")
        r = run("wr_doctor", "--root", proj)
        self.assertEqual(r.returncode, 1)
        self.assertIn("state/bible/Doran Pike.md is outside the entity folders", r.stdout)
        self.assertNotIn("state/bible/DESCRIPTION.md is outside", r.stdout)

    def test_unknown_style_is_refused_even_with_one_style_file(self):
        r = self.bible(EXAMPLE, "--style", "Ashen Ledger")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('No style file matches "Ashen Ledger"; nothing was loaded', r.stdout)
        self.assertNotIn("FILE: Style:", r.stdout)

    def test_matching_style_with_one_file_still_loads(self):
        r = self.bible(EXAMPLE, "--style", "Default")
        self.assertIn("FILE: Style: writing_concepts/styles/Default Style.md", r.stdout)

    def test_output_file_and_receipt(self):
        proj = self.copy(EXAMPLE)
        args = ["--story", self.STORY, "--world", WORLD, "--position", "1",
                "--char", "Mara Quill", "--char", "Doran Pike", "--char", "Nobody"]
        full = run("load_bible", "--root", proj, *args).stdout
        r = run("load_bible", "--root", proj, *args, "--output", "current_chapter/.context.md")
        self.assertEqual(r.returncode, 0, r.stderr)
        saved = (proj / "current_chapter" / ".context.md").read_bytes().decode("utf-8")
        self.assertEqual(saved, full)
        self.assertNotIn("═", r.stdout)  # only the receipt is printed
        self.assertIn(f"{saved.count(chr(10))} lines", r.stdout)
        self.assertIn("entity: characters/Mara Quill [story-local]", r.stdout)
        self.assertIn("entity: characters/Doran Pike [snapshot] — worlds/Harrowmere/snapshots/1/characters/Doran Pike.md", r.stdout)
        self.assertIn("⚠ entity: characters/Nobody — NOT FOUND", r.stdout)
        lines = saved.split("\n")
        for row in r.stdout.splitlines():
            if "Mara Quill [story-local]" in row:
                start, end = map(int, row.split()[1].split("-"))
                self.assertIn("FILE: characters/Mara Quill", "\n".join(lines[start - 1:end]))

    def test_bare_output_goes_to_the_work_folder_with_an_absolute_path(self):
        proj = self.copy(EXAMPLE)
        sub = proj / self.STORY / "chapters"  # run from inside the story: the result must not depend on the cwd
        r = run("load_bible", "--story", self.STORY, "--world", WORLD, "--no-style", "--char", "Mara Quill",
                "--output", cwd=sub)
        self.assertEqual(r.returncode, 0, r.stderr)
        saved = proj / ".writing-room-work" / "stories" / "Salt and Signal" / "load_bible.md"
        self.assertTrue(saved.is_file())
        self.assertIn(f"Wrote {saved.resolve()} —", r.stdout)
        self.assertEqual((proj / ".writing-room-work" / ".gitignore").read_text(encoding="utf-8").splitlines()[-1], "*")
        self.assertIn("0 error(s)", run("wr_doctor", "--root", proj).stdout)

    def test_load_world_output_receipt_has_block_ranges(self):
        proj = self.copy(EXAMPLE)
        args = ["--world", WORLD, "--position", "1", "--entity", "characters/Mara Quill", "--entity", "characters/Nobody"]
        full = run("load_world", "--root", proj, *args).stdout
        r = run("load_world", "--root", proj, *args, "--output")
        self.assertEqual(r.returncode, 0, r.stderr)
        saved = (proj / ".writing-room-work" / "worlds" / "Harrowmere" / "load_world.md").read_bytes().decode("utf-8")
        self.assertEqual(saved, full)
        self.assertIn("2 items, 1 warning(s)", r.stdout)
        lines = saved.split("\n")
        ranges = [tuple(map(int, row.split()[1].split("-"))) for row in r.stdout.splitlines() if row.startswith("  lines ")]
        self.assertEqual(ranges[0][0], 1)
        self.assertEqual(ranges[0][1] + 1, ranges[1][0])
        self.assertIn("FILE: characters/Mara Quill", "\n".join(lines[ranges[0][0] - 1:ranges[0][1]]))
        self.assertIn("Nobody", "\n".join(lines[ranges[1][0] - 1:ranges[1][1]]))

    def test_story_after_a_book_takes_the_books_first_row_as_baseline(self):
        proj = self.copy(EXAMPLE)
        order = proj / "worlds" / "Harrowmere" / "WORLD_ORDER.md"
        row = "| 2 | [[Salt and Signal]] | Full Story | Early winter, the same year | Complete | The sealed room |"
        text = order.read_text(encoding="utf-8")
        self.assertIn(row, text)
        book = "\n".join(f"| {1 + n} | [[Salt and Signal]] | Ch. {n} | Early winter | Complete | |" for n in range(1, 5))
        order.write_text(text.replace(row, book + "\n| 6 | [[Next Tale]] | TBD | Spring | Planned | |"), encoding="utf-8")

        def query(story):
            r = run("query_position", "--root", proj, "--world", WORLD, "--story", story, "--format", "json")
            self.assertEqual(r.returncode, 0, r.stderr)
            return json.loads(r.stdout)

        nxt = query("Next Tale")
        self.assertEqual((nxt["before"]["position"], nxt["before"]["story"]), (2, "Salt and Signal"))
        book_q = query("Salt and Signal")  # the book itself: found at its first row, baseline is the story before
        self.assertEqual((book_q["position"], book_q["before"]["position"]), (2, 1))


class LoadBiblePresets(Tmp):
    """load_bible --for: the short form skills use, which works out the world, baseline and structure."""

    LONG = {  # each preset's long-form flags, as the skills passed them before presets existed
        "planner": ["--no-last-chapter", "--structure", "Freytag's Pyramid"],
        "draft-writer": [],
        "reviewer-consistency": ["--no-style", "--no-last-chapter", "--description"],
        "reviewer-character": ["--no-style", "--no-last-chapter", "--no-timeline"],
        "draft-fixer": ["--no-last-chapter", "--no-timeline",
                        "--reviews-dir", "stories/Salt and Signal/current_chapter/current_reviews"],
        "story-analyzer": ["--no-style", "--no-last-chapter", "--hooks"],
    }

    @staticmethod
    def without_context(text):
        """The output minus the leading CONTEXT block."""
        head = "\n" + "═" * 60 + "\nCONTEXT for "
        assert text.startswith(head), text[:200]
        end = text.index("═" * 60 + "\n", len(head)) + 61
        return text[end:]

    def test_every_preset_prints_what_its_long_form_prints(self):
        entities = ["--char", "Mara Quill", "--loc", "The Ashwood"]
        for preset, flags in self.LONG.items():
            with self.subTest(preset=preset):
                short = run("load_bible", "--root", EXAMPLE, "--for", preset, "--story", "Salt and Signal", *entities)
                self.assertEqual(short.returncode, 0, short.stderr)
                long = run("load_bible", "--root", EXAMPLE, "--story", "stories/Salt and Signal", "--world", WORLD,
                           "--position", "1", *flags, *entities)
                self.assertEqual(self.without_context(short.stdout), long.stdout)

    def test_context_block_says_what_was_worked_out(self):
        r = run("load_bible", "--root", EXAMPLE, "--for", "planner", "--story", "stories/Salt and Signal")
        self.assertIn("CONTEXT for planner — story: stories/Salt and Signal", r.stdout)
        self.assertIn("World: worlds/Harrowmere  (from stories/Salt and Signal/CONCEPT.md)", r.stdout)
        self.assertIn("Baseline: snapshot position 1  (from worlds/Harrowmere/WORLD_ORDER.md", r.stdout)
        self.assertIn("Structure: Freytag's Pyramid  (from stories/Salt and Signal/CONCEPT.md)", r.stdout)

    def test_first_story_has_no_baseline(self):
        r = run("load_bible", "--root", EXAMPLE, "--for", "reviewer-character", "--story", "stories/The Tallow Ledger",
                "--char", "Hesk Varrow")
        self.assertIn("Baseline: none  (first story in worlds/Harrowmere/WORLD_ORDER.md)", r.stdout)
        self.assertIn("[world bible]", r.stdout)

    def test_given_values_win_and_none_turns_the_baseline_off(self):
        r = run("load_bible", "--root", EXAMPLE, "--for", "reviewer-character", "--story", "stories/Salt and Signal",
                "--position", "none", "--char", "Doran Pike")
        self.assertIn("Baseline: none  (--position none)", r.stdout)
        self.assertIn("[world bible]", r.stdout)
        r = run("load_bible", "--root", EXAMPLE, "--for", "reviewer-character", "--story", "stories/Salt and Signal",
                "--position", "2", "--char", "Doran Pike")
        self.assertIn("Baseline: snapshot position 2  (given)", r.stdout)
        self.assertIn("[snapshot pos 2]", r.stdout)

    def test_story_missing_from_world_order_warns_and_loads_the_current_world(self):
        proj = self.copy(EXAMPLE)
        shutil.copytree(proj / "stories" / "Salt and Signal", proj / "stories" / "Unlisted")
        r = run("load_bible", "--root", proj, "--for", "reviewer-character", "--story", "stories/Unlisted",
                "--char", "Mara Quill", "--output")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("BASELINE: ⚠ Story 'Unlisted' not found in worlds/Harrowmere/WORLD_ORDER.md", r.stdout)

    def test_no_world_line_is_a_clear_error(self):
        proj = self.copy(EXAMPLE)
        concept = proj / "stories" / "Salt and Signal" / "CONCEPT.md"
        concept.write_text(concept.read_text(encoding="utf-8").replace("**World:**", "**Setting:**"), encoding="utf-8")
        r = run("load_bible", "--root", proj, "--for", "draft-writer", "--story", "stories/Salt and Signal")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("has no **World:** line", r.stderr)
        self.assertIn('--world "worlds/<World>"', r.stderr)

    def test_unknown_story_is_a_clear_error(self):
        r = run("load_bible", "--root", EXAMPLE, "--for", "draft-writer", "--story", "Nope")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('no story folder at "Nope"', r.stderr)

    def test_book_of_a_series_takes_the_world_from_the_series_concept(self):
        r = run("load_bible", "--root", SYNTHETIC, "--for", "draft-writer",
                "--story", "stories/Test Series/Book 01 - Opening")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("World: worlds/Test World  (from stories/Test Series/CONCEPT.md)", r.stdout)
        self.assertIn("Baseline: snapshot position 1", r.stdout)
        self.assertIn("The first day.", r.stdout)

    def test_long_form_has_no_context_block(self):
        r = run("load_bible", "--root", EXAMPLE, "--story", "stories/Salt and Signal", "--world", WORLD, "--no-style")
        self.assertNotIn("CONTEXT for", r.stdout)

    def test_recipes_list_every_preset_without_a_project(self):
        empty = self.tmp / "empty"
        empty.mkdir()
        r = run("load_bible", "--recipes", cwd=empty)
        self.assertEqual(r.returncode, 0, r.stderr)
        for preset in self.LONG:
            self.assertIn(f"--for {preset} --story", r.stdout)
        self.assertIn("stands for: --world <from CONCEPT.md> --position <baseline> --no-style --no-last-chapter --hooks",
                      r.stdout)


class LoadWorldPresets(Tmp):
    """load_world --for: one call per step for the story-ideator and outliner, with the SUMMARY.md check done."""

    @staticmethod
    def after_context(text):
        """The output from the first FILE block on (drops the CONTEXT block)."""
        return text[text.index("\n" + "═" * 60 + "\nFILE:"):]

    def test_ideator_preset_is_the_world_overview_short_structures_and_a_summary_check(self):
        short = run("load_world", "--root", EXAMPLE, "--for", "story-ideator", "--world", "Harrowmere")
        self.assertEqual(short.returncode, 0, short.stderr)
        plain = run("load_world", "--root", EXAMPLE, "--world", WORLD).stdout
        body = self.after_context(short.stdout)
        world_part = plain[:plain.index("FILE: story_structure/")]
        self.assertTrue(body.startswith(world_part), "the world files come first, unchanged")
        for name in ("GUIDE.md", "Format Reference.md"):  # in full
            start = plain.index(f"FILE: story_structure/{name}")
            end = plain.index("\n" + "═" * 60 + "\nFILE:", start)
            self.assertIn(plain[start:end], body)
        self.assertIn('FILE: story_structure/Three-Act Structure.md  (Overview only; the full file loads with '
                      '--structure "Three-Act Structure")', body)
        self.assertIn("**Best suited for:**", body)
        self.assertNotIn("## Act One — The Setup", body)
        self.assertLess(len(body), len(plain) * 0.6)
        self.assertIn("SUMMARY CHECK: SUMMARY.md matches the 16 entity files", body)
        self.assertNotIn("FILE: characters/", short.stdout)

    def test_structure_is_added_to_a_follow_up_load(self):
        r = run("load_world", "--root", EXAMPLE, "--world", "Harrowmere", "--entity", "characters/Mara Quill",
                "--structure", "Fichtean Curve")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("FILE: characters/Mara Quill", r.stdout)
        self.assertIn("FILE: story_structure/Fichtean Curve\n", r.stdout)
        self.assertIn("## Quick Reference", r.stdout)
        self.assertNotIn("FILE: DESCRIPTION.md", r.stdout)

    def test_stale_summary_loads_every_entity_in_the_same_call(self):
        proj = self.copy(EXAMPLE)
        (proj / "worlds" / "Harrowmere" / "characters" / "New Face.md").write_text("# New Face\n", encoding="utf-8")
        r = run("load_world", "--root", proj, "--for", "story-ideator", "--world", "Harrowmere",
                "--entity", "characters/Mara Quill")
        self.assertIn("SUMMARY CHECK: ⚠ SUMMARY.md is stale", r.stdout)
        self.assertIn("characters/ not listed: New Face", r.stdout)
        self.assertIn("FILE: characters/New Face  [world bible]", r.stdout)
        self.assertIn("FILE: factions/Harbor Guild  [world bible]", r.stdout)
        self.assertEqual(r.stdout.count("# Mara Quill\n"), 1)  # not loaded twice

    def test_missing_summary_loads_every_entity(self):
        proj = self.copy(EXAMPLE)
        (proj / "worlds" / "Harrowmere" / "SUMMARY.md").unlink()
        r = run("load_world", "--root", proj, "--for", "story-ideator", "--world", WORLD)
        self.assertIn("SUMMARY CHECK: ⚠ no SUMMARY.md — all 16 entity files are loaded below.", r.stdout)
        self.assertIn("FILE: characters/Mara Quill  [world bible]", r.stdout)

    def test_outliner_preset_takes_world_and_structure_from_the_concept(self):
        r = run("load_world", "--root", EXAMPLE, "--for", "outliner", "--story", "Salt and Signal",
                "--entity", "characters/Mara Quill", "--trope", "Redeemed Villain")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("World: worlds/Harrowmere  (from stories/Salt and Signal/CONCEPT.md)", r.stdout)
        self.assertIn("Structure: Freytag's Pyramid  (from stories/Salt and Signal/CONCEPT.md)", r.stdout)
        structure = run("load_world", "--root", EXAMPLE, "--world", WORLD, "--structure", "Freytag's Pyramid").stdout
        self.assertTrue(self.after_context(r.stdout).startswith(structure))
        for label in ("FILE: WORLD_ORDER.md", "SUMMARY CHECK: SUMMARY.md matches", "FILE: characters/Mara Quill",
                      "FILE: tropes/Redeemed Villain"):
            self.assertIn(label, r.stdout)
        self.assertNotIn("FILE: HOOKS.md", r.stdout)

    def test_entity_form_takes_craft_files_and_a_bare_world_name(self):
        r = run("load_world", "--root", EXAMPLE, "--world", "Harrowmere", "--entity", "characters/Mara Quill",
                "--trope", "Redeemed Villain", "--archetype", "The Mentor")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("FILE: characters/Mara Quill", r.stdout)
        self.assertIn("FILE: tropes/Redeemed Villain", r.stdout)
        self.assertIn("FILE: archetypes/The Mentor", r.stdout)
        self.assertNotIn("FILE: DESCRIPTION.md", r.stdout)

    def test_craft_files_alone_are_not_the_overview(self):
        r = run("load_world", "--root", EXAMPLE, "--world", WORLD, "--trope", "Redeemed Villain")
        self.assertIn("FILE: tropes/Redeemed Villain", r.stdout)
        self.assertNotIn("FILE: DESCRIPTION.md", r.stdout)

    def test_presets_explain_what_is_missing(self):
        r = run("load_world", "--root", EXAMPLE, "--for", "story-ideator")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('needs --world "<World>"', r.stderr)
        r = run("load_world", "--root", EXAMPLE, "--for", "outliner", "--story", "Nope")
        self.assertIn('no CONCEPT.md for "Nope"', r.stderr)


class NewStory(Tmp):
    """new_story.py: the story-ideator's bookkeeping in one call, all checks before any write."""

    def project(self, fmt="Novelette", world="Harrowmere"):
        import re
        proj = self.copy(EXAMPLE)
        concept = (WR / "shared" / "templates" / "story" / "concept.md").read_text(encoding="utf-8")
        concept = concept.replace("<World name>", world).replace("<Short Story / Novelette / Book / Book Series>", fmt)
        concept = re.sub(r"<[A-Z][^<>\n]*>", "Filled", concept)
        draft = proj / ".writing-room-work" / "worlds" / "Harrowmere" / "CONCEPT.md"
        draft.parent.mkdir(parents=True)
        draft.write_text(concept, encoding="utf-8")
        return proj, draft

    def test_creates_the_story_row_and_hook_status(self):
        proj, draft = self.project()
        r = run("new_story", "--root", proj, "--world", "Harrowmere", "--story", "Tide Debt", "--hook", "the third seal")
        self.assertEqual(r.returncode, 0, r.stderr)
        story = proj / "stories" / "Tide Debt"
        concept = (story / "CONCEPT.md").read_text(encoding="utf-8")
        self.assertIn("\n# Tide Debt\n", concept)
        self.assertNotIn("# Filled", concept)
        for d in ("chapters", "current_chapter"):
            self.assertTrue((story / d).is_dir())
        self.assertIn("# Timeline — Tide Debt", (story / "state" / "Timeline.md").read_text(encoding="utf-8"))
        for f in ("ACTIVE_SCHEMES.md", "STORY_FACTS.md"):
            self.assertNotIn("<Story Name>", (story / "state" / f).read_text(encoding="utf-8"))
        order = (proj / "worlds" / "Harrowmere" / "WORLD_ORDER.md").read_text(encoding="utf-8")
        self.assertIn("| 2 | [[Salt and Signal]] |", order)
        self.assertIn("| 3 | [[Tide Debt]] | Full Story | — | Not Started | |", order)
        self.assertIn("added at position 3", order)
        hooks = (proj / "worlds" / "Harrowmere" / "HOOKS.md").read_text(encoding="utf-8")
        self.assertIn("- **Status:** `In Use (Tide Debt)`", hooks)
        self.assertFalse(draft.exists(), "the draft is removed once copied")
        self.assertEqual(run("query_position", "--root", proj, "--world", WORLD, "--story", "Tide Debt",
                             "--format", "json").returncode, 0)

    def test_book_row_and_position_order(self):
        proj, _ = self.project(fmt="Book")
        r = run("new_story", "--root", proj, "--world", WORLD, "--story", "stories/Long Tide", "--position", "1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("concurrent with [[The Tallow Ledger]]", r.stdout)
        order = (proj / "worlds" / "Harrowmere" / "WORLD_ORDER.md").read_text(encoding="utf-8")
        rows = [line for line in order.splitlines() if line.startswith("| ") and "[[" in line]
        self.assertEqual(rows[1], "| 1 | [[Long Tide]] | TBD | — | Not Started | Placeholder — expand after Outliner |")
        self.assertIn("[[Salt and Signal]]", rows[2])

    def test_replaces_the_placeholder_row_of_an_empty_world_keeping_crlf(self):
        proj, _ = self.project()
        order = proj / "worlds" / "Harrowmere" / "WORLD_ORDER.md"
        text = order.read_text(encoding="utf-8")
        sep = text.index("|----------|")
        sep_end = text.index("\n", sep)
        table_end = text.index("\n\n---", sep)
        text = text[:sep_end + 1] + "| — | — | — | — | — | — |" + text[table_end:]
        order.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
        r = run("new_story", "--root", proj, "--world", WORLD, "--story", "Tide Debt")
        self.assertEqual(r.returncode, 0, r.stderr)
        text = order.read_bytes().decode("utf-8")
        self.assertIn("|-------|\r\n| 1 | [[Tide Debt]] | Full Story | — | Not Started | |\r\n", text)
        self.assertNotIn("| — | — |", text)
        self.assertNotIn("\r\r", text)

    def test_refuses_and_changes_nothing(self):
        proj, draft = self.project()
        before = {p: p.read_bytes() for p in (proj / "worlds").rglob("*.md")}
        draft.write_text("<!-- draft: not yet approved -->\n" + draft.read_text(encoding="utf-8") + "\n<Left Over>\n",
                         encoding="utf-8")
        r = run("new_story", "--root", proj, "--world", WORLD, "--story", "Salt and Signal", "--hook", "No Such Hook")
        self.assertEqual(r.returncode, 1)
        for problem in ("stories/Salt and Signal already exists", "<Left Over>", "still marked as a draft",
                        "not found in HOOKS.md: No Such Hook", "[[Salt and Signal]] is already in WORLD_ORDER.md"):
            self.assertIn(problem, r.stderr)
        self.assertEqual(before, {p: p.read_bytes() for p in (proj / "worlds").rglob("*.md")})
        self.assertTrue(draft.exists())

    def test_wrong_world_in_concept_and_missing_draft(self):
        proj, draft = self.project(world="Elsewhere")
        r = run("new_story", "--root", proj, "--world", WORLD, "--story", "Tide Debt")
        self.assertIn("**World:** is 'Elsewhere', not 'Harrowmere'", r.stderr)
        draft.write_text(draft.read_text(encoding="utf-8").replace("Novelette", "Novella"), encoding="utf-8")
        r = run("new_story", "--root", proj, "--world", WORLD, "--story", "Tide Debt")
        self.assertIn("**Format:** is 'Novella'", r.stderr)
        draft.unlink()
        r = run("new_story", "--root", proj, "--world", WORLD, "--story", "Tide Debt")
        self.assertIn("no concept at .writing-room-work/worlds/Harrowmere/CONCEPT.md", r.stderr)
        self.assertFalse((proj / "stories" / "Tide Debt").exists())

    def test_dry_run_writes_nothing(self):
        proj, draft = self.project()
        r = run("new_story", "--root", proj, "--world", WORLD, "--story", "Tide Debt", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Dry run — would write:", r.stdout)
        self.assertFalse((proj / "stories" / "Tide Debt").exists())
        self.assertTrue(draft.exists())


class WorldOrder(Tmp):
    """world_order.py: every WORLD_ORDER.md row change in one call, unchanged rows kept byte for byte."""

    def story(self, name, fmt, total=None):
        proj = self.proj
        d = proj / "stories" / name
        d.mkdir(parents=True)
        (d / "CONCEPT.md").write_text(f"# {name}\n\n- **World:** Harrowmere\n- **Format:** {fmt}\n", encoding="utf-8")
        if total:
            (d / "OUTLINE.md").write_text(f"# {name}\n\n- **Total chapters:** {total}\n", encoding="utf-8")

    def order(self):
        return (self.proj / "worlds" / "Harrowmere" / "WORLD_ORDER.md").read_text(encoding="utf-8")

    def rows(self):
        return [line for line in self.order().splitlines() if line.startswith("| ") and "[[" in line]

    def wo(self, *args):
        return run("world_order", *args[:1], "--root", self.proj, "--world", "Harrowmere", *args[1:])

    def setUp(self):
        super().setUp()
        self.proj = self.copy(EXAMPLE)

    def test_full_story_is_complete_only_after_its_last_chapter(self):
        self.story("Tide Debt", "Novelette", total=3)
        self.assertEqual(self.wo("add", "--story", "Tide Debt", "--unit", "Full Story").returncode, 0)
        r = self.wo("chapter", "--story", "Tide Debt", "--chapter", "1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Story complete: no", r.stdout)
        self.assertEqual(self.rows()[2], "| 3 | [[Tide Debt]] | Full Story | — | In Progress | |")
        r = self.wo("chapter", "--story", "Tide Debt", "--chapter", "3")
        self.assertIn("Story complete: yes", r.stdout)
        self.assertEqual(self.rows()[2], "| 3 | [[Tide Debt]] | Full Story | — | Complete | |")
        self.assertIn("after [[Tide Debt]] Chapter 3 analyzed (story complete)", self.order())

    def test_book_chapters_fill_the_tbd_row_then_shift_later_rows(self):
        self.story("Long Tide", "Book", total=2)
        before = self.rows()
        r = self.wo("add", "--story", "Long Tide", "--unit", "TBD", "--position", "1", "--notes", "Placeholder — expand after Outliner")
        self.assertIn("concurrent with [[The Tallow Ledger]]", r.stdout)
        r = self.wo("chapter", "--story", "Long Tide", "--chapter", "1")
        self.assertIn("TBD → Ch. 1, Complete", r.stdout)
        self.assertIn("Story complete: no", r.stdout)
        r = self.wo("chapter", "--story", "Long Tide", "--chapter", "2")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Story complete: yes", r.stdout)
        self.assertEqual(self.rows(), [
            before[0],
            "| 1 | [[Long Tide]] | Ch. 1 | — | Complete | |",
            "| 2 | [[Long Tide]] | Ch. 2 | — | Complete | |",
            before[1].replace("| 2 |", "| 3 |", 1),
        ])
        r = self.wo("status", "--story", "Long Tide", "--to", "In Progress")
        self.assertEqual(r.returncode, 1)
        self.assertIn("has 2 rows (Ch. 1, Ch. 2); name one with --unit", r.stderr)

    def test_move_shift_renumber_and_status(self):
        r = self.wo("move", "--story", "The Tallow Ledger", "--to", "5")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([row.split("|")[1].strip() for row in self.rows()], ["2", "5"])
        self.assertEqual(self.wo("renumber").returncode, 0)
        self.assertEqual([row.split("|")[2].strip() for row in self.rows()], ["[[Salt and Signal]]", "[[The Tallow Ledger]]"])
        self.assertEqual([row.split("|")[1].strip() for row in self.rows()], ["1", "2"])
        r = self.wo("add", "--story", "Prelude", "--unit", "Full Story", "--position", "1", "--shift")
        self.assertIn("rows from position 1 on moved down by one", r.stdout)
        self.assertEqual([row.split("|")[1].strip() for row in self.rows()], ["1", "2", "3"])
        self.wo("status", "--story", "Prelude", "--to", "In Progress")
        self.assertEqual(self.rows()[0], "| 1 | [[Prelude]] | Full Story | — | In Progress | |")

    def test_refusals_and_dry_run_change_nothing(self):
        before = self.order()
        for args, problem in ((("status", "--story", "Nobody", "--to", "Complete"), "no row for [[Nobody]]"),
                              (("add", "--story", "Salt and Signal", "--unit", "Full Story"), "already has a Full Story row"),
                              (("chapter", "--story", "Nobody", "--chapter", "1"), "no CONCEPT.md at stories/Nobody")):
            r = self.wo(*args)
            self.assertEqual(r.returncode, 1, args)
            self.assertIn(problem, r.stderr)
        r = self.wo("move", "--story", "Salt and Signal", "--to", "1", "--dry-run")
        self.assertIn("Dry run — would change", r.stdout)
        self.assertIn("concurrent with [[The Tallow Ledger]]", r.stdout)
        self.assertEqual(before, self.order())



class WrPaths(Tmp):
    """wr_paths.py: AGENTS.md names the framework folder; the doctor checks it; the rest of the file is kept."""

    def setUp(self):
        super().setUp()
        sys.path.insert(0, str(SCRIPTS))
        import wr_paths
        self.wp = wr_paths
        self.proj = self.copy(EXAMPLE)
        self.wr = self.proj / ".agents" / "skills" / "writing-room"
        shutil.copytree(WR, self.wr, ignore=shutil.ignore_patterns("__pycache__"))
        self.agents = self.proj / "AGENTS.md"
        self.agents.write_bytes(b"# Project\r\n\r\nIntro.\r\n\r\n## Rules\r\n\r\nKeep.\r\n")

    def test_write_is_relative_idempotent_keeps_crlf_and_strips_back(self):
        before = self.agents.read_bytes()
        self.assertEqual(self.wp.write(self.proj), ("added", ".agents/skills/writing-room"))
        data = self.agents.read_bytes()
        self.assertNotIn(b"\n", data.replace(b"\r\n", b""))  # CRLF kept throughout
        text = data.decode("utf-8")
        self.assertLess(text.index("## Writing Room paths"), text.index("## Rules"))
        self.assertIn("relative to the project root", text)
        self.assertEqual(self.wp.write(self.proj)[0], "unchanged")
        self.assertEqual(self.wp.strip(text.replace("\r\n", "\n")), before.decode("utf-8").replace("\r\n", "\n"))
        self.assertEqual(self.wp.read(self.proj), (".agents/skills/writing-room", True))

    def test_outside_install_is_absolute(self):
        status, shown = self.wp.write(self.proj, WR)
        self.assertEqual(status, "added")
        self.assertEqual(shown, WR.resolve().as_posix())
        self.assertIn("These are absolute paths.", self.agents.read_text(encoding="utf-8"))

    def test_doctor_reports_a_missing_or_broken_block_and_wr_paths_repairs_it(self):
        out = run("wr_doctor", "--root", self.proj).stdout
        self.assertIn("AGENTS.md has no Writing Room paths block", out)
        self.wp.write(self.proj)
        text = self.agents.read_text(encoding="utf-8").replace("`<WR>` = `.agents/skills/writing-room`",
                                                              "`<WR>` = `gone/writing-room`")
        self.agents.write_text(text, encoding="utf-8")
        r = run("wr_doctor", "--root", self.proj)
        self.assertEqual(r.returncode, 1)
        self.assertIn("AGENTS.md says the framework (<WR>) is `gone/writing-room`", r.stdout)
        self.assertEqual(run("wr_paths", "--root", self.proj, "--check").returncode, 1)
        r = run("wr_paths", "--root", self.proj)
        self.assertIn("Updated the Writing Room paths block in AGENTS.md: <WR> = .agents/skills/writing-room", r.stdout)
        self.assertEqual(run("wr_paths", "--root", self.proj, "--check").returncode, 0)
        out = run("wr_doctor", "--root", self.proj).stdout
        self.assertIn("wr_paths  : .agents/skills/writing-room", out)
        self.assertNotIn("AGENTS.md says", out)
        self.assertNotIn("has no Writing Room paths block", out)

    def test_no_agents_md_is_not_a_warning(self):
        self.agents.unlink()
        out = run("wr_doctor", "--root", self.proj).stdout
        self.assertIn("no AGENTS.md (skills look for writing-room beside their own folder)", out)
        self.assertEqual(run("wr_paths", "--root", self.proj).returncode, 1)
        self.assertFalse(self.agents.exists())

if __name__ == "__main__":
    unittest.main()


class ConceptFrontmatter(Tmp):
    """Optional CONCEPT.md frontmatter (world, status) mirrors the body fields; the doctor flags drift."""

    def _copy(self):
        d = self.tmp / "proj"
        shutil.copytree(EXAMPLE, d)
        return d

    def _concept(self, d):
        return next(d.glob("stories/*/CONCEPT.md"))

    def test_matching_frontmatter_is_clean(self):
        d = self._copy()
        c = self._concept(d)
        import re
        t = c.read_text(encoding="utf-8")
        world = re.search(r"\*\*World:\*\*\s*(.+)", t).group(1).strip()
        status = re.search(r"\*\*Status:\*\*\s*`?([A-Za-z ]+?)`?\s*(?:$|\n|\*)", t).group(1).strip()
        c.write_bytes((f"---\nworld: {world}\nstatus: {status}\n---\n\n" + t).encode("utf-8"))
        r = run("wr_doctor", "--root", d)
        self.assertNotIn("frontmatter", r.stdout, r.stdout)

    def test_drifting_frontmatter_warns(self):
        d = self._copy()
        c = self._concept(d)
        c.write_bytes(("---\nworld: Nowhere\nstatus: Concept\n---\n\n" + c.read_text(encoding="utf-8")).encode("utf-8"))
        r = run("wr_doctor", "--root", d)
        self.assertEqual(r.returncode, 0, r.stdout)   # a warning, never an error
        self.assertIn("frontmatter world 'Nowhere'", r.stdout)

    def test_template_has_frontmatter(self):
        t = (WR / "shared" / "templates" / "story" / "concept.md").read_text(encoding="utf-8")
        self.assertTrue(t.startswith("---\nworld: <World name>\nstatus: Concept\n---\n"))


class StaleTemplates(Tmp):
    """wr_templates.py: unedited copies of shipped templates are found and moved aside; edited ones are kept."""

    def project(self):
        proj = self.copy(EXAMPLE)
        shared = WR / "shared" / "templates" / "story"
        legacy = LEGACY / "templates" / "story"
        (proj / "templates" / "story").mkdir(parents=True, exist_ok=True)
        shutil.copy(legacy / "chapter_plan.md", proj / "templates" / "story" / "chapter_plan.md")  # older
        shutil.copy(shared / "outline.md", proj / "templates" / "story" / "outline.md")  # same
        (proj / "templates" / "story" / "concept.md").write_text("# Mine\n", encoding="utf-8")  # edited
        return proj

    def test_lists_retires_and_the_doctor_warns(self):
        proj = self.project()
        r = run("wr_templates", "--root", proj)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Older framework version (hides the current one): 1\n  templates/story/chapter_plan.md", r.stdout)
        self.assertIn("Same as the framework's current copy: 1\n  templates/story/outline.md", r.stdout)
        self.assertIn("Edited or your own (kept): 1\n  templates/story/concept.md", r.stdout)
        doctor = run("wr_doctor", "--root", proj).stdout
        self.assertIn("1 project template/craft file(s) are unchanged copies of an older framework version", doctor)
        self.assertIn("templates/story/chapter_plan.md", doctor)
        self.assertTrue((proj / "templates" / "story" / "chapter_plan.md").exists(), "listing changes nothing")

        r = run("wr_templates", "--root", proj, "--retire")
        self.assertIn("Moved 2 file(s) to .writing-room-legacy/", r.stdout)
        self.assertEqual(sorted(p.name for p in (proj / "templates" / "story").iterdir()), ["concept.md"])
        arch = proj / ".writing-room-legacy" / "templates" / "story"
        self.assertEqual((arch / "chapter_plan.md").read_bytes(), (LEGACY / "templates" / "story" / "chapter_plan.md").read_bytes())
        resolved = run("wr_resolve", "--root", proj, "templates/story/chapter_plan.md").stdout.strip()
        self.assertTrue(Path(resolved).is_relative_to(WR), resolved)
        self.assertNotIn("template/craft", run("wr_doctor", "--root", proj).stdout)

    def test_crlf_copy_still_counts_as_unedited(self):
        proj = self.project()
        f = proj / "templates" / "story" / "chapter_plan.md"
        f.write_bytes(f.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
        self.assertIn("Older framework version", run("wr_templates", "--root", proj).stdout)

    def test_every_shipped_template_is_recorded(self):
        r = subprocess.run([sys.executable, str(REPO / "tools" / "record_templates.py"), "--check"],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stdout + "\nRun: python tools/record_templates.py")
