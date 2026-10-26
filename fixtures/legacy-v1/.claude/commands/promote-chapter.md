---
description: Promotes current_chapter/CONTENT.md to chapters/Chapter_NN.md and clears current_chapter/. Run after the Story Analyzer has completed. Confirms before deleting anything.
model: claude-sonnet-4-6
---

# /promote-chapter

You are executing the `/promote-chapter` command. Your job is to promote the current chapter draft to the completed chapters archive and reset `current_chapter/` for the next chapter.

This is a mechanical file operation. Be precise, confirm before deleting, and report exactly what you did.

---

## Step 1 — Identify the Story

Glob `stories/*/current_chapter/CONTENT.md`. If exactly one exists, use it. If multiple exist, list them and ask the user to pick.

**Book Series:** also Glob `stories/*/Book */current_chapter/CONTENT.md`.

---

## Step 2 — Verify Prerequisites

**CONTENT.md does not exist:** stop. Tell the user to invoke the Draft Writer first.

**CHAPTER_PLAN.md does not exist:** stop. Cannot determine the chapter number without it.

Read `current_chapter/CHAPTER_PLAN.md` and extract:
- Chapter number (the `**Chapter:** N of <Total>` line)
- Working title
- Story name

---

## Step 3 — Soft-check: Story Analyzer

Read `state/Timeline.md`. If there is no entry for this chapter number, warn:

> "The Timeline has no entry for Chapter N — the Story Analyzer may not have run yet. Promoting without analyzing means world bible updates and hook suggestions will be skipped for this chapter. Proceed anyway?"

Continue on explicit confirmation, or stop if the user wants to run the Story Analyzer first.

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

On confirmation:

1. Use Bash `cp` to copy `current_chapter/CONTENT.md` to `chapters/Chapter_NN.md` directly:
   ```bash
   cp "stories/<path>/current_chapter/CONTENT.md" "stories/<path>/chapters/Chapter_NN.md"
   ```
2. Delete `current_chapter/` contents:
   ```bash
   rm "stories/<path>/current_chapter/CONTENT.md"
   rm "stories/<path>/current_chapter/CHAPTER_PLAN.md"
   rm -rf "stories/<path>/current_chapter/current_reviews"
   ```
   Use the correct absolute or relative path based on where the story lives.

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

Next step: Invoke the Planner for Chapter N+1.
```
