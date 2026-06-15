# Transcript mode agents

Claude Code subagents that process a transcript into a specific kind of output. Share a transcript
(or point at `sub.txt`) and invoke the agent — e.g. `@"travel-guide (agent)"`.

These agents are also the **design home** for future `smart_transcript.py` modes: once a prompt is
proven here, port it into `smart_transcript.py --mode <name>` (CLI + batch). Refactor to a
`MODES = {...}` registry dict *before* adding many Python modes to avoid touching 5 places per mode.

## Built (this batch)

| Agent | What it produces |
| --- | --- |
| `travel-guide` | Practical travel briefing — two tiers: facts from the video + clearly-labeled added context (geographic anchors, Google Maps links). |
| `roleplay` | Two-sided **You / Partner** script from real dialogue, to practice speaking one side. |
| `summary` | One tight third-person spoken summary of the whole video. |
| `debate-prep` | For / Against / Nuanced argument positions + Steelman block + Key Vocabulary — for practicing spoken argumentation on news, opinion, or tech topics. |

## TODO — future modes (not built yet)

| Mode | Idea | Verbatim or generated |
| --- | --- | --- |
| `qa` | Generated open questions about the content for unscripted self-talk practice. | Generated |
| `vocab-in-context` | Reusable expressions/idioms kept **with** the sentence they appeared in. | Mostly verbatim |
| `shadowing` | Transcript re-chunked into speaker-natural pieces with pause markers for repeat-aloud. | Verbatim (could run offline) |

## Notes

- These overlap conceptually with `smart_transcript.py` (`organize`, `speaking`) and the
  `passive-to-active-english` skill. They are intentionally separate for now; porting is future work
  (accepted duplication).
- Each agent omits the `tools:` field, so it inherits all tools (travel-guide needs web search/fetch
  for Maps links and place verification).
