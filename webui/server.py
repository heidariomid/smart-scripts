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
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8765
LLM_TIMEOUT = 480  # infographic / travel-guide can be slow

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
    "course-docs": "-course-docs.md",
    "passive-to-active-english": "-speaking-practice.md",
}

# Model aliases offered in the UI. Aliases are accepted by `claude --model` and
# always resolve to the latest model in each tier, so they stay correct as the
# CLI updates.
MODELS = [
    {"alias": "opus", "label": "Opus 4.8 (most capable)"},
    {"alias": "sonnet", "label": "Sonnet 4.6 (balanced)"},
    {"alias": "haiku", "label": "Haiku 4.5 (fastest)"},
]

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
# LLM invocation (mirrors smart_transcript.py organize_with_llm)
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


def sanitize_prompt(prompt: str) -> str:
    """Remove 'write the file yourself' instructions so the model returns text."""
    cleaned = _WRITE_LINE_RE.sub("", prompt)
    return cleaned.rstrip() + (
        "\n\nReturn the complete result as plain text in your reply. "
        "Do not wrap it in a code fence."
    )


def run_claude(text: str, prompt: str, model: str | None = None,
               timeout: int = LLM_TIMEOUT) -> str:
    if shutil.which("claude") is None:
        raise RuntimeError("claude CLI not found on PATH — install it and log in")

    # No tools => the model cannot write files (no permission prompts) and must
    # return the result on stdout. --tools "" disables tools; --disallowedTools
    # additionally denies the write-capable ones so the model reports cleanly
    # instead of emitting stray function-call text.
    cmd = ["claude", "-p", sanitize_prompt(prompt),
           "--output-format", "text",
           "--tools", "",
           "--disallowedTools", "Write", "Edit", "NotebookEdit", "Bash"]
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
    # file doesn't accumulate prefixes (e.g. "foo-organized-speaking-practice").
    known_suffixes = [
        "-organized", "-formatted", "-speaking", "-summary", "-roleplay",
        "-travel-guide", "-infographic", "-course-docs", "-speaking-practice",
    ]
    for s in known_suffixes:
        if stem.endswith(s):
            stem = stem[: -len(s)]
            break
    suffix = MODE_SUFFIX.get(mode, f"-{mode}.md")
    if mode == "organize" and Path(input_name).suffix.lower() == ".md":
        suffix = "-formatted.md"
    return f"{stem}{suffix}"


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
                self._send_json({
                    "modes": list_modes(),
                    "models": MODELS,
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

            mode = (fields.get("mode") or "").strip()
            model = (fields.get("model") or "").strip() or None
            file_part = fields.get("file")

            if mode not in MODE_SUFFIX:
                self._send_json({"error": f"unknown mode: {mode!r}"}, 400)
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
            # Save a copy of the input next to the output.
            (OUTPUT_DIR / filename).write_text(raw, encoding="utf-8")

            prompt = load_prompt(mode)
            result = run_claude(text, prompt, model=model)

            out_path = OUTPUT_DIR / output_name_for(filename, mode)
            out_path.write_text(result, encoding="utf-8")

            self._send_json({
                "ok": True,
                "mode": mode,
                "model": model,
                "outputPath": str(out_path),
                "isHtml": out_path.suffix.lower() == ".html",
                "content": result,
            })
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
