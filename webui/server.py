#!/usr/bin/env python3
"""Local web UI for running the transcript agents.

Drop or pick a transcript file, choose an agent and a model, and the selected
agent's prompt is run through `claude -p`. The output is saved to your Desktop
(alongside a copy of the input) and shown in the browser to download.

Pure standard library — no third-party dependencies. Run with:

    python3 webui/server.py

then open the printed http://127.0.0.1:PORT URL.

The agent prompts are loaded verbatim from `.claude/agents/<mode>.md`, so this
server never duplicates prompt text — those files stay the single source.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8765
LLM_TIMEOUT = 480  # infographic / travel-guide can be slow
MAX_PARALLEL = 3   # how many agents run at once when several are selected

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"
INDEX_HTML = HERE / "index.html"
OUTPUT_DIR = Path.home() / "Desktop"  # where inputs + outputs are saved

# Transcript file types we read.
SOURCE_EXTS = {".txt", ".srt", ".md", ".vtt"}

# mode -> output suffix (extension included). organize is special-cased for .md inputs.
MODE_SUFFIX = {
    "organize": "-organized.md",
    "speaking": "-speaking.md",
    "summary": "-summary.md",
    "roleplay": "-roleplay.md",
    "travel-guide": "-travel-guide.md",
    "infographic": "-infographic.html",
    "infographic-advanced": "-infographic-advanced.html",
    "course-docs": "-course-docs.md",
    "passive-to-active-english": "-speaking-practice.md",
}

# Most agents run with NO tools (the model returns text on stdout; the server
# writes the file). A few agents' prompts genuinely call for read-only web
# access — e.g. travel-guide tells the model to web-search and verify places
# before stating them, and to build real map links. For those, allow ONLY the
# read-only web tools. Write/Edit/Bash stay denied via --disallowedTools, so
# this never reintroduces file-write or permission-prompt risk.
# mode -> space/comma-separated tool list for `claude --tools`. Absent => "" (no tools).
MODE_TOOLS = {
    "travel-guide": "WebSearch,WebFetch",
}

# Model aliases offered in the UI. Aliases are accepted by `claude --model` and
# always resolve to the latest model in each tier, so they stay correct as the
# CLI updates.
MODELS = [
    {"alias": "opus", "label": "Opus 4.8 (most capable)"},
    {"alias": "sonnet", "label": "Sonnet 4.6 (balanced)"},
    {"alias": "haiku", "label": "Haiku 4.5 (fastest)"},
]

# Effort (reasoning) levels accepted by `claude --effort`. Higher = more
# thinking, slower + more expensive. An empty alias means "model default".
EFFORTS = [
    {"alias": "", "label": "Default"},
    {"alias": "low", "label": "Low (fastest)"},
    {"alias": "medium", "label": "Medium"},
    {"alias": "high", "label": "High"},
    {"alias": "xhigh", "label": "Extra high"},
    {"alias": "max", "label": "Max (most thorough)"},
]
VALID_EFFORTS = {e["alias"] for e in EFFORTS if e["alias"]}

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


# ---------------------------------------------------------------------------
# Agent + model discovery
# ---------------------------------------------------------------------------

def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body). Minimal YAML — only top-level key: value."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text.strip()
    fm: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip().strip('"').strip("'")
    body = text[m.end():].strip()
    return fm, body


def list_modes() -> list[dict]:
    """Discover agents from .claude/agents/*.md (README excluded)."""
    modes = []
    for path in sorted(AGENTS_DIR.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        fm, _ = _parse_frontmatter(path.read_text(encoding="utf-8"))
        name = fm.get("name") or path.stem
        modes.append({"name": name, "description": fm.get("description", "")})
    return modes


def load_prompt(mode: str) -> str:
    """Load the agent prompt body for `mode` from its .md file."""
    path = AGENTS_DIR / f"{mode}.md"
    if not path.is_file():
        raise FileNotFoundError(f"no agent file for mode {mode!r}")
    _, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
    if not body:
        raise RuntimeError(f"agent file {path.name} has an empty prompt body")
    return body


# ---------------------------------------------------------------------------
# Reading transcripts (incl. .vtt / .srt cleanup)
# ---------------------------------------------------------------------------

_VTT_TS = re.compile(r"^\d{2}:\d{2}[:.]\d{2}.*-->")
_SRT_TS = re.compile(r"^\d{2}:\d{2}:\d{2},\d{3}\s*-->")
_TAG = re.compile(r"</?[cviub][^>]*>|<\d{2}:\d{2}:\d{2}\.\d{3}>")


def clean_transcript(raw: str, ext: str) -> str:
    """Strip WebVTT/SRT timing cruft so the LLM sees clean text."""
    if ext not in (".vtt", ".srt"):
        return raw
    lines_out: list[str] = []
    for line in raw.splitlines():
        s = line.strip()
        if not s:
            continue
        if s == "WEBVTT" or s.startswith(("NOTE", "STYLE", "REGION")):
            continue
        if _VTT_TS.match(s) or _SRT_TS.match(s):
            continue
        if s.isdigit():  # SRT cue index
            continue
        s = _TAG.sub("", s)
        if s:
            lines_out.append(s)
    cleaned = "\n".join(lines_out).strip()
    return cleaned or raw


# ---------------------------------------------------------------------------
# LLM invocation
# ---------------------------------------------------------------------------

# Some agent prompts (e.g. infographic) tell the model to WRITE its output to a
# file with the Write tool. That is wrong here: this server captures stdout and
# writes the file itself. Rather than *contradict* the prompt with an override
# (which the model can read as prompt injection and refuse), we strip the
# file-writing lines out and let the prompt simply ask for the result.
_WRITE_LINE_RE = re.compile(
    r"(?im)^.*(?:write (?:it|the file|the html|directly)|with the write tool|"
    r"write the file to the path|then confirm the path).*$\n?"
)


def sanitize_prompt(prompt: str, extra: str | None = None) -> str:
    """Remove 'write the file yourself' instructions so the model returns text.

    `extra`, if given, is the user's free-text instructions from the web UI; it
    is appended as an explicit, high-priority addendum the model must honor on
    top of the base agent prompt.
    """
    cleaned = _WRITE_LINE_RE.sub("", prompt).rstrip()
    if extra:
        cleaned += (
            "\n\n## Additional instructions from the user (high priority)\n"
            "Apply these on top of everything above. Where they conflict with the "
            "defaults, the user's instructions win:\n\n" + extra.strip()
        )
    return cleaned + (
        "\n\nReturn the complete result as plain text in your reply. "
        "Do not wrap it in a code fence."
    )


def run_claude(text: str, prompt: str, model: str | None = None,
               effort: str | None = None, timeout: int = LLM_TIMEOUT,
               extra: str | None = None, tools: str = "") -> str:
    if shutil.which("claude") is None:
        raise RuntimeError("claude CLI not found on PATH — install it and log in")

    # By default, no tools => the model cannot write files (no permission
    # prompts) and must return the result on stdout. `tools` may name read-only
    # tools to allow (e.g. "WebSearch,WebFetch" for travel-guide). --disallowedTools
    # always denies the write-capable ones, so even with web tools enabled the
    # model can't write files or run shell — it still reports on stdout.
    cmd = ["claude", "-p", sanitize_prompt(prompt, extra),
           "--output-format", "text",
           "--tools", tools,
           "--disallowedTools", "Write", "Edit", "NotebookEdit", "Bash"]
    if model:
        cmd += ["--model", model]
    if effort:
        cmd += ["--effort", effort]
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
    fence = re.match(r"^```(?:markdown|md|html)?\n(.*)\n```$", doc, re.DOTALL)
    if fence:
        doc = fence.group(1).strip()
    if len(doc) < 20:
        raise RuntimeError("claude CLI returned unusable output")
    return doc


def output_name_for(input_name: str, mode: str) -> str:
    """Derive the output filename from the input name + mode."""
    stem = Path(input_name).stem
    # Strip any previously appended mode suffix so re-processing an output
    # file doesn't accumulate suffixes (e.g. "foo-speaking-roleplay").
    known_suffixes = [
        "-organized", "-formatted", "-speaking", "-summary", "-roleplay",
        "-travel-guide", "-infographic-advanced", "-infographic", "-course-docs", "-speaking-practice",
    ]
    # Also handle bare mode-word stems (e.g. input file named "organized.md")
    bare_mode_words = {s.lstrip("-") for s in known_suffixes}
    for s in known_suffixes:
        if stem.endswith(s):
            stem = stem[: -len(s)]
            break
    # If the entire stem is a bare mode word with no base, drop the stem entirely
    if stem in bare_mode_words or stem == "":
        stem = ""
    suffix = MODE_SUFFIX.get(mode, f"-{mode}.md")
    if mode == "organize" and Path(input_name).suffix.lower() == ".md":
        suffix = "-organized.md"
    if stem == "":
        suffix = suffix.lstrip("-")
    return f"{stem}{suffix}"


def process_one(mode: str, text: str, filename: str, model: str | None,
                effort: str | None, extra: str | None) -> dict:
    """Run a single agent over `text` and write its output file.

    Returns a per-agent result dict (never raises) so that one failing agent
    in a multi-agent batch doesn't abort the others.
    """
    try:
        prompt = load_prompt(mode)
        tools = MODE_TOOLS.get(mode, "")
        result = run_claude(text, prompt, model=model, effort=effort,
                            extra=extra, tools=tools)
        out_path = OUTPUT_DIR / output_name_for(filename, mode)
        out_path.write_text(result, encoding="utf-8")
        return {
            "mode": mode,
            "ok": True,
            "outputPath": str(out_path),
            "isHtml": out_path.suffix.lower() == ".html",
            "content": result,
        }
    except Exception as exc:  # noqa: BLE001
        return {"mode": mode, "ok": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# Minimal multipart/form-data parser (stdlib only; `cgi` is gone in 3.13)
# ---------------------------------------------------------------------------

def parse_multipart(body: bytes, content_type: str) -> dict:
    """Parse a multipart/form-data body into {field: value}.

    Text fields decode to str; the uploaded file maps to a dict
    {filename, content (bytes)}. Good enough for this tiny single-file form.
    """
    m = re.search(r"boundary=([^;]+)", content_type)
    if not m:
        raise RuntimeError("missing multipart boundary")
    boundary = b"--" + m.group(1).strip().strip('"').encode()
    fields: dict = {}
    for part in body.split(boundary):
        if not part or part in (b"--\r\n", b"--"):
            continue
        part = part.strip(b"\r\n")
        if b"\r\n\r\n" not in part:
            continue
        header_blob, _, data = part.partition(b"\r\n\r\n")
        headers = header_blob.decode("utf-8", "replace")
        name_m = re.search(r'name="([^"]+)"', headers)
        if not name_m:
            continue
        name = name_m.group(1)
        file_m = re.search(r'filename="([^"]*)"', headers)
        if file_m:
            fields[name] = {"filename": file_m.group(1), "content": data}
        else:
            fields[name] = data.decode("utf-8", "replace").strip()
    return fields


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # quieter logging
        sys.stderr.write("[webui] " + (fmt % args) + "\n")

    def _send_json(self, payload: dict, status: int = 200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            try:
                body = INDEX_HTML.read_bytes()
            except OSError:
                self._send_json({"error": "index.html missing"}, 500)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path == "/api/config":
            try:
                # Only offer agents that are actually runnable here (present in
                # MODE_SUFFIX). debate-prep and the agent-reviewer meta-agent are
                # discovered but intentionally not wired into the web UI.
                runnable = [m for m in list_modes() if m["name"] in MODE_SUFFIX]
                self._send_json({
                    "modes": runnable,
                    "models": MODELS,
                    "efforts": EFFORTS,
                    "sourceExts": sorted(SOURCE_EXTS),
                    "outputDir": str(OUTPUT_DIR),
                })
            except Exception as exc:  # noqa: BLE001
                self._send_json({"error": str(exc)}, 500)
            return

        self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path != "/api/process":
            self._send_json({"error": "not found"}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else b""
            fields = parse_multipart(body, self.headers.get("Content-Type", ""))

            # Accept one or more agents. `modes` is the multi-agent field
            # (comma-separated); `mode` is kept as a single-agent fallback.
            modes_raw = (fields.get("modes") or fields.get("mode") or "").strip()
            model = (fields.get("model") or "").strip() or None
            effort = (fields.get("effort") or "").strip() or None
            extra = (fields.get("extra") or "").strip() or None
            file_part = fields.get("file")

            if extra and len(extra) > 4000:
                self._send_json({"error": "extra instructions too long (max 4000 chars)"}, 400)
                return

            seen: set[str] = set()
            modes = [m.strip() for m in modes_raw.split(",") if m.strip()]
            modes = [m for m in modes if not (m in seen or seen.add(m))]
            if not modes:
                self._send_json({"error": "no agent selected"}, 400)
                return
            unknown = [m for m in modes if m not in MODE_SUFFIX]
            if unknown:
                self._send_json({"error": f"unknown mode(s): {', '.join(unknown)}"}, 400)
                return
            if effort and effort not in VALID_EFFORTS:
                self._send_json({"error": f"unknown effort: {effort!r}"}, 400)
                return
            if not isinstance(file_part, dict) or not file_part.get("filename"):
                self._send_json({"error": "no file uploaded"}, 400)
                return

            filename = Path(file_part["filename"]).name
            ext = Path(filename).suffix.lower()
            if ext not in SOURCE_EXTS:
                self._send_json(
                    {"error": f"unsupported file type {ext!r}; "
                              f"expected one of {', '.join(sorted(SOURCE_EXTS))}"}, 400)
                return

            raw = file_part["content"].decode("utf-8", "replace")
            text = clean_transcript(raw, ext)
            if len(text.strip()) < 5:
                self._send_json({"error": "file is empty or unreadable"}, 400)
                return

            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            # Save a copy of the input next to the output(s).
            (OUTPUT_DIR / filename).write_text(raw, encoding="utf-8")

            # Run the selected agents. One is run inline; several run in a
            # bounded thread pool so independent `claude -p` processes overlap.
            # ThreadPoolExecutor.map preserves the input order of `modes`.
            if len(modes) == 1:
                results = [process_one(modes[0], text, filename, model, effort, extra)]
            else:
                with ThreadPoolExecutor(max_workers=min(len(modes), MAX_PARALLEL)) as ex:
                    results = list(ex.map(
                        lambda m: process_one(m, text, filename, model, effort, extra),
                        modes,
                    ))

            overall_ok = any(r["ok"] for r in results)
            self._send_json({
                "ok": overall_ok,
                "model": model,
                "effort": effort,
                "results": results,
            }, 200 if overall_ok else 500)
        except Exception as exc:  # noqa: BLE001
            self._send_json({"ok": False, "error": str(exc)}, 500)


def main():
    if not AGENTS_DIR.is_dir():
        sys.exit(f"agents dir not found: {AGENTS_DIR}")
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}"
    print(f"[webui] serving transcript agents at {url}")
    print(f"[webui] outputs are saved to {OUTPUT_DIR}")
    print("[webui] press Ctrl-C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[webui] stopping")
        server.shutdown()


if __name__ == "__main__":
    main()
