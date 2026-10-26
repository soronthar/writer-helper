---
name: promote-chapter
description: "Promote the finished chapter draft to the story's chapters folder and clear current_chapter/ for the next chapter. Use after the story-analyzer skill has run on a reviewed and fixed draft. Copies current_chapter/CONTENT.md to chapters/Chapter_NN.md, then deletes the chapter plan, draft and review reports, but only after showing exactly what will happen and getting the user's confirmation."
---

# Promote Chapter

Shared rules and the meaning of `<WR>`: `../writing-room/references/conventions.md`.

Your job is to promote the current chapter draft to the completed chapters archive and reset `current_chapter/` for the next chapter.

This is a mechanical file operation. Be precise, confirm before deleting, and report exactly what you did.

---

## Step 1 — Identify the Story

List files matching `stories/*/current_chapter/CONTENT.md`. If exactly one exists, use it. If multiple exist, list them and ask the user to pick.

**Book Series:** also list files matching `stories/*/Book */current_chapter/CONTENT.md`.

---

## Step 2 — Verify Prerequisites

**CONTENT.md does not exist:** stop. Tell the user to run the `draft-writer` skill first.

**CHAPTER_PLAN.md does not exist:** stop. Cannot determine the chapter number without it.

Read `current_chapter/CHAPTER_PLAN.md` and extract:
- Chapter number (the `**Chapter:** N of <Total>` line)
- Working title
- Story name

---

## Step 3 — Soft-check: has `story-analyzer` run?

Read `state/Timeline.md`. If there is no entry for this chapter number, warn:

> "The Timeline has no entry for Chapter N — the `story-analyzer` skill may not have run yet. Promoting without analyzing means world bible updates and hook suggestions will be skipped for this chapter. Proceed anyway?"

Continue on explicit confirmation, or stop if the user wants to run the `story-analyzer` skill first.

---

## Step 4 — Build the Destination Path

Zero-pad the chapter number to two digits: Chapter 1 → `Chapter_01.md`, Chapter 9 → `Chapter_09.md`, Chapter 10 → `Chapter_10.md`.

Destination: `stories/<Story>/chapters/Chapter_NN.md`

**Destination already exists:** warn the user before proceeding.

> "chapters/Chapter_NN.md already exists. Overwrite it?"

Continue only on explicit confirmation.

---

## Step 5 — Preview and Confirm

Show the user exactly what is about to happen:

```
Ready to promote:

  Copy:   current_chapter/CONTENT.md
      →   chapters/Chapter_NN.md

  Delete: current_chapter/CONTENT.md
          current_chapter/CHAPTER_PLAN.md
          current_chapter/current_reviews/  (and all files inside)

Proceed? (yes / no)
```

Do not touch any files until the user confirms.

---

## Step 6 — Execute

On confirmation, with `<story>` the story (or book) folder and `NN` the chapter number:

- **If you can run commands:** `python "<WR>/scripts/promote_chapter.py" --story "<story>" --chapter N` (add `--overwrite` only if the user confirmed replacing an existing chapter file). It copies, verifies the copy is identical, and only then deletes. `--dry-run` prints the plan without changing anything.
- **Otherwise**, with whatever file operations you have, in this order:
  1. Copy `<story>/current_chapter/CONTENT.md` to `<story>/chapters/Chapter_NN.md`.
  2. Check the new file exists and has the same content as the source.
  3. Delete `<story>/current_chapter/CONTENT.md`, `<story>/current_chapter/CHAPTER_PLAN.md`, and the `<story>/current_chapter/current_reviews/` folder with everything in it. Delete nothing else.

If the copy cannot be verified, stop and delete nothing.

---

## Step 7 — Report

```
### Chapter Promoted

**Story:** <Story Name>
**Chapter:** N — <Working Title>

**Created:**
- stories/<path>/chapters/Chapter_NN.md

**Cleared from current_chapter/:**
- CONTENT.md
- CHAPTER_PLAN.md
- current_reviews/ (<N> review files)

**current_chapter/ is now empty and ready for the next chapter.**

**Next step:** run the `planner` skill for Chapter N+1.
```
