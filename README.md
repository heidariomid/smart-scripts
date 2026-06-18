# smart-scripts

Turn a transcript or text file into a useful artifact — a summary, speaking practice, a roleplay
script, a travel briefing, an infographic, and more — with Claude doing the work.

There are **two ways** to use it. Both run the exact same prompts (`.claude/agents/*.md`).

## 1. In Claude Code

Open this project in Claude Code, share a transcript (paste it, drop a file, or point at one), and
ask for what you want in plain language:

- *"summarize this video"* → a short spoken recap
- *"make a roleplay from this"* → a two-sided You/Partner script to rehearse
- *"help me practice English with this"* → tense + phrase practice
- *"make an infographic from this"* → a self-contained HTML visual
- *"what do I need to know about this place"* → a practical travel briefing

The matching agent runs automatically and writes the output file. See the full trigger list in
[CLAUDE.md](CLAUDE.md).

## 2. In the web UI

```bash
python3 webui/server.py     # then open http://127.0.0.1:8765
# or: make dev
```

Drop or pick a transcript (`.txt` / `.srt` / `.md` / `.vtt`), choose an agent and a model, click
Run. The output (and a copy of the input) is saved to your **Desktop** and shown in the page to
download. `.srt` / `.vtt` timestamps are stripped automatically before the text reaches the model.

## The agents

| Agent | What it produces |
| --- | --- |
| `summary` | One tight third-person spoken summary of the whole transcript |
| `organize` | Faithful Markdown reformat — preserves every word |
| `speaking` | Verbatim high-value spoken lines per scene + Recap paragraphs to read aloud |
| `passive-to-active-english` | Scene Recaps + a Tense Focus Practice block (natural re-tellings in purpose-labeled time frames) + Phrases + Fill-in-the-Blank |
| `roleplay` | Two-sided You/Partner dialogue script to practice one side |
| `debate-prep` | For / Against / Nuanced positions + Steelman + key vocabulary |
| `travel-guide` | Practical travel briefing — logistics, costs, bookings, map links (uses web search) |
| `course-docs` | Engineering-quality reference doc from a course/tutorial transcript |
| `infographic` | Self-contained, offline, CSS-only HTML infographic (no JS, print-friendly) |
| `infographic-advanced` | Immersive, library-powered interactive HTML (Three.js + D3 + GSAP + maps; needs internet on first open) |

> The web UI currently lists 9 of these — `debate-prep` isn't wired into the UI yet. It works as a
> Claude Code agent.

## How it fits together

- **One prompt per agent**, in `.claude/agents/<name>.md`. Both surfaces read it — no duplication.
- The web UI ([webui/server.py](webui/server.py)) is pure Python standard library. It shells out to
  the `claude` CLI with file-writing tools disabled, captures the text output, and writes the file
  itself.
- Working on the project? See [CLAUDE.md](CLAUDE.md) for the rules (the prompt-sanitizer check, how
  to add an agent, the server-restart gotcha).

## Requirements

- Python 3.10+
- The `claude` CLI, logged in: `npm install -g @anthropic-ai/claude-code`
