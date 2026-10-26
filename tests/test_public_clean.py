"""Tests for the publication guard: check_public_clean.py and export_public.py.

Run with:  python -m unittest discover -s tests -v
They build throwaway repositories; the real repository is never modified.
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS = REPO / "tools"
sys.path.insert(0, str(TOOLS))

import check_public_clean as cpc  # noqa: E402
import export_public as exp  # noqa: E402


def git(cwd, *args):
    r = subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *args], cwd=cwd, capture_output=True,
                       text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return r.stdout


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="wr-pub-")
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self.tmp = Path(self._tmp).resolve()

    def private_project(self):
        """A stand-in for the author's own project, with distinctive names."""
        src = self.tmp / "private"
        for rel, text in {
            "worlds/Zorblax/DESCRIPTION.md": "# Zorblax\n",
            "worlds/Zorblax/characters/Quenby Marlowe.md": "# Quenby Marlowe\n",
            "worlds/Zorblax/factions/The Gilded Hand.md": "# The Gilded Hand\n",
            "worlds/Zorblax/points_of_interest/Wexford Deep.md": "# Wexford Deep\n",
            "worlds/Zorblax/snapshots/1/characters/Snapshot Only.md": "# not a name we want\n",
            "stories/The Hollow Crown/CONCEPT.md": "# The Hollow Crown\n",
            "stories/The Hollow Crown/state/bible/mythology/The Last Toll.md": "# The Last Toll\n",
        }.items():
            p = src / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        return src

    def repo_with(self, files):
        repo = self.tmp / "repo"
        repo.mkdir()
        git(repo, "init", "-q", "-b", "main")
        for rel, text in files.items():
            p = repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "first")
        return repo


class Names(Base):
    def test_names_are_derived_from_the_authors_project(self):
        names = cpc.names_from_source(self.private_project())
        self.assertEqual(names, {"Zorblax", "Quenby Marlowe", "The Gilded Hand", "Wexford Deep", "The Hollow Crown",
                                 "The Last Toll"})  # snapshot copies and short names are not added twice or at all

    def test_names_file(self):
        f = self.tmp / "names.txt"
        f.write_text("# comment\nAlpha Beta\n\nGamma Delta\n", encoding="utf-8")
        self.assertEqual(cpc.names_from_file(f), {"Alpha Beta", "Gamma Delta"})

    def test_whole_word_match_only(self):
        repo = self.repo_with({"a.md": "Zorblaxian is fine but Zorblax is not.\n", "b.md": "Zorblaxian only.\n"})
        hits = cpc.scan_tree(repo, {"Zorblax"})
        self.assertEqual(sorted(hits), ["a.md"])

    def test_untracked_files_are_scanned_but_ignored_ones_are_not(self):
        repo = self.repo_with({".gitignore": "secret/\n", "ok.md": "nothing\n"})
        (repo / "new.md").write_text("Quenby Marlowe\n", encoding="utf-8")
        (repo / "secret").mkdir()
        (repo / "secret" / "x.md").write_text("Quenby Marlowe\n", encoding="utf-8")
        self.assertEqual(sorted(cpc.scan_tree(repo, {"Quenby Marlowe"})), ["new.md"])

    def test_history_is_searched(self):
        repo = self.repo_with({"a.md": "Wexford Deep\n"})
        (repo / "a.md").write_text("cleaned\n", encoding="utf-8")
        git(repo, "commit", "-q", "-am", "clean it")
        self.assertEqual(cpc.scan_tree(repo, {"Wexford Deep"}), {})  # the tree is clean...
        self.assertIn("Wexford Deep", cpc.scan_history(repo, {"Wexford Deep"}))  # ...the history is not

    def test_command_line_exit_codes(self):
        src = self.private_project()
        clean = self.repo_with({"a.md": "nothing private here\n"})
        run = lambda *a: subprocess.run([sys.executable, str(TOOLS / "check_public_clean.py"), *a], cwd=REPO,
                                        capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(run("--source", str(src), "--root", str(clean)).returncode, 0)
        (clean / "b.md").write_text("The Gilded Hand\n", encoding="utf-8")
        r = run("--source", str(src), "--root", str(clean))
        self.assertEqual(r.returncode, 1)
        self.assertIn("FOUND  b.md", r.stdout)
        self.assertEqual(run().returncode, 2)  # argparse error: a source or names file is required


class Export(Base):
    def test_export_makes_a_fresh_single_commit_repository(self):
        repo = self.repo_with({"a.md": "hello\n", ".gitignore": "ignored.md\n", "sub/b.md": "world\n"})
        git(repo, "commit", "-q", "--allow-empty", "-m", "second")
        (repo / "ignored.md").write_text("never exported\n", encoding="utf-8")
        (repo / "untracked.md").write_text("exported\n", encoding="utf-8")
        git(repo, "add", "untracked.md")
        git(repo, "commit", "-q", "-m", "third")
        dest = self.tmp / "out"
        exp.export(repo, dest)
        self.assertEqual(sorted(p.relative_to(dest).as_posix() for p in dest.rglob("*") if p.is_file() and ".git" not in p.parts),
                         [".gitignore", "a.md", "sub/b.md", "untracked.md"])
        self.assertEqual(git(dest, "rev-list", "--count", "HEAD").strip(), "1")
        self.assertEqual(git(repo, "rev-list", "--count", "HEAD").strip(), "3")  # the source keeps its history

    def test_export_refuses_a_non_empty_destination(self):
        repo = self.repo_with({"a.md": "x\n"})
        dest = self.tmp / "out"
        dest.mkdir()
        (dest / "keep.txt").write_text("x", encoding="utf-8")
        with self.assertRaises(SystemExit):
            exp.export(repo, dest)

    def test_export_refuses_uncommitted_changes_unless_allowed(self):
        repo = self.repo_with({"a.md": "x\n"})
        (repo / "a.md").write_text("changed\n", encoding="utf-8")
        with self.assertRaises(SystemExit):
            exp.export(repo, self.tmp / "out1")
        exp.export(repo, self.tmp / "out2", allow_dirty=True)
        self.assertTrue((self.tmp / "out2" / ".git").is_dir())

    def test_export_stops_when_a_private_name_is_present(self):
        repo = self.repo_with({"a.md": "mentions Quenby Marlowe\n"})
        dest = self.tmp / "out"
        with self.assertRaises(SystemExit) as ctx:
            exp.export(repo, dest, names={"Quenby Marlowe"})
        self.assertIn("private names", str(ctx.exception))
        self.assertFalse((dest / ".git").exists())  # no repository was created

    def test_clean_export_of_a_history_that_had_the_name(self):
        repo = self.repo_with({"a.md": "Wexford Deep\n"})
        (repo / "a.md").write_text("cleaned\n", encoding="utf-8")
        git(repo, "commit", "-q", "-am", "clean")
        self.assertIn("Wexford Deep", cpc.scan_history(repo, {"Wexford Deep"}))
        dest = self.tmp / "out"
        exp.export(repo, dest, names={"Wexford Deep"})
        self.assertEqual(cpc.scan_history(dest, {"Wexford Deep"}), {})


class Update(Base):
    """Later releases: the tree goes on top of the public repository as one commit."""

    def published(self, files):
        repo = self.repo_with(files)
        dest = self.tmp / "public"
        exp.export(repo, dest, tag="v0.1.0")
        return repo, dest

    def files_in(self, root):
        return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and ".git" not in p.parts)

    def test_a_release_is_one_commit_on_top_of_the_public_history(self):
        repo, dest = self.published({"a.md": "one\n", "old/gone.md": "x\n", "keep.md": "k\n"})
        (repo / "a.md").write_text("two\n", encoding="utf-8")
        (repo / "new.md").write_text("added\n", encoding="utf-8")
        shutil.rmtree(repo / "old")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "work 1")
        git(repo, "commit", "-q", "--allow-empty", "-m", "work 2")
        copied, removed = exp.update(repo, dest, tag="v0.2.0")
        self.assertEqual((copied, removed), (3, 1))
        self.assertEqual(self.files_in(dest), ["a.md", "keep.md", "new.md"])  # the empty old/ folder is gone too
        self.assertEqual((dest / "a.md").read_text(encoding="utf-8"), "two\n")
        self.assertEqual(git(dest, "log", "--format=%s").split("\n")[:2], ["Release v0.2.0", "Initial commit"])
        self.assertEqual(git(dest, "tag", "--list").split(), ["v0.1.0", "v0.2.0"])
        self.assertEqual(git(dest, "rev-list", "--count", "HEAD").strip(), "2")  # the working history stays private
        self.assertEqual(git(dest, "status", "--porcelain"), "")

    def test_update_refuses_a_clone_with_uncommitted_changes(self):
        repo, dest = self.published({"a.md": "one\n"})
        (dest / "a.md").write_text("edited in the clone\n", encoding="utf-8")
        with self.assertRaises(SystemExit) as ctx:
            exp.update(repo, dest, tag="v0.2.0")
        self.assertIn("uncommitted", str(ctx.exception))

    def test_update_refuses_a_folder_that_is_not_a_repository(self):
        repo = self.repo_with({"a.md": "one\n"})
        (self.tmp / "plain").mkdir()
        with self.assertRaises(SystemExit):
            exp.update(repo, self.tmp / "plain", tag="v0.2.0")

    def test_update_refuses_an_existing_tag_and_an_unchanged_tree(self):
        repo, dest = self.published({"a.md": "one\n"})
        with self.assertRaises(SystemExit) as ctx:
            exp.update(repo, dest, tag="v0.1.0")
        self.assertIn("already has the tag", str(ctx.exception))
        with self.assertRaises(SystemExit) as ctx:
            exp.update(repo, dest, tag="v0.2.0")
        self.assertIn("Nothing to release", str(ctx.exception))
        self.assertEqual(git(dest, "tag", "--list").split(), ["v0.1.0"])

    def test_update_stops_on_a_private_name_and_leaves_the_clone_alone(self):
        repo, dest = self.published({"a.md": "one\n"})
        (repo / "a.md").write_text("now mentions The Gilded Hand\n", encoding="utf-8")
        git(repo, "commit", "-q", "-am", "oops")
        with self.assertRaises(SystemExit) as ctx:
            exp.update(repo, dest, names={"The Gilded Hand"}, tag="v0.2.0")
        self.assertIn("was not changed", str(ctx.exception))
        self.assertEqual((dest / "a.md").read_text(encoding="utf-8"), "one\n")
        self.assertEqual(git(dest, "status", "--porcelain"), "")
        self.assertEqual(git(dest, "rev-list", "--count", "HEAD").strip(), "1")

    def test_command_line_update_needs_a_tag(self):
        r = subprocess.run([sys.executable, str(TOOLS / "export_public.py"), "--update", "--dest", str(self.tmp)],
                           cwd=REPO, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--update needs --tag", r.stderr)


if __name__ == "__main__":
    unittest.main()
