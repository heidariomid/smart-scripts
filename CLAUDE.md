# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.

## What this is

A toolkit that turns a raw transcript or text file into a structured artifact (Markdown, or HTML for
the infographics). There are **two surfaces**, and they share one prompt source:

- **Claude Code agents** — `.claude/agents/*.md`. Share a transcript here and ask for one of the
  outputs below; the matching subagent runs and writes the file. (See the routing table.)
- **Web UI** — `webui/server.py`. A local browser app: drop a file, pick an agent + model, click
  Run. Output saves to `~/Desktop`.

**Single source of truth:** every agent is one file, `.claude/agents/<name>.md`. The web UI reads
that file's body as the LLM prompt; Claude Code uses the same file as a subagent definition. There
is no separate skills layer and no CLI — don't reintroduce prompt duplication.

> The web UI exposes **9** of the 10 transcript→artifact agents — `debate-prep` is missing from
> `MODE_SUFFIX` in [webui/server.py](webui/server.py). Add it there if you want it in the UI.

> **Non-UI meta-agent:** [.claude/agents/agent-reviewer.md](.claude/agents/agent-reviewer.md) is a
> deliberate exception to the "every agent is a transcript→artifact transformer" rule. Its input is
> *another agent's prompt*, and it reviews that prompt for product quality. It is **intentionally not
> in `MODE_SUFFIX`** (nothing to drop a file into) — invoke it only inside Claude Code, e.g. "review
> the travel-guide agent." It writes a structured report to `reviews/<agent>-review.md` (e.g.
> `reviews/speaking-review.md`). Don't wire it into the web UI or the routing table below.

## Running the web UI

```bash
python3 webui/server.py   # http://127.0.0.1:8765 ; outputs save to ~/Desktop
# or: make dev  (kills any process on :8765 first, then starts)
```

After editing `server.py`, **restart it** — Python caches the old code in memory:
`lsof -ti tcp:8765 | xargs kill -9 && python3 webui/server.py`.

## Editing agent prompts — the sanitizer rule

The web UI strips "write the file yourself" instructions from each prompt (`sanitize_prompt()` in
[webui/server.py](webui/server.py)) because the server captures stdout and writes the file itself.
So when you edit an agent:

- Keep any file-writing instruction on its **own line** so it strips cleanly.
- Never let a normal content line accidentally match `_WRITE_LINE_RE` (patterns: "write it / the
  file / the html / directly", "with the write tool", "then confirm the path").

Self-check after editing an agent (`AGENT_NAME` = the file stem):

```bash
python3 -c "import sys; sys.path.insert(0,'webui'); import server; \
 p=server.sanitize_prompt(server.load_prompt('AGENT_NAME')); \
 assert 'with the Write tool' not in p and 'then confirm the path' not in p; \
 print('AGENT_NAME sanitizes clean')"
```

## Other notes

- The web UI **ignores** each agent's `model:` frontmatter — the UI dropdown's `--model` is what
  runs. Frontmatter `model:` only applies inside Claude Code.
- The model runs with **no write tools** (`--tools ""` + denied Write/Edit/Bash); it returns text on
  stdout and the server does all file writing. The one exception is read-only web access for agents
  that need it — see `MODE_TOOLS` (currently just `travel-guide` → `WebSearch,WebFetch`).

## Adding a new agent

1. Create `.claude/agents/<name>.md` (frontmatter `name:` must equal the filename stem; `description:`
   is shown in the UI dropdown and drives Claude Code routing).
2. To expose it in the web UI, add one entry to `MODE_SUFFIX` in [webui/server.py](webui/server.py):
   `"<name>": "-<suffix>.md"` (or `.html`). The server auto-discovers the prompt file; no other
   server change is needed.

## Agent routing — automatic dispatch

When the user references a transcript or text file and asks for one of these, **invoke the matching
agent automatically** — do not ask which one. Pass the full file content in the prompt; the agent
writes its own output file using the suffix shown.

| Trigger | Agent | Output suffix |
| --- | --- | --- |
| "summarize", "what was it about", "give me a recap", "short summary" | `summary` | `-summary.md` |
| "speaking practice", "lines to practice", "speaking mode", "rehearsal" | `speaking` | `-speaking.md` |
| "organize", "format", "clean up", "make this Markdown", "reformat" | `organize` | `-organized.md` |
| "roleplay", "practice one side of this conversation", "two-person script", "rehearse turn-taking" | `roleplay` | `-roleplay.md` |
| "travel guide", "how do they get around", "what do I need to know about this place" | `travel-guide` | `-travel-guide.md` |
| "infographic", "visualize", "HTML visual", "make a graphic", "visual summary" (offline, CSS-only, no JS) | `infographic` | `-infographic.html` |
| "immersive", "interactive experience", "3D", "scrollytelling", "cinematic", "premium visual", "data-driven storytelling", "NYT/Apple/Nat Geo style", "make this extraordinary" | `infographic-advanced` | `-infographic-advanced.html` |
| "document this course", "course notes", "follow-along guide", "course cheatsheet", "reference doc from this tutorial" | `course-docs` | `-course-docs.md` |
| "help me practice English", "give me sentences to repeat", "what can I say from this video", "tense practice" | `passive-to-active-english` | `-speaking-practice.md` |
| "debate prep", "argue this", "for and against", "practice arguing", "defend a position", "steelman" | `debate-prep` | `-debate-prep.md` |

`passive-to-active-english` does tense-focus + phrase practice (Recaps → a Tense Focus Practice block
that re-tells each scene *naturally* in purpose-labeled time frames → Phrases + Fill-in-the-Blank),
**not** verbatim line extraction — use `speaking` for that.

`infographic` vs `infographic-advanced`: both produce one HTML file, but `infographic` is **offline,
CSS-only, no JavaScript, zero dependencies** (works fully offline / print-friendly); `infographic-advanced`
is the **immersive, library-powered** version (Three.js + D3 + GSAP + MapLibre/Deck.gl) and **needs
internet on first open** for CDN libraries + map tiles. Pick `infographic-advanced` for "immersive /
interactive / 3D / cinematic / premium"; pick `infographic` when offline-self-contained matters.

## Dependencies

| Dependency | Required for |
| --- | --- |
| Python 3.10+ | Running the web UI |
| `claude` CLI (logged in) | The LLM engine behind the web UI. Install: `npm install -g @anthropic-ai/claude-code` |
