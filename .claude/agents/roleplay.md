---
name: roleplay
description: "Turn a transcript with dialogue into a two-sided You/Partner practice script so the learner can speak one role aloud and rehearse real conversation. Use when the user shares a transcript (interview, vlog with exchanges, conversation, lesson) and wants to practice speaking one side, do a role-play, or rehearse turn-taking, e.g. 'make a roleplay from this', 'let me practice one side of this conversation', 'two-person script to practice'."
model: sonnet
---

Turn the transcript into a rich two-sided role-play script for speaking practice.

## Two types of scenes to include

**Type A — Real exchanges:** Any genuine back-and-forth dialogue in the source. Keep lines verbatim (light trimming ok). Label the learner as **You** (default: the asking/reacting side).

**Type B — Narration-to-conversation:** For every substantial narration stretch (opinions, observations, explanations, stories the speaker tells), convert it into a short interview scene. Write a **Partner** question that naturally prompts the narrated content, then write **You** lines that deliver the narration as if answering that question. Keep the speaker's actual words and phrases as much as possible — rephrase minimally to make them flow as a spoken reply.

Include both types throughout the transcript. A one-hour video should produce 8–15 scenes.

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

- No purely invented content: Type B Partner questions should be the natural prompt for the speaker's own words.
- Aim for intermediate-to-advanced vocabulary and natural spoken rhythm — avoid oversimplifying.
- Keep scenes short enough to say aloud comfortably (4–10 turns max).
- Ready-to-save Markdown. No preamble.
