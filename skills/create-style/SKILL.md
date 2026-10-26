---
name: create-style
description: "Create a new prose style file through a guided interview. Use when the user wants to define how their fiction should sound: narrative voice, vocabulary, sentence and paragraph structure, dialogue, description, tone, forbidden elements and example prose. Walks through 10 sections one question at a time, lets any question be skipped, and writes writing_concepts/styles/<Style Name>.md after the user confirms. The draft-writer and draft-fixer skills follow this file."
---

# Create Style

You are helping the user define a new writing style for the Writing Room framework. Style files live in `writing_concepts/styles/` and are read by the `draft-writer` and `draft-fixer` skills when generating or fixing prose. Shared rules and where templates are found: `../writing-room/references/conventions.md`.

Before starting the interview, read the template file fresh:
`templates/writing_concepts/style.md`

---

## Rules

- Work through all 10 sections in order.
- Ask each question clearly. Where options exist, list them explicitly.
- **If the user types "skip"**, leave that field's `<placeholder>` text in place — do not invent an answer.
- **If the user types "skip section"**, skip all remaining questions in the current section and move to the next.
- Ask one section at a time. Announce each section with its number and name before asking its questions.
- After all sections are complete, show a summary (filled vs. skipped) and ask for confirmation before writing anything.
- Write the file only after the user confirms.

---

## Opening

Greet the user and explain that you'll work through the 10 style sections together, one at a time. Any question can be skipped and filled in manually later.

Then ask:

1. **Style name** — What would you like to name this style? *(Becomes the filename: `<Style Name>.md`)*
2. **One-line description** — In one sentence, what kind of story or writing does this style suit?

---

## Section 1 — Narrative Voice

1. **Point of View** — Which POV does this style use?
   *Options: First person / Second person / Third person limited / Third person omniscient / Multiple POV*
   - If **Multiple POV**: What is the rule for shifts? *(One POV per chapter / Shifts permitted at section breaks only / Other — describe)*

2. **Tense** — Past or present?

3. **Narrator Distance** — How close is the narrator to the character's inner experience?
   *Options: Intimate (deep interiority, free indirect discourse) / Close (strong interiority, clearly third person) / Moderate (balanced interiority and observation) / Remote (primarily external, minimal interiority)*

4. **Narrator Reliability** — Reliable or unreliable?
   - If **unreliable**: How and to what degree?

5. **Narrator Presence** — Does the narrator have their own personality?
   *Options: Transparent (narrator is invisible) / Slightly present (occasional dry observation) / Strong (narrator is a voice in their own right)*

6. **Free Indirect Discourse** — Can narrator and character thought blend without attribution?
   *Options: Yes / No (interiority always clearly marked with italics or attribution)*

---

## Section 2 — Vocabulary

1. **Register** — What is the overall vocabulary register?
   *Options: Formal / Literary / Neutral / Conversational / Colloquial / Archaic*

2. **Complexity** — How complex should the vocabulary be?
   *Options: Simple and accessible / Moderate — varied but not ostentatious / Rich — precise, literary vocabulary expected*

3. **Domain / Period Language** — Any setting-specific or period-specific language?
   *Examples: medieval trade terms, contemporary British slang, medical terminology for a doctor POV. Type "none" if not applicable.*

4. **Consistency Across POVs** — Do all POVs share the same vocabulary register, or does each character have their own?

5. **Common Expressions** — Are there recurring phrases, oaths, affirmations, or idioms that belong to this style's world or voice?
   *Examples: "Sure thing", "Yes, ma'am", "By the Compact", "Right enough". List them, or skip.*

6. **Prohibited Words / Phrases** — Any specific words or filler phrases to ban?
   *Examples: "very", "suddenly", anachronistic slang in a historical setting. List them, or skip.*

---

## Section 3 — Sentence Structure

1. **Typical Length** — What is the average sentence length?
   *Options: Short (5–12 words) / Medium (12–20 words) / Long (20+ words) / Varied (deliberate rhythm alternating short and long)*

2. **Dominant Syntax** — What syntactic pattern dominates?
   *Options: Subject-verb-object (direct, declarative) / Inverted or suspended (verb or object held back for effect) / Cumulative (main clause first, details after) / Periodic (details first, main clause at end)*

3. **Subordinate Clauses** — How heavily are they used?
   *Options: Minimal / Moderate / Heavy*

4. **Parallelism and Lists** — How are parallel structures used?
   *Options: Avoid — prefer varied structure / Use sparingly for emphasis / Use freely for rhythm*

5. **Sentence Fragments** — Are fragments permitted?
   *Options: Not permitted / In action sequences only / In interiority only / Permitted freely*

6. **Rhetorical Patterns** — Any recurring syntactic devices that define this style?
   *Examples: anaphora ("She had not eaten. She had not slept. She had not stopped."), chiasmus, deliberate repetition. Describe, or skip.*

---

## Section 4 — Paragraph Structure

1. **Typical Length** — How long are paragraphs?
   *Options: Very short (1–3 sentences) / Short (3–5 sentences) / Medium (5–8 sentences) / Long (8+ sentences) / Varied*

2. **Single-Sentence Paragraphs** — Are they permitted?
   *Options: Not permitted / For emphasis only — use sparingly / Permitted freely*

3. **Scene vs. Summary Balance** — How much narrative compression is used?
   *Options: Scene-dominant (most paragraphs render action or dialogue in real time) / Balanced / Summary-dominant (narrator frequently compresses time and reports events)*

4. **Paragraph Openings** — Any rules for how paragraphs begin?
   *Options: No rule / Avoid starting consecutive paragraphs with the same word or construction / Each paragraph should open with a grounding beat (action, image, or statement)*

5. **Transitions Between Paragraphs** — How are paragraphs connected?
   *Options: Hard cuts (no transitional phrases, reader bridges the gap) / Soft transitions (light connective tissue) / Explicit transitions (time markers and connective phrases used freely)*

6. **White Space / Section Breaks** — When are section breaks (`***`) used?
   *Options: Scene changes only / Used freely to shift focus or create pause / No section breaks within chapters*

---

## Section 5 — Chapter Structure

Remind the user before this section: **Chapter Opening, Chapter Ending, and Pacing are defaults.** Individual chapter plans can override them.

1. **Typical Length** — What is the target word count range per chapter?
   *Example: "1,500–3,000 words". Or "No fixed length".*

2. **POV per Chapter** — What is the POV rule at chapter level?
   *Options: Single POV — one character per chapter, no exceptions / Single POV — shifts permitted at section breaks / Multiple POVs permitted within a chapter*

3. **Chapter Titles** — Numbered only, or does each chapter get a title?
   - If **titles**: What is the naming convention? *(Single word / Character name / Place name / Other — describe)*

4. **Chapter Opening (default)** — How do chapters typically begin?
   *Options: In medias res (middle of action or dialogue) / Establishing beat (grounding in place and character before action) / Image or mood (observation or image that sets tone)*

5. **Chapter Ending (default)** — How do chapters typically end?
   *Options: Cliffhanger or unresolved beat / Quiet close (reflection, image, or rest) / Resolution (chapter completes its own mini-arc)*

6. **Pacing Within a Chapter (default)** — What is the typical pacing pattern?
   *Options: Front-loaded (tension early, winds down) / Back-loaded (builds steadily toward the closing beat) / Even (consistent throughout)*

---

## Section 6 — Dialogue

1. **Dialogue Tags** — What attribution convention does this style use?
   *Options: "said" only / "said" and "asked" only / Varied tags with action beats / Action beats preferred — minimize "said"*

2. **Adverbs on Tags** — Are adverbs permitted on dialogue tags?
   *Options: Never — convey manner through the dialogue itself / Sparingly — only when manner can't be shown otherwise / Permitted freely*

3. **Dialect and Accent** — How is dialect represented?
   *Options: Standard spelling only (imply through word choice and rhythm) / Light phonetic marking (dropped g's, contractions) / Full dialect spelling*

4. **Subtext** — Do characters say what they mean?
   *Options: Dialogue is direct / Subtext — what is said and what is meant regularly diverge / Mixed — character-dependent (describe)*

5. **Conversation Rhythm** — How long are exchanges?
   *Options: Short exchanges (quick back-and-forth) / Mixed (alternates short and long turns) / Speeches permitted (characters may hold the floor for a paragraph or more)*

6. **Internal Monologue** — How is a character's inner voice rendered?
   *Options: Italics, no attribution — `She was lying, wasn't she?` / Italics with attribution — `She was lying`, she thought / Third person, no italics — woven in via free indirect discourse / Not used — interiority expressed through action and observation*

7. **Punctuation Conventions** — Standard, or any non-standard conventions?
   *Standard = comma before tag, period for action beat. Describe any variations, or skip.*

---

## Section 7 — Description

1. **Descriptive Density** — How much description does this style use?
   *Options: Sparse (reader fills the gaps) / Moderate (key details for atmosphere and grounding) / Rich (extended, layered; world is fully rendered)*

2. **Sensory Priority** — Which senses dominate?
   *Options: Visual-dominant / Multi-sensory (all five senses used actively) / Other — specify dominant non-visual sense*

3. **Metaphor and Simile** — How much figurative language?
   *Options: Avoided (plain literal description) / Sparse (one strong image per scene) / Moderate (woven throughout) / Rich (figurative language is a defining feature)*

4. **Metaphor Source** — Where do metaphors come from?
   *Options: No rule / Grounded in the POV character's world and experience (a soldier's metaphors come from war) / Consistent domain — describe (e.g. "natural world", "trade and commerce", "architecture")*

5. **Character Description** — How are characters physically described?
   *Options: Immediate (full description on first appearance) / Gradual (details emerge over several scenes) / Functional (only what is relevant to the scene)*

6. **Setting Description** — How are locations described?
   *Options: Establishing (dedicated description block when entering a new location) / Embedded (woven into action and dialogue, no dedicated blocks) / Atmospheric (mood and selected sensory detail, no inventory)*

7. **Describing Others Through POV** — Are descriptions of other characters filtered through the POV character's feelings and biases?
   *Options: Objective (neutral descriptions) / Filtered (descriptions reflect the POV character's feelings toward the person being described)*

---

## Section 8 — Tone / Mood

1. **Overall Register** — What is the dominant emotional tone?
   *Options: Dark / Melancholic / Tense / Gritty / Neutral / Wry / Dry / Hopeful / Light / Comic*
   *Choose one primary, optionally one secondary.*

2. **Consistency** — Does the tone stay constant or shift?
   *Options: Constant / Shifting (describe the pattern if known) / Character-dependent (each POV has its own tonal register)*

3. **Emotional Distance** — How does the narrator relate to what's happening?
   *Options: Close (emotionally engaged) / Neutral (observes without editorialising) / Ironic (detachment or wry distance)*

4. **Humour** — What role does humour play?
   *Options: None / Dry wit (understated, situational) / Dark humour (comedy from grim circumstances) / Warm humour (character-based, affectionate) / Satirical*

5. **Tension** — How is tension built in this style?
   *Examples: withholding information from the reader, short clipped sentences in action beats, dramatic irony, dread through mundane detail. Describe, or skip.*

6. **Tension Release** — How is tension released?
   *Options: Through resolution of the immediate conflict / Tension releases are rare — pressure accumulates across chapters / Comic beats / Quiet character moments*

---

## Section 9 — Forbidden Elements

Explain to the user: **this section is a hard prohibition list**, not a preference list. The `draft-writer` and `draft-fixer` skills treat everything here as an absolute ban, and a reviewer uses this list when evaluating drafts. Skipping an item means that category has no prohibitions.

For each sub-list, show the template's example items and ask the user to **keep them, replace them, add to them, or skip the entire sub-list**.

1. **Prose Patterns to Avoid**
   *Template examples: throat-clearing openings (weather, waking up, mirror), passive constructions used to avoid agency, over-explained emotion (showing then immediately telling), physically impossible simultaneous actions.*

2. **Words and Phrases to Avoid**
   *Template examples: adverbs on dialogue tags ("whispered softly"), filler intensifiers ("very", "really", "just"), AI-slop abstractions ("a wave of relief", "something shifted inside her"), melodramatic standbys ("little did she know", "nothing would ever be the same").*

3. **Structural Patterns to Avoid**
   *Template examples: dream sequences for exposition, flashbacks longer than one paragraph without narrative reason, characters explaining things both parties already know.*

4. **Tonal Registers to Avoid**
   *Template examples: sentimentality (reaching for feeling the prose hasn't earned), ironic detachment applied to moments that require sincerity.*

5. **Tropes to Avoid**
   *Any story tropes or character clichés incompatible with this style. Cross-reference `writing_concepts/tropes/` if applicable. List, or skip.*

---

## Section 10 — Examples

Explain to the user: **the Style Excerpt is the single most important field in the entire template.** The `draft-writer` re-reads it before writing each chapter. If anything in sections 1–9 conflicts with the excerpt, the excerpt wins.

1. **Reference Authors / Works** — Any authors or works whose prose this style resembles?
   *Ask for the name and the specific quality being referenced — not just "Hemingway" but "Hemingway's short declarative sentences and refusal to explain emotion". List, or skip.*

2. **Style Excerpt** — A paragraph or two of prose that exemplifies this style.
   *Can be sourced from a reference work (with attribution) or written by the user as a target sample. Paste it here, or skip — but encourage the user to return and fill this in, as it is the ground truth for the `draft-writer`.*

3. **Anti-Example** — A passage or description of what this style must NOT sound like.
   *Optional but high-value when the user knows the specific failure mode they're trying to avoid. Describe or paste, or skip.*

---

## After the Interview

1. Display a summary table:

   | Section | Field | Status |
   |---------|-------|--------|
   | 1. Narrative Voice | Point of View | Filled: Third person limited |
   | 1. Narrative Voice | Free Indirect Discourse | **Skipped** |
   | ... | ... | ... |

2. Ask: *"Does this look right? Type 'yes' to write the file, or tell me what to change."*

3. Once confirmed:
   - Read `templates/writing_concepts/style.md` fresh.
   - Assemble the file by replacing each `<placeholder>` with the user's answer. For skipped fields, leave the original `<placeholder>` text exactly as it appears in the template.
   - Write the completed file to `writing_concepts/styles/<Style Name>.md`.
   - Report with the full file path and a list of all fields still requiring manual completion.

**Next step:** the style is used automatically by `draft-writer`. With one style file it is picked up as is; with several, name the one to use in the story's `CONCEPT.md` Notes.
