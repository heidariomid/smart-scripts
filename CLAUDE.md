# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`smart_transcript.py` — a single-file, multi-mode CLI that turns raw text or transcripts into Markdown. Selected with `--mode` (default `organize`):

- **`organize`** — faithful, word-preserving Markdown reformat. Has an offline regex fallback when the `claude` CLI is unavailable.
- **`speaking`** — curates verbatim high-value spoken lines per scene, each followed by a generated 3rd-person **Recap** paragraph. **LLM-required** — no offline fallback; errors cleanly if `claude` is missing.

## Running the script

```bash
# Single file, LLM engine (default)
python3 smart_transcript.py --input notes.txt --output out.md

# Offline only (organize mode only)
python3 smart_transcript.py --input notes.txt --output out.md --no-llm

# Speaking practice (needs claude CLI, ~90s)
python3 smart_transcript.py --mode speaking --input sub.txt --output speaking.md

# Batch (always add --source-glob "*.txt" in speaking mode to avoid re-processing outputs)
python3 smart_transcript.py --mode speaking --all . --source-glob "*.txt" --dry-run
python3 smart_transcript.py --mode speaking --all . --source-glob "*.txt" --force
```

## Validation / smoke tests

```bash
# 1. Syntax (both copies)
python3 -c "import ast; ast.parse(open('smart_transcript.py').read()); ast.parse(open('$HOME/bin/smart_transcript.py').read()); print('OK')"

# 2. --no-llm guard errors cleanly, writes nothing
python3 ~/bin/smart_transcript.py --mode speaking -i sub.txt -o /tmp/x.md --no-llm
# expect: exit=1, /tmp/x.md not created

# 3. --all path + glob resolves correctly (no writes)
python3 ~/bin/smart_transcript.py --mode speaking --all . --source-glob "*.txt" --dry-run

# 4. End-to-end with Recap check (~90-110s, needs claude CLI)
python3 ~/bin/smart_transcript.py --mode speaking -i sub.txt -o /tmp/recap_test.md --llm-timeout 480
grep -c "^### Recap" /tmp/recap_test.md   # should equal the scene count
```

## Architecture

The script has two engines and two modes:

**Engines** (tried in order, unless `--no-llm`):
1. `organize_with_llm()` — shells out to `claude -p <PROMPT> --output-format text`, pipes `<text>…</text>` on stdin.
2. `organize_passthrough()` — pure-stdlib offline formatter: detects unstructured prose via `_looks_unstructured()`, calls `restructure_prose()` to split into paragraphs + promote headings, then runs normalisation passes (bullets, blank lines, bare command backticks). **Word-preserving** — only whitespace and `#` markers are added.

**Mode wiring** — a new mode requires touching **5 places** in the script (documented in `SMART_TRANSCRIPT-NOTES.md §4`):
1. A `*_PROMPT` constant at the top
2. Prompt selection in `process_file()`
3. LLM-required guard in `process_file()`
4. `--mode choices` in `argparse`
5. Output suffix defaults

Before adding many modes, refactor to the `MODES = {...}` registry described in `SMART_TRANSCRIPT-NOTES.md §8`.

## Critical sync requirements

**Two file copies:** The canonical script is `~/bin/smart_transcript.py`. The project-folder copy can drift. After any edit, sync: `cp ~/bin/smart_transcript.py ./smart_transcript.py` (or reverse).

**Spec duplication:** `SPEAKING_PROMPT` in the script and the `passive-to-active-english` skill (`SKILL.md`) both define the speaking mode spec. **Both must be edited together** — nothing enforces this.

## Common pitfalls

- `--all` batch in speaking mode with the default `--source-glob "*.txt,*.md"` will re-ingest its own `*-speaking.md` outputs. Always add `--source-glob "*.txt"`.
- `--mode speaking --no-llm` is intentionally an error — do not add an offline fallback; regex cannot judge speaking value.
- `argparse` "file modified since read" errors when iterating fast — re-Read before each Edit.

## Agent routing — automatic dispatch

Eight dedicated subagents live in `.claude/agents/`. When the user references a transcript or text file and asks for one of the modes below, **always invoke the matching agent automatically** — do not ask the user to specify it.

| Trigger | Agent | When to fire |
| --- | --- | --- |
| "summarize", "what was it about", "give me a recap", "short summary" | `summary` | User wants the overall gist of a transcript |
| "speaking practice", "lines to practice", "speaking mode", "practice English", "rehearsal" | `speaking` | User wants verbatim spoken lines + Recap paragraphs |
| "organize", "format", "clean up", "make this Markdown", "reformat" | `organize` | User wants faithful Markdown reformat of raw text |
| "infographic", "visualize", "HTML visual", "make a graphic", "visual summary" | `infographic` | User wants a self-contained HTML infographic from the content |
| "roleplay", "practice one side of this conversation", "two-person script", "rehearse turn-taking" | `roleplay` | User wants a two-sided dialogue practice script |
| "travel guide", "how do they get around", "what do I need to know about this place" | `travel-guide` | User wants practical travel logistics from a vlog transcript |
| "document this course", "course notes", "follow-along guide", "course cheatsheet", "reference doc from this tutorial" | `course-docs` | User wants engineering-quality reference docs from a course transcript |
| "help me practice English", "turn this into speaking practice", "give me sentences to repeat", "what can I say from this video", "tense practice", "practice tenses with this" | `passive-to-active-english` | User wants tense drilling + phrase practice: scene Recaps (3rd-person) → same events in 4 first-person tenses → Phrases Worth Reviewing + Fill-in-the-Blank with 3 variations each. No verbatim line extraction (use `speaking` for that). |

Pass the full file content to the agent in the prompt. The agent writes its own output file — derive the output path from the input filename using the suffix conventions: `-summary.md`, `-speaking.md`, `-organized.md`, `-roleplay.md`, `-travel-guide.md`, `-infographic.html`, `-course-docs.md`, `-speaking-practice.md`.

## Web UI

`webui/server.py` — a local web UI over all eight agents. Drop or pick a transcript (`.txt` / `.srt` / `.md` / `.vtt`), choose an agent and a model, and run. Output is saved to `~/Desktop`.

```bash
python3 webui/server.py   # then open http://127.0.0.1:8765
```

After editing `server.py`, restart the server — Python keeps the old code in memory:
```bash
lsof -ti tcp:8765 | xargs kill -9 && python3 webui/server.py
```

**Model selection:** The `model:` field in each agent's frontmatter (e.g. `model: sonnet` in `infographic.md`) is **only used when the agent is invoked inside Claude Code**. The web UI ignores it entirely — the model dropdown passes `--model <alias>` directly to `claude -p`, so whatever you select in the UI is what runs. The frontmatter default has no effect on web UI runs.

**How it works:**
- Prompts are loaded verbatim from `.claude/agents/<mode>.md` — no prompt duplication.
- The server strips "write the file yourself" instructions from prompts and runs with `--tools ""` + `--disallowedTools Write Edit Bash`, so the model returns text on stdout; the server saves it. No permission prompts.
- `.vtt` / `.srt` timestamps and cue numbers are stripped before the text reaches the model.
- Accepts `.txt`, `.srt`, `.md`, `.vtt`. Outputs use the same suffix conventions as `smart_transcript.py`.

## Dependencies

| Dependency | Required for |
| --- | --- |
| Python 3.10+ | Everything |
| `claude` CLI (logged in) | LLM engine (default). Install: `npm install -g @anthropic-ai/claude-code` |
| `yt-dlp` | Downloading transcripts (`brew install yt-dlp`) |
