Upgrade the remaining agent prompt files in .claude/agents/ to bake in the same "maximum depth, completeness, and visual/structural richness" standard that .claude/agents/infographic.md now sets. infographic.md is the GOLD STANDARD — read it first and mirror its approach (adapted to each agent's output format).

Agents to upgrade (skip infographic.md, README.md): summary, speaking, organize, roleplay, travel-guide, course-docs, passive-to-active-english, debate-prep

For EACH agent, adapt (don't blindly copy) infographic.md's four moves to that agent's job:

1. A "Prime directive — maximum depth" header: this is NOT a summarizer; extract and preserve as much substantive content as possible (details, context, stats, names, exact numbers, quotes, examples, relationships); no artificial length limits; "if the result reads like a thin summary, it has failed." (EXCEPTION: `summary` is intentionally a tight single recap — for it, deepen QUALITY/faithfulness/coverage, NOT length. Don't turn it into a long doc.)
2. Step-1 extraction guidance with "capture everything present — these are minimums, not caps."
3. A richer, multi-section output menu with "lean toward more coverage, not less," every section holding real source content (no placeholders).
4. An explicit "What NOT to include" anti-thin-summary / anti-filler block.

HARD CONSTRAINTS — do not break these:

- The web UI (webui/server.py) strips any line matching "write the file / with the Write tool / then confirm the path" via \_WRITE_LINE_RE, then runs the model with no tools so it returns text on stdout. Keep each agent's file-writing instruction on its OWN line so it strips cleanly. After editing, verify with the sanitizer (see below).
- Output suffixes are fixed in MODE_SUFFIX (server.py): only infographic is .html; all others are .md. Do NOT change an agent's output format contract.
- speaking.md is mirrored by SPEAKING_PROMPT in smart_transcript.py — if you change speaking.md's spec, update that constant too (or flag the divergence).
- Preserve each agent's frontmatter (name, description, model) and its core output structure — you're deepening the standard, not redesigning the task.

Process: do them ONE AT A TIME. For each, read the current file, rewrite it, then run the server's sanitizer to confirm the write-instruction still strips and no contradictory lines remain:

python3 -c "import sys; sys.path.insert(0,'webui'); import server; \
 p=server.sanitize_prompt(server.load_prompt('AGENT_NAME')); \
 assert 'with the Write tool' not in p and 'then confirm the path' not in p; \
 print('AGENT_NAME sanitizes clean')"

When all 8 are done, restart the web UI and confirm /api/config still lists all agents: lsof -ti tcp:8765 | xargs kill -9; python3 webui/server.py & sleep 2; \
 curl -s http://127.0.0.1:8765/api/config | python3 -m json.tool | head -40

Show me a one-line before/after (line count + what changed) for each agent at the end. Do NOT commit — leave changes in the working tree for me to review.
