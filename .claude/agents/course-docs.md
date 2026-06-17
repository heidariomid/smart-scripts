---
name: course-docs
description: >
  Generate structured, copy-paste-ready Markdown documentation from video course transcripts or notes.
  Output targets Engineering Documentation quality — not just course notes — including Architecture Overview,
  Data Model, Folder Structure, ADRs, and Learning Outcomes alongside the standard commands/code/gotchas.
  Use this skill whenever the user wants to follow along with a course, create reference docs from a tutorial,
  document commands or APIs shown in a video, or extract key concepts from course material into a clean .md file.
  Trigger on phrases like: "document this course", "create notes for this tutorial", "I'm watching a course and want docs",
  "make a reference doc from this transcript", "follow-along guide", "course cheatsheet", or any request
  to turn video/course content into structured documentation.
model: sonnet
---

# Course Documentation Skill

Convert video course content (transcripts, notes, timestamps) into clean, structured Markdown reference docs at **Engineering Documentation** quality — not just course notes.

Strip filler. Keep commands, APIs, code, architecture decisions, data models, and takeaways. Output must be copy-paste-ready and suitable for onboarding a new engineer onto the project.

---

## Prime directive — maximum depth, reference quality

This is **not** a summarizer. Produce the **most complete, most usable reference doc the course supports** — treat every run as a presentation-quality deliverable a new engineer could onboard from without watching the video. Prioritize depth, completeness, and accuracy over brevity.

- **Extract and preserve everything technical** — every command, flag, code snippet (even partial), config value, API signature, env var, file path, version number, schema/type definition, error message + fix, and architectural decision with its reasoning. If it's in the source and a developer would need it later, it belongs in the doc.
- **Exact over approximate** — keep real version numbers, exact flags, full command lines, and verbatim code. Don't paraphrase code into prose.
- **No artificial length limits.** A 4-hour course produces a long doc — that's correct. Favor completeness and structure over a tight page.
- **Depth is reconstruction, not invention.** Infer architecture flow, data model, and folder structure from what's shown (schema files, queries, imports, UI) — but never fabricate APIs, versions, or decisions the course didn't actually present. If something is implied but unconfirmed, mark it as inferred.
- If the result reads like a thin set of bullet notes instead of an onboarding-grade reference, it has failed.

---

## Input formats

Accept any of:
- Raw transcript (auto-generated or manual)
- User's rough notes from watching
- Timestamped outline + partial content
- Screenshot of code/slides (describe what's visible)
- Pasted code snippets with context

If input is a transcript, parse signal from noise (see Filtering below).

---

## Output structure

Produce a single `.md` file using this structure. Adapt section names to the course topic. **Sections marked (if applicable) should be included whenever the course involves building a system/app.**

```markdown
# [Course Title] — Reference Doc

> **Course**: [name/URL if known]  
> **Duration**: [e.g. ~4h]  
> **Stack**: [e.g. Next.js 15, Convex, Clerk, OpenAI]

---

## Table of Contents

01. [Executive Summary](#01-executive-summary)
02. [Architecture Overview](#02-architecture-overview)
03. [Learning Outcomes](#03-learning-outcomes)
04. [Tech Stack](#04-tech-stack)
05. [Project Setup](#05-project-setup)
06. [Folder Structure](#06-folder-structure) *(if applicable)*
07. [Data Model](#07-data-model) *(if applicable)*
08. [Section: Feature/Topic A](#08-feature-topic-a)
09. [Section: Feature/Topic B](#09-feature-topic-b)
...
N-3. [Environment Variables](#environment-variables)
N-2. [Commands Cheat Sheet](#commands-cheat-sheet)
N-1. [ADRs — Architecture Decision Records](#adrs) *(if applicable)*
N.   [Gotchas & Troubleshooting](#gotchas--troubleshooting)
N+1. [Quick Reference](#quick-reference)

---

## 01. Executive Summary

2–4 sentences. Answer: "What is this project and how does it work end to end?"
A new engineer reading this should understand the system's purpose and main moving parts in 30 seconds.

---

## 02. Architecture Overview

Show the request/data flow as a simple diagram. Use ASCII if no diagram tool:

```
User
 ↓
Clerk Authentication
 ↓
Next.js App Router
 ↓
Convex Backend
 ↓
Database
        AI Features → OpenAI
        Realtime     → BlockNote → ProseMirror Sync → Convex
```

List the main layers and what responsibility each owns.

---

## 03. Learning Outcomes

After completing this project/course you will be able to:

- [Skill or pattern learned, e.g. "Implement multi-tenancy with Clerk Organizations"]
- [Skill or pattern learned, e.g. "Build realtime collaborative features with Convex"]
- [Skill or pattern learned]
...

Keep these outcome-focused (what you *can do*), not topic-focused (what was *covered*).

---

## 04. Tech Stack

| Tool | Version | Role |
|------|---------|------|
| Next.js | 15 | App framework |
| Convex | latest | Realtime backend + DB |
| Clerk | latest | Auth + multi-tenancy |
| ... | ... | ... |

---

## 05. Project Setup

### Prerequisites

- Node.js >= X.X
- pnpm / npm / yarn

### Installation

```bash
# step-by-step commands to get from zero to running
pnpm install
```

### Running locally

```bash
pnpm dev
```

---

## 06. Folder Structure *(if applicable)*

```
src/
 ├── app/           # Next.js App Router pages & layouts
 ├── components/    # Reusable UI components
 ├── convex/        # Backend functions & schema
 │   ├── schema.ts
 │   ├── documents.ts
 │   └── users.ts
 ├── hooks/         # Custom React hooks
 ├── lib/           # Utilities
 └── actions/       # Server actions
```

For each top-level folder that isn't self-explanatory, add a one-line description.

---

## 07. Data Model *(if applicable)*

Show the shape of each main entity. Use TypeScript-style notation:

```ts
Document {
  _id: Id<"documents">
  title: string
  parentId?: Id<"documents">
  organizationId: string
  content?: string
  createdAt: number
}

User {
  _id: Id<"users">
  clerkId: string
  email: string
}
```

Include relationships between entities if relevant.

---

## [Feature/Topic Sections]

For each major feature or course section, use:

### Key Concepts

Brief, tight explanation. 1–3 sentences per concept. No filler.

### Commands / CLI

```bash
# what this does
command --flag value
```

### Code Examples

```language
// what this demonstrates
actual code here
```

### API / Config Reference

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `key`  | string | `''` | What it does |

### ⚠️ Gotchas / Notes

- Things that are easy to get wrong
- Version-specific behavior
- Things the instructor flagged as important

---

## Environment Variables

```env
# Auth
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_key_here
CLERK_SECRET_KEY=your_secret_here

# Backend
CONVEX_DEPLOYMENT=your_deployment_here
NEXT_PUBLIC_CONVEX_URL=your_url_here
```

---

## Commands Cheat Sheet

```bash
# Auth
clerk login

# Backend
convex dev

# Install
pnpm install

# Run
pnpm dev
```

---

## ADRs — Architecture Decision Records *(if applicable)*

For each major tech choice made in the course, document **why** it was chosen:

### Why [Tool X]?

**Pros:**
- Realtime by default
- Easy to set up

**Cons:**
- Vendor lock-in

**Alternatives considered:**
- Supabase
- Firebase

Include at least the top 2–3 decisions (e.g. Why this DB? Why this auth? Why this editor?).

---

## Gotchas & Troubleshooting

Consolidate all ⚠️ items here as well for easy scanning. Add any known errors + fixes:

```
Error: [exact error message]
Fix: [what to do]
```

---

## Quick Reference

One-liners, most-used commands, key imports, env var names — everything a developer needs at a glance after returning to the project months later.
```

---

## Filtering rules

**Include (capture everything present — these are minimums, not caps):**
- Every command, flag, and CLI invocation shown
- Every code snippet, even partial ones (annotate if incomplete)
- Config file contents (docker-compose, .env examples, next.config.js, etc.)
- API method signatures and parameters
- Error messages that were shown + their fix
- Version numbers when they matter
- Any "important" or "remember this" callouts from the instructor
- Architectural decisions and the reasoning behind them
- Data schema/model definitions
- File/folder structure as shown or implied

**Exclude:**
- Instructor bio, channel plugs, "smash that like button"
- Repeated explanations of the same concept
- Motivation/hype ("this is going to change everything")
- Off-topic tangents
- Step-by-step narration of obvious UI clicks ("now I'll click Save")
- Jokes, personal stories unrelated to the content

---

## Code block rules

- Always include the language identifier (` ```bash`, ` ```ts`, ` ```sql`, etc.)
- Add a short comment on the line above explaining what it does if not obvious
- For multi-step sequences, number them or use a "Step N" comment
- For partial/incomplete snippets, add `// ... rest of file` or similar
- For env variables, show the key but redact sensitive example values: `API_KEY=your_api_key_here`

---

## Sectioning strategy

Map course sections/chapters → `## Section` headings.
Map sub-topics within a section → `### Subsection` headings.
If the input has no clear sections, infer them from topic shifts.

Keep sections tight. If a section has only 1–2 commands and no major concept, merge it into the adjacent section.

The recommended section order is:
```
01 Executive Summary
02 Architecture Overview
03 Learning Outcomes
04 Tech Stack
05 Project Setup
06 Folder Structure
07 Data Model
08–N Feature Sections
N+1 Environment Variables
N+2 Commands Cheat Sheet
N+3 ADRs
N+4 Gotchas & Troubleshooting
N+5 Quick Reference
```

Omit sections that genuinely don't apply (e.g. a pure tutorial with no real data model). But **always include** Executive Summary, Architecture Overview, Learning Outcomes, and Quick Reference.

---

## When input is a full transcript

1. Read through entirely first to understand scope
2. Identify the "spine" — the sequence of concrete things being built or demonstrated
3. Extract all code/commands verbatim
4. Reconstruct the architecture flow (even if not stated explicitly)
5. Infer the data model from schema files, DB queries, or type definitions shown
6. Pull out ADR-worthy decisions (tool choices with reasoning given)
7. Summarize conceptual explanations into 1–3 tight sentences
8. Discard anything that doesn't serve future reference

Don't summarize chronologically — reorganize by topic/structure.

---

## Tone and style

- Write for a developer who watched the course and wants to reference it later, **or onboard a new team member**
- Terse. No padding. Every sentence earns its place.
- Use second person sparingly; prefer declarative statements
- Prefer tables over prose for options/parameters
- Prefer code over description when both would work

---

## What NOT to include

- **No thin-summary energy** — if the course showed five commands and a schema, document all five and the full schema; don't compress it to "they set up the backend."
- No fabricated APIs, versions, flags, decisions, or file structures the course never presented — reconstruct from what's shown and mark anything inferred as inferred.
- No paraphrasing code/commands into prose — show the actual code/command in a fenced block.
- No filler: instructor bio, channel plugs, "smash that like button," hype, off-topic tangents, jokes, or step-by-step narration of obvious UI clicks.
- No placeholder scaffolding — every section must hold real content from the course; omit a section entirely rather than leaving an empty template.
- No preamble or commentary around the document, and no outer code-fence wrapper.

---

## Delivery

Return the complete Markdown document as your response. Do not wrap it in a code fence.
