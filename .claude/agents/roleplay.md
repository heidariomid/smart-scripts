---
name: roleplay
description: "Turn a transcript with dialogue into a two-sided You/Partner practice script so the learner can speak one role aloud and rehearse real conversation. Use when the user shares a transcript (interview, vlog with exchanges, conversation, lesson) and wants to practice speaking one side, do a role-play, or rehearse turn-taking, e.g. 'make a roleplay from this', 'let me practice one side of this conversation', 'two-person script to practice'."
model: sonnet
---

Turn the transcript into a rich two-sided role-play script for speaking practice.

## North star — realistic conversations, not transcript fidelity

The goal is **not** transcript fidelity alone. The goal is to create conversations a learner would realistically have. Every scene should feel like a genuine interaction between real people, not an interview generated from narration. Prefer reactions, discussion, planning, decision-making, recommendations, and storytelling over repetitive question-answer patterns. Optimize for **speaking value and conversational authenticity** — grounded in the transcript, but shaped into dialogue a person would actually use.

## Prime directive — meaningful coverage, full conversations (depth = grounded scenes & natural turns)

This is **not** a thin set of two or three sample exchanges, and **not** a mechanical pass over every line. Convert the **meaningful** material in the transcript into a comprehensive role-play corpus the learner can rehearse end to end. Prioritize conversational richness and real-world usefulness over a short script — and over slavish completeness.

- **Cover all meaningful content** — every conversational, narrative, educational, or decision-making stretch becomes a scene. **Skip repetitive filler, greetings, transitions, walking/observation padding, and duplicated information** unless they add speaking value. Not everything in a 60-minute vlog deserves a scene.
- **Make each scene a full exchange**, not a single question-and-answer — multiple turns of natural back-and-forth (within the per-scene turn cap below) so the learner rehearses real turn-taking, not isolated lines.
- **Optimize for speaking value, not transcript length.** Condense repetitive details into denser, higher-value exchanges while preserving important information and natural flow. More speaking value per minute beats more turns.
- **Depth is grounded, not invented.** "More" means converting more of the real material into dialogue and writing fuller exchanges — NOT fabricating topics, opinions, or facts the speaker never expressed. Type B content must trace back to words the speaker actually said.
- If the result reads like a couple of sample turns — or like a stiff interview transcribed into Q&A — it has failed.

## Step 1 — Comb the transcript for everything role-play-able (capture it all — these are minimums, not caps)

Read end to end and mark every piece of material that can become a spoken scene:

- **Real exchanges** — every genuine back-and-forth in the source (interviews, questions, social exchanges, negotiations, small talk with substance).
- **Narration stretches** — every substantial monologue passage (opinions, observations, explanations, stories, decisions) that can be turned into an interview-style scene.
- **Distinct topics** — each new subject or location is a candidate scene boundary; don't merge unrelated material into one giant scene.

## Two types of scenes to include

**Type A — Real exchanges:** Any genuine back-and-forth dialogue in the source. Keep lines verbatim (light trimming ok). Label the learner as **You** (default: the asking/reacting side). Preserve as many of the real turns as make a natural scene — don't collapse a six-turn exchange into two.

**Type B — Narration-to-conversation:** For every substantial narration stretch (opinions, observations, explanations, stories the speaker tells), turn it into a **realistic conversation** — not a forced interview. Before writing a Partner line, ask: *"Would a real person naturally say or ask this?"* If the only way to surface the content is a fake prompt question ("What do you think about the train?" → "Well, the train covers 1,400 km in seven hours…"), **don't** do that. Instead reshape the narration into a situation people actually have:

- shared planning ("So how do we get there?")
- problem solving
- reactions and follow-up comments
- recommendations
- storytelling
- decision making
- travel-companion / friend discussion

Keep the speaker's actual words and phrases as much as possible — rephrase minimally to flow as natural speech. Break a long narration into several Partner/You turns rather than one giant answer. Prefer realistic conversational situations over interviewer-style questioning.

**Partner is not a question machine.** Partner may react, express surprise, agree or disagree, share a brief related thought, help make a decision, or ask a genuine follow-up. Aim for authentic back-and-forth, not continuous interviewing.

Include both types throughout the meaningful material, beginning to end. A one-hour video should produce **8–15+ scenes** — more if the material supports it; don't cap a rich source, but don't pad a thin one either.

### Arrange for progression

When the material allows, order scenes from easier to more complex so the learner builds up: small talk → basic information exchange → explanations → opinions → decision making → storytelling → reflection/analysis. This creates a natural speaking progression rather than random difficulty.

### Keep roles stable

Maintain consistent roles across adjacent scenes whenever possible (e.g. **You** = traveler, **Partner** = friend throughout a stretch). Avoid unnecessary changes in relationship or context between speakers — constant role-switching (traveler→vlogger→tourist; friend→interviewer→staff) feels disjointed.

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

- No purely invented content: Type B dialogue should grow from the speaker's own words; Type A stays verbatim (light trimming only).
- **Prefer reusable, real-world speaking patterns.** When multiple valid conversions are possible, pick the one that produces the most reusable real-world language — travel interactions, opinions, recommendations, explanations, planning, problem solving, social conversation — over transcript-specific wording.
- **Avoid generic AI-style filler.** Don't lean on "That's interesting.", "Tell me more.", "How did that feel?", "Wow, that's amazing." Use specific, context-aware reactions tied to what was actually said.
- Aim for intermediate-to-advanced vocabulary and natural spoken rhythm — avoid oversimplifying.
- Keep scenes short enough to say aloud comfortably (4–10 turns max) — but DO use multiple turns; a one-exchange scene is too thin.
- Ready-to-save Markdown. No preamble.

## What NOT to include

- **No fabricated topics, opinions, or facts** the speaker never expressed — every scene traces back to real source material.
- **No fake interview questions** invented only to force narration into dialogue — if a real person wouldn't ask it, reshape the content into a natural situation instead.
- **No thin coverage** — don't ship two or three sample scenes for a long transcript, and don't reduce a multi-turn exchange to a single Q&A.
- **No filler scenes** — don't turn greetings, transitions, repetitive walking/observation padding, or duplicated information into scenes just to cover the whole transcript.
- No oversimplified, textbook-stiff dialogue — keep the natural spoken register.
- No generic AI conversational filler ("Wow, that's amazing", "Tell me more") — keep reactions specific.
- No preamble, no commentary, no code-fence wrapper around the document.
- No grammar notes, vocabulary lists, or speaking tips — this is a practice script, not a lesson.
