# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.

> **Full picture:** [PROJECT-OVERVIEW.md](PROJECT-OVERVIEW.md) — architecture, web-UI internals, the
> agent depth-standard, how to add a mode/agent, validation, and the cleanup backlog. Read it before
> any non-trivial change. This file is the short list of must-follow rules.

## What this is

A toolkit that turns raw text / transcripts into Markdown (and one HTML) artifacts, three ways:

- **`smart_transcript.py`** — single-file CLI, two runnable modes: `organize` (faithful word-preserving reformat, has an offline fallback) and `speaking` (verbatim spoken lines + generated **Recap** paragraphs; **LLM-required**, no fallback).
- **`.claude/agents/*.md`** — ten Claude Code subagents (see routing table below).
- **`webui/server.py`** — local browser UI that runs the agent prompts via the `claude` CLI.

> Three surfaces have **different counts**: CLI = **2 modes**; agents = **10**; web UI = **9** (debate-prep is still missing from `MODE_SUFFIX` — see PROJECT-OVERVIEW.md). Don't conflate them.

## Running

```bash
# CLI (LLM engine, default)
python3 smart_transcript.py --input notes.txt --output out.md
python3 smart_transcript.py --input notes.txt --output out.md --no-llm   # offline, organize only
python3 smart_transcript.py --mode speaking --input sub.txt --output speaking.md   # ~90s, needs claude CLI

# Batch — ALWAYS add --source-glob "*.txt" in speaking mode (see pitfalls)
python3 smart_transcript.py --mode speaking --all . --source-glob "*.txt" --dry-run

# Web UI
python3 webui/server.py   # http://127.0.0.1:8765 ; outputs save to ~/Desktop
```

Smoke tests and the full validation block are in [PROJECT-OVERVIEW.md](PROJECT-OVERVIEW.md).

## Critical sync requirements

- **Two script copies.** Canonical: `~/bin/smart_transcript.py`. The repo copy can drift. After any edit, sync both: `cp ~/bin/smart_transcript.py ./smart_transcript.py` (or reverse). The `~/bin` copy is outside git — commits don't carry it.
- **Spec duplication.** `SPEAKING_PROMPT` in the script and `.claude/agents/speaking.md` both define the speaking spec. **Edit both together** — nothing enforces this.
- After editing `webui/server.py`, **restart it** (Python caches the old code): `lsof -ti tcp:8765 | xargs kill -9 && python3 webui/server.py`.
- After editing any agent prompt, run the **sanitizer self-check** (in PROJECT-OVERVIEW.md): keep any file-writing instruction on its own line and never let a content line match `_WRITE_LINE_RE`.

## Common pitfalls

- `--all` batch in speaking mode with the default `--source-glob "*.txt,*.md"` re-ingests its own `*-speaking.md` outputs. Always pass `--source-glob "*.txt"`.
- `--mode speaking --no-llm` is intentionally an error — do **not** add an offline fallback; regex can't judge speaking value.
- `argparse` "file modified since read" errors when iterating fast — re-Read before each Edit.
- The web UI **ignores** each agent's `model:` frontmatter — the UI dropdown's `--model` is what runs. Frontmatter `model:` only applies inside Claude Code.

## Agent routing — automatic dispatch

Ten subagents live in `.claude/agents/`. When the user references a transcript or text file and asks for one of these, **always invoke the matching agent automatically** — do not ask which one. Pass the full file content in the prompt; the agent writes its own output file using the suffix shown.

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

`passive-to-active-english` does tense drilling + phrase practice (Recaps → 4 first-person tenses → Phrases + Fill-in-the-Blank), **not** verbatim line extraction — use `speaking` for that.

`infographic` vs `infographic-advanced`: both produce one HTML file, but `infographic` is **offline, CSS-only, no JavaScript, zero dependencies** (works fully offline / print-friendly); `infographic-advanced` is the **immersive, library-powered** version (Three.js + D3 + GSAP + MapLibre/Deck.gl) and **needs internet on first open** for CDN libraries + map tiles. Pick `infographic-advanced` for "immersive / interactive / 3D / cinematic / premium"; pick `infographic` when offline-self-contained matters.

## Dependencies

| Dependency | Required for |
| --- | --- |
| Python 3.10+ | Everything |
| `claude` CLI (logged in) | LLM engine (default) + web UI. Install: `npm install -g @anthropic-ai/claude-code` |
