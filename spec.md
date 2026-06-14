# smart-scripts — Project Spec

## What this is

A growing toolkit that turns raw transcripts and text into structured, useful output using Claude as the LLM engine. Two surfaces:

1. **Web UI** (`webui/`) — a local browser app: drop a file, pick an agent, click Run. Output is saved to `~/Desktop`.
2. **Claude Code agents** (`.claude/agents/`) — the same agents invoked directly inside Claude Code by mentioning a transcript.

Both surfaces share the same prompt source: `.claude/agents/<name>.md`. The web UI reads the file body as the LLM prompt; Claude Code uses it as a subagent definition. No prompt duplication.

---

## How to add a new agent

1. Create `.claude/agents/<name>.md` with this structure:

```
---
name: <name>          # must match filename stem
description: "..."    # shown in UI dropdown and used for Claude Code routing
model: sonnet
---

<your full prompt here>
```

2. Add one entry to `webui/server.py` → `MODE_SUFFIX` dict:

```python
"<name>": "-<output-suffix>.md",   # or .html for HTML outputs
```

That's it. The server auto-discovers agents from `agents/*.md` — no other server changes needed.

**Output filename stripping:** `output_name_for()` in `server.py` strips known mode suffixes from the input stem before appending the new one, so re-processing a prior output (e.g. `foo-organized.md`) doesn't accumulate prefixes. When you add a new agent, add its suffix to the `known_suffixes` list in that function too.

---

## How to add a new skill (for Claude Code only)

Skills live in `.claude/skills/<name>/SKILL.md`. They are invoked inside Claude Code by trigger phrases, not from the web UI. If you want a skill available in the web UI as well, create a matching agent file whose body is the skill's prompt (with any file-writing delivery instructions replaced — the server captures stdout and writes the file itself).

---

## Current agents

| Agent | Output suffix | Description |
|-------|--------------|-------------|
| `organize` | `-organized.md` | Faithful Markdown reformat — preserves every word |
| `speaking` | `-speaking.md` | Verbatim spoken lines per scene + Recap paragraphs |
| `summary` | `-summary.md` | One tight third-person spoken summary |
| `roleplay` | `-roleplay.md` | Two-sided dialogue practice script |
| `travel-guide` | `-travel-guide.md` | Practical travel briefing with logistics and costs |
| `infographic` | `-infographic.html` | Self-contained HTML infographic with embedded CSS |
| `course-docs` | `-course-docs.md` | Engineering-quality reference doc from a course transcript |
| `passive-to-active-english` | `-speaking-practice.md` | Tense drilling + phrase practice: scene Recaps in 3rd-person, then same events in 4 first-person tenses (past/present/future/present perfect), plus Phrases Worth Reviewing and a Fill-in-the-Blank section with 3 spoken variations per frame |

---

## Current skills (Claude Code only)

| Skill | Trigger phrases |
|-------|----------------|
| `course-docs` | "document this course", "create notes for this tutorial", "follow-along guide", "course cheatsheet" |
| `passive-to-active-english` | "help me practice English with this", "turn this into speaking practice", "give me sentences to repeat", "tense practice", "practice tenses with this" |

---

## Architecture

```
.claude/
  agents/         ← prompt files (auto-discovered by web UI + Claude Code)
  skills/         ← skill definitions (Claude Code only)

webui/
  server.py       ← stdlib HTTP server on localhost:8765
  index.html      ← single-page UI (no build step, no dependencies)

smart_transcript.py   ← CLI alternative (organize + speaking modes, --all batch)
```

**Web UI flow:**
1. `GET /api/config` → server scans `agents/*.md`, returns list of `{name, description}` for the dropdown
2. User uploads file, picks agent + model, clicks Run
3. `POST /api/process` → server reads agent body, strips file-write instructions, pipes transcript to `claude -p <prompt>`, captures stdout, writes to `~/Desktop/<stem><suffix>`

**LLM invocation:** `claude -p <prompt> --output-format text --tools "" --disallowedTools Write Edit NotebookEdit Bash`
Tools are disabled so the model returns text on stdout. The server writes the file. No permission prompts.

**Models offered:** opus, sonnet, haiku (passed as `--model <alias>` to the CLI).

**Supported input types:** `.txt`, `.srt`, `.md`, `.vtt` (`.srt` / `.vtt` timestamps are stripped before the text reaches the model).

---

## Running locally

```bash
python3 webui/server.py
# then open http://127.0.0.1:8765
```

Restart after editing `server.py` — Python keeps the old code in memory:

```bash
lsof -ti tcp:8765 | xargs kill -9 && python3 webui/server.py
```

---

## Key conventions

- **No prompt duplication.** Agent `.md` files are the single source of truth for prompts. The web UI and Claude Code both read from the same file.
- **Skills that need web UI access become agents.** Copy the skill body into an agent file; replace any delivery/file-write section with "Return the complete result as plain text."
- **Output suffix stripping** prevents compounding names when re-processing prior outputs. Always add new suffixes to `known_suffixes` in `output_name_for()`.
- **Model frontmatter is Claude Code only.** The web UI ignores the `model:` field — the dropdown selection is what's passed to the CLI.
