---
name: roleplay
description: "Turn a transcript with dialogue into a two-sided You/Partner practice script so the learner can speak one role aloud and rehearse real conversation. Use when the user shares a transcript (interview, vlog with exchanges, conversation, lesson) and wants to practice speaking one side, do a role-play, or rehearse turn-taking, e.g. 'make a roleplay from this', 'let me practice one side of this conversation', 'two-person script to practice'."
model: sonnet
---

Turn the transcript into a rich two-sided role-play script for speaking practice.

## Prime directive — maximum coverage, full conversations (depth = more scenes & turns, grounded in the source)

This is **not** a thin set of two or three sample exchanges. Convert the **whole** transcript into a comprehensive role-play corpus the learner can rehearse end to end. Prioritize completeness and natural conversational richness over a short script.

- **Cover the entire transcript** — every real exchange AND every substantial narration stretch becomes a scene. Don't stop after the first few; a long source yields many scenes.
- **Make each scene a full exchange**, not a single question-and-answer — multiple turns of natural back-and-forth (within the per-scene turn cap below) so the learner rehearses real turn-taking, not isolated lines.
- **No artificial length limits** on the number of scenes. More coverage is better, as long as every scene is grounded in the source.
- **Depth is grounded, not invented.** "More" means converting more of the real material into dialogue and writing fuller exchanges — NOT fabricating topics, opinions, or facts the speaker never expressed. Type B questions must be the natural prompt for words the speaker actually said.
- If the result reads like a couple of sample turns rather than a rehearsal script for the whole conversation, it has failed.

## Step 1 — Comb the transcript for everything role-play-able (capture it all — these are minimums, not caps)

Read end to end and mark every piece of material that can become a spoken scene:

- **Real exchanges** — every genuine back-and-forth in the source (interviews, questions, social exchanges, negotiations, small talk with substance).
- **Narration stretches** — every substantial monologue passage (opinions, observations, explanations, stories, decisions) that can be turned into an interview-style scene.
- **Distinct topics** — each new subject or location is a candidate scene boundary; don't merge unrelated material into one giant scene.

## Two types of scenes to include

**Type A — Real exchanges:** Any genuine back-and-forth dialogue in the source. Keep lines verbatim (light trimming ok). Label the learner as **You** (default: the asking/reacting side). Preserve as many of the real turns as make a natural scene — don't collapse a six-turn exchange into two.

**Type B — Narration-to-conversation:** For every substantial narration stretch (opinions, observations, explanations, stories the speaker tells), convert it into a short interview scene. Write a **Partner** question that naturally prompts the narrated content, then write **You** lines that deliver the narration as if answering that question. Keep the speaker's actual words and phrases as much as possible — rephrase minimally to make them flow as a spoken reply. Break a long narration into several Partner/You turns rather than one giant answer.

Include both types throughout the transcript, beginning to end. A one-hour video should produce **8–15+ scenes** — more if the material supports it; don't cap a rich source.

## Output format

```
# Role-play — [Title]

## Scene 1 — [label]
> *Real exchange* / *Narration → conversation*

**Partner:** …
**You:** …
**Partner:** …
**You:** …

## Scene 2 — [label]
…
```

Mark each scene header with `> *Real exchange*` or `> *Narration → conversation*` so the learner knows which type it is.

## Rules

- No purely invented content: Type B Partner questions should be the natural prompt for the speaker's own words; Type A stays verbatim (light trimming only).
- Aim for intermediate-to-advanced vocabulary and natural spoken rhythm — avoid oversimplifying.
- Keep scenes short enough to say aloud comfortably (4–10 turns max) — but DO use multiple turns; a one-exchange scene is too thin.
- Ready-to-save Markdown. No preamble.

## What NOT to include

- **No fabricated topics, opinions, or facts** the speaker never expressed — every scene traces back to real source material.
- **No thin coverage** — don't ship two or three sample scenes for a long transcript, and don't reduce a multi-turn exchange to a single Q&A.
- No oversimplified, textbook-stiff dialogue — keep the natural spoken register.
- No preamble, no commentary, no code-fence wrapper around the document.
- No grammar notes, vocabulary lists, or speaking tips — this is a practice script, not a lesson.
