# Consistency pass: categories and severity

Work through CONTENT.md from the first paragraph to the last. For every factual claim in the prose — every place, every object, every assertion about what a character knows, every cause-and-effect relationship — ask: *"Does what I have read support this?"*

Check all six categories:

#### Consistency Category 1 — Geography and Location

- Can characters reach each location they visit given the travel time implied by the prose?
- Are locations described consistently with their world bible entries (physical layout, atmosphere, notable features, surroundings)?
- Do relative positions of locations match DESCRIPTION.md and the location files?

**Flag:** a character arrives somewhere too quickly for the established distance; a building is on the wrong side of a river; a location's interior contradicts its world bible entry.

#### Consistency Category 2 — Timeline and Chronology

- Does the chapter's opening situation connect plausibly to where the previous chapter ended in time of day, elapsed time, and immediate circumstance?
- Is the time of day internally consistent throughout the chapter?
- Do seasonal or environmental details (light quality, vegetation, weather patterns) fit the established point in the story's calendar?
- Does the chapter refer to past events consistently with the Timeline — nothing referenced as past that hasn't happened; nothing referenced as future that the Timeline already records?
- Does the chapter honour in-force commitments recorded as `Current` entries in STORY_FACTS.md with a `Commitment` category? (e.g., the terms of a truce, the schedule of a standing meeting, the deadline of an agreement)

**Flag:** a chapter opens at dawn when the previous chapter ended at midday with no time skip; a character references "last winter's battle" when the Timeline places that battle two years away; the foliage is autumnal when the Timeline puts this in spring; a chapter violates or ignores a Current Commitment fact from STORY_FACTS.md without an on-page beat that supersedes it.

#### Consistency Category 3 — World Rules

- Does any use of magic, technology, or special ability operate within the rules established in `DESCRIPTION.md` and the relevant world bible entries?
- Do the political facts, authority structures, and power relationships between factions match their current status files?
- Do economic details (what is scarce, what is common, what currency is used, what trade relationships exist) match the world bible?

**Flag:** a character uses magic that the rules say requires preparation and uses it spontaneously; a faction issues orders it lost the authority to issue; characters trade in a currency that was abolished.

#### Consistency Category 4 — Prop and Object Continuity

- Does every significant object a character uses or references exist for them to have? Was it acquired? Was it previously lost, destroyed, given away, or confiscated?
- Do physical details about objects (condition, appearance, modifications) match how they were last described?
- Do injuries, wounds, scars, or physical conditions carry over correctly from prior chapters? Do they heal at a plausible rate?
- Does the chapter respect quantities, forensic fingerprints, and logistical specifics recorded as `Current` entries in STORY_FACTS.md? (e.g., a count of remaining resources, an institutional code format, a meeting place or password)

**Flag:** a character draws a sword that was taken from them in the previous chapter; a document is destroyed in Chapter 3 and then produced again in Chapter 5; a severe wound from yesterday is entirely forgotten; a quantity in the prose contradicts a Current Quantity or Fingerprint fact from STORY_FACTS.md without an on-page supersession beat.

#### Consistency Category 5 — Character Knowledge State

- Does a character act on information they could not yet possess? Consider: was this information available to them, delivered to them, or observable by them before this chapter?
- Does a character fail to act on information they definitively have — especially if failure would be conspicuous or uncharacteristic given what they know?
- Are secrets maintained correctly — does a character act as though they do not know something that has not yet been revealed to them?
- **Active schemes compliance.** For every `Active` or `Complicated` scheme in ACTIVE_SCHEMES.md: does the prose preserve the scheme's Specifics field in the presence of any character listed under Knowledge gaps? A leak is any dialogue, narrated action, or internal monologue (when the POV belongs to someone inside the scheme) that reveals to a Target what the scheme is concealing, without a scene beat that explicitly justifies the reveal. For `Exposed` and `Resolved` entries in the Resolution Log: is the chapter consistent with those events having already happened?

**Note:** Do not flag emotional reactions, personality-based decisions, or behaviour that might simply be in-character. Only flag *factual knowledge*: does this character *know* this fact at this point in the story? Emotional and behavioural consistency belongs to the character pass.

**Flag:** a character navigates unerringly to a location they have never been told about; a character is shocked by a revelation that was told to them two chapters ago; a spy acts on intelligence they could only have obtained after this chapter's events; a character whose Active scheme conceals fact X from [[Target]] casually mentions X in [[Target]]'s presence with no beat acknowledging the slip; a character behaves as if a deception is still live after the Resolution Log records it as Exposed.

#### Consistency Category 6 — Cause and Effect

- Does this chapter's opening situation follow causally from the previous chapter's conclusion?
- Are consequences established in previous chapters carried through? If a character was imprisoned, they are still imprisoned unless released. If an alliance was broken, it is still broken unless repaired.
- If the chapter contradicts a prior consequence, is there a stated reason in the prose?

**Flag:** a locked city gate that ended the previous chapter is open without explanation; a character who was publicly disgraced walks into court without remark; an army positioned to attack has vanished with no mention.

---

**Severity assessment for consistency issues:**

- **Critical** — a hard factual contradiction that cannot be rationalized. The `draft-fixer` must address this before the chapter can be promoted.
- **Moderate** — a soft contradiction or discrepancy that might be intentional but is not clearly signalled as such. The author needs to make a decision.
- **Minor** — a potential inconsistency or ambiguity. The text is not obviously wrong, but something does not fully align. Flagged for awareness.

**Deliberate choices:** if a potential inconsistency could plausibly be intentional, mark it **Minor** with the note: *"Possible deliberate choice — verify with author."*

**World bible gaps:** if the world bible is silent on a point the chapter addresses, do not flag it as an inconsistency. Note it in Reviewer Notes as a gap, and suggest the `writing-assistant` be invoked to document it.

Hold all consistency findings in memory. Do not write any file yet.
