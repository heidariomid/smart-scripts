# Transcript Agents — Web UI

A small local web UI over the transcript agents in `.claude/agents/`. Drop or pick a transcript
file (`.txt` / `.srt` / `.md` / `.vtt`), choose an agent and a model, and run. The output (and a
copy of the input) is **saved to your Desktop** and shown in the page to download.

## Run

```bash
python3 webui/server.py
```

Then open the printed URL (default <http://127.0.0.1:8765>).

**Note:** after editing `server.py`, stop and restart the server — a running process keeps the old
code in memory: `lsof -ti tcp:8765 | xargs kill -9` then re-run.

## How it works

- **Upload-based.** The file's bytes are sent to the server, processed, and the result is written
  to `~/Desktop` (e.g. `sub.vtt` → `~/Desktop/sub-summary.md`). No filesystem paths or permissions
  involved.
- **`.vtt` / `.srt`** files have their WebVTT/SRT headers, cue numbers, timestamps, and inline
  tags stripped before the text reaches the model.
- **Model selector** offers the three current Claude tiers (Opus / Sonnet / Haiku), passed to
  `claude --model`. The aliases always resolve to the latest model in each tier.
- The model runs with **no tools** (`--tools ""` + denied Write/Edit/Bash), so it can only return
  text — it never writes files itself or triggers permission prompts. The server does all file
  writing.

## Notes

- **Zero dependencies** — pure Python standard library. Requires the `claude` CLI on PATH and
  logged in (same requirement as `smart_transcript.py`'s LLM engine).
- Agents are discovered automatically from `.claude/agents/*.md`; prompts are read verbatim from
  those files, so nothing is duplicated.
- Output suffixes: `-organized.md` (`-formatted.md` for `.md` input), `-speaking.md`,
  `-summary.md`, `-roleplay.md`, `-travel-guide.md`, `-infographic.html`.
- `infographic` and `travel-guide` are the slowest modes; the server uses a 480s LLM timeout.
