# Project Overview — smart-scripts

The full picture of this project for anyone (human or agent) doing development work here.
For the short, must-follow operating rules, see [CLAUDE.md](CLAUDE.md) — this document is the
deep reference behind those rules.

---

## What this project is

A small toolkit for turning **raw text and video/podcast transcripts into useful Markdown (and one HTML) artifacts**, exposed three ways:

1. **`smart_transcript.py`** — a single-file CLI with two runnable modes (`organize`, `speaking`).
2. **`.claude/agents/*.md`** — nine specialized Claude Code subagents, auto-dispatched by intent, each producing a different artifact from the same kind of input.
3. **`webui/server.py`** — a local browser UI that runs the agent prompts through the `claude` CLI and saves the output to your Desktop.

All three share the same philosophy: faithful, maximum-depth transformation of the source — never a thin summary (except the deliberately-tight `summary` agent).

### Three surfaces, three different "mode" counts

This trips people up, so be precise:

| Surface | Count | Members |
| --- | --- | --- |
| `smart_transcript.py` `--mode` | **2** | `organize`, `speaking` only |
| `.claude/agents/` (Claude Code) | **9** | summary, speaking, organize, roleplay, travel-guide, infographic, course-docs, passive-to-active-english, debate-prep |
| `webui` `MODE_SUFFIX` (browser) | **8** | all agents **except `debate-prep`** (see Known gaps) |

The CLI only knows two modes; the other seven artifacts exist **only** as Claude Code agents / web-UI modes, not as `--mode` choices.

---

## Repository layout

```
smart-scripts/
├── smart_transcript.py        # the CLI (canonical copy lives at ~/bin/smart_transcript.py)
├── CLAUDE.md                  # lean operating rules, auto-loaded every session
├── PROJECT-OVERVIEW.md        # this file — deep reference
├── .claude/
│   └── agents/                # 9 agent prompt files + README.md
│       ├── summary.md
│       ├── speaking.md
│       ├── organize.md
│       ├── roleplay.md
│       ├── travel-guide.md
│       ├── infographic.md     # the GOLD-STANDARD depth/structure prompt
│       ├── course-docs.md
│       ├── passive-to-active-english.md
│       └── debate-prep.md
└── webui/
    ├── server.py              # stdlib HTTP server; runs agent prompts via `claude -p`
    └── index.html             # single-page UI
```

---

## The CLI (`smart_transcript.py`)

### Two engines

Tried in order, unless `--no-llm`:

1. **`organize_with_llm()`** — shells out to `claude -p <PROMPT> --output-format text`, pipes the source as `<text>…</text>` on stdin. Used by both modes.
2. **`organize_passthrough()`** — pure-stdlib **offline** formatter. Detects unstructured prose via `_looks_unstructured()`, calls `restructure_prose()` to split paragraphs + promote headings, then runs normalisation passes (bullets, blank lines, bare command backticks). **Word-preserving** — only whitespace and `#` markers are added. Exists **only for `organize`**; `speaking` has no offline fallback.

### Two modes

- **`organize`** — faithful, word-preserving Markdown reformat. Falls back to `organize_passthrough()` if the `claude` CLI is unavailable.
- **`speaking`** — curates verbatim high-value spoken lines per scene, each followed by a generated third-person **Recap** paragraph. **LLM-required** — errors cleanly if `claude` is missing; `--mode speaking --no-llm` is intentionally an error (regex can't judge speaking value).

### Prompt constants

`LLM_PROMPT` (organize) and `SPEAKING_PROMPT` (speaking) live at the top of the script. `SPEAKING_PROMPT` is a **duplicate of `.claude/agents/speaking.md`** and must be kept in sync — see [CLAUDE.md](CLAUDE.md) → Critical sync requirements.

### Adding a new CLI mode — the 5 touch-points

A new `--mode` currently requires touching **5 places** in the script:

1. A `*_PROMPT` constant at the top
2. Prompt selection in `process_file()`
3. LLM-required guard in `process_file()`
4. `--mode choices` in `argparse`
5. Output suffix defaults

**Refactor note:** before adding many modes, collapse these into a single `MODES = {...}` registry dict so a new mode is one entry, not five edits. (Most "modes" today are agents/web-UI-only and never become CLI modes, which is why this refactor hasn't been forced yet.)

---

## The agents (`.claude/agents/`)

Nine subagents, each a Markdown file with YAML frontmatter (`name`, `description`, `model`) and a prompt body. They are auto-dispatched by Claude Code based on user intent (see the routing table in [CLAUDE.md](CLAUDE.md)).

| Agent | Output | Purpose |
| --- | --- | --- |
| `summary` | `-summary.md` | One tight third-person spoken recap of the whole transcript. **The one agent that stays short by design.** |
| `speaking` | `-speaking.md` | Verbatim high-value spoken lines per scene + a Recap paragraph each. Mirrored by `SPEAKING_PROMPT`. |
| `organize` | `-organized.md` | Faithful, word-preserving Markdown reformat. |
| `roleplay` | `-roleplay.md` | Two-sided You/Partner practice script. |
| `travel-guide` | `-travel-guide.md` | Practical travel briefing. **Three-tier structure** (From the video / Added context / Suggested itinerary) — diverges from the others by design. |
| `infographic` | `-infographic.html` | Self-contained HTML infographic. **The gold-standard prompt** the others are modeled on. |
| `course-docs` | `-course-docs.md` | Engineering-documentation-quality reference from a course transcript. |
| `passive-to-active-english` | `-speaking-practice.md` | Tense drilling + phrase practice (Recap → 4 first-person tenses → Phrases + Fill-in-the-Blank). No verbatim lines. |
| `debate-prep` | `-debate-prep.md` | For / Against / Nuanced argument positions + Steelman + vocabulary. |

### The "maximum depth" standard

Every agent prompt (except `summary`) follows a shared four-move structure adapted from `infographic.md`:

1. **Prime directive — maximum depth** — "not a summarizer"; extract/preserve as much substantive content as possible; no artificial length limits; "if it reads like a thin summary, it has failed."
2. **Step-1 extraction** with "capture everything present — these are minimums, not caps."
3. **A rich, multi-section output menu** with "lean toward more coverage, not less"; every section holds real source content.
4. **A "What NOT to include"** anti-thin-summary / anti-filler block.

Adaptations per agent:
- `summary` is the **inverse** — depth means quality/faithfulness/coverage *within a tight recap*, never length.
- `organize` — depth means **structural fidelity** (more headings/lists/tables), never new words (it's word-preserving).
- `speaking` / `roleplay` / `passive-to-active-english` — depth means **more real lines / scenes / frames**, never invented content (verbatim and no-invention rules are absolute).
- `debate-prep` — depth lives **inside each real claim**; the up-to-3-topics cap and no-manufactured-topics rule are absolute.

### Adding a new agent

1. Create `.claude/agents/<name>.md` with frontmatter + a prompt following the four-move standard.
2. Add a row to the **agent routing table** in [CLAUDE.md](CLAUDE.md).
3. Add the output suffix to **`MODE_SUFFIX` in `webui/server.py`** (and to `output_name_for`'s `known_suffixes` if re-processing should strip it). **Missing this is the `debate-prep` bug** — the agent works in Claude Code but fails in the web UI.
4. If (and only if) it should also be a CLI `--mode`, do the 5 touch-points above and mirror its prompt into a `*_PROMPT` constant.
5. Verify: restart the web UI, confirm `/api/config` lists it, and run it once.

---

## The web UI (`webui/server.py`)

A pure-stdlib (`http.server`) local server. Drop or pick a transcript (`.txt` / `.srt` / `.md` / `.vtt`), choose an agent and a model, and run. Input copy + output are saved to `~/Desktop`.

```bash
python3 webui/server.py        # serves http://127.0.0.1:8765
```

After editing `server.py`, **restart it** — Python keeps the old code in memory:

```bash
lsof -ti tcp:8765 | xargs kill -9 && python3 webui/server.py
```

### How it works internally

- **Agent discovery** — `list_modes()` reads `.claude/agents/*.md` directly (README excluded) and parses frontmatter. This is why `/api/config` can list an agent (`debate-prep`) that the run endpoint then rejects: discovery and `MODE_SUFFIX` are two separate lists.
- **Prompt loading** — `load_prompt(mode)` returns the agent file's body verbatim. **No prompt text is duplicated in the server** — the agent files stay the single source.
- **Prompt sanitizing** — `sanitize_prompt()` strips "write the file yourself" lines via `_WRITE_LINE_RE` (the server captures stdout and writes the file itself). It then appends any user "extra instructions" and a "return as plain text" footer.
  - **Consequence for agent authors:** keep any file-writing instruction on its **own line** so it strips cleanly, and never let a content line accidentally match `_WRITE_LINE_RE` (patterns include "write the file", "with the write tool", "then confirm the path", "write it/directly").
- **No-tools execution** — `run_claude()` runs `claude -p <prompt> --output-format text --tools "" --disallowedTools Write Edit NotebookEdit Bash`, so the model cannot write files (no permission prompts) and returns the result on stdout, which the server saves.
- **Transcript cleanup** — `clean_transcript()` strips WebVTT/SRT timestamps and cue numbers before the text reaches the model.
- **Model selection** — the UI dropdown passes `--model <alias>` directly to `claude -p`. The `model:` field in each agent's frontmatter is **only** used when the agent runs inside Claude Code; the web UI ignores it entirely.
- **Output naming** — `output_name_for()` derives the filename from input + `MODE_SUFFIX`, stripping previously-appended suffixes so re-processing doesn't stack them (`foo-speaking-roleplay`). `organize` on a `.md` input is special-cased.

### Sanitizer self-check (run after editing any agent prompt)

```bash
python3 -c "import sys; sys.path.insert(0,'webui'); import server; \
 p=server.sanitize_prompt(server.load_prompt('AGENT_NAME')); \
 assert 'with the Write tool' not in p and 'then confirm the path' not in p; \
 print('AGENT_NAME sanitizes clean')"
```

---

## Validation / smoke tests

```bash
# 1. Syntax (both script copies)
python3 -c "import ast; ast.parse(open('smart_transcript.py').read()); ast.parse(open('$HOME/bin/smart_transcript.py').read()); print('OK')"

# 2. --no-llm guard errors cleanly, writes nothing
python3 ~/bin/smart_transcript.py --mode speaking -i sub.txt -o /tmp/x.md --no-llm
# expect: exit=1, /tmp/x.md not created

# 3. --all path + glob resolves correctly (no writes)
python3 ~/bin/smart_transcript.py --mode speaking --all . --source-glob "*.txt" --dry-run

# 4. End-to-end with Recap check (~90-110s, needs claude CLI)
python3 ~/bin/smart_transcript.py --mode speaking -i sub.txt -o /tmp/recap_test.md --llm-timeout 480
grep -c "^### Recap" /tmp/recap_test.md   # should equal the scene count

# 5. Web UI lists every agent
lsof -ti tcp:8765 | xargs kill -9; python3 webui/server.py & sleep 2; \
 curl -s http://127.0.0.1:8765/api/config | python3 -m json.tool | head -40
```

---

## Dependencies

| Dependency | Required for |
| --- | --- |
| Python 3.10+ | Everything |
| `claude` CLI (logged in) | LLM engine (default) and the web UI. Install: `npm install -g @anthropic-ai/claude-code` |

---

## Known gaps / cleanup backlog

- **`debate-prep` missing from `webui/server.py` `MODE_SUFFIX`** — `/api/config` lists it (discovery reads agent files), but selecting it in the UI fails with `unknown mode: 'debate-prep'`. Fix: add `"debate-prep": "-debate-prep.md"` to `MODE_SUFFIX` (and to `output_name_for`'s `known_suffixes`). Works fine inside Claude Code.
- **Two script copies can drift** — `~/bin/smart_transcript.py` (canonical) vs the repo copy. The `~/bin` copy is outside git, so commits don't carry it; sync manually after edits.
- **`SPEAKING_PROMPT` ↔ `speaking.md` duplication** — nothing enforces the mirror; both must be edited together.
- **5-touch-point mode wiring** — candidate for a `MODES = {...}` registry refactor before more CLI modes are added.
