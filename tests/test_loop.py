"""Phase 3 tests: wr_next, the full chapter loop, router coverage, project guidance files.

Run with:  python -m unittest discover -s tests -v
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WR = REPO / "skills" / "writing-room"
SCRIPTS = WR / "scripts"
SYNTHETIC = REPO / "fixtures" / "synthetic-v1"
EXAMPLE = REPO / "examples" / "sample-project"


def run(script, *args, cwd=None):
    return subprocess.run([sys.executable, str(SCRIPTS / f"{script}.py"), *map(str, args)],
                          cwd=cwd, capture_output=True, text=True, encoding="utf-8")


def nxt(root, *extra):
    r = run("wr_next", "--root", root, "--json", *extra)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def unit(data, name):
    return next(u for u in data["units"] if u["name"] == name)


class WrNext(unittest.TestCase):
    def test_synthetic_project_states(self):
        d = nxt(SYNTHETIC)
        short = unit(d, "Short Piece")
        self.assertEqual(short["next_skill"], "draft-fixer")
        self.assertEqual(short["current"]["chapter"], 2)
        self.assertEqual(short["chapters_done"], 1)
        book = unit(d, "Test Series / Book 01 - Opening")
        self.assertEqual(book["next_skill"], "story-status")
        self.assertIn("without CHAPTER_PLAN.md", book["reason"])
        self.assertIsNone(d["recommended"])  # two stories in progress: the user chooses

    def test_paths_are_root_relative(self):
        for u in nxt(SYNTHETIC)["units"]:
            self.assertFalse(Path(u["path"]).is_absolute(), u["path"])

    def test_story_filter(self):
        d = nxt(SYNTHETIC, "--story", "stories/Short Piece")
        self.assertEqual([u["name"] for u in d["units"]], ["Short Piece"])
        self.assertEqual(d["recommended"], "stories/Short Piece")

    def test_unknown_story(self):
        self.assertEqual(run("wr_next", "--root", SYNTHETIC, "--story", "stories/Nope").returncode, 1)

    def test_finished_and_consolidated_stories_need_nothing(self):
        d = nxt(EXAMPLE)
        for name in ("The Tallow Ledger", "Salt and Signal"):
            u = unit(d, name)
            self.assertIsNone(u["next_skill"], name)
            self.assertTrue(u["consolidated"], name)
        self.assertIsNone(d["recommended"])
        self.assertEqual(d["project"]["next_skill"], "story-ideator")  # everything is finished: start a new story

    def test_status_still_active_after_consolidation_is_flagged(self):
        # A real quirk of older projects: every chapter promoted and consolidated, CONCEPT still says Active.
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "p"
            shutil.copytree(EXAMPLE, proj)
            concept = proj / "stories" / "Salt and Signal" / "CONCEPT.md"
            concept.write_text(concept.read_text(encoding="utf-8").replace("`Complete`", "`Active`"), encoding="utf-8")
            u = unit(nxt(proj), "Salt and Signal")
            self.assertEqual(u["next_skill"], "writing-room")
            self.assertIn("Status to Complete", u["reason"])
            self.assertEqual(nxt(proj)["recommended"], "stories/Salt and Signal")

    def test_text_output(self):
        r = run("wr_next", "--root", SYNTHETIC)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("next skill: draft-fixer", r.stdout)
        self.assertIn("Several stories are in progress", r.stdout)

    def test_runs_from_a_subdirectory_without_root(self):
        r = run("wr_next", "--json", cwd=EXAMPLE / "stories" / "The Tallow Ledger" / "chapters")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["worlds"], ["Harrowmere"])

    def test_empty_project_needs_a_world_then_a_story(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "p"
            self.assertEqual(run("wr_init", proj).returncode, 0)
            self.assertEqual(nxt(proj)["project"]["next_skill"], "create-world")
            (proj / "worlds" / "W").mkdir()
            (proj / "worlds" / "W" / "DESCRIPTION.md").write_text("# W\n", encoding="utf-8")
            self.assertEqual(nxt(proj)["project"]["next_skill"], "story-ideator")

    def test_a_review_that_stopped_partway_goes_back_to_the_reviewer(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "p"
            shutil.copytree(SYNTHETIC, proj)
            reviews = proj / "stories" / "Short Piece" / "current_chapter" / "current_reviews"
            character = reviews / "Reviewer-Character.md"
            old = character.read_text(encoding="utf-8")
            self.assertNotIn("**Review status:**", old)  # older reports have no status line: finished

            def short():
                return unit(nxt(proj), "Short Piece")

            self.assertEqual(short()["next_skill"], "draft-fixer")
            character.unlink()  # stopped after the consistency pass
            u = short()
            self.assertEqual(u["next_skill"], "reviewer")
            self.assertIn("Reviewer-Character.md (not written yet)", u["reason"])
            character.write_text("# Reviewer — Character\n\n**Review status:** In progress — plan check done; "
                                 "character pass not yet run\n", encoding="utf-8")  # stopped during the character pass
            u = short()
            self.assertEqual(u["next_skill"], "reviewer")
            self.assertEqual(u["current"]["unfinished_reviews"], ["Reviewer-Character.md"])
            character.write_text("# Reviewer — Character\n\n**Review status:** Complete\n", encoding="utf-8")
            self.assertEqual(short()["next_skill"], "draft-fixer")

    def test_a_saved_working_draft_is_reported_for_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "p"
            shutil.copytree(SYNTHETIC, proj)
            cur = proj / "stories" / "Short Piece" / "current_chapter"
            (cur / "CONTENT.md").unlink()
            shutil.rmtree(cur / "current_reviews")

            def short():
                return unit(nxt(proj), "Short Piece")

            self.assertEqual(short()["reason"], "Chapter 2 is planned but not drafted.")
            self.assertIsNone(short()["current"]["working_draft"])
            work = proj / ".writing-room-work" / "stories" / "Short Piece" / "current_chapter"
            work.mkdir(parents=True)
            draft = work / "CONTENT.md"
            draft.write_text("<!-- draft: Chapter 2, 2 of 4 scenes saved; self-check: not started -->\n"
                             "<!-- scene 1 -->\nText.\n", encoding="utf-8")
            u = short()
            self.assertEqual(u["next_skill"], "draft-writer")
            self.assertIn("a working draft with 2 of 4 scenes saved", u["reason"])
            self.assertIn(".writing-room-work/stories/Short Piece/current_chapter/CONTENT.md", u["reason"])
            self.assertIn("resume", u["reason"])
            self.assertEqual(u["current"]["working_draft"]["saved"], 2)
            draft.write_text("<!-- draft: Chapter 2, 4 of 4 scenes saved; self-check: in progress -->\n", encoding="utf-8")
            self.assertIn("4 of 4 scenes saved (self-check: in progress)", short()["reason"])
            draft.write_text("<!-- draft: Chapter 1, 4 of 4 scenes saved; self-check: done -->\n", encoding="utf-8")
            u = short()  # left over from another chapter: not offered as this chapter's draft
            self.assertEqual(u["reason"], "Chapter 2 is planned but not drafted.")
            self.assertEqual(u["current"]["working_draft"]["stale_chapter"], 1)

    def test_fixes_that_stopped_partway_go_back_to_the_draft_fixer(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "p"
            shutil.copytree(SYNTHETIC, proj)
            log = proj / "stories" / "Short Piece" / "current_chapter" / "current_reviews" / "Draft-Fixer-Log.md"

            def short():
                return unit(nxt(proj), "Short Piece")

            self.assertEqual(short()["next_skill"], "draft-fixer")  # no log yet
            log.write_text("# Draft Fixer — Fix Log\n\n**Fix status:** In progress — 2 of 5 entries done\n", encoding="utf-8")
            u = short()
            self.assertEqual(u["next_skill"], "draft-fixer")
            self.assertIn("fixes stopped partway (2 of 5 entries done)", u["reason"])
            self.assertEqual(u["current"]["fixes_in_progress"], "2 of 5 entries done")
            self.assertFalse(u["current"]["fixed"])
            (log.parent / "Reviewer-Character.md").unlink()  # the author chose to fix a partial review
            self.assertEqual(short()["next_skill"], "draft-fixer")
            log.write_text("# Draft Fixer — Fix Log\n\n**Fix status:** Complete\n", encoding="utf-8")
            self.assertEqual(short()["next_skill"], "story-analyzer")
            log.write_text("# Draft Fixer — Fix Log\n\nOlder log without a status line.\n", encoding="utf-8")
            self.assertEqual(short()["next_skill"], "story-analyzer")

    def test_series_without_outline_needs_the_outliner(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "p"
            shutil.copytree(SYNTHETIC, proj)
            (proj / "stories" / "Test Series" / "SERIES_OUTLINE.md").unlink()
            series = next(u for u in nxt(proj)["units"] if u["kind"] == "series")
            self.assertEqual(series["next_skill"], "outliner")


class FullLoop(unittest.TestCase):
    """Walk a project through every stage the way the skills do, and check the router's answer at each step."""

    def test_two_chapter_story_from_concept_to_consolidated(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "p"
            self.assertEqual(run("wr_init", proj).returncode, 0)
            story = proj / "stories" / "Tale"
            world = proj / "worlds" / "Realm"
            rel = "stories/Tale"
            seen = []

            def step(expected, **kw):
                d = nxt(proj, "--story", rel)
                u = d["units"][0]
                got = u["next_skill"]
                seen.append(got)
                self.assertEqual(got, expected, f"after {seen[:-1]}: {u['reason']}")
                return u

            def put(path, text):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((text).encode("utf-8"))

            # create-world, story-ideator
            put(world / "DESCRIPTION.md", "# Realm\n")
            put(world / "HOOKS.md", "# Hooks\n")
            put(story / "CONCEPT.md", "# Tale\n- **World:** Realm\n- **Status:** `Concept`\n")
            put(story / "state" / "Timeline.md", "# Timeline\n\n## Events\n\n*(No entries yet.)*\n")
            step("outliner")

            # outliner
            put(story / "OUTLINE.md", "# Outline\n- **Total chapters:** 2\n")
            put(story / "CONCEPT.md", "# Tale\n- **World:** Realm\n- **Status:** `In Development`\n")

            for n in (1, 2):
                step("planner")
                put(story / "current_chapter" / "CHAPTER_PLAN.md", f"# Plan\n- **Chapter:** {n} of 2\n")
                step("draft-writer")
                put(story / "current_chapter" / "CONTENT.md", f"# Chapter {n}\n\nProse.\n")
                step("reviewer")
                put(story / "current_chapter" / "current_reviews" / "Reviewer-Consistency.md", "# R\n")
                put(story / "current_chapter" / "current_reviews" / "Reviewer-Character.md", "# R\n")
                step("draft-fixer")
                put(story / "current_chapter" / "current_reviews" / "Draft-Fixer-Log.md", "# Log\n")
                step("story-analyzer")
                tl = (story / "state" / "Timeline.md").read_text(encoding="utf-8")
                put(story / "state" / "Timeline.md", tl + f"- **[Chapter {n} — Title]** Something happened.\n")
                step("promote-chapter")
                r = run("promote_chapter", "--root", proj, "--story", rel, "--chapter", n)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertTrue((story / "chapters" / f"Chapter_{n:02d}.md").is_file())

            # all chapters promoted
            u = step("world-archivist")
            self.assertIn("set Status to Complete", u["reason"])
            put(story / "CONCEPT.md", "# Tale\n- **World:** Realm\n- **Status:** `Complete`\n")
            u = step("world-archivist")
            self.assertIn("consolidate", u["reason"])
            put(world / "TIMELINE.md", "# Timeline\n\n### [[Tale]] (Position 1)\n")
            step(None)

            expected = ["outliner", "planner", "draft-writer", "reviewer", "draft-fixer", "story-analyzer",
                        "promote-chapter", "planner", "draft-writer", "reviewer", "draft-fixer", "story-analyzer",
                        "promote-chapter", "world-archivist", "world-archivist", None]
            self.assertEqual(seen, expected)

    def test_the_loop_order_matches_the_skills_next_step_chain(self):
        order = ["planner", "draft-writer", "reviewer", "draft-fixer", "story-analyzer", "promote-chapter"]
        for cur, nxt_skill in zip(order, order[1:]):
            text = (REPO / "skills" / cur / "SKILL.md").read_text(encoding="utf-8")
            self.assertRegex(text, rf"\*\*Next step:\*\*[^\n]*`{nxt_skill}`", cur)


class RouterAndGuidance(unittest.TestCase):
    def skills(self):
        return sorted(p.name for p in (REPO / "skills").iterdir() if p.is_dir())

    def test_router_names_every_other_skill(self):
        router = (WR / "SKILL.md").read_text(encoding="utf-8")
        for name in self.skills():
            if name != "writing-room":
                self.assertIn(f"`{name}`", router, f"router does not mention {name}")

    def test_router_mentions_both_script_and_no_shell_paths(self):
        router = (WR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("<WR>/scripts/wr_next.py", router)
        self.assertIn("Without a shell", router)

    def test_no_deprecated_reviewer_skills(self):
        names = self.skills()
        self.assertNotIn("reviewer-consistency", names)
        self.assertNotIn("reviewer-character", names)
        self.assertIn("reviewer", names)

    def test_project_guidance_files(self):
        agents = (WR / "shared" / "project" / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("`writing-room`", agents)
        for name in ("planner", "draft-writer", "reviewer", "draft-fixer", "story-analyzer", "promote-chapter"):
            self.assertIn(name, agents)
        self.assertEqual((WR / "shared" / "project" / "CLAUDE.md").read_text(encoding="utf-8").strip(), "@AGENTS.md")
        self.assertEqual((REPO / "CLAUDE.md").read_text(encoding="utf-8").strip(), "@AGENTS.md")
        self.assertTrue((REPO / "AGENTS.md").is_file())

    def test_init_adds_guidance_without_overwriting(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "p"
            proj.mkdir()
            (proj / "AGENTS.md").write_text("MINE", encoding="utf-8")
            self.assertEqual(run("wr_init", proj).returncode, 0)
            self.assertTrue((proj / "AGENTS.md").read_text(encoding="utf-8").startswith("MINE\n"))
            self.assertIn("## Writing Room paths", (proj / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertEqual((proj / "CLAUDE.md").read_text(encoding="utf-8").strip(), "@AGENTS.md")

    def test_init_no_guidance(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "p"
            self.assertEqual(run("wr_init", proj, "--no-guidance").returncode, 0)
            self.assertFalse((proj / "AGENTS.md").exists())
            self.assertFalse((proj / "CLAUDE.md").exists())

    def test_every_skill_script_mentioned_exists(self):
        scripts = {p.name for p in SCRIPTS.glob("*.py")}
        for md in (REPO / "skills").rglob("*.md"):
            for name in re.findall(r"<WR>/scripts/([\w]+\.py)", md.read_text(encoding="utf-8")):
                self.assertIn(name, scripts, f"{md.name} references missing script {name}")


if __name__ == "__main__":
    unittest.main()
