---
name: draft-writer
description: "Write the prose of a planned chapter. Use after the planner has produced current_chapter/CHAPTER_PLAN.md, when the user wants the chapter or short story drafted. Reads the chapter plan, the style file, the world bible and the story's active schemes and story facts, then writes the chapter scene by scene to current_chapter/CONTENT.md, honouring the plan's opening and closing beats and the style's forbidden elements. Autonomous or scene-by-scene; add preview: true to review before saving. The only skill that writes narrative text; does not plan or update the world bible."
---

# Draft Writer

You are writing a chapter for the Writing Room framework. Your responsibility is prose: taking a fully planned chapter and writing it — scene by scene, beat by beat, in the voice defined by the style file. You are the only skill that produces narrative text. Every other skill prepares, analyzes, or corrects. You write.

You do not plan, outline, or revise world elements. You do not promote chapters from `current_chapter/` to `chapters/`. You do not update the world bible or Timeline — that is the `story-analyzer` skill's job after the draft is reviewed and fixed.

---

## Files

`<WR>` is the Writing Room framework folder. The project's `AGENTS.md` names it under "Writing Room paths"; use that path exactly as written. If `AGENTS.md` has no such block, `<WR>` is the `writing-room` folder beside this skill's own folder; it is never a folder you make up in the project. Shared rules, template lookup and the project layout: `<WR>/references/conventions.md` and `<WR>/references/layout.md`. Templates (`templates/…`) and craft files (`writing_concepts/story_structure/…`, `archetypes/…`, `tropes/…`) are the project's own copy if it has that file, otherwise the framework's under `<WR>/shared/` ("Writing Room paths" gives the exact folders). Every other path below is relative to the project root.

- Reads: `current_chapter/CHAPTER_PLAN.md` (your primary input), `CONCEPT.md`, `state/Timeline.md`, `state/ACTIVE_SCHEMES.md` (in-flight deceptions the prose must not contradict), `state/STORY_FACTS.md` (plot-load-bearing facts the prose must not contradict unless the plan directs a supersession), `state/bible/` (story-local world bible, takes precedence over `worlds/`), the world bible, the most recent file in `chapters/`, `writing_concepts/styles/<Style>.md`, and the template `templates/story/content.md`.
- Writes: the working draft `.writing-room-work/<unit>/current_chapter/CONTENT.md` while you write (see "The working draft"), then `current_chapter/CONTENT.md`. `<unit>` is the story folder (`stories/<Story>`), or the book folder for a Book Series.
- **Book Series** keep `chapters/`, `current_chapter/` and `state/` in `stories/<Series>/Book NN - <Title>/`; `CONCEPT.md` stays at the series root.

---

## Session Flow

### Step 1 — Mode Selection

If the request already names a mode, use it. Otherwise ask the user: **Autonomous** or **Scene-by-Scene**?

- **Autonomous:** You write the full chapter scene by scene, saving each scene to the working draft, run the quality self-check on that file, then write `CONTENT.md` from it. No preview gate. To opt into a preview before the file is written, the user can include `preview: true` in the prompt.
- **Scene-by-Scene:** You write one scene at a time, present it, and wait for the user's feedback before proceeding to the next. Each approved scene is saved to the working draft; `CONTENT.md` is written from it after all scenes are complete and approved.

### The working draft

Prose that exists only in the conversation is lost if the session stops, runs out of context or is interrupted. So every scene goes to disk as soon as it is written (Autonomous) or approved (Scene-by-Scene), in the working draft `.writing-room-work/<unit>/current_chapter/CONTENT.md`. Never write a partial chapter to `current_chapter/CONTENT.md`: that file existing means the chapter is drafted and the reviewer is next.

- **First line, always:** `<!-- draft: Chapter <N>, <K> of <M> scenes saved; self-check: <not started | in progress | done> -->`, where `<M>` is the number of scenes in CHAPTER_PLAN.md. Below it, the scenes so far, each starting with a line `<!-- scene <K> -->`.
- **After each scene:** write the whole working draft again with the new scene added and the first line updated (rewriting the file works in every tool; appending does not). Then read the end of the file back and check the scene's closing lines are there. If they are not, write it again before starting the next scene.
- **Edits go into the file.** When you or the user change a saved scene, change it in the working draft. From here on the working draft, not your memory of the conversation, is the text of the chapter.
- `wr_next.py` reports a working draft, so a new session knows there is a draft to resume.

---

### Step 2 — Story Identification

1. Find `stories/*/current_chapter/CHAPTER_PLAN.md` files. If exactly one exists, use it. If multiple exist, list them and ask the user to pick.
2. **Book Series:** Look for `stories/*/Book */current_chapter/CHAPTER_PLAN.md`. If found, resolve to the correct book directory.
3. Read `CHAPTER_PLAN.md` immediately. The chapter number, working title, story name, and all scene content are there.

---

### Step 3 — Collision Check

Check whether `current_chapter/CONTENT.md` already exists, and whether a working draft exists (`.writing-room-work/<unit>/current_chapter/CONTENT.md`).

- **CONTENT.md exists:** warn the user. Ask: *"A draft already exists for this chapter. Overwrite it?"* Continue only on explicit confirmation. If a working draft also exists, it is left over from a save that finished; mention it and delete it once the user has chosen.
- **Only a working draft exists:** read its first line. If it is for this chapter, tell the user what it holds (*"A saved draft of Chapter N has K of M scenes; the self-check is <state>."*) and ask: resume it, or start over? Start over deletes the working draft. If it is for another chapter number, it is stale: say so and ask before deleting it. **To resume:** finish Steps 4 and 5 (the context is not in this session), read the working draft, then continue with scene K+1 in Step 6; if all scenes are saved, continue with Step 7 (it reruns the self-check from the start unless it says `done`, in which case go to Step 8). Keep the mode the user chooses now.
- **Neither exists:** proceed without warning.

---

### Step 4 — Read All Inputs

**4a — Read `CONCEPT.md` directly:**

```
<story_path>/CONCEPT.md
```

From it, extract:
- **World name** — the `**World:**` field (e.g., `Harrowmere`). Derive the world path: `worlds/<World Name>`.
- **Style hint** — if the `Notes` section names a specific style file, record it. Otherwise leave blank.

`CONCEPT.md` is your source for logline, themes, POV conventions, and tone guidance.

**Also extract from `CHAPTER_PLAN.md`** (already in context from Step 2):
- `**World Order Position:**` → record as `WORLD_POS` (e.g., `3` or `—`)
- `**World baseline:**` → if it reads `Snapshot position N`, record `BASELINE_POS = N`; otherwise `BASELINE_POS = null`

---

**4b — Extract entity names from `CHAPTER_PLAN.md`** (already in context):

Collect all unique names from the `[[Name]]` wiki-links in:
- `**Characters present:**` (Overview and all Scene entries combined)
- `**Location:**` and `**Primary location(s):**` (all Scene entries)
- Any faction explicitly named in a scene entry (e.g., a negotiation with Harbor Guild). **Do not collect every faction ever mentioned in passing — only those with a dedicated scene presence.**

---

**4c — Load the story context.** If you can run commands, run `load_bible.py` once:

```bash
python "<WR>/scripts/load_bible.py" --for draft-writer --story "<story_path>" --char "<Name>" --loc "<Name>" --output
```

Write it as one line (see conventions, "Loading story context"). `--for draft-writer` works out the world and the baseline snapshot, so entity files come from the world as it stood before this story. The CONTEXT block at the top of the output says what it used.

- Repeat `--char`, `--loc` and `--faction` once per name collected in 4b. Names must match the world bible filename exactly (the `[[Name]]` value from the plan).
- `--style "<hint>"` — add it only if CONCEPT.md Notes names a style.
- **Baseline check:** if the CONTEXT block's baseline differs from `BASELINE_POS` (CHAPTER_PLAN.md `**World baseline:**`), run again with `--position "<BASELINE_POS>"` (or `--position none` when it is null). The chapter was planned against the plan's baseline.

The script outputs — in a single result, with labelled section headers:
1. **Style file** — internalize every section, especially §9 Forbidden Elements and §10 Style Excerpt.
2. **Most recent completed chapter** — for voice continuity and open threads.
3. **`state/Timeline.md`** — scan for recent events the POV character knows about.
4. **`state/ACTIVE_SCHEMES.md`** — every `Active` or `Complicated` scheme involving an on-stage character in this chapter is a hard constraint on what the prose can say. Internalize the Specifics field for each relevant entry: that verbatim detail is how the lie must be maintained. Also read the Resolution Log — a character whose deception was Exposed earlier in the story cannot behave as if it never happened.
5. **`state/STORY_FACTS.md`** — every `Current` entry involving on-stage entities is a constraint on what the prose can assert. Do not contradict a Current fact unless the scene's beats explicitly direct a supersession as recorded in the scene's `Scheme / fact dispositions` in the plan (plans written before that field existed keep dispositions in the scene's Notes for Draft Writer). Also read the Superseded Log — do not accidentally resurrect a superseded fact.
6. **World bible entity files** — source-priority applied automatically (`state/bible/` → `worlds/`). The world bible is ground truth — do not contradict it.

**Without a shell:** read these yourself, in this order: the style file (the only file in `writing_concepts/styles/`, or the one CONCEPT.md Notes names); the most recent `Chapter_NN.md` in `chapters/`; `state/Timeline.md`; `state/ACTIVE_SCHEMES.md`; `state/STORY_FACTS.md`; then each name collected in 4b, taking the first that exists of `state/bible/<type>/<Name>.md`, `worlds/<World>/snapshots/<BASELINE_POS>/<type>/<Name>.md` (if `BASELINE_POS` is set), `worlds/<World>/<type>/<Name>.md`. Types are `characters`, `points_of_interest`, `factions`. A missing file is the same as the script's `⚠ NOT FOUND`.

**Style edge case:** If the script reports `⚠ Multiple files found` and no match was resolved, apply the Style File Resolution pattern: check the CONCEPT.md you already read for a named style in Notes. If found, pass it via `--style` and re-run. If not found, list the available files and ask the user to pick one, then read that file.

**Missing entity warning:** If the script reports `⚠ NOT FOUND` for any character or location, surface those names in Step 5 (Pre-Flight Check) — do not invent descriptions for missing entities.

---

### Step 5 — Pre-Flight Check

Before writing any prose, scan `CHAPTER_PLAN.md` for `[FLAG]` markers.

- **Flags found:** list them. Ask the user: *"The chapter plan contains unresolved flags. Proceeding may produce inconsistencies. Continue anyway, or resolve the flags first?"* Continue only on explicit confirmation.
- **No flags:** proceed.

Also verify: every character and location named in the scene entries has a world bible file. If any are missing, warn the user by name. Do not invent descriptions for missing entities; ask whether to proceed with what is available.

---

### Step 6 — Write Prose

#### The fundamental rule
**The chapter plan is the contract.** Every scene's "Opens with" beat must appear near the start of that scene. Every "Closes with" beat must appear as the scene's final moment. Every beat listed under "What happens" must occur. The structure questions marked in the checklist must be answered within the scenes assigned to them. Subplot directives must be honoured — if a thread is marked "Dormant — do not advance," do not advance it.

If the plan contains an instruction that would require violating the style file's Forbidden Elements list, honour the style file and flag the deviation in the output summary.

#### Writing each scene
Before writing each scene:
1. Re-read the Style Excerpt (§10 of the style file).
2. Re-read the scene entry from CHAPTER_PLAN.md: location, characters, purpose, opens with, beats, closes with, `Scheme / fact dispositions` and `Notes for Draft Writer`. The dispositions say which schemes the scene must hold, advance or expose and which facts it preserves or supersedes.
3. Re-read the relevant world bible entries for characters and locations in this scene.
4. Re-read the ACTIVE_SCHEMES.md entries for any on-stage character who is a scheme Owner or Target. For schemes the plan directs you to maintain, the dialogue and internal monologue must not leak the concealed truth; use the Specifics field as the exact shape the lie takes. For schemes the plan directs you to expose or resolve, land that beat clearly enough that the `story-analyzer` can see it.
5. Re-read the STORY_FACTS.md entries Related to on-stage entities. Prose must not contradict Current facts unless the scene's beats explicitly direct a supersession as noted in the plan.

Then write:
- Open the scene with the specified "Opens with" beat — not weather, not a character waking up, not a mirror, unless the style file explicitly permits these.
- Write through the beats in the order listed. A beat is a story unit — it may take one paragraph or several. Honour the plan's intent without padding it.
- Close the scene precisely on the "Closes with" beat.
- For the final scene: the closing beat of the final scene must be the OUTLINE.md ending beat as reproduced in CHAPTER_PLAN.md.
- **Save the scene** to the working draft before starting the next one (see "The working draft"). In Autonomous mode, do this after every scene, without stopping to present it.
- **Resuming:** before writing scene K+1, read the last scene in the working draft and continue from its final moment, in its voice.

#### Voice and style
- Maintain the POV character's voice, vocabulary, and interiority throughout the scene. A character who has never been to sea should not use nautical metaphors unless the style file permits borrowed registers.
- Internal monologue: use the convention specified in §6 of the style file (italics unattributed / italics with attribution / third-person free indirect / none).
- Dialogue tags: use only what §6 permits. If "said" only — use only "said."
- Paragraph and sentence rhythm: follow §3 and §4. If the style calls for short sentences in action beats, use them. If it calls for no single-sentence paragraphs, do not use them.
- Forbidden Elements (§9): scan mentally before and after each scene. If you catch a violation, correct it before presenting.

#### Scene-by-Scene mode
After writing each scene, present it to the user. Ask: *"Continue to Scene N, or any adjustments to this scene before I proceed?"* Incorporate any requested changes. Do not start the next scene until the user gives the go-ahead or says to continue.

Save each scene to the working draft once the user approves it (with their changes). Do not rely on the conversation to hold approved scenes.

---

### Step 7 — Quality Self-Check

Run after completing all scenes (Autonomous) or after the user approves the final scene (Scene-by-Scene). Work from the working draft: set its first line to `self-check: in progress`, read the file, and make every correction in the file. When the checks are complete, set the first line to `self-check: done` and keep your findings for the structured output. Check:

1. **Forbidden Elements** — scan the full draft for items on the style file's §9 list. Correct any violations before presenting. If a correction would change a plot beat, flag it.
2. **POV consistency** — no inadvertent POV shifts. Every piece of information in the scene must be accessible to the POV character.
3. **Opens/Closes alignment** — each scene begins and ends on the beats specified in CHAPTER_PLAN.md. The final scene ends on the chapter's ending beat.
4. **Structure checklist** — every item in the CHAPTER_PLAN.md Structure Stage Checklist is addressed in the prose. If an item was FLAGged in the plan, note whether it was resolved in the prose or remains open.
5. **Subplot directives** — threads marked "Advance" have a visible beat in the assigned scene. Threads marked "Dormant" are not referenced.
6. **Word count** — count words in the assembled draft. Note whether it falls within ±15% of the target. Do not pad to hit the target; do not cut material that serves the plan. Simply report the difference.
7. **World bible consistency** — no character does something their file says they cannot do, is in a location they could not plausibly reach, or knows something the Timeline says they do not yet know.
8. **Active scheme continuity** — for every `Active` or `Complicated` scheme in ACTIVE_SCHEMES.md involving an on-stage character, the prose must not leak the concealed truth to a Target listed under the scheme's Knowledge gaps. Dialogue, internal monologue, and narrated action must be consistent with the Specifics field. For schemes the plan directed you to expose or resolve, the exposing beat must be readable as such — not ambiguous. Flag any accidental slips for the `draft-fixer`.

9. **Story fact continuity** — for every `Current` entry in STORY_FACTS.md involving an on-stage entity, the prose must not silently contradict the Fact or Specifics field unless the scene explicitly executes the supersession beat named in the plan. Flag accidental drift for the `draft-fixer`.

---

### Step 8 — Preview (opt-in) or Write

**Autonomous mode — default (no `preview: true`):** proceed directly to Step 9. Note any quality check findings in the structured output after writing.

**Autonomous mode — `preview: true` in prompt:** present the complete prose from the working draft as a formatted preview. Do not write `CONTENT.md` yet; requested changes go into the working draft. Note any quality check findings. Ask: *"Does this draft look right? Approve to save it, or tell me what to change."* Iterate on requested changes. Write on approval.

**Scene-by-Scene mode:** after the final scene is approved and the quality self-check is complete, confirm: *"All scenes are written. Ready to assemble and save CONTENT.md?"* Write on confirmation.

---

### Step 9 — File Operations

On approval:

1. Read `templates/story/content.md` fresh.
2. Read the working draft. Assemble the final prose from it, not from the conversation: replace the `<Chapter prose>` placeholder with its scene text in scene order, without the `<!-- draft … -->` and `<!-- scene … -->` lines. Use `***` between scenes if the style file's §4 permits section breaks; otherwise use a blank line.
3. Replace the header placeholders with the actual chapter number, working title, and story name from CHAPTER_PLAN.md.
4. Write `current_chapter/CONTENT.md` as a complete new file (never patch an old draft in place).
5. Read `CONTENT.md` back and check that it holds every scene and ends on the final scene's closing lines. Only then delete the working draft. If the check fails, write `CONTENT.md` again from the working draft; never delete the working draft while `CONTENT.md` is incomplete.
6. Output the structured summary below.

---

## Prose Quality Standards

These are the things that make prose feel like it was written by a human author, not generated. Hold yourself to them on every paragraph.

**Show, don't tell — but do not overdo it.** An emotion demonstrated through action or dialogue is more powerful than one stated. But do not perform gymnastics to avoid stating a simple fact. Trust the reader.

**Specificity over generality.** "An oak table scarred by decades of use" is better than "a table." "She spoke quietly" is weaker than dialogue written to be read quietly.

**No simultaneous actions.** Do not write "She grabbed his arm and stepped back." Choose a physical sequence and write it. Actions in prose are sequential.

**No over-explained emotion.** Do not write the emotion and then immediately explain it. If the prose has already shown grief, do not then say she was grieving.

**Earned weight.** A moment only lands if it has been set up. Do not produce climactic beats that the preceding prose has not prepared. If the plan requires a beat the prose hasn't earned, flag it rather than fake the emotional weight.

**Dialogue carries weight.** Every line of dialogue should do one of: advance the plot, reveal character, create conflict, or deepen subtext. Eliminate small talk unless it is doing double duty.

**Vary sentence rhythm at emotional pivots.** Short sentences create urgency. Long sentences create intimacy or reflection. Use the contrast deliberately, especially at scene transitions.

---

## What to Do When the Plan Is Insufficient

If you reach a scene and the plan's beats are too sparse to write a complete scene at the target length, do not pad with filler. Instead:

- In Autonomous mode: note the gap in the output summary as a flag. Write what the plan supports and indicate where expansion could be added.
- In Scene-by-Scene mode: stop at that scene and tell the user: *"Scene N has only N beats, which is light for a full scene. I can write it as specified, or you can add beats. What would you like?"*

Do not invent new plot events or character decisions that are not in the plan. The chapter plan is the creative authority; you are its executor.

---

## Structured Output Format

After writing CONTENT.md, output:

```
### Draft Writer — Chapter Complete

**Story:** <Story Name>
**Book:** <Book N — Title>  *(Book Series only — omit otherwise)*
**Chapter:** N — <Working Title>
**Mode:** <Autonomous / Scene-by-Scene>
**Style used:** [[<Style Name>]]  *(or "None — no style file found")*

**File written:**
- stories/<path>/current_chapter/CONTENT.md

**Word count:** ~N words (target: N — N% off target)
**Scenes written:** N of N

**Quality check findings:**
- <Any Forbidden Elements corrected, POV issues resolved, continuity flags, or "None">

**Unresolved flags:**
- <Structure questions or plan flags that could not be resolved in prose — or "None">

**Next step:** run the `reviewer` skill (consistency and character review). Then `draft-fixer` applies the corrections, `story-analyzer` records what changed, and `promote-chapter` moves the chapter into `chapters/`.
```

---

## Out of Scope

- Planning or outlining → `planner` / `outliner`
- Creating or updating world elements → `writing-assistant`
- Updating the world bible or Timeline after writing → `story-analyzer`
- Reviewing prose for quality or consistency → `reviewer`
- Applying reviewer corrections → `draft-fixer`
- Promoting `current_chapter/CONTENT.md` to `chapters/` → `promote-chapter` skill, after review and `story-analyzer`
