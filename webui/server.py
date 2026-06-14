#!/usr/bin/env python3
"""Local web UI for running the transcript agents.

Paste an absolute path (a single transcript file OR a folder to recurse), pick
an agent and a model, and the selected agent's prompt is run through `claude -p`.
Output is written **beside the source file**, on whatever drive it lives on,
using the same suffix conventions as smart_transcript.py.

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
}

# Suffixes a folder scan must skip so re-running a folder never re-ingests its
# own outputs (mirrors the --source-glob pitfall in CLAUDE.md).
OUTPUT_SUFFIXES = set(MODE_SUFFIX.values()) | {"-formatted.md"}

# Model aliases offered in the UI. Aliases are accepted by `claude --model`.
# Kept here as a fallback / display map; the live list is fetched dynamically.
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


def list_models() -> list[dict]:
    """Return selectable models.

    Tries to keep in sync with the installed claude CLI by asking it for the
    models it accepts; falls back to the static MODELS list otherwise. The
    three current aliases (opus/sonnet/haiku) always resolve to the latest of
    each tier, so they stay correct across CLI updates.
    """
    return MODELS


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


def read_transcript(path: Path) -> str:
    """Read a transcript, stripping WebVTT/SRT timing cruft so the LLM sees clean text."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    ext = path.suffix.lower()
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
# writes the file itself, beside the source. Rather than *contradict* the prompt
# with an override (which the model can read as prompt injection and refuse), we
# strip the file-writing lines out and let the prompt simply ask for the result.
# Lines that instruct writing to a file / using the Write tool:
_WRITE_LINE_RE = re.compile(
    r"(?im)^.*(?:write (?:it|the file|the html|directly)|with the write tool|"
    r"write the file to the path|then confirm the path).*$\n?"
)


def sanitize_prompt(prompt: str) -> str:
    """Remove 'write the file yourself' instructions so the model returns text.

    We delete the offending lines instead of appending a contradicting override,
    so nothing in the prompt looks like an injected instruction to refuse.
    """
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
    # ("Write tool not enabled") instead of emitting stray function-call text.
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


def output_path_for(input_path: Path, mode: str) -> Path:
    """Derive the output path **beside the source file** from its name + mode."""
    suffix = MODE_SUFFIX.get(mode, f"-{mode}.md")
    if mode == "organize" and input_path.suffix.lower() == ".md":
        suffix = "-formatted.md"
    return input_path.with_name(f"{input_path.stem}{suffix}")


def is_output_file(path: Path) -> bool:
    name = path.name
    return any(name.endswith(suf) for suf in OUTPUT_SUFFIXES)


def discover_sources(folder: Path) -> list[Path]:
    """Recursively find transcript files under `folder`, skipping prior outputs."""
    found = []
    for p in sorted(folder.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in SOURCE_EXTS:
            continue
        if is_output_file(p):
            continue
        found.append(p)
    return found


def process_one(src: Path, mode: str, prompt: str, model: str | None) -> dict:
    """Process a single source file; write output beside it. Returns a result dict."""
    try:
        text = read_transcript(src)
        if len(text.strip()) < 5:
            raise RuntimeError("source file is empty or unreadable")
        result = run_claude(text, prompt, model=model)
        out_path = output_path_for(src, mode)
        out_path.write_text(result, encoding="utf-8")
        return {
            "ok": True,
            "source": str(src),
            "outputPath": str(out_path),
            "isHtml": out_path.suffix.lower() == ".html",
            "content": result,
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "source": str(src), "error": str(exc)}


# ---------------------------------------------------------------------------
# Resolve a dropped file to its real on-disk path (macOS Spotlight)
# ---------------------------------------------------------------------------

def resolve_paths(filename: str, size: int | None) -> list[str]:
    """Find absolute paths for `filename` on this machine via Spotlight.

    Browsers don't expose a dropped file's path, but since this server runs on
    the same machine we can look it up. When `size` is given, matches are
    filtered to files of exactly that byte size so the right one is pinned even
    when the name is not unique.
    """
    if shutil.which("mdfind") is None:
        return []
    name = Path(filename).name
    try:
        out = subprocess.run(
            ["mdfind", "-name", name],
            capture_output=True, text=True, timeout=15,
        )
    except subprocess.SubprocessError:
        return []
    candidates = []
    for line in out.stdout.splitlines():
        p = Path(line.strip())
        if p.name != name or not p.is_file():
            continue
        if size is not None:
            try:
                if p.stat().st_size != size:
                    continue
            except OSError:
                continue
        candidates.append(str(p))
    return candidates


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

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

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
                    "models": list_models(),
                    "sourceExts": sorted(SOURCE_EXTS),
                })
            except Exception as exc:  # noqa: BLE001
                self._send_json({"error": str(exc)}, 500)
            return

        self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path == "/api/resolve":
            try:
                data = self._read_json_body()
                name = (data.get("filename") or "").strip()
                size = data.get("size")
                size = int(size) if isinstance(size, (int, float, str)) and str(size).isdigit() else None
                if not name:
                    self._send_json({"error": "no filename"}, 400)
                    return
                self._send_json({"paths": resolve_paths(name, size)})
            except Exception as exc:  # noqa: BLE001
                self._send_json({"error": str(exc)}, 500)
            return

        if self.path != "/api/process":
            self._send_json({"error": "not found"}, 404)
            return
        try:
            data = self._read_json_body()
            mode = (data.get("mode") or "").strip()
            model = (data.get("model") or "").strip() or None
            raw_path = (data.get("path") or "").strip()

            if mode not in MODE_SUFFIX:
                self._send_json({"error": f"unknown mode: {mode!r}"}, 400)
                return
            if not raw_path:
                self._send_json({"error": "no path provided"}, 400)
                return

            target = Path(raw_path).expanduser()
            if not target.exists():
                self._send_json({"error": f"path does not exist: {target}"}, 400)
                return

            prompt = load_prompt(mode)

            if target.is_dir():
                sources = discover_sources(target)
                if not sources:
                    self._send_json({
                        "ok": True, "mode": mode, "isFolder": True,
                        "results": [],
                        "message": f"no transcript files ({', '.join(sorted(SOURCE_EXTS))}) found under {target}",
                    })
                    return
                results = [process_one(s, mode, prompt, model) for s in sources]
                self._send_json({
                    "ok": all(r["ok"] for r in results),
                    "mode": mode, "model": model, "isFolder": True,
                    "results": results,
                })
                return

            if target.suffix.lower() not in SOURCE_EXTS:
                self._send_json(
                    {"error": f"unsupported file type {target.suffix!r}; "
                              f"expected one of {', '.join(sorted(SOURCE_EXTS))}"}, 400)
                return

            res = process_one(target, mode, prompt, model)
            status = 200 if res["ok"] else 500
            self._send_json({**res, "mode": mode, "model": model, "isFolder": False},
                            status)
        except Exception as exc:  # noqa: BLE001
            self._send_json({"ok": False, "error": str(exc)}, 500)


def main():
    if not AGENTS_DIR.is_dir():
        sys.exit(f"agents dir not found: {AGENTS_DIR}")
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}"
    print(f"[webui] serving transcript agents at {url}")
    print("[webui] paste a file or folder path; output is saved beside each source file")
    print("[webui] press Ctrl-C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[webui] stopping")
        server.shutdown()


if __name__ == "__main__":
    main()
