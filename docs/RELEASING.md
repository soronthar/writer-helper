# Releasing

The repository is developed in a private working repository whose history is never published. The public repository, https://github.com/soronthar/writer-helper, has **one commit per release**: the first release is a fresh repository with a single commit, and each later release adds one commit on top of it. This keeps the public repository clean regardless of what the working history contains, and nothing ever needs a force push.

The **public clone** is a local copy of the public repository, kept next to the working repository as `../writing-room-public`. The first release creates it; every later release is made in it. If it is lost, clone it again:

```bash
git clone https://github.com/soronthar/writer-helper.git ../writing-room-public
```

## Checklist

1. **Everything committed** in the working repository. The export refuses a dirty tree.
2. **Tests and lint**, on Windows and on a POSIX system:
   ```bash
   python tools/lint_skills.py
   python -m unittest discover -s tests
   ```
   Also run `claude plugin validate .` if the Claude Code CLI is available.
3. **Version.** Update `skills/writing-room/VERSION` and `.claude-plugin/plugin.json` (a test keeps them equal), and make the top of `CHANGELOG.md` that version, with the date.
4. **Export** with the author's own project as the source of names to look for, and the author's GitHub noreply address as the identity, so the public commit and tag do not carry a personal email (the working repository's own git config is not changed):
   ```bash
   export GIT_AUTHOR_NAME=Soronthar GIT_COMMITTER_NAME=Soronthar
   export GIT_AUTHOR_EMAIL=898992+soronthar@users.noreply.github.com GIT_COMMITTER_EMAIL=898992+soronthar@users.noreply.github.com
   ```
   In PowerShell set the same four variables with `$env:GIT_AUTHOR_NAME = "Soronthar"` and so on. Then:
   - **First release only** (the public clone does not exist yet):
     ```bash
     python tools/export_public.py --dest ../writing-room-public --source "<the author's own project folder>" --tag v0.1.0
     ```
     This makes `../writing-room-public` a new repository with one initial commit on `main` and the tag.
   - **Every later release:** first make sure the public clone is up to date (`git -C ../writing-room-public pull`), then:
     ```bash
     python tools/export_public.py --update --dest ../writing-room-public --source "<the author's own project folder>" --tag v0.2.0
     ```
     This replaces the clone's files with the working tree (files deleted in the working repository are deleted there too) and commits the change as one commit, `Release v0.2.0`, with the tag. It refuses a clone that has uncommitted changes, is not on `main` or already has the tag, and it refuses to make an empty release.

   Both modes copy the tracked and untracked-but-not-ignored files, stop before committing if any private name appears, and push nothing. Check the identity before publishing: `git -C ../writing-room-public log -1 --format="%an <%ae> / %cn <%ce>"` and `git -C ../writing-room-public for-each-ref refs/tags --format="%(refname:short) %(taggeremail)"` must show only the noreply address.
5. **Check the export** including its history:
   ```bash
   python tools/check_public_clean.py --source "<the author's own project folder>" --root ../writing-room-public --history
   ```
   It must say `clean`. Then run the tests once from inside the public clone (`cd ../writing-room-public && python -m unittest discover -s tests`) to prove it is self-contained.
6. **Read what you are about to publish.** The name check cannot see reworded plot or phrasing from private fiction. For the first release, skim `skills/writing-room/shared/craft/` (story structures, archetypes, tropes, the starter style), the examples inside skill text, and the generated sample. For a later release, read the release commit itself: `git -C ../writing-room-public show --stat HEAD`, then the diff of anything new or rewritten.
7. **Publish.** This step is yours.
   - **First release:** create the public repository on GitHub, empty (no README, license or .gitignore: the export has them), then from `../writing-room-public`:
     ```bash
     git remote add origin https://github.com/soronthar/writer-helper.git
     git push -u origin main
     git push origin v0.1.0
     ```
   - **Later releases:** from `../writing-room-public`, `git push origin main` and `git push origin v0.2.0`. Never force-push: if the push is rejected, the public repository has a commit the clone lacks (see below).

## Changes made on the public repository

If something is changed on GitHub directly (a merged pull request, an edit in the web interface), the public repository has a commit the working repository does not. Bring the change into the working repository first, then `git pull` in the public clone before the next `--update`; otherwise the next release replaces the clone's files with the working tree and undoes the change.

## Pre-release and 1.0

Versions before `1.0.0` are pre-releases. The README says what is and is not verified. `1.0.0`, a Claude Code marketplace listing, and any claim that Devin, OpenCode or Hermes Agent are supported wait until each real agent has run a chapter loop on the sample project (the smoke tests, the last phase of the plan in `docs/development/`).

## Telling users how to update

Users update with `wr_update.py` from the new build (see `docs/INSTALL.md`). Make sure each release's `CHANGELOG.md` entry says what changed in plain words, because the updater prints those entries to the person updating. If a release changes the project layout, it must ship a migration and say so at the top of its entry.
