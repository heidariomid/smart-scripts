# Plan: Infographic Agent + MCP Research

## Context

The user wants to visualize transcripts (like `sub.txt`) as self-contained HTML infographics. No dedicated agent exists for this yet. The question is: do we need an MCP, and if so which one — then create the `infographic` agent.

---

## MCP Research Findings

### Option A — No MCP (Recommended for HTML infographics)
Claude can write complete, self-contained HTML/CSS/JS infographics directly without any MCP. For a transcript-to-infographic use case this is the **simplest and most portable** path: output is one `.html` file, opens in any browser, zero dependencies, no API keys.

### Option B — `@antv/mcp-server-chart` (Best if charts needed)
- **npm**: `@antv/mcp-server-chart` · 136K downloads · 3.3K GitHub stars
- **Install**: `npx @antv/mcp-server-chart`
- **Supports**: 26+ chart types (bar, line, pie, radar, heatmap, fishbone…)
- **Best for**: Embedding rendered chart images inside an infographic
- **Trade-off**: Generates chart images, not full-page HTML infographics

### Option C — `napkin-ai-mcp` (Best professional infographics)
- **npm**: `napkin-ai-mcp`
- **Output**: SVG / PNG / PPT from text — mindmaps, timelines, comparisons
- **Trade-off**: Requires Napkin.AI API key; currently in developer preview

### Option D — Mermaid MCPs
- Good for flowcharts/architecture diagrams, not rich HTML infographics.
- Not a fit here.

---

## Recommendation

**For this project**: No MCP needed. The `infographic` agent generates a self-contained HTML file directly. If the user later wants embedded charts, add `@antv/mcp-server-chart` and update the agent to call it.

---

## What to build

Create `.claude/agents/infographic.md` — an agent that:

1. **Extracts** structured data from the transcript: key stats, timeline, places, costs, highlights, verdict
2. **Designs** a single-page HTML infographic with:
   - Embedded CSS (no external dependencies)
   - Section cards, stat callouts, color bands, timeline strip
   - Unicode icons (no external icon fonts)
3. **Outputs** one self-contained `.html` file (e.g. `sub-infographic.html`) the user can open in any browser

**Trigger phrases** (to add to CLAUDE.md routing table):
- "infographic", "visualize", "HTML visual", "make a graphic", "visual summary"

**Output suffix**: `-infographic.html`

---

## Files to create/edit

| File | Change |
|---|---|
| `.claude/agents/infographic.md` | Create new agent |
| `CLAUDE.md` | Add `infographic` row to the Agent routing table |

## Verification

1. Invoke agent on `sub.txt` — confirm `sub-infographic.html` is written
2. Open in browser — confirm it renders without errors, no external requests
3. Check CLAUDE.md routing fires automatically on "visualize this"
