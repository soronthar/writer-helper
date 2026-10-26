# Standard Patterns

These patterns are implemented inside each agent individually (agents are self-contained). This file is the **canonical reference**: when a pattern needs to change, update here first, then propagate to affected agents.

---

### Style File Resolution

Used by: Planner, Draft Writer, Draft Fixer

```
1. Glob writing_concepts/styles/
2. One file found       → use it; no question needed
3. Multiple files found → check CONCEPT.md Notes for a named style;
                          if found, use that file;
                          if not found, list options and ask the user
4. No files found       → set all style-dependent fields to
                          "No style file — [agent] uses own judgment"
```

---

### World Bible Source Priority

Used by: Reviewer, Story Analyzer, Planner, Draft Writer

```
For any character, location, faction, or mythology file:
1. Check state/bible/<type>/<Name>.md  → use if it exists
2. Else: check worlds/<World>/<type>/<Name>.md  → use if it exists
3. Else: entity has no bible file (flag / stub as appropriate)

state/bible/ is the story-local copy and always takes precedence.
It diverges from worlds/ as the story progresses.
The Story Analyzer writes to state/bible/ only — never to worlds/.
```

---

### Book Series Detection and Path Resolution

Used by: all agents that identify the story

```
1. Glob stories/*/current_chapter/<target-file>      ← non-series
2. Glob stories/*/Book */current_chapter/<target-file> ← book series
3. If a series is detected, resolve to a specific book directory.
   All subsequent file operations use that book directory as the story root.
4. Status updates (CONCEPT.md) target the series-root CONCEPT.md,
   not the per-book directory.
```

---

### SUMMARY.md Staleness Check

Used by: Story Ideator, Outliner

```
1. Glob each entity directory: characters/, factions/, points_of_interest/, mythology/
2. Compare file counts to table row counts in SUMMARY.md
   (a single — placeholder row does not count as a data row)
3. Mismatch on any directory → warn user, fall back to reading all entity files directly this session
4. All counts match → proceed with selective reads using SUMMARY.md as world index
5. Never regenerate SUMMARY.md from the Ideator or Outliner — that is the Writing Assistant's job
```

Note: This check detects entity additions and deletions. Users who edit entity files
directly in Obsidian without adding or removing files should request a SUMMARY.md
regeneration from the Writing Assistant afterward.

---

### "Next Chapter" Detection

Used by: Planner, /promote-chapter

```
1. Glob stories/<path>/chapters/*.md
2. Count the result. Next chapter = count + 1.
3. If chapters/ is empty or absent: next chapter = 1.
4. Also accept explicit chapter numbers from the user ("chapter 3", "3").
   Explicit input overrides the auto-detected value.
```

---

### Obsidian Wiki Link Convention

Used by: all agents that reference named entities in markdown output

```
All references to named characters, locations, factions, and myths
use [[Name]] format — no folder paths inside the brackets.

Correct:   [[Mara Quill]]
Correct:   [[Harbor Guild]]
Incorrect: [[characters/Mara Quill]]
Incorrect: [[worlds/Example World/characters/Mara Quill]]

This applies to: Relationships tables, Key Members tables,
Current Status fields, HOOKS.md Related fields, and any inline
prose reference in a structured document.
```

---

### ACTIVE_SCHEMES.md Status Values and Lifecycle

Used by: Story Analyzer (writer), Planner, Draft Writer, Reviewer, Draft Fixer (readers)

```
Location: stories/<Story>/state/ACTIVE_SCHEMES.md  (story-local; never merged into worlds/)
Template: templates/story/active_schemes.md
Loader:   load_bible.py loads by default; suppress with --no-schemes.

Status values:
  Active       — deception is in force; prose must preserve the Specifics in the presence of Targets.
  Complicated  — deception is strained: a Target has partial information, a Specifics detail is under pressure,
                 or a new actor has entered the scheme. Still a concealment; treat as Active for prose constraints
                 but flag in the Ledger so the Planner can resolve or escalate next chapter.
  Exposed      — a Target learned the concealed truth on-page. Prose can no longer behave as if the lie holds
                 between those parties. Move Detail block to Resolution Log; note the chapter of exposure.
  Resolved     — the scheme has ended because the Owner abandoned it, the stakes it protected are gone,
                 or the concealment was voluntarily revealed. Move Detail block to Resolution Log.

Required Detail fields per entry: Owner, Target(s), Nature, Status, Origin (chapter), Last touched (chapter),
Specifics (the verbatim lie/promise/concealed fact), Knowledge gaps (who does NOT know).

Who promotes a row to Active?
  The Story Analyzer, after a chapter establishes a concrete, operational detail of concealment —
  a specific lie told, a promise extracted, a document falsified, an identity maintained. Vague
  character tension or generic "has secrets" framing does NOT qualify; those belong in character bibles.

Who moves a row to Exposed/Resolved?
  The Story Analyzer, after reading the chapter that contains the exposure or resolution beat.
  The World Archivist's Consolidate operation audits the ledger at story close and refuses to
  silently archive a story with live Active/Complicated rows — see world-archivist.md Step 3.6b.

See also: STORY_FACTS.md Admission Criterion pattern below — for facts that are simply true of the
world, not actively concealed. If the same detail has both a concealment and an underlying truth,
record the deception in ACTIVE_SCHEMES.md Specifics and the truth (if plot-consequential) in STORY_FACTS.md.
```

---

### STORY_FACTS.md Admission Criterion and Lifecycle

Used by: Story Analyzer (writer), Planner, Draft Writer, Reviewer, Draft Fixer (readers)

```
Location: stories/<Story>/state/STORY_FACTS.md  (story-local; never merged into worlds/)
Template: templates/story/story_facts.md
Loader:   load_bible.py loads by default; suppress with --no-facts.

Admission criterion — BOTH required:
  1. Plot-consequential: if the prose contradicted this fact, a reader would notice a
     continuity error or a character would behave incoherently.
  2. Cross-cuts entities OR belongs to the story's ongoing situation: a fact about
     the world-state that does not live naturally in a single character's or location's
     bible entry.

In scope:
  - Quantities in play (how many guards, how much coin, how many doses remain)
  - Forensic fingerprints (a distinctive weapon, a unique method, a traceable artefact)
  - Logistical specifics (a journey took exactly N days; a safe route was established)
  - In-force commitments between parties (a deal struck, a debt acknowledged on-page)

Out of scope:
  - Facts already fully captured in a character's or location's bible file
  - Vague world atmosphere ("the city is tense") — no single prose contradiction possible
  - Facts that are also actively concealed → record in ACTIVE_SCHEMES.md Specifics instead

Scheme / fact disambiguation:
  If actively concealed → ACTIVE_SCHEMES.md Specifics field (the lie, the cover story).
  If simply true of the world (no Owner, no concealment) → STORY_FACTS.md.
  Both can coexist: the concealed truth goes in STORY_FACTS.md; the deception in ACTIVE_SCHEMES.md.

Status values:
  Current    — fact holds as of the most recently analyzed chapter; all agents must honour it.
  Superseded — fact was changed on-page; moved to Superseded Log with before/after record.

Fact IDs:
  Assigned by the Story Analyzer: F1, F2, ... Stable and never reused — a superseded fact
  keeps its original ID in the Superseded Log; the replacement fact receives a new Fy ID.

Superseded Log:
  When a fact changes on-page, the Story Analyzer cuts the entry from the Ledger and appends
  to the Superseded Log: original ID, what it said, what chapter superseded it, and the new Fy ID.
  Do not silently delete — the before/after record is the audit trail.

Lifecycle:
  Story Analyzer creates entries after chapters that establish qualifying facts.
  Planner reads all Current entries before scene planning (second internalized input, after ACTIVE_SCHEMES.md).
  Draft Writer must not contradict Current entries unless the plan explicitly directs a supersession.
  Reviewer flags silent contradictions in Categories 2 and 4.
  Draft Fixer must not silently contradict Current entries; supersessions require author decision.
  World Archivist: STORY_FACTS.md is never merged into worlds/; no lifecycle audit at story close.
```

See also: ACTIVE_SCHEMES.md Status Values and Lifecycle pattern above — for facts that are actively
concealed by an Owner.

---

### HOOKS.md Status Field Format

Used by: Story Analyzer, Writing Assistant

```
Status values: `Open` · `In Use (<Story Name>)` · `Archived`

When appending a new hook:
- If the hook is not yet used in any story → Status: `Open`

When updating a hook because it is used in a chapter:
- Change Status from `Open` to `In Use (<Story Name>)`
- Example: `In Use (The Tallow Ledger)`

If a hook transitions from one story to another:
- Update the story name in the status
- Example: change from `In Use (Story A)` to `In Use (Story B)`

When a hook is no longer in development:
- Change Status to `Archived`
```

---

### Outline Payoff Annotations

Used by: Story Analyzer (writer), Planner (reader), Outliner (preserve-only constraint)

**Qualification — a prose beat earns an annotation when all three hold:**
1. It introduces a mechanism or commitment (named plan, forensic fingerprint, deferred promise).
2. A specific future chapter is the natural payoff point.
3. The original Outline entry is silent or generic about the mechanism.

**Annotation shape** (appended by Story Analyzer under the target chapter's existing Outline entry):

```markdown
#### Payoff Annotations
_Appended by Story Analyzer as prose commits to specifics. Additive only — the Planner must honour these alongside the entry above._

- **From Ch. N** (Scheme [[Sx]], Fact [[Fy]]) — <constraint: what the target chapter must honour, or retire in an in-scene beat>
  > Honoured in Ch. N — <resolution note>   ← added by Story Analyzer when the payoff chapter is analyzed
```

**Unscheduled setups** — if no target chapter can be identified, Story Analyzer writes to `## Unscheduled Payoff Setups` at the **top** of OUTLINE.md:

```markdown
## Unscheduled Payoff Setups
_Setups with no identifiable target chapter. Assign each or ask the Outliner to revise._

- **From Ch. N** (Scheme [[Sx]]) — <mechanism description>
```

**Hard non-goals:**
- Outliner never creates `#### Payoff Annotations` — only the Story Analyzer appends them.
- Annotations are never deleted; they accumulate as historical record.
- Cross-book setups are never auto-annotated; they surface as user-decision flags.
- Annotations are constraints on how to honour prose already written — not new plot beats.

**Planner:** each bullet is a hard constraint equal in weight to the Outliner's original entry. Quality Check 10 verifies coverage before writing the plan.
