# How to Use — Course Docs Pipeline

Three small Python tools that turn raw text, subtitles, or a YouTube video into clean Markdown — from a faithful reformat all the way up to an engineering-quality reference doc.

> **Files**: `to_md.py`, `smart_transcript.py`, `generate_course_docs.py`, `course_pattern.yaml` **Design details**: see [PIPELINE-NOTES.md](PIPELINE-NOTES.md) **Quality target**: see [goodexample.md](goodexample.md)

---

## Quick Reference (`smart_transcript.py`)

Installed globally at `~/bin/smart_transcript.py` with two shell shortcuts (run from any folder; output lands next to the input):

```bash
speaking() { python3 ~/bin/smart_transcript.py --mode speaking "$@"; }   # speaking-practice doc
organize() { python3 ~/bin/smart_transcript.py "$@"; }                   # faithful reformat
```

| Goal | Command |
| --- | --- |
| One transcript → speaking practice | `speaking -i sub.txt -o speaking.md` |
| One file → faithful reformat | `organize -i notes.txt -o notes.md` |
| Whole folder → speaking (raw transcripts only) | `speaking --all . --source-glob "*.txt"` |
| A specific folder | `speaking --all /path/to/videos --source-glob "*.txt"` |
| Preview a batch first (writes nothing) | `speaking --all . --source-glob "*.txt" --dry-run` |
| Re-run and overwrite existing outputs | `… --force` |
| Pick the model / raise the timeout | `… --model claude-sonnet-4-6 --llm-timeout 480` |

**Mental model:** `speaking --all WHERE --source-glob WHICH` → make docs from *which* files, *where*.
- **`--all [folder]` = where** (omit for current folder; searches subfolders too).
- **`--source-glob "..."` = which files** (default `*.txt,*.md`; use `"*.txt"` so a batch doesn't re-process its own `*-speaking.md` output).

> ⚠️ `--mode speaking` needs the `claude` CLI — `--no-llm` is `organize`-only. Full details below.

---

## Which Tool Do I Want?

| If you want to… | Use | Changes your words? |
| --- | --- | --- |
| Clean up subtitles (`.vtt`/`.srt`) or merge several transcripts into one file | **`to_md.py`** | Light — normalizes whitespace, auto-wraps code/URLs |
| Reformat raw text into tidy Markdown **without altering a single word** | **`smart_transcript.py`** | No — content-preserving by design |
| Turn a transcript into spoken-English **speaking practice** material | **`smart_transcript.py --mode speaking`** | Selective — keeps high-value lines verbatim, drops the rest |
| Produce a full engineering reference doc (summary, architecture, ADRs, gotchas…) | **`generate_course_docs.py`** | Yes — it synthesizes and rewrites |

They also chain together — see [The Full Pipeline](#the-full-pipeline).

---

## 1. `to_md.py` — Ingest & Convert

Smart converter: `.vtt` / `.srt` / `.txt` / `.str` → structured Markdown. Strips subtitle timestamps, splits walls of text into paragraphs, detects headings, and builds a Table of Contents. Best for getting messy source material into a readable starting point.

```bash
# Single subtitle/text file → Markdown
python3 to_md.py notes.txt -o test.md          # NOTE: input is positional, not --input
python3 to_md.py "VideoTitle.en.vtt" -o notes.md --title "My Course Notes"

# Convert every .txt in a directory
python3 to_md.py /path/to/dir --ext txt

# Merge several videos/transcripts into ONE file (auto-enabled for multiple inputs)
python3 to_md.py video1.en.vtt video2.en.vtt -o notes.md
python3 to_md.py *.txt -o combined.md --merge

# Skip the table of contents
python3 to_md.py notes.txt -o test.md --no-toc
```

| Flag | Default | Meaning |
| --- | --- | --- |
| `inputs` (positional) | — | Files, directories, or glob patterns |
| `-o`, `--output` | `<input>.md` (or `merged.md` for multiple) | Output file |
| `--ext` | — | Filter by extension when an input is a directory (e.g. `txt`) |
| `--title` | derived from filename | H1 title for the document |
| `--no-toc` | off | Skip the Table of Contents |
| `--merge` | auto for >1 input | Merge all inputs into one file |

> **Heads up**: `to_md.py` lightly rewrites — it collapses whitespace and auto-wraps things like `func()`, `--flags`, `$vars`, and URLs. If you need byte-faithful text, use `smart_transcript.py` instead.

---

## 2. `smart_transcript.py` — Reformat & Speaking Practice

A multi-mode transcript toolkit, selected with `--mode`:

- **`organize`** (default) — reformats raw text into clean Markdown while **preserving every word**. It only inserts whitespace, paragraph breaks, and headings around the existing text — never rewrites, summarizes, or drops content. Same two-engine design as the doc generator.
- **`speaking`** — curates a transcript into spoken-English practice material (see [`--mode speaking`](#--mode-speaking--speaking-practice) below).

More modes may be added over time; the flags below apply across modes unless noted.

```bash
# Reformat a single file (LLM engine — best structure)
python3 smart_transcript.py --input notes.txt --output out.md

# Offline only (no claude call) — mechanical formatting + prose splitting
python3 smart_transcript.py --input notes.txt --output out.md --no-llm

# Batch: --all takes the folder directly (no --root needed)
python3 smart_transcript.py --all                      # the current folder
python3 smart_transcript.py --all /path/to/notes/      # a specific folder
python3 smart_transcript.py --all . --force            # this folder, overwrite
python3 smart_transcript.py --all . --dry-run          # preview, write nothing

# Pick the model the claude CLI uses
python3 smart_transcript.py --input notes.txt --output out.md --model claude-sonnet-4-6
```

### `--mode speaking` — Speaking Practice

The same script has a second mode that turns a transcript into **spoken-English practice material** instead of a faithful reformat. It curates only the lines with speaking value — reactions, opinions, decisions, natural exchanges — copied **verbatim**, grouped into scenes, followed by a flat "Phrases Worth Reviewing" list. Facts, prices, names, and filler are dropped.

Each scene also ends with a **Recap** block — a ready-to-read, third-person narration of the scene (2–4 complete sentences) written out for you to read aloud, e.g. *"So they get picked up by a private driver, and in the back there are bougie snacks waiting for them. When they arrive, they're swept off their feet…"*. It models the shift from the speaker's 1st-person/present voice to 3rd-person/past, so you practice narrating to someone else. That block is the one generated (non-verbatim) part, so it relies on the LLM (already required by this mode).

```bash
# Turn raw subtitles into a speaking-practice doc (→ sub-speaking.md by default)
python3 smart_transcript.py --mode speaking --input sub.txt --output speaking.md

# Batch every .txt transcript in a folder (outputs → *-speaking.md)
python3 smart_transcript.py --mode speaking --all . --source-glob "*.txt"
python3 smart_transcript.py --mode speaking --all /path/to/videos --source-glob "*.txt"
```

> **How `--all`, the path, and `--source-glob` work together.** They answer two different questions:
> - **`--all [folder]` = _where to look._** Give it a folder (or `.` for the current one); leave it blank for the current folder. It searches that folder **and its subfolders**.
> - **`--source-glob "..."` = _which files to pick._** A filename pattern. Default is `*.txt,*.md` (comma = multiple patterns). Restrict it with `--source-glob "*.txt"` so the batch only grabs raw transcripts.
>
> ⚠️ **Why almost always add `--source-glob "*.txt"` in speaking mode:** the default also matches `*.md`, which includes the `*-speaking.md` files this mode *produces* — so a plain `--all .` would try to re-process its own output. Limiting to `*.txt` (or `*.vtt` for subtitles) avoids that.

> **Requires the `claude` CLI.** Speaking extraction needs the LLM to judge speaking value — the offline formatter only reshapes whitespace and cannot curate. `--mode speaking --no-llm` errors out cleanly (writes nothing) rather than producing a useless file, and so does a missing/failed `claude` call (no offline fallback in this mode).

> **Output naming**: in speaking mode the default suffix becomes `-speaking` (single-file output defaults to `<stem>-speaking.md`), so it never clashes with `*-organized.md`.

### The Two Engines

| Engine | When used | What it does |
| --- | --- | --- |
| **LLM (default)** | `claude` CLI installed & logged in | Infers proper heading hierarchy, lists, and tables — still word-for-word faithful |
| **Offline (`--no-llm`)** | `--no-llm`, or automatic fallback | Splits run-on prose into paragraphs at transitional cues; promotes "I call it X" / "this trick called X" sentences into `## ` headings; normalizes bullets and spacing |

> **Fidelity guarantee (offline mode)**: the body word sequence is identical to the source — only blank lines and `#` heading markers are added. Headings are built from words already in the text.

| Flag | Default | Meaning |
| --- | --- | --- |
| `--mode` | `organize` | `organize`: faithful reformat. `speaking`: curate spoken-English practice lines (requires `claude` CLI) |
| `--input`, `-i` | `input.txt` | Source text file |
| `--output`, `-o` | `<stem>-organized.md` (`<stem>-speaking.md` in speaking mode) | Output path |
| `--no-llm` | off | Skip the `claude` CLI; offline formatter only (incompatible with `--mode speaking`) |
| `--model` | CLI default | Model id passed to `claude --model` |
| `--llm-timeout` | `300` | Seconds to wait for the `claude` CLI per file |
| `--all [DIR]` | off | Batch mode: find source files under DIR (recursively). DIR is optional — omit it for the current folder, or pass a path / `.` |
| `--files FILE ...` | — | Explicit list of input files |
| `--root` | current dir | Legacy search root for `--all`; only used when `--all` is given **without** a path. Prefer `--all DIR` |
| `--source-glob` | `*.txt,*.md` | Which filenames `--all` picks (comma-separated patterns). Use `"*.txt"` to skip generated `*.md` outputs |
| `--output-suffix` | `-organized` (`-speaking` in speaking mode) | Suffix appended to stem for `--all` output |
| `--force` | off | Overwrite existing outputs |
| `--dry-run` | off | List what would be processed; write nothing |

---

## 3. `generate_course_docs.py` — Engineering Reference Doc

The heavy lifter. Takes a transcript and **synthesizes** a structured reference document — executive summary, architecture overview, learning outcomes, ADRs, gotchas, quick reference. Unlike the other two, it rewrites spoken prose into crisp technical writing and infers structure the instructor only states verbally.

```bash
# Single file (defaults: --input merged.md → course-docs.md next to it)
python3 generate_course_docs.py
python3 generate_course_docs.py --input notes.md --output docs.md

# Offline / no LLM call
python3 generate_course_docs.py --input notes.md --output docs.md --no-llm

# Pick the model (see "Choosing a Model" below)
python3 generate_course_docs.py --input notes.md --output docs.md --model claude-sonnet-4-6

# Batch: every merged.md found under a root directory
python3 generate_course_docs.py --all --root /path/to/courses/
python3 generate_course_docs.py --all --force          # overwrite existing outputs
python3 generate_course_docs.py --all --dry-run        # preview what would run

# Explicit file list
python3 generate_course_docs.py --files week1/merged.md week2/merged.md

# Custom section/stack/filler config
python3 generate_course_docs.py --input notes.md --pattern my_pattern.yaml
```

### The Two Engines

| Engine | When used | Quality | Speed | Network |
| --- | --- | --- | --- | --- |
| **LLM (default)** | `claude` CLI installed & logged in | goodexample.md level — synthesized prose, concept maps, worked-example tables | ~60s per file | Yes (via your Claude Code login; no API key needed) |
| **Regex (offline)** | `--no-llm`, or automatic fallback when `claude` is missing/fails/times out | ~50–80% — correct structure, extracted sentences, needs polish | <1s | None — pure stdlib |

The command **never fails because the LLM is unavailable** — it prints a warning and falls back to the regex engine.

> **Why two engines?** Regex can only _extract_ sentences; it cannot synthesize an executive summary or rewrite spoken filler into prose (PIPELINE-NOTES.md §7). The LLM engine is what reaches goodexample.md quality.

| Flag | Default | Meaning |
| --- | --- | --- |
| `--input`, `-i` | `merged.md` | Source transcript file |
| `--output`, `-o` | `course-docs.md` next to input | Output doc path |
| `--no-llm` | off | Skip the `claude` CLI; use the offline regex engine only |
| `--model` | CLI default | Model id passed to `claude --model` |
| `--llm-timeout` | `600` | Seconds to wait for the `claude` CLI per file before falling back |
| `--all` | off | Auto-discover all `--source-name` files under `--root` |
| `--files FILE ...` | — | Explicit list of transcript files |
| `--root` | script's grandparent dir | Search root for `--all` |
| `--source-name` | `merged.md` | Filename to discover in `--all` mode |
| `--output-name` | `course-docs.md` | Output filename in `--all` mode |
| `--force` | off | Overwrite existing outputs in `--all` mode |
| `--dry-run` | off | List what would be processed; write nothing |
| `--pattern`, `-p` | `course_pattern.yaml` beside script | Custom pattern config (regex engine + stack detection) |

### What the Output Looks Like

Follows the `/course-docs` structure (sections with no content are skipped):

1. Title + metadata blockquote (Course / Week / Stack / Instructor Theme)
2. Numbered Table of Contents
3. Executive Summary — synthesized, 2–4 sentences
4. Architecture Overview — ASCII system diagram (engineering courses) or Concept Map (theory)
5. Learning Outcomes — "you will be able to…" action bullets
6. Tech Stack / Setup / Folder Structure / Data Model — only if present in the source
7. One section per major concept, with rewritten prose, tables, and the instructor's worked examples
8. Env Vars / Commands Cheat Sheet / ADRs — only if present
9. Gotchas & Troubleshooting — Symptom / Fix / Why blocks
10. Quick Reference — term → definition table + key principle

The LLM engine also infers structure the instructor only states verbally (e.g. "there are four tricks" → numbered trick sections), which regex cannot do.

---

## The Full Pipeline

Chain all three to go from a YouTube video to a reference doc:

```bash
# Step 1 — download the transcript (no video)
yt-dlp --skip-download --write-auto-sub --sub-lang en --sub-format vtt \
  -o "%(title)s" "https://youtube.com/watch?v=VIDEO_ID"

# Step 2 — convert .vtt subtitles → structured Markdown      [to_md.py]
python3 to_md.py "VideoTitle.en.vtt" -o notes.md --title "My Course Notes"

# Step 3 — generate the reference doc                        [generate_course_docs.py]
python3 generate_course_docs.py --input notes.md --output docs.md
```

`smart_transcript.py` slots in whenever you have raw notes you want tidied **without** any rewriting — e.g. cleaning a transcript before archiving it, or formatting hand-written notes that should stay verbatim.

---

## Choosing a Model

Applies to both `smart_transcript.py` and `generate_course_docs.py` (anything with `--model`). Without `--model`, the script inherits the **`claude` CLI's default model** — whatever is set in `~/.claude/settings.json` (`"model"` key) or chosen via `/model` inside Claude Code.

```bash
python3 generate_course_docs.py --input notes.md --output docs.md --model claude-sonnet-4-6
```

| Model id | Tier | When to use |
| --- | --- | --- |
| `claude-fable-5` | Highest quality | Best synthesis; slowest (~60s/file); heaviest on plan quota |
| `claude-opus-4-8` | High quality | Strong synthesis, slightly faster/cheaper than Fable |
| `claude-sonnet-4-6` | Balanced **(recommended for batches)** | Near-goodexample quality at a fraction of the time/quota |
| `claude-haiku-4-5-20251001` | Fastest / cheapest | Fine for short or simple transcripts; check output before batch use |

Notes:

- Runs go through your Claude Code login and draw from your **plan's usage quota** — smaller models burn less of it, which matters in `--all` batch mode.
- Aliases like `sonnet`, `opus`, `haiku` also work (`--model sonnet`), resolving to the CLI's current default for that tier.
- To change the default for every run instead of per run, set it once inside Claude Code with `/model`, or edit the `"model"` key in `~/.claude/settings.json`.
- If a model id is invalid, the `claude` call fails and the script falls back to its offline engine — check the warning line if you get a thin output.

---

## Customizing (`course_pattern.yaml`)

Used by `generate_course_docs.py`'s **regex engine** (and for stack detection). Three editable lists — no Python changes needed:

- **`sections`** — output section order and conditions
- **`stack_patterns`** — regexes that detect tools for the Tech Stack table
- **`filler_patterns`** — transcript phrases to drop from summaries

For a different course type, copy and trim:

```bash
cp course_pattern.yaml theory_pattern.yaml
# edit: remove project-setup / folder-structure / data-model sections
python3 generate_course_docs.py --input notes.md --pattern theory_pattern.yaml
```

The LLM prompts live inside each script as the `LLM_PROMPT` constant — edit there to change output style or sections.

---

## Requirements

| Dependency | Needed for | Install |
| --- | --- | --- |
| Python 3.10+ | everything | — |
| `claude` CLI, logged in | LLM engines (default in `smart_transcript.py` & `generate_course_docs.py`) | `npm install -g @anthropic-ai/claude-code`, then `claude` → `/login` |
| `PyYAML` | loading `course_pattern.yaml` (optional — falls back to built-in defaults) | `pip install pyyaml` |
| `yt-dlp` | Pipeline Step 1 only | `brew install yt-dlp` |

---

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `to_md.py: error: unrecognized arguments: --input` | `to_md.py` takes input **positionally**: `python3 to_md.py notes.txt -o out.md` |
| `LLM unavailable (claude CLI not found on PATH)` | Install Claude Code or accept the offline fallback; use `--no-llm` to silence the warning |
| `claude CLI timed out` | Raise `--llm-timeout`, or split the source with `to_md.py` |
| `smart_transcript.py` output looks like a near-identical copy | Source was already structured (or too short) — the offline restructurer only fires on unstructured run-on prose; try without `--no-llm` |
| `--mode speaking requires the claude CLI; drop --no-llm` | Speaking mode can't use the offline formatter — remove `--no-llm` (and make sure `claude` is installed & logged in) |
| Output is the thin regex version | The LLM fell back — check the warning line above `saved →` for the reason |
| Thin sections even in LLM mode | The transcript genuinely lacks that content — the prompt forbids inventing facts |
| `pattern loaded` line missing | PyYAML not installed; using built-in defaults (`pip install pyyaml`) |
| `SKIP (exists)` in batch mode | Output already exists; add `--force` to regenerate |

---

## Validation

```bash
# to_md.py smoke test
python3 to_md.py notes.txt -o /tmp/test.md

# smart_transcript.py smoke test (offline, faithful)
python3 smart_transcript.py --input notes.txt --output /tmp/org.md --no-llm

# smart_transcript.py speaking mode (needs claude CLI; ~30s)
python3 smart_transcript.py --mode speaking --input sub.txt --output /tmp/speaking.md

# generate_course_docs.py smoke test (offline, <1s)
python3 generate_course_docs.py --input notes.md --output /tmp/docs.md --no-llm

# Full-quality test (~60s)
python3 generate_course_docs.py --input notes.md --output /tmp/docs.md

# Verify the pattern file parses
python3 -c "import yaml; p = yaml.safe_load(open('course_pattern.yaml')); print(len(p['sections']), 'sections')"
```
