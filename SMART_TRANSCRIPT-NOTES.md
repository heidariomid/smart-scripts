# smart_transcript.py — Recap & How to Add Modes

> **Read this first** before extending `smart_transcript.py`. It maps the existing modes,
> shows the exact recipe to add a new one, and lists the traps we already hit.
> Canonical script: **`~/bin/smart_transcript.py`** (the project-folder copy is a working copy — see §8).

## 0. One-paragraph summary

`smart_transcript.py` is a single-file, multi-mode CLI that turns a transcript/raw text into Markdown.
A mode is selected with `--mode` (default `organize`). Each mode is essentially **one LLM prompt
constant + a few wiring touch-points**. Today there are two modes: **`organize`** (faithful,
word-preserving reformat; has an offline regex fallback) and **`speaking`** (curate verbatim
high-value spoken lines, each scene followed by a generated 3rd-person **Recap** paragraph to read
aloud; LLM-required, no offline fallback). The script lives globally at `~/bin/smart_transcript.py`
and is driven by two `~/.zshrc` shortcuts — `organize` and `speaking` — that run from any folder and
write output **next to the input file**. The spec for speaking mode is duplicated in the
`passive-to-active-english` skill (`SKILL.md`); **both must be edited together** or they drift.
Goal going forward: add many more modes (e.g. summary, vocab, Q&A, role-play) the same way.

## 1. First response when something breaks

1. **Run the smoke checks in §9.** They catch 90% of regressions (syntax, the `--no-llm` guard, mode wiring).
2. **Read the engine line the script prints.** `engine: claude (speaking extraction) ...` vs
   `engine: claude (LLM formatting) ...` vs `LLM unavailable (...) — falling back to passthrough`
   tells you which path actually ran. Thin/empty output usually means it silently fell back.
3. **Check you edited the right copy.** Canonical is `~/bin/smart_transcript.py`. The project-folder
   copy is separate; edits to one do not propagate. (§8)
4. **If speaking output looks wrong, also check `SKILL.md`** — the chat-invoked skill uses its own
   copy of the prompt spec, not the script's.

## 2. Mode cheat sheet

| Mode | What it produces | Verbatim? | Offline fallback? | Default output suffix |
| --- | --- | --- | --- | --- |
| `organize` (default) | Faithful Markdown reformat, every word preserved | Yes (whole doc) | **Yes** (regex passthrough) | `-organized` |
| `speaking` | Curated spoken lines per scene + a generated 3rd-person **Recap** + "Phrases Worth Reviewing" | Extracted lines only; Recap is generated | **No** (errors if no LLM) | `-speaking` |

Shell shortcuts (`~/.zshrc`): `organize() { python3 ~/bin/smart_transcript.py "$@"; }` ·
`speaking() { python3 ~/bin/smart_transcript.py --mode speaking "$@"; }`

## 3. Symptom → cause → fix

| Symptom | Cause | Fix |
| --- | --- | --- |
| `--mode speaking requires the claude CLI; drop --no-llm` | Speaking mode can't curate offline (by design) | Remove `--no-llm`; ensure `claude` is installed & logged in |
| `speaking --all .` re-processes its own `*-speaking.md` outputs | Default `--source-glob` is `*.txt,*.md` and matches generated `.md` | Always pass `--source-glob "*.txt"` (or `*.vtt`) in batch mode |
| `--all` scans the wrong folder / finds nothing | Old behavior rooted at the *script's* dir | Use the new form: `--all .` or `--all /path` (path arg wins; defaults to **cwd**) |
| Edited the script but behavior didn't change | Edited the project copy, ran the `~/bin` copy (or vice-versa) | Edit `~/bin/smart_transcript.py` (canonical); re-sync the other (§8) |
| New shortcut not found in an open terminal | `~/.zshrc` not reloaded | `source ~/.zshrc` or open a new tab |
| Speaking output via the **skill** differs from the **CLI** | `SKILL.md` and `SPEAKING_PROMPT` drifted | Re-sync both copies of the spec |

## 4. The working approach — how a mode is wired (with anchors)

A mode = a prompt constant + **5 wiring touch-points**. Current anchors in `smart_transcript.py`:

| # | Touch-point | Where (approx) | What it does |
| --- | --- | --- | --- |
| 1 | `*_PROMPT` constant | `LLM_PROMPT` ~L43, `SPEAKING_PROMPT` ~L78 | The mode's entire behavior — it's a prompt |
| 2 | prompt selection | `process_file`, `prompt = SPEAKING_PROMPT if mode == "speaking" else LLM_PROMPT` ~L444 | Maps mode → prompt |
| 3 | LLM-required guard | ~L447 (`if mode == "speaking" and not use_llm`) and ~L458 (no offline fallback) | Modes that can't run offline error cleanly instead of writing junk |
| 4 | `--mode` choices | `parser.add_argument("--mode", choices=["organize","speaking"], ...)` ~L520 | Registers the flag value |
| 5 | output naming | suffix default ~L536, single-file name ~L563 | `*-speaking.md` etc. so modes don't clobber each other |

**Why each earned its place (don't remove):**
- The **guard (3)** exists because the offline regex formatter only reshapes whitespace — it cannot
  judge "speaking value." Without the guard, `--mode speaking --no-llm` produced a useless file.
  Proven: we ran it; it now exits 1 and writes nothing.
- **Output naming (5)** exists because `--all` with the default glob would otherwise overwrite or
  re-ingest prior outputs. `-speaking` vs `-organized` keeps them separate.
- **`--all` taking a path** replaced the old `--root`-only form so the tool works from any folder
  (it's installed globally). Proven from `/tmp` against the project folder via the `speaking` shortcut.

## 5. Pitfalls that cost time (do NOT repeat)

- **Two copies drift.** The script exists in the project folder *and* `~/bin`; the speaking spec
  exists in the script *and* `SKILL.md`. Every speaking change touched **both** prompt copies plus the
  two doc files. Treat "edit one copy" as a bug.
- **`argparse` Edit churn.** Editing the same file repeatedly triggered "file modified since read" —
  re-Read before each Edit when iterating fast.
- **Default `--source-glob` includes `.md`.** Easy to forget; causes the batch to eat its own outputs.
- **All-caps shouting in transcripts.** The raw `sub.txt` has lines like `OH, IT'S WORKING` (auto-caps
  for shouting). Verbatim-mode output normalized these to sentence case for readability — a conscious
  exception to "character-for-character," worth remembering if strict fidelity is ever required.

## 6. Tried and rejected, and why

| Idea | Why rejected |
| --- | --- |
| Multiple separate speaking modes (`qa-prompts`, `roleplay`, `retell`, `shadowing`) | User wanted focus, not feature sprawl — folded one idea (retell) into `speaking` instead |
| Retell as a **task** (beats + a "Starter:" line for the learner to finish) | User explicitly reversed this: they want to *read*, not produce — replaced with a **full written Recap** (complete 3rd-person sentences) |
| New `--mode retell` | User chose to **fold** it into `speaking`, not add a mode |
| Offline fallback for speaking mode | Regex can't curate by speaking value — better to error than emit junk |
| Symlink `~/bin` → project copy | Fragile (project lives in `~/Downloads`, may move/delete) — chose `~/bin` as canonical instead |
| `--recursive` flag | Recursion is already always-on via `rglob`; not needed yet (revisit if shallow scans are wanted) |

## 7. Hard limits / ceilings

- **Speaking mode needs the LLM.** No code change makes offline curation good; the honest options are
  "use the `claude` CLI" or "don't use speaking mode." This is intentional, not a bug.
- **Mode logic is hardwired in 5 places.** Fine for 2–3 modes; if you add *many* modes, the
  `if mode == "..."` branches and naming logic get unwieldy. See §8 for the suggested refactor before
  scaling — otherwise each new mode means touching 5 scattered spots and risking the guard/naming.
- **Two-way spec duplication (script ↔ SKILL.md)** has no enforcement; nothing fails if they diverge.

## 8. Current state / loose ends

**Working & verified:**
- `smart_transcript.py` with `organize` + `speaking` modes; `--mode speaking` produces per-scene
  **Recap** prose (verified: 21 scenes / 21 Recaps, full 3rd-person sentences, no beats/starter).
- Global install: `~/bin/smart_transcript.py`; shortcuts `organize` / `speaking` in `~/.zshrc`
  (tested from `/tmp`).
- `--all [DIR]` path form; `--no-llm` guard; `*-speaking.md` naming.
- Docs updated: `how-to-use.md` (quick-reference at top, §2 reframed as multi-mode).
- `SKILL.md` (`passive-to-active-english`) synced with the Recap spec.

**Loose ends / watch out:**
- **Project-folder copy vs `~/bin` copy** are both present and currently identical — they can drift.
  Decide on one canonical (recommended: `~/bin`) and always re-sync after edits:
  `cp ~/bin/smart_transcript.py "<project>/smart_transcript.py"` (or the reverse).
- **Project `speaking.md` was NOT regenerated** in the latest run — it may still reflect an older
  format. Regenerate with `speaking -i sub.txt -o speaking.md` when wanted.
- **No refactor yet** to a mode registry (see below) — do this *before* adding many modes.

### Recommended refactor before adding many modes (not yet done)

Collapse the 5 touch-points into one table so a new mode is a single entry:

```python
MODES = {
    "organize": {"prompt": LLM_PROMPT,      "needs_llm": False, "suffix": "-organized"},
    "speaking": {"prompt": SPEAKING_PROMPT, "needs_llm": True,  "suffix": "-speaking"},
    # add: "summary", "vocab", "qa", "roleplay" ...
}
```
Then derive `choices=list(MODES)`, prompt/guard/suffix from `MODES[args.mode]`. Adding a mode becomes:
write a `*_PROMPT`, add one dict row. **Keep the `SKILL.md` sync discipline** regardless.

## 9. Quick validation

Run from the project folder (uses `~/bin` copy via the shortcuts; adjust path if testing the local copy):

```bash
# 1. Syntax (both copies)
python3 -c "import ast; ast.parse(open('smart_transcript.py').read()); ast.parse(open('$HOME/bin/smart_transcript.py').read()); print('OK')"

# 2. --no-llm guard still errors cleanly, writes nothing
python3 ~/bin/smart_transcript.py --mode speaking -i sub.txt -o /tmp/x.md --no-llm; \
  echo "exit=$? exists=$([ -f /tmp/x.md ] && echo YES || echo NO)"   # expect exit=1 exists=NO

# 3. --all path + glob resolves correctly (no writes)
python3 ~/bin/smart_transcript.py --mode speaking --all . --source-glob "*.txt" --dry-run

# 4. End-to-end (needs claude CLI, ~90-110s) — check Recap blocks
python3 ~/bin/smart_transcript.py --mode speaking -i sub.txt -o /tmp/recap_test.md --llm-timeout 480
grep -c "^### Recap" /tmp/recap_test.md   # should equal the scene count

# 5. No stale references to the old name anywhere
grep -rl organize_text . 2>/dev/null || echo "clean"
```
