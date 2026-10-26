# Analysis rules: what to record for each chapter

Used in Step 5. Work through each section for the chapter being analyzed.

#### Characters

For every named character who appears in the chapter, determine:

**Location:** Where does the chapter leave them? Be specific — "Harrowmere, lower city, Mara's rooms" is better than "Harrowmere." If they are in transit, record "En route from X to Y."

**Physical condition:** Any new injuries, illness, exhaustion, or healing? Record precisely. "Left shoulder wound from an arrow, Chapter 3" is better than "Injured." If unchanged, no update needed.

**Story state:** Alive / Captured / Deceased / Missing / Changed status? Update only if it changed.

**Relationship changes:** Only update if a significant, durable change occurred — a trust broken, an alliance formed, a secret revealed between two characters. Do not record every conversation. One interaction, even intense, rarely warrants a Relationships table update unless it materially redefines how these characters regard each other.

**Knowledge state — highest priority:** What significant new information does this character now possess? This feeds every future Reviewer-Consistency check. Append to the character's Notes section:

```
**Knows (as of <Story Name> — Chapter N):** <specific fact they learned — e.g., "The eastern valley of the Drowned Flats exists and is omitted from official maps.">
```
For a Book Series, use: `**Knows (as of <Series Name> — Book N — Chapter M):**`
```

Write one line per distinct fact. Be specific enough that a future reviewer can evaluate whether a character "should know" something. Vague entries ("Knows more about the conspiracy") are useless.

#### Locations

For each location with significant events, determine:

**Condition:** Did the physical state of the location change? Damage, destruction, occupation, abandonment?

**Key Inhabitants / Factions:** Did the controlling faction or a notable resident change?

**Do not update** a location file merely because a scene was set there. The location must have experienced a material change. A tavern where characters had a conversation is unchanged. A tavern that burned down is not.

#### Factions

For each faction with politically significant chapter events, determine:

**Standing:** Did the faction's position in the broader landscape shift?

**Internal condition:** Any leadership changes, public fractures, consolidation of power?

**Do not update** a faction file for a background mention. The faction must have been an active participant in a meaningful development.

#### Active Schemes

Read `state/ACTIVE_SCHEMES.md` (already in context from the script output in Step 4b). For each Active or Complicated entry in the Active Ledger, determine how the chapter affected it:

- **Advanced, unchanged status** — the owner reinforced the deception, repeated the lie, extracted another concession. Update `Last touched: Chapter N`. Add a short line to Notes if the chapter added a meaningful specific (new detail in the lie, new pressure on the target). No status change.
- **Complicated** — a target began to suspect; a precondition is faltering; the owner had to improvise around a near-exposure. Change Status `Active → Complicated`. Update `Last touched: Chapter N`. Note the specific slippage.
- **Exposed** — the deception was revealed to its target(s). Change Status to `Exposed`. Update `Last touched: Chapter N`. Move the full Detail block to the Resolution Log, adding a one-line resolution summary at the top of the moved block.
- **Resolved** — the scheme concluded on the owner's terms (paid off, quietly abandoned, absorbed into a larger scheme). Change Status to `Resolved`. Move to Resolution Log with a one-line summary.
- **No mention** — entry unchanged. Do not touch `Last touched`.

Then scan the chapter for **new schemes** — any deception, concealment, manipulation, or unresolved operational commitment a character initiated or inherited that is not already in the ledger. A new scheme qualifies if:
- A character told a lie a reader is meant to recognize as a lie.
- A character extracted a promise or concession the chapter frames as consequential.
- A character concealed an object, fact, or identity whose later revelation would matter.
- A character accepted an obligation whose payoff is deferred.

For each new scheme, draft an entry (next available `SN` ID) with: Owner, Target(s), Nature, Status `Active`, Origin = Chapter N, Last touched = Chapter N, Specifics (verbatim or near-verbatim from the prose so the `planner` can keep it consistent), Knowledge gaps, Notes if any.

Do not create scheme entries for trivial social lies ("I'm fine"), in-the-moment misdirection with no carry-over, or a character simply withholding information they have never been asked about. The test is whether a future chapter would need to know the specific shape of the deception.

---

#### Story Facts

After updating Active Schemes, scan the chapter for new plot-consequential facts to record in `state/STORY_FACTS.md`, and for changes to existing `Current` facts.

**Admission criterion — both required:**
1. **Plot-consequential** — a downstream chapter contradicting this fact would be a noticeable continuity error, or would require the `planner`/`draft-writer` to invent a reason for the change.
2. **Cross-cuts entities OR belongs to the story's ongoing situation** — the fact does not belong naturally in any single character/faction/location bible file. If it belongs in a single entity file, record it there via the `state/bible/` lazy-copy mechanism instead, not here.

**In scope:** quantities that can shift (e.g., "47 Archive keys remain"), logistical specifics (meeting places, routes, passwords), forensic/institutional fingerprints (e.g., "the authorization code carries Customs formatting"), terms of in-force agreements or commitments.

**Out of scope:** stable character traits, world-baseline facts (those go in entity bibles), one-off scene details no future chapter will reference.

**Scheme/fact disambiguation:** if there is an Owner actively concealing the fact from a Target, it belongs in ACTIVE_SCHEMES.md under Specifics — not here. If the fact is simply true of the story world, independent of any deceiver, it belongs here.

**When in doubt, lean toward omission.** A leaner ledger is more useful than a bloated one.

**For each new qualifying fact:**
Draft an entry (next available `Fy` ID) with: Category (`Quantity / Fingerprint / Logistics / Commitment / Other`), Fact (one-line canonical form), Specifics (verbatim prose detail when precision matters), Status `Current`, Origin = Chapter N, Last touched = Chapter N, Related entities if any, Notes if any.

**For each existing `Current` fact:**
- **Referenced or confirmed** — update `Last touched: Chapter N`. Add a short note if the chapter added a meaningful specific.
- **Superseded** — if the chapter changes the fact on-page (e.g., a quantity drops), move the Detail block to the Superseded Log with a one-line pointer (`→ Superseded at Chapter N; see Fy for updated value.`), and create the replacement as a new `Fy` ID.
- **No mention** — entry unchanged. Do not touch `Last touched`.

---

#### Outline Payoff Annotations

After updating Active Schemes, scan the chapter for setup-for-later mechanisms that deserve an annotation on a future chapter's OUTLINE.md entry. A prose beat qualifies when **all three** conditions hold:

1. **It introduces a mechanism or commitment** — a specific way a later event is set up, a named plan, a piece of evidence with a forensic signature, a promise whose fulfilment is deferred.
2. **A specific future chapter is the natural payoff point** — either the `outliner`'s entry explicitly covers that event, or the prose itself points at a scheduled beat.
3. **The original Outline entry is silent or generic about the mechanism** — annotating is only valuable when the `outliner` couldn't have known this specific detail. If the Outline already names it, no annotation is needed.

**In scope:** payoff setups, specific framings the prose commits to, forensic fingerprints a later beat must acknowledge, scheduled reveals, named fallback plans.

**Out of scope:** general mood, thematic observations, character-development notes, anything that reshapes the `outliner`'s intended plot direction.

**Non-goals (hard constraints):**
- Never modify the `outliner`'s original text. Annotations are strictly additive.
- Never invent plot direction. Annotations state what the target chapter must honour — not new beats.
- Never auto-annotate a different book's OUTLINE.md. Cross-book setups surface as a flag in the structured output for user decision.
- Never delete an existing annotation. Once written, it stays as a historical record.

**For each qualifying setup:**

1. **Identify the target chapter.** Prefer the chapter whose Outline entry names the payoff event. If none, use the nearest future chapter whose beats implicate the mechanism. If no target chapter can be identified, treat as unscheduled (see below).

2. **Compose the annotation bullet:**
   ```
   - **From Ch. N** (Scheme [[Sx]], Fact [[Fy]]) — <1–3 sentences: what the target chapter must honour, and if relevant an alternative: "or the mechanism must be explicitly retired in an in-scene beat.">
   ```
   Reference ledger IDs from ACTIVE_SCHEMES.md and STORY_FACTS.md so the `planner` can resolve full context. If no ledger ID applies, omit the parenthetical.

3. **Check for annotations to resolve.** Read the `#### Payoff Annotations` subsection (if any) in the *current chapter's* own Outline entry. For each bullet that named this chapter as the target, determine whether the prose honoured or retired the setup:
   - **Honoured** — append below the bullet: `  > Honoured in Ch. N — <one-line note of how it landed.>`
   - **Retired** — append: `  > Retired per plan in Ch. N — <one-line note of the in-scene beat that closed it.>`
   - **Unresolved** — do not add a note; surface as `⚠ Unresolved annotation` in the structured output.

**Unscheduled setups:** if no target chapter can be identified, write the setup to the `## Unscheduled Payoff Setups` section at the **top** of OUTLINE.md (create the section if absent):

```markdown
## Unscheduled Payoff Setups
_Setups detected by `story-analyzer` with no identifiable target chapter. Assign each to a chapter or ask the `outliner` to revise the outline._

- **From Ch. N** (Scheme [[Sx]]) — <mechanism description>
```

Surface each in the structured output as `⚠ Unscheduled setup` with the mechanism description, instructing the user to assign it to a chapter manually or via an `outliner` revision.
