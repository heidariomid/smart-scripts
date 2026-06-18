# Transcript agents

Claude Code subagents that turn a transcript into a specific kind of output. Share a transcript and
invoke the agent — e.g. `@"travel-guide (agent)"` — or just ask in plain language and the right one
is dispatched automatically (routing table in [../../CLAUDE.md](../../CLAUDE.md)).

Each agent's `.md` file is the single source of truth for its prompt: the same file backs both
Claude Code and the web UI ([../../webui/server.py](../../webui/server.py)).

## Agents

| Agent | What it produces |
| --- | --- |
| `summary` | One tight third-person spoken summary of the whole transcript. |
| `organize` | Faithful Markdown reformat — preserves every word. |
| `speaking` | Verbatim high-value spoken lines per scene + Recap paragraphs to read aloud. |
| `passive-to-active-english` | Scene Recaps + a Tense Focus Practice block (natural re-tellings in purpose-labeled time frames) + Phrases Worth Reviewing + Fill-in-the-Blank. |
| `roleplay` | Two-sided **You / Partner** script from real dialogue, to practice speaking one side. |
| `debate-prep` | For / Against / Nuanced argument positions + Steelman block + Key Vocabulary. |
| `travel-guide` | Practical travel briefing — facts from the video + clearly-labeled added context (geographic anchors, Google Maps links). |
| `course-docs` | Engineering-quality reference doc from a course/tutorial transcript. |
| `infographic` | Self-contained, **offline / CSS-only / no-JS** HTML infographic — visual cards, stat callouts, timelines, color sections. The gold-standard depth prompt. |
| `infographic-advanced` | Immersive, **library-powered** interactive HTML (Three.js + D3 + GSAP + MapLibre/Deck.gl). **Needs internet on first open** for CDN libs + map tiles. |

## Ideas — not built yet

| Idea | What it would do | Verbatim or generated |
| --- | --- | --- |
| `qa` | Generated open questions about the content for unscripted self-talk practice. | Generated |
| `vocab-in-context` | Reusable expressions/idioms kept **with** the sentence they appeared in. | Mostly verbatim |
| `shadowing` | Transcript re-chunked into speaker-natural pieces with pause markers for repeat-aloud. | Verbatim |

## Notes

- Most agents omit the `tools:` field and inherit all tools. `travel-guide` needs web search/fetch
  for Maps links and place verification. In the web UI, write tools are disabled regardless — see
  `MODE_TOOLS` in the server.
- `debate-prep` is the one agent not yet wired into the web UI (missing from `MODE_SUFFIX`).
