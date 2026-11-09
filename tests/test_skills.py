"""Skill lint and promote_chapter tests.

Run with:  python -m unittest discover -s tests -v
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import lint_skills  # noqa: E402

WR = REPO / "skills" / "writing-room"
SYNTHETIC = REPO / "fixtures" / "synthetic-v1"


class SkillsLintClean(unittest.TestCase):
    def test_shipped_skills_pass_lint(self):
        errors, _warnings = lint_skills.lint(REPO / "skills")
        self.assertEqual(errors, [], "\n".join(errors))


class LintCatchesProblems(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="wr-lint-")
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self.root = Path(self._tmp)

    def skill(self, name, frontmatter, body="Body.\n"):
        d = self.root / name
        d.mkdir()
        (d / "SKILL.md").write_text(f"---\n{frontmatter}\n---\n{body}", encoding="utf-8")

    def errors(self):
        return "\n".join(lint_skills.lint(self.root)[0])

    def test_clean_skill_passes(self):
        self.skill("ok-skill", "name: ok-skill\ndescription: \"Does a thing.\"")
        self.assertEqual(self.errors(), "")

    def test_harness_frontmatter_rejected(self):
        self.skill("a", "name: a\ndescription: \"x\"\nmodel: claude-opus-4-6\ntools:")
        self.assertIn("frontmatter key 'model'", self.errors())
        self.assertIn("frontmatter key 'tools'", self.errors())

    def test_name_must_match_folder_and_pattern(self):
        self.skill("one", "name: two\ndescription: \"x\"")
        self.skill("Bad_Name", "name: Bad_Name\ndescription: \"x\"")
        out = self.errors()
        self.assertIn("does not match folder", out)
        self.assertIn("must match", out)

    def test_description_required_and_limited(self):
        self.skill("nodesc", "name: nodesc")
        self.skill("long", 'name: long\ndescription: "' + "x" * 1025 + '"')
        out = self.errors()
        self.assertIn("no description", out)
        self.assertIn("1025 chars", out)

    def test_unquoted_description_is_rejected(self):
        # "Status: Concept" inside an unquoted description is invalid YAML; harnesses silently drop the metadata.
        self.skill("colon", "name: colon\ndescription: Use when Status: Concept applies.")
        self.assertIn("must be a double-quoted string", self.errors())

    def test_banned_wording(self):
        body = ("Use Glob to find files, then invoke the Planner agent via the Task tool.\n"
                "Read [[Writing_Room/worlds/X]] and run /story-status.\n")
        self.skill("bad", "name: bad\ndescription: \"x\"", body)
        out = self.errors()
        for needle in ("tool name 'Glob'", "agent delegation", "subagent wording", "legacy root path",
                       "wiki-link to a path", "slash command"):
            self.assertIn(needle, out)

    def test_entity_wikilinks_and_fenced_blocks_are_allowed(self):
        body = "Link names like [[Mara Quill]].\n\n```\nUse Glob here; it is output text.\n```\n"
        self.skill("fine", "name: fine\ndescription: \"x\"", body)
        self.assertEqual(self.errors(), "")

    def test_missing_references_detected(self):
        self.skill("refs", "name: refs\ndescription: \"x\"", "See `references/nope.md`, `<WR>/references/nope.md` "
                   "and `../other/x.md`.\n")
        out = self.errors()
        self.assertIn("referenced file 'references/nope.md'", out)
        self.assertIn("referenced path '<WR>/references/nope.md' does not exist", out)
        self.assertIn("sibling-relative path '../other/'", out)


def promote(*args, root):
    return subprocess.run([sys.executable, str(WR / "scripts" / "promote_chapter.py"), "--root", str(root), *args],
                          capture_output=True, text=True, encoding="utf-8")


class PromoteChapter(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="wr-promote-")
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self.proj = Path(self._tmp) / "p"
        shutil.copytree(SYNTHETIC, self.proj)
        self.story = self.proj / "stories" / "Short Piece"

    def test_promotes_and_clears(self):
        content = (self.story / "current_chapter" / "CONTENT.md").read_bytes()
        r = promote("--story", "stories/Short Piece", "--chapter", "2", root=self.proj)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.story / "chapters" / "Chapter_02.md").read_bytes(), content)
        cur = self.story / "current_chapter"
        self.assertTrue(cur.is_dir())
        self.assertEqual(list(cur.iterdir()), [])
        # other chapters and state are untouched
        self.assertTrue((self.story / "chapters" / "Chapter_01.md").is_file())
        self.assertTrue((self.story / "state" / "Timeline.md").is_file())

    def test_dry_run_changes_nothing(self):
        before = sorted(str(p) for p in self.story.rglob("*"))
        r = promote("--story", "stories/Short Piece", "--chapter", "2", "--dry-run", root=self.proj)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Dry run", r.stdout)
        self.assertEqual(sorted(str(p) for p in self.story.rglob("*")), before)

    def test_refuses_to_overwrite_without_flag(self):
        r = promote("--story", "stories/Short Piece", "--chapter", "1", root=self.proj)
        self.assertEqual(r.returncode, 1)
        self.assertIn("--overwrite", r.stderr)
        self.assertTrue((self.story / "current_chapter" / "CONTENT.md").is_file())
        r = promote("--story", "stories/Short Piece", "--chapter", "1", "--overwrite", root=self.proj)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.story / "chapters" / "Chapter_01.md").read_text(encoding="utf-8"),
                         "# Chapter 2\n\nAda hid the ledger under the floor.\n")

    def test_missing_content_stops(self):
        (self.story / "current_chapter" / "CONTENT.md").unlink()
        r = promote("--story", "stories/Short Piece", "--chapter", "2", root=self.proj)
        self.assertEqual(r.returncode, 1)
        self.assertTrue((self.story / "current_chapter" / "CHAPTER_PLAN.md").is_file())

    def test_series_book(self):
        book = "stories/Test Series/Book 01 - Opening"
        r = promote("--story", book, "--chapter", "2", root=self.proj)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.proj / book / "chapters" / "Chapter_02.md").is_file())
        self.assertFalse((self.proj / book / "current_chapter" / "CONTENT.md").exists())

    def test_bad_chapter_number(self):
        r = promote("--story", "stories/Short Piece", "--chapter", "0", root=self.proj)
        self.assertEqual(r.returncode, 2)


LEGACY_AGENTS = REPO / "fixtures" / "legacy-v1" / ".claude" / "agents"

# Data-format phrases a converted skill must not lose: template field names and registry names
# that existing projects, plans and reviews use. Converting agent names to skill names must never touch them.
PROTECTED = {
    "planner": ["Notes for Draft Writer", "Structure Stage Checklist", "Subplot Directives", "World Order Position",
                "World baseline", "Style Directives", "Payoff Annotations", "ACTIVE_SCHEMES.md", "STORY_FACTS.md",
                "Opens with", "[FLAG]", "Dormant — do not advance", "Questions to answer"],
    "reviewer": ["Write Reviewer-Consistency.md", "Write Reviewer-Character.md", "Reviewer Notes", "PLAN VIOLATION",
                 "Suggested correction", "verify with author", "Verify with author", "Knowledge gaps",
                 "BASELINE_POS", "Critical", "Moderate", "Minor", "ACTIVE_SCHEMES.md", "STORY_FACTS.md",
                 "Current Status", "POV filter"],
    "draft-fixer": ["Verify with author", "Draft-Fixer-Log.md", "Applied Fixes", "Skipped Issues",
                    "Verify-with-Author Items", "Escalated to author", "Preview All", "Interactive", "Autonomous",
                    "Style Compliance Pass", "Conflict — superseded by Fix N.", "Could not be placed", "passage not found", "BASELINE_POS", "Forbidden Elements",
                    "ACTIVE_SCHEMES.md", "STORY_FACTS.md", "Knowledge gaps", "Specifics"],
    "story-analyzer": ["Knows (as of", "Payoff Annotations", "Unscheduled Payoff Setups", "Resolution Log",
                       "Superseded Log", "Last touched", "Honoured in Ch.", "Retired per plan in Ch.",
                       "Last synchronized", "Full Story", "TBD", "Case A", "Case B", "Case C", "Case D",
                       "In Use (", "Knowledge gaps", "Specifics", "Preview All", "Autonomous",
                       "Total chapters", "state/bible/", "worlds/<World>/HOOKS.md", "Cross-book setup"],
    "outliner": ["Payoff Annotations", "Unscheduled Payoff Setups", "Book 01 - ", "In Development", "Open Questions",
                 "Subplot Threads", "Format Reference", "Key Tensions", "Avoiding", "Incorporating", "Notes field",
                 "Flags for the Planner", "stories/<Series Name>/SERIES_OUTLINE.md"],
    "story-ideator": ["Hooks Used", "In Use", "Open Questions", "Last synchronized", "Not Started",
                      "Placeholder — expand after Outliner", "Full Story", "| TBD |", "None at this time.",
                      "Autonomous", "Collaborative", "Story Order", "state/Timeline.md", "stories/<Story Name>/state/ACTIVE_SCHEMES.md",
                      "stories/<Story Name>/state/STORY_FACTS.md"],
    "writing-assistant": ["Last updated in", "Unknown", "To be determined", "None at this time.", "In Use (",
                          "Fields requiring follow-up", "Consistency notes", "Source:** User-defined",
                          "Writing Guidance", "World Bible Setup", "Core Traits", "Archived", "Open`"],
    "world-archivist": ["Add Entry", "Update Status", "Change Position", "Reorder", "Mark Concurrent", "Initialize",
                        "Not Started", "In Progress", "Last synchronized", "Never proceed without confirming",
                        "Clean merges", "Conflicts requiring your decision", "Active Schemes at story close",
                        "Persist", "open thread", "Position <P>", "Consolidation Plan", "TIMELINE.md",
                        "never copied into snapshots", "Story Order"],
    "draft-writer": ["Notes for Draft Writer", "Opens with", "Closes with", "[FLAG]", "World baseline",
                     "World Order Position", "ACTIVE_SCHEMES.md", "STORY_FACTS.md", "Dormant — do not advance",
                     "Forbidden Elements", "Style Excerpt", "Specifics", "Resolution Log", "Superseded Log"],
}

# Phrases deliberately used less often than in the legacy agent; they must still appear.
# planner: scheme/fact dispositions moved from "Notes for Draft Writer" to their own scene field.
RELOCATED = {("planner", "Notes for Draft Writer")}


class ConversionFidelity(unittest.TestCase):
    def test_protected_phrases_survive_conversion(self):
        for name, phrases in PROTECTED.items():
            old = (LEGACY_AGENTS / f"{name}.md").read_text(encoding="utf-8")
            folder = REPO / "skills" / name
            shared = sorted((REPO / "skills" / "writing-room" / "references").glob("*.md"))
            parts = [folder / "SKILL.md", *sorted((folder / "references").glob("*.md")), *shared]
            new = "\n".join(f.read_text(encoding="utf-8") for f in parts)
            for ph in phrases:
                floor = 1 if (name, ph) in RELOCATED else old.count(ph)
                self.assertGreaterEqual(new.count(ph), floor, f"{name}: '{ph}' lost or altered")

    def test_script_using_skills_have_a_no_shell_fallback(self):
        for name in ("planner", "draft-writer", "reviewer", "draft-fixer", "story-analyzer", "promote-chapter"):
            text = (REPO / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("<WR>/scripts/", text, name)
            self.assertRegex(text, r"(?i)without a shell|otherwise\W+, with whatever file operations", name)

    def test_world_loading_skills_use_the_shared_reference_with_a_no_shell_path(self):
        ref = REPO / "skills" / "writing-room" / "references" / "world-loading.md"
        ref_text = ref.read_text(encoding="utf-8")
        self.assertIn("<WR>/scripts/load_world.py", ref_text)
        self.assertGreaterEqual(ref_text.count("Without a shell"), 3)
        for name in ("outliner", "story-ideator"):
            text = (REPO / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("<WR>/references/world-loading.md", text, name)

    def test_every_script_call_outside_the_runtime_has_a_no_shell_path(self):
        for md in sorted((REPO / "skills").glob("*/**/*.md")):
            if md.relative_to(REPO / "skills").parts[0] == "writing-room":
                continue
            text = md.read_text(encoding="utf-8")
            if "<WR>/scripts/" in text:
                self.assertRegex(text, r"(?i)without a shell|otherwise|see the world-loading", str(md))

    def test_unplaced_fixes_are_reported_in_summary(self):
        text = (REPO / "skills" / "draft-fixer" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("**Could not be placed (needs your attention):**", text)
        self.assertIn("never leave an unplaced fix unreported", text.lower())

    def test_pipeline_next_steps_follow_the_canonical_order(self):
        order = ["story-ideator", "outliner", "planner", "draft-writer", "reviewer", "draft-fixer", "story-analyzer", "promote-chapter"]
        for cur, nxt in zip(order, order[1:]):
            path = REPO / "skills" / cur / "SKILL.md"
            if path.exists():
                self.assertRegex(path.read_text(encoding="utf-8"), rf"\*\*Next step:\*\*[^\n]*`{nxt}`", cur)



class WorkflowContracts(unittest.TestCase):
    """Spec conflicts found in a recorded run; each must stay resolved."""

    def read(self, *parts):
        return (REPO / "skills").joinpath(*parts).read_text(encoding="utf-8")

    def test_loader_commands_are_one_line_presets(self):
        # Multi-line commands (backslash continuations, [optional] brackets) were copied literally by local models,
        # which then fell back to reading every file one by one.
        presets = {"planner": "load_bible.py\" --for planner", "draft-writer": "load_bible.py\" --for draft-writer",
                   "reviewer": "load_bible.py\" --for reviewer-character", "draft-fixer": "load_bible.py\" --for draft-fixer",
                   "story-analyzer": "load_bible.py\" --for story-analyzer",
                   "story-ideator": "load_world.py\" --for story-ideator", "outliner": "load_world.py\" --for outliner"}
        for name, call in presets.items():
            self.assertIn(call, self.read(name, "SKILL.md"), name)
        self.assertIn("load_bible.py\" --for reviewer-consistency", self.read("reviewer", "SKILL.md"))
        for md in sorted((REPO / "skills").glob("*/**/*.md")):
            for line in md.read_text(encoding="utf-8").splitlines():
                if "load_bible.py" in line or "load_world.py" in line:
                    self.assertFalse(line.rstrip().endswith("\\"), f"{md}: {line}")

    def test_ideator_saves_the_approved_concept_and_scripts_its_bookkeeping(self):
        # A local-model run lost its context after approval, then saved a concept nobody approved and
        # failed again and again to hand-edit the WORLD_ORDER.md and HOOKS.md tables.
        t = self.read("story-ideator", "SKILL.md")
        self.assertIn(".writing-room-work/worlds/<World Name>/CONCEPT.md", t)
        self.assertIn("never rebuild the concept from memory", t)
        self.assertIn('new_story.py" --world "<World Name>" --story "<Story Name>"', t)
        self.assertIn("<!-- draft: not yet approved -->", t)
        self.assertIn("**Resume check.**", t)
        self.assertIn("This is the only question round", t)
        self.assertIn("If the request names a world that is in the list, that is the confirmation", t)
        self.assertNotIn("follow the `writing-assistant` skill yourself", t)
        self.assertIn('--structure "<Structure Name>"', t)

    def test_chapter_plan_has_per_scene_dispositions_and_a_length_directive(self):
        t = self.read("writing-room", "shared", "templates", "story", "chapter_plan.md")
        scene = t.split("### Scene 1 of N", 1)[1].split("### Scene 2 of N", 1)[0]
        self.assertIn("**Scheme / fact dispositions:**", scene)
        self.assertIn("**Notes for Draft Writer:**", scene)
        self.assertIn("- **Length:**", t.split("## Style Directives", 1)[1].split("---", 1)[0])

    def test_planner_accepts_a_length_override_and_checks_continuity_without_prose(self):
        text = self.read("planner", "SKILL.md")
        qc7 = text.split("7. **Word count plausibility**", 1)[1].splitlines()[0]
        self.assertIn("Length: Override", qc7)
        qc8 = text.split("8. **Continuity**", 1)[1].splitlines()[0]
        self.assertIn("state/Timeline.md", qc8)
        self.assertNotIn("most recent completed chapter", qc8)

    def test_analyzer_loads_the_same_baseline_and_gates_hooks_after_state_writes(self):
        text = self.read("story-analyzer", "SKILL.md")
        load = text.split("### Step 4", 1)[1].split("### Step 5", 1)[0]
        self.assertIn('--position "<BASELINE_POS>"', load)
        self.assertIn("snapshots/<BASELINE_POS>/", load)
        self.assertLess(text.index("### Step 8 — Apply Story-State Changes"), text.index("### Step 9 — Hooks"))
        hooks = text.split("### Step 9 — Hooks", 1)[1].split("### Step 10", 1)[0]
        self.assertLess(hooks.index("#### 9c — The gate"), hooks.index("#### 9d — Write approved items only"))
        self.assertIn("Do not edit `worlds/<World>/HOOKS.md` before the gate", hooks)
        rules = self.read("story-analyzer", "references", "write-rules.md")
        self.assertIn("[snapshot pos N]", rules)

    def test_review_issues_carry_an_explicit_author_decision_field(self):
        for name in ("review_consistency.md", "review_character.md"):
            t = self.read("writing-room", "shared", "templates", "story", name)
            self.assertIn("**Author decision required:**", t, name)
            self.assertIn("**Sources loaded:**", t, name)
        self.assertIn("**Author decision required** is `Yes`", self.read("draft-fixer", "SKILL.md"))

    def test_reviewer_writes_each_report_when_its_pass_ends_and_resumes(self):
        text = self.read("reviewer", "SKILL.md")

        def step(n):
            return text.split(f"### Step {n} ", 1)[1].split("### Step ", 1)[0]

        self.assertIn("**Write `Reviewer-Consistency.md` now.**", step(5))
        self.assertIn("**Write `Reviewer-Character.md` now, as a checkpoint.**", step(7))
        self.assertIn("In progress — plan check done; character pass not yet run", step(7))
        self.assertIn("**Rewrite `Reviewer-Character.md` in full now**", step(8))
        self.assertNotIn("Hold all", text)  # nothing is kept only in memory until the end
        resume = step(2)
        self.assertIn("Resume: Step 3, then Steps 6–8 (skip 4–5)", resume)
        self.assertIn("In progress — being redone", resume)
        for name in ("review_consistency.md", "review_character.md"):
            self.assertIn("**Review status:**", self.read("writing-room", "shared", "templates", "story", name))
        self.assertIn("**Review not finished:**", self.read("draft-fixer", "SKILL.md"))


class DraftWriterCheckpoints(unittest.TestCase):
    """The draft-writer saves every scene to a working draft and can resume from it."""

    def test_scenes_are_saved_checked_from_the_file_and_resumable(self):
        text = (REPO / "skills" / "draft-writer" / "SKILL.md").read_text(encoding="utf-8")

        def step(n):
            return text.split(f"### Step {n} ", 1)[1].split("### Step ", 1)[0]

        self.assertIn("### The working draft", text)
        self.assertIn("`<!-- draft: Chapter <N>, <K> of <M> scenes saved; self-check: <not started | in progress | done> -->`", text)
        self.assertIn("Never write a partial chapter to `current_chapter/CONTENT.md`", text)
        self.assertIn("read the end of the file back", text)
        self.assertIn("**Only a working draft exists:**", step(3))
        self.assertIn("**To resume:**", step(3))
        self.assertIn("**Save the scene** to the working draft", step(6))
        self.assertNotIn("Keep all approved scene text in the conversation", text)
        self.assertIn("set its first line to `self-check: in progress`", step(7))
        self.assertIn("Assemble the final prose from it, not from the conversation", step(9))
        self.assertIn("Only then delete the working draft", step(9))


class DraftFixerCheckpoints(unittest.TestCase):
    """The draft-fixer backs up the draft, keeps its log current fix by fix, and resumes from it."""

    def test_backup_checkpoint_log_and_resume(self):
        text = (REPO / "skills" / "draft-fixer" / "SKILL.md").read_text(encoding="utf-8")

        def step(n):
            return text.split(f"### Step {n} ", 1)[1].split("### Step ", 1)[0]

        self.assertIn("**Fix log in progress**", step(3))
        self.assertIn("**To resume:**", step(3))
        self.assertIn("the corrected passage is there, the fix landed before the log was updated", step(3))
        self.assertIn("restore `CONTENT.md` from the backup", step(3))
        self.assertIn("#### Checkpoints (all modes)", step(8))
        self.assertIn("Chapter_NN.before-fixes.md", step(8))
        self.assertIn("**After each fix or decision,** update the log and write it again", step(8))
        self.assertIn("set `**Fix status:** Complete`", step(10))
        t = (REPO / "skills" / "writing-room" / "shared" / "templates" / "story" / "draft_fixer_log.md").read_text(encoding="utf-8")
        for needle in ("**Fix status:**", "**Original draft:**", "## Fix Plan", "| Decision | State |"):
            self.assertIn(needle, t)
        self.assertIn("**Fix status:**", (REPO / "skills" / "writing-room" / "SKILL.md").read_text(encoding="utf-8"))


class WorldOrderWriters(unittest.TestCase):
    """The skills that change WORLD_ORDER.md call world_order.py, keeping their manual steps for no shell."""

    def test_analyzer_and_archivist_run_world_order(self):
        rules = (REPO / "skills" / "story-analyzer" / "references" / "write-rules.md").read_text(encoding="utf-8")
        self.assertIn('world_order.py" chapter --world "worlds/<World Name>" --story "<Story Name>" --chapter <N>', rules)
        self.assertIn("Story complete:", rules)
        archivist = (REPO / "skills" / "world-archivist" / "SKILL.md").read_text(encoding="utf-8")
        for cmd in ("add --world", "status --world", "move --world", "renumber --world"):
            self.assertIn(f"`{cmd}", archivist)
        for text in (rules, archivist):
            self.assertIn("Without a shell", text)


if __name__ == "__main__":
    unittest.main()
