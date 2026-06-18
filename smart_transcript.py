#!/usr/bin/env python3
"""
smart_transcript.py — Turn raw text or transcripts into useful Markdown.

A small multi-mode toolkit. Pick a --mode:
  organize  Reformat/organize raw text into clean Markdown, preserving every word.
  speaking  Curate high-value spoken lines + a per-scene third-person Recap,
            as spoken-English practice material (requires the `claude` CLI).

The organize mode pipes the input to the local `claude` CLI (headless) with a
prompt that strictly preserves content while applying Markdown structure, and
falls back to a lightweight pass-through formatter when `claude` is unavailable.

Single file:
    python smart_transcript.py
    python smart_transcript.py --input notes.txt --output notes.md
    python smart_transcript.py --no-llm

All *.txt / *.md files found under a directory:
    python smart_transcript.py --all                  # current directory
    python smart_transcript.py --all /path/to/folder
    python smart_transcript.py --all . --force

Preview without writing:
    python smart_transcript.py --all . --dry-run

Speaking practice (curate high-value spoken lines; requires claude CLI):
    python smart_transcript.py --mode speaking --input sub.txt --output speaking.md
    python smart_transcript.py --mode speaking --all
"""

import argparse
import re
import shutil
import subprocess
import sys
import textwrap
import time
from pathlib import Path

# ── LLM engine (default) ─────────────────────────────────────────────────────

LLM_PROMPT = """\
You are a document formatter. Your only job is to reformat the raw text provided \
between <text> tags into a clean, well-structured Markdown document.

## Strict rules

1. **Preserve every word.** Do NOT modify, rewrite, summarize, or remove any \
information. Do NOT change meaning, wording, tone, or intent.
2. **Format only.** Apply appropriate Markdown syntax: headings, subheadings, \
lists, tables, blockquotes, code blocks, emphasis, horizontal rules, and spacing.
3. **Infer hierarchy.** Use logical section groupings and heading levels \
(H1 → H2 → H3) based on the content structure.
4. **Fix formatting inconsistencies** only when necessary to improve readability \
(e.g. inconsistent bullet styles, missing blank lines between sections).
5. **Preserve technical content exactly.** All code snippets, URLs, commands, \
environment variables, file paths, and examples must appear verbatim.
6. **Use code blocks** for any command-line instructions, code, config files, \
or technical strings that were inline in the original.
7. **Use tables** when the source contains structured comparisons or attribute \
lists that would read more clearly as a table.
8. **Use blockquotes** for callouts, quotes, or important notes that were \
visually distinguished in the original.
9. **No additions.** Do NOT add summaries, introductions, explanations, \
commentary, or new content of any kind.

## Output rules

- Return ONLY the final Markdown content.
- Do NOT wrap the output in a code fence.
- Do NOT add any preamble, closing remarks, or meta-commentary.
- The result must be 100% faithful to the source — only the presentation changes.
"""

# ── speaking-practice engine (--mode speaking) ───────────────────────────────

SPEAKING_PROMPT = """\
You are a speaking rehearsal coach, not an English teacher, working for an \
upper-intermediate / advanced (B2–C1) learner. Turn the transcript provided \
between <text> tags into a curated corpus of high-value spoken English the \
learner will say out loud — not a reading list, not a cleaned-up transcript.

The learner already speaks fluent everyday English, so the corpus must clear a \
PROFICIENCY FLOOR: real, natural, everyday conversation is exactly what you \
want, but the trivially easy lines an upper-intermediate already says without a \
second thought do NOT belong. Keep the everyday lines that still carry a \
reusable structure, a natural phrasing, or some expressive colour; drop the bare \
ones that teach nothing.

## Prime directive — maximum useful coverage (depth = more, not invented)

This is NOT a thin highlight reel. Mine the ENTIRE transcript and surface EVERY \
line that genuinely earns a place — comb it end to end and keep all the \
high-value spoken English, not just a token handful per scene. Prioritize \
completeness of capture over a short page.

- Cover the whole transcript — divide it into as many scenes as the content has; \
don't stop after the first few. A long video should yield many scenes, not five.
- Keep every line that passes both tests below — if ten lines in a scene are \
reusable, keep ten. Don't ration to 2–3 for tidiness.
- No artificial length limits. A rich source produces a long corpus — that's \
correct, not a problem.
- Crucial constraint — depth NEVER means inventing. "Maximum depth" here is \
achieved by selecting more real lines and writing fuller Recaps, never by \
composing lines that aren't in the transcript. The VERBATIM RULE below is \
absolute and overrides any urge to pad. If a scene is genuinely thin, it stays \
thin.

## The three tests — every line must pass ALL THREE

1. Natural speech: would a native speaker realistically say this in everyday life?
2. Speaking value: if the learner said it aloud 50 times, would their spoken \
English improve?
3. Proficiency floor (B2–C1): is this above the level an upper-intermediate \
learner already produces automatically? Reject anything a confident everyday \
speaker already says cold — bare greetings and sign-offs ("hey", "how are you", \
"how's your day going?"), plain thanks/apologies ("thank you so much", "I really \
appreciate it", "I am so sorry"), and trivial one-clause reactions or logistics \
with no reusable structure ("I have no idea", "I'm going to miss my train", "I \
don't understand any of the signs", "this is not a good start"). These are \
natural and have some value, but they sit below the floor — drop them.

The floor is NOT "idioms only". Plenty of plain everyday conversation passes — \
keep it when the line carries a transferable frame, a natural collocation, a \
hedge/intensifier/discourse move, or real expressive colour. The point is to cut \
the trivially easy lines, not the everyday register. Gut check: would learning \
this line move an upper-intermediate forward, or do they already say it in their \
sleep? Keep the first kind; drop the second.

Pure information — facts, statistics, prices, addresses, proper-noun lists — \
fails test 2 even when natural. Drop it. When a line mixes information with a \
reusable frame, keep only the frame ("It cost like forty bucks, which honestly \
surprised me" → keep "which honestly surprised me").

## What to extract

Hunt specifically for, and keep all of: reactions, opinions, observations, \
decisions, storytelling beats, social exchanges (offers, thanks-and-deflect, \
introductions), and connective phrases people reuse across many situations. \
Works the same for monologue (solo speaker) as for dialogue.

## VERBATIM RULE — absolute (applies to the extracted lines)

Copy every extracted line character-for-character from the transcript. Never \
paraphrase, reword, or "clean up". Keep contractions, fillers, and casual \
phrasing exactly as spoken (I'm, gonna, wanna, I mean, kind of, you know). Your \
job is to SELECT lines, never to COMPOSE them. If a line is not in the transcript \
word-for-word, it does not appear. (The one exception is the "Recap" block \
below, which is a generated third-person narration — see its rules.)

## Recap block — one per scene

After the verbatim lines of EACH scene, add a "### Recap" block: a ready-to-read, \
third-person narration of the scene that the learner reads ALOUD to practice \
speaking. Write the full recap yourself — the learner reads it, they do not \
finish it. Rules:

- Write 2–4 COMPLETE sentences narrating what happened in THIS scene, in the \
third person and mostly past tense (e.g. "So they get picked up by a private \
driver, and in the back there are bougie snacks waiting for them. When they \
arrive, they're swept off their feet, and the staff offer them a glass of house \
wine."). Make them full and faithful — cover the real beats of the scene, not a \
one-line gloss.
- It is a MODEL narration, not a task. Do NOT use bullet "beats", a "Mention:" \
line, or a "Starter:" fragment, and do NOT trail off with "..." — write whole \
sentences.
- Cover only what actually happened in the scene. No invented facts.
- Natural spoken style is good (So..., and..., they're...) — this is for saying \
out loud, not formal writing.

## Coverage

Visit the whole transcript beginning to end. Divide it into scenes by topic, \
location, or conversation shift — as many scenes as the material genuinely has. \
Each scene is a CURATED SELECTION — keeping only a fraction of each scene's words \
is correct, but skipping whole stretches of the transcript is not. A scene that \
is pure facts may yield few or no lines; a rich social scene should yield many.

## Output format — a single Markdown document, no preamble

# [Inferred Title]

## Scene-by-Scene Extraction

### Scene 1 — [short label]

[verbatim line]
[verbatim line]

### Recap

So they ... . When they ... , they ... . [2–4 complete third-person sentences]

### Scene 2 — [short label]

[verbatim line]

### Recap

So she ... , and then ... . [2–4 complete third-person sentences]

## Phrases Worth Reviewing

- [reusable frame, stripped to the transferable part]
- ...

Rules for the phrase list: the most reusable frames (aim for 8–20+, more for a \
rich transcript — don't cap a long source at 20), distilled to the frame, \
deduplicated, flat bullets. Exclude bare greetings and throwaway small talk \
("hi", "okay", "thanks").

## Output rules

- Return ONLY the Markdown document. No code fence, no preamble, no commentary.
- The document contains only: the per-scene extraction (each scene = verbatim \
lines + its "Recap" block) and the final "Phrases Worth Reviewing" list — \
nothing else.
- No grammar notes, vocabulary, definitions, or speaking tips anywhere.

## What NOT to include

- No composed or paraphrased lines — the verbatim rule is absolute; never \
fabricate a line to look more thorough.
- No grammar notes, vocabulary definitions, or speaking tips anywhere.
- No cleaned-up transcript, no reading-list dump of every sentence — this is \
curated high-value speech, not the raw text reformatted.
- No filler kept for length: drop pure facts/stats/prices/addresses, bare \
greetings, and "okay/sure/thanks" on their own.
- No below-floor basic English — even when verbatim and natural. Drop bare \
greetings/sign-offs ("hey", "how are you", "how's your day going?"), plain \
thanks/apologies ("thank you so much", "I really appreciate it", "I am so \
sorry"), and trivial one-clause reactions/logistics with no reusable structure \
("I have no idea", "I'm going to miss my train", "this is not a good start"). \
Target B2–C1: keep everyday lines that still teach a frame, collocation, or \
expressive move; cut the ones an upper-intermediate already says automatically.
- No thin-coverage failure either: don't keep only 2–3 lines per scene or skip \
late scenes — if a scene has ten reusable lines, keep ten, and cover the \
transcript to its end.
"""


def organize_with_llm(text: str, model: str | None = None,
                      timeout: int = 300, prompt: str = LLM_PROMPT) -> str:
    """Reorganize the text by piping it to `claude -p`.

    Raises RuntimeError if the claude CLI is unavailable or produces
    unusable output, so the caller can fall back to the passthrough formatter.
    """
    if shutil.which("claude") is None:
        raise RuntimeError("claude CLI not found on PATH")

    cmd = ["claude", "-p", prompt, "--output-format", "text"]
    if model:
        cmd += ["--model", model]

    try:
        result = subprocess.run(
            cmd,
            input=f"<text>\n{text}\n</text>",
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"claude CLI timed out after {timeout}s") from exc

    if result.returncode != 0:
        raise RuntimeError(f"claude CLI failed: {result.stderr.strip()[:300]}")

    doc = result.stdout.strip()
    # Unwrap if the model fenced the whole document despite instructions
    fence = re.match(r"^```(?:markdown|md)?\n(.*)\n```$", doc, re.DOTALL)
    if fence:
        doc = fence.group(1).strip()

    if len(doc) < 20:
        raise RuntimeError("claude CLI returned unusable output")
    return doc


# ── lightweight passthrough formatter (offline fallback) ─────────────────────

def _detect_code_block_lines(lines: list[str]) -> set[int]:
    """Return indices of lines that are inside fenced code blocks."""
    inside = set()
    in_fence = False
    fence_marker = ""
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not in_fence:
            m = re.match(r"^(`{3,}|~{3,})", stripped)
            if m:
                in_fence = True
                fence_marker = m.group(1)[0] * len(m.group(1))
                inside.add(i)
        else:
            inside.add(i)
            if stripped.startswith(fence_marker) and len(stripped) >= len(fence_marker):
                in_fence = False
    return inside


def _ensure_blank_before_heading(lines: list[str], code_lines: set[int]) -> list[str]:
    """Insert a blank line before ## / ### headings if one is missing."""
    out = []
    for i, line in enumerate(lines):
        if i not in code_lines and re.match(r"^#{1,6}\s", line):
            if out and out[-1].strip():
                out.append("")
        out.append(line)
    return out


def _ensure_blank_after_heading(lines: list[str], code_lines: set[int]) -> list[str]:
    """Insert a blank line after headings if one is missing."""
    out = []
    for i, line in enumerate(lines):
        out.append(line)
        if i not in code_lines and re.match(r"^#{1,6}\s", line):
            if i + 1 < len(lines) and lines[i + 1].strip():
                out.append("")
    return out


def _collapse_excess_blank_lines(lines: list[str], code_lines: set[int]) -> list[str]:
    """Reduce 3+ consecutive blank lines to 2 outside code blocks."""
    out: list[str] = []
    blank_count = 0
    for i, line in enumerate(lines):
        if i in code_lines:
            out.append(line)
            blank_count = 0
        elif not line.strip():
            blank_count += 1
            if blank_count <= 2:
                out.append(line)
        else:
            blank_count = 0
            out.append(line)
    return out


def _normalise_bullets(lines: list[str], code_lines: set[int]) -> list[str]:
    """Normalise mixed bullet markers (* and +) to - outside code blocks."""
    out = []
    for i, line in enumerate(lines):
        if i not in code_lines:
            line = re.sub(r"^(\s*)[\*\+](\s+)", r"\1-\2", line)
        out.append(line)
    return out


def _wrap_bare_commands(lines: list[str], code_lines: set[int]) -> list[str]:
    """Wrap bare inline commands (backtick-free) in backticks when safe."""
    CMD_RE = re.compile(
        r"(?<![`\w/])"
        r"((?:npm|npx|pnpm|yarn|pip|python3?|node|git|gh|docker|brew|uv|claude|cd|ls|mkdir|rm|cp|mv|curl|chmod|cat|source|export)\s+\S[^\s,;.\"\']{0,80})"
        r"(?![`\w])",
    )
    out = []
    for i, line in enumerate(lines):
        if i not in code_lines and not re.match(r"^#{1,6}\s", line):
            line = CMD_RE.sub(r"`\1`", line)
        out.append(line)
    return out


# ── prose restructuring (for unstructured run-on text) ──────────────────────
#
# These passes operate ONLY on text that has no existing Markdown structure
# (no headings, no lists). They split run-on prose into paragraphs and promote
# "section-announcing" sentences into headings. Crucially, they NEVER change,
# add, or remove any words — every word of the source survives verbatim; only
# whitespace and Markdown heading markers (`#`) are inserted between sentences.

# Cues that signal the *start* of a new paragraph/topic in spoken prose.
_PARAGRAPH_CUES = [
    r"And the (?:first|second|third|fourth|fifth|next|final|last) (?:trick|thing|point|step|reason|one)\b",
    r"The (?:first|second|third|fourth|fifth|next|final|last) (?:trick|thing|point|step|reason)\b",
    r"Okay,?\s+(?:so\s+)?(?:that'?s|let'?s|now)\b",
    r"And then (?:also|there'?s|we)\b",
    r"Now,?\s+(?:let'?s|the|we|I)\b",
    r"So,?\s+(?:let'?s|the|in|to|that)\b",
    r"Let'?s (?:get into it|move on|talk about|look at)\b",
    r"Here'?s (?:a|the|another|one)\b",
    r"But (?:wait|of course|in fact)\b",
]
_PARAGRAPH_CUE_RE = re.compile(r"^(?:" + "|".join(_PARAGRAPH_CUES) + r")", re.IGNORECASE)

# Sentences that *name* a concept — candidates to become headings.
# We capture the concept name so the heading text is taken verbatim from source.
_HEADING_PATTERNS = [
    re.compile(r"\bI call it (?:the\s+)?([a-z][a-z' ]{4,40}?)\.", re.IGNORECASE),
    re.compile(r"\bthis trick called ([a-z][a-z' ]{3,40}?)\.", re.IGNORECASE),
    re.compile(r"\bsomething (?:different,? but [a-z ]+ )?(?:sounding similar,? )?called (?:like )?an? ([a-z][a-z' ]{3,40}?)\b", re.IGNORECASE),
]


def _split_sentences(text: str) -> list[str]:
    """Split prose into sentences, keeping terminal punctuation attached."""
    # Split on sentence-ending punctuation followed by whitespace + capital/quote.
    parts = re.split(r"(?<=[.!?])\s+(?=[\"'A-Z])", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _looks_unstructured(text: str) -> bool:
    """True if the text is run-on prose with no Markdown structure worth keeping."""
    body = text.strip()
    # Strip a single wrapping bullet ("- " over the whole blob).
    if body.startswith(("- ", "* ", "+ ")):
        body = body[2:]
    has_heading = bool(re.search(r"^#{1,6}\s", body, re.MULTILINE))
    # Multiple real list items (not just one wrapping bullet)?
    list_items = len(re.findall(r"^\s*(?:[-*+]|\d+\.)\s+\S", body, re.MULTILINE))
    has_paragraphs = "\n\n" in body
    # Unstructured = no headings, ≤1 list marker, and not already paragraphed.
    return not has_heading and list_items <= 1 and not has_paragraphs


def _heading_for(sentence: str) -> str | None:
    """If a sentence announces a named concept, return a Title-Case heading text."""
    for pat in _HEADING_PATTERNS:
        m = pat.search(sentence)
        if m:
            name = m.group(1).strip(" '").rstrip(".")
            # Reject overly generic captures.
            if 4 <= len(name) <= 40 and not name.lower().startswith(("it", "this", "that")):
                return name.title()
    return None


def restructure_prose(text: str) -> str:
    """Turn an unstructured run-on transcript into paragraphs with headings.

    Word-preserving: only inserts blank lines and `#`/`##` heading lines built
    from text the source itself uses. No source words are altered or dropped.
    """
    body = text.strip()
    # Unwrap a single leading bullet that wraps the entire blob.
    if body.startswith(("- ", "* ", "+ ")):
        body = body[2:].lstrip()

    sentences = _split_sentences(body)
    if len(sentences) < 4:
        return text  # too short to benefit; leave as-is

    blocks: list[str] = []          # rendered output blocks (headings + paragraphs)
    para: list[str] = []            # current paragraph's sentences

    def flush() -> None:
        if para:
            blocks.append(" ".join(para))
            para.clear()

    for sent in sentences:
        # A concept-naming sentence becomes its own H2, on its own paragraph.
        heading = _heading_for(sent)
        if heading:
            flush()
            blocks.append(f"## {heading}")
            para.append(sent)
            continue
        # A transitional cue starts a new paragraph.
        if para and _PARAGRAPH_CUE_RE.search(sent):
            flush()
        para.append(sent)
        # Soft cap paragraph length so we don't recreate a wall of text.
        if len(" ".join(para)) > 600:
            flush()
    flush()

    return "\n\n".join(blocks)


def organize_passthrough(text: str) -> str:
    """Apply formatting fixes without touching content.

    For already-structured Markdown: normalise whitespace, bullets, headings.
    For unstructured run-on prose: split into paragraphs and promote announced
    concepts into headings (word-preserving) before the cleanup passes.
    """
    if _looks_unstructured(text):
        text = restructure_prose(text)

    lines = text.splitlines()

    code_lines = _detect_code_block_lines(lines)
    lines = _normalise_bullets(lines, code_lines)
    code_lines = _detect_code_block_lines(lines)  # recompute after bullet change
    lines = _ensure_blank_before_heading(lines, code_lines)
    code_lines = _detect_code_block_lines(lines)
    lines = _ensure_blank_after_heading(lines, code_lines)
    code_lines = _detect_code_block_lines(lines)
    lines = _collapse_excess_blank_lines(lines, code_lines)
    code_lines = _detect_code_block_lines(lines)
    lines = _wrap_bare_commands(lines, code_lines)

    return "\n".join(lines).strip() + "\n"


# ── file processing ───────────────────────────────────────────────────────────

def process_file(input_path: Path, output_path: Path,
                 use_llm: bool = True, model: str | None = None,
                 llm_timeout: int = 300, mode: str = "organize") -> bool:
    try:
        text = input_path.read_text(encoding="utf-8")
        doc = None
        prompt = SPEAKING_PROMPT if mode == "speaking" else LLM_PROMPT
        # Speaking extraction needs the LLM — the offline formatter only
        # reshapes whitespace and can't curate lines by speaking value.
        if mode == "speaking" and not use_llm:
            print("  ERROR: --mode speaking requires the claude CLI; "
                  "drop --no-llm")
            return False
        if use_llm:
            try:
                engine = "speaking extraction" if mode == "speaking" else "LLM formatting"
                print(f"  engine: claude ({engine}) ...")
                doc = organize_with_llm(text, model=model, timeout=llm_timeout,
                                        prompt=prompt)
            except RuntimeError as exc:
                if mode == "speaking":
                    print(f"  ERROR: claude CLI unavailable ({exc}); "
                          "speaking mode cannot fall back to the offline formatter")
                    return False
                print(f"  LLM unavailable ({exc}) — falling back to passthrough formatter")
        if doc is None:
            doc = organize_passthrough(text)
        output_path.write_text(doc, encoding="utf-8")
        print(f"  saved → {output_path}  ({len(doc):,} chars)")
        return True
    except Exception as exc:
        print(f"  ERROR: {exc}")
        return False


def discover_files(root: Path, pattern: str) -> list[Path]:
    results: list[Path] = []
    for p in pattern.split(","):
        results.extend(sorted(root.rglob(p.strip())))
    return sorted(set(results))


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reformat and organize raw text into clean Markdown (content-preserving).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python smart_transcript.py
              python smart_transcript.py --input notes.txt --output notes.md
              python smart_transcript.py --no-llm
              python smart_transcript.py --all                 # current dir
              python smart_transcript.py --all /path/to/folder
              python smart_transcript.py --all . --force
              python smart_transcript.py --all . --dry-run
              python smart_transcript.py --mode speaking -i sub.txt -o speaking.md
              python smart_transcript.py --mode speaking --all . --source-glob "*.txt"
        """),
    )

    source = parser.add_mutually_exclusive_group()
    source.add_argument("--all", nargs="?", type=Path, const=Path("."),
                        default=None, metavar="DIR",
                        help="Auto-discover source files under DIR "
                             "(default: current directory). "
                             "e.g. --all .  or  --all /path/to/folder")
    source.add_argument("--files", nargs="+", type=Path, metavar="FILE",
                        help="Explicit list of input files")

    parser.add_argument("--input",       "-i", type=Path, default=Path("input.txt"))
    parser.add_argument("--output",      "-o", type=Path, default=None)
    parser.add_argument("--root",              type=Path, default=None)
    parser.add_argument("--source-glob",       type=str,  default="*.txt,*.md",
                        help="Glob pattern(s) for --all discovery (default: *.txt,*.md)")
    parser.add_argument("--output-suffix",     type=str,  default="-organized",
                        help="Suffix appended to stem for --all output (default: -organized)")
    parser.add_argument("--force",             action="store_true",
                        help="Overwrite existing output files")
    parser.add_argument("--dry-run",           action="store_true",
                        help="Preview which files would be processed without writing")
    parser.add_argument("--mode",              choices=["organize", "speaking"],
                        default="organize",
                        help="organize: faithful Markdown reformat (default). "
                             "speaking: curate high-value spoken lines into "
                             "speaking-practice material (requires claude CLI)")
    parser.add_argument("--no-llm",            action="store_true",
                        help="Skip the claude CLI and use the offline passthrough formatter only")
    parser.add_argument("--model",             type=str,  default=None,
                        help="Model passed to `claude --model` (default: CLI default)")
    parser.add_argument("--llm-timeout",       type=int,  default=300,
                        help="Seconds to wait for the claude CLI per file (default: 300)")

    args = parser.parse_args()

    # In speaking mode, default the output naming to "-speaking" unless the
    # user explicitly chose a suffix.
    if args.mode == "speaking" and args.output_suffix == "-organized":
        args.output_suffix = "-speaking"

    jobs: list[tuple[Path, Path]] = []

    if args.all is not None or args.files:
        if args.all is not None:
            # Root precedence: path given to --all > --root > current directory.
            root = (args.all if args.all != Path(".") else (args.root or Path.cwd())).resolve()
            sources = discover_files(root, args.source_glob)
        else:
            sources = [p.resolve() for p in args.files]

        for src in sources:
            stem = src.stem
            out = src.parent / f"{stem}{args.output_suffix}.md"
            if out.exists() and not args.force:
                print(f"  SKIP (exists) {src}")
                continue
            if src.resolve() == out.resolve():
                print(f"  SKIP (would overwrite input) {src}")
                continue
            jobs.append((src, out))
    else:
        inp = args.input.resolve()
        if args.output:
            out = args.output.resolve()
        elif args.mode == "speaking":
            out = inp.parent / f"{inp.stem}-speaking.md"
        else:
            out = inp.parent / f"{inp.stem}{'-organized' if not inp.suffix == '.md' else '-formatted'}.md"
        jobs.append((inp, out))

    if not jobs:
        print("Nothing to process. Use --force to overwrite existing files.")
        return

    if args.dry_run:
        print(f"\nDry run — {len(jobs)} file(s) would be processed:\n")
        for inp, out in jobs:
            size = f"{inp.stat().st_size:,}" if inp.exists() else "?"
            print(f"  {inp}\n    → {out}  ({size} bytes)")
        return

    print(f"\nProcessing {len(jobs)} file(s) ...\n" + "─" * 60)

    succeeded, failed = [], []
    for idx, (inp, out) in enumerate(jobs, 1):
        print(f"\n[{idx}/{len(jobs)}] {inp.name}  ({inp.stat().st_size:,} bytes)")
        t0 = time.time()
        ok = process_file(inp, out,
                          use_llm=not args.no_llm, model=args.model,
                          llm_timeout=args.llm_timeout, mode=args.mode)
        print(f"  elapsed: {time.time() - t0:.1f}s")
        (succeeded if ok else failed).append(inp)

    print("\n" + "─" * 60)
    print(f"Done.  {len(succeeded)} succeeded  |  {len(failed)} failed")
    if failed:
        for f in failed:
            print(f"  FAILED: {f}")
        sys.exit(1)


if __name__ == "__main__":
    main()
