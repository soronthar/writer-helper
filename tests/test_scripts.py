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
        # user content, templates and the style folder are exactly as before
        self.assertEqual(self.retire_tree(proj), before_content)
        self.assertTrue((proj / "templates").is_dir())
        self.assertTrue((proj / "writing_concepts").is_dir())
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
