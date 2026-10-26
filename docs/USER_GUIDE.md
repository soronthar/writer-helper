# A first story, step by step

This walks through starting from nothing. The conversation with your agent is in plain language; the quoted lines are examples of what you might say. Every skill saves its work to files, so you can stop and resume at any point.

## 0. Install and create the project

```bash
python skills/writing-room/scripts/wr_install.py --harness claude --project my-novel     # your agent: claude, devin, opencode, hermes
python skills/writing-room/scripts/wr_init.py my-novel
```

Open `my-novel` in your agent. Everything below happens in that session. If a step seems to be skipped, ask the agent to "use the writing-room skill and tell me where I am": it reads the files and says what is next.

## 1. A world

> "Use the writing-room skill. I want to start a new world."

The `create-world` skill interviews you: overview, geography, history, population, economy, magic or technology, belief systems, current state, notes. Say "skip" to any question and it leaves a placeholder for later. At the end it shows a summary table and writes the files only after you say yes.

You do not need a finished world. Add characters, factions, places and myths whenever you like: *"Add a character, a retired harbor inspector who knows too much."* (`writing-assistant`).

## 2. A style (optional, recommended)

> "Create a writing style."

`create-style` asks ten short sections about voice, vocabulary, sentences, dialogue, description, tone, and what to forbid. The most valuable answer is a short sample of prose that sounds like what you want; the draft-writer re-reads it before every chapter. With no style file the draft-writer uses its own judgment.

## 3. A concept

> "Come up with a story for this world."

`story-ideator` offers two modes. In **autonomous** mode you give a few constraints (format, characters, hooks, tropes) and it proposes a full concept. In **collaborative** mode you build it together in conversation. Either way you approve before anything is saved. It also gives the story a working title and places it in the world's chronology.

## 4. An outline

> "Outline it."

`outliner` maps the story structure's stages onto chapters, tracks subplot threads, and settles the concept's open questions. If the story needs a character or place that does not exist yet, it creates one (with your approval in collaborative mode).

## 5. The chapter loop

Repeat for each chapter. You can say "next" or "continue my story" between steps.

1. **Plan.** *"Plan chapter 1."* The planner breaks the chapter into scenes and checks the plan against the outline, the structure, the style, the schemes and facts. Add `preview: true` to read the plan before it is saved.
2. **Draft.** *"Write it."* The draft-writer follows the plan scene by scene. Choose scene-by-scene mode if you want to approve each scene.
3. **Review.** *"Review the chapter."* Two reports appear in `current_chapter/current_reviews/`: continuity (places, time, props, who knows what) and character (voice, behaviour, arc). Nothing is changed.
4. **Fix.** *"Fix the problems."* The draft-fixer makes the smallest change that resolves each reported issue. Anything marked "verify with author" stops and asks you. Fixes it cannot place exactly are listed for you to apply by hand.
5. **Record.** *"Record the chapter."* The story-analyzer updates the story's own copy of the world bible (above all what each character now knows), the timeline, the ledgers of schemes and facts, and suggests new hooks for you to approve.
6. **Promote.** *"Promote the chapter."* After showing exactly what will happen, `promote-chapter` moves the draft into `chapters/` and clears the working folder.

At any time, *"where am I?"* gives a dashboard (`story-status`).

## 6. Finishing a story

When the last chapter is promoted, the router offers to mark the story `Complete` and to **consolidate** it: `world-archivist` shows a plan, resolves conflicts with you, merges the story's world changes into the master bible, adds its events to the world timeline, refreshes the snapshot and rebuilds `SUMMARY.md`. A later story set after it starts from that snapshot.

## Editing by hand

Everything is Markdown. You can fix a draft, reword a plan, or edit a character between any two steps; the next skill reads the file as it is. One caution: `SUMMARY.md` is rebuilt from scratch, so edit entity files, then ask the `world-archivist` to regenerate the summary.

## When something looks wrong

```bash
python skills/writing-room/scripts/wr_doctor.py --root my-novel     # layout, stale index, installation
python skills/writing-room/scripts/wr_next.py --root my-novel       # which skill comes next, per story
```

See also the troubleshooting list in the [README](../README.md#troubleshooting). The sample in [`examples/sample-project`](../examples/sample-project) shows what a finished project looks like.
