# Milestone 3: BuilderIO Skills Audit & Inventory Report

**Subagent**: `teamwork_preview_explorer_m3_1` (Explorer)  
**Milestone**: Milestone 3 — BuilderIO Skills Audit & Inventory  
**Working Directory**: `/Users/rmanaloto/agy-graphify-research/.agents/teamwork_preview_explorer_m3_1`  
**Date**: 2026-07-31  

---

## 1. Executive Summary

As the Explorer subagent for Milestone 3, I conducted a genuine, comprehensive audit of the official **`BuilderIO/skills`** repository (https://github.com/BuilderIO/skills). The repository was cloned locally into `scratch/builderio_skills` via `git clone --depth 1 https://github.com/BuilderIO/skills.git /Users/rmanaloto/agy-graphify-research/scratch/builderio_skills`.

### Key Findings
1. **Total Skills Audited**: Exactly **12 user-facing skills** under `skills/`, plus **1 internal meta-skill** under `.agents/skills/adding-a-skill`.
2. **Visual Skills Identified**:
   - `visual-plan` (MDX visual planning, flowcharts, architecture diagrams, wireframes)
   - `visual-recap` (Git diff & PR visual summarization, schema/API diff maps)
   - `visual-edit` (Live localhost app iframe overview canvas & visual editing bridge)
3. **Workflow & Governance Skills Identified**:
   - `agent-watchdog` (Cross-agent auditing and gap verification)
   - `efficient-fable` (Claude Fable orchestration with cheaper helper subagents)
   - `efficient-frontier` (Frontier model delegation architecture)
   - `plan-arbiter` (Multi-agent plan comparison & arbitration)
   - `plow-ahead` (Autonomous ambiguity resolution)
   - `quick-recap` (Red/yellow/green final status block convention)
   - `read-the-damn-docs` (Documentation-first web search discipline)
   - `rewind` (Clips Rewind local screen memory MCP integration)
   - `stay-within-limits` (Usage limit & rate limit wave throttling)
4. **Documentation & Inventory Deliverable**: `docs/builderio_skills_inventory.md` has been authored and created in the workspace, covering 100% of all audited skills.
5. **Project-Scoped Porting Plan**: Visual skills will be ported strictly to project directories (`.gemini/skills/` and `.agents/skills/`) without modifying global `~/.codex` or `~/.gemini`.

---

## 2. Comprehensive Inventory of BuilderIO Skills (100% Coverage)

| # | Skill Name | Category | Primary Purpose & Trigger Keywords | Key Files | Visual? |
| :-: | :--- | :--- | :--- | :--- | :-: |
| 1 | `visual-plan` | Visual Presentation | Turn ordinary text plans into rich interactive visual plans with diagrams, file maps, annotated code, and wireframe/prototype reviews. | `SKILL.md`, `README.md`, `references/canvas.md`, `references/connection.md`, `references/document-quality.md`, `references/exemplar.md`, `references/local-files.md`, `references/wireframe.md` | **YES** |
| 2 | `visual-recap` | Visual Presentation | Turn PRs, commits, or git diffs into interactive visual recaps with diagrams, file maps, API/schema summaries, and UI state summaries. | `SKILL.md`, `README.md`, `references/connection.md`, `references/local-files.md`, `references/wireframe.md` | **YES** |
| 3 | `visual-edit` | UI Generation | Open a running local app in Design overview mode as URL-backed iframe screens for visual editing and route-state exploration. | `SKILL.md`, `README.md` | **YES** |
| 4 | `agent-watchdog` | Audit & Review | Audit, watch, review, or fix another agent's work from a Codex session ID, Claude Code transcript, PR, or branch. | `SKILL.md`, `README.md`, `agents/openai.yaml` | NO |
| 5 | `efficient-fable` | Orchestration | Use Claude Fable as orchestrator while cheaper subagents handle token-heavy research, coding, testing, and summarization. | `SKILL.md`, `README.md`, `assets/fable-orchestrator.excalidraw`, `assets/fable-orchestrator.png` | NO |
| 6 | `efficient-frontier` | Orchestration | Apply frontier-model delegation (expensive model plans/reviews, cheaper subagents execute) to any high-cost frontier model. | `SKILL.md`, `README.md` | NO |
| 7 | `plan-arbiter` | Arbitration | Compare, cross-review, judge, merge, or arbitrate competing plans from multiple agents (Codex vs. Claude Code). | `SKILL.md`, `README.md`, `agents/openai.yaml` | NO |
| 8 | `plow-ahead` | Autonomous Execution | Proceed through ordinary ambiguity with conservative assumptions, completing execution and validation without clarification stops. | `SKILL.md`, `README.md`, `agents/openai.yaml` | NO |
| 9 | `quick-recap` | Response Convention | Add red/yellow/green status blocks (`🔴`/`🟡`/`🟢`) to the end of agent responses to communicate completion state clearly. | `SKILL.md`, `README.md` | NO |
| 10 | `read-the-damn-docs` | Docs Discipline | Force agents to web-search official documentation for external APIs, SDKs, CLIs, and cloud services before assuming from memory. | `SKILL.md`, `README.md`, `agents/openai.yaml` | NO |
| 11 | `rewind` | Context Memory | Retrieve local screen context from Clips Rewind screen memory MCP when asked "what just happened". | `SKILL.md`, `README.md` | NO |
| 12 | `stay-within-limits` | Budget Management | Track active 5-hour and weekly usage limits between waves of subagents, pausing execution at 95% threshold. | `SKILL.md`, `README.md` | NO |
| 13 | `adding-a-skill` | Repository Meta | Internal guideline for formatting and submitting new skills to `BuilderIO/skills`. | `.agents/skills/adding-a-skill/SKILL.md`, `agents/openai.yaml` | NO |

---

## 3. Deep Dive into Visual Skills

### 3.1 `visual-plan`
- **Core Value**: Replaces wall-of-text plans with scannable MDX documents containing interactive wireframes, architecture diagrams, file tree maps, data model schemas, and API endpoint specifications.
- **Surface Options**: UI wireframe canvas, live prototype tab, or hybrid review.
- **Privacy Mode**: Local-files mode (`references/local-files.md`) allows local rendering via localhost bridge without cloud database writes.

### 3.2 `visual-recap`
- **Core Value**: Summarizes existing git diffs/PRs visually for code reviewers before line-by-line inspection.
- **Rule**: Must ALWAYS publish as an Agent-Native Plan (never inline chat text).

### 3.3 `visual-edit`
- **Core Value**: Visual inspection and component editing of running web applications directly from the coding session canvas.

---

## 4. Visual Skills Porting Plan (Project-Scoped)

### 4.1 Strict Constraints & Safety
- **Zero Global Mutation**: DO NOT write to `~/.codex` or `~/.gemini`.
- **Project-Only Scope**: Port visual skills strictly to workspace target directories:
  1. `.gemini/skills/`
  2. `.agents/skills/`

### 4.2 Destination Hierarchy

```
.gemini/skills/
├── visual_plan/
│   ├── SKILL.md
│   └── references/ (canvas.md, connection.md, document-quality.md, exemplar.md, local-files.md, wireframe.md)
├── visual_recap/
│   ├── SKILL.md
│   └── references/ (connection.md, local-files.md, wireframe.md)
└── visual_edit/
    └── SKILL.md

.agents/skills/
├── visual_plan/
│   ├── SKILL.md
│   └── references/ ...
├── visual_recap/
│   ├── SKILL.md
│   └── references/ ...
└── visual_edit/
    └── SKILL.md
```

---

## 5. Summary of Created Artifacts

1. **`docs/builderio_skills_inventory.md`**: Complete, 100% genuine inventory covering all 12 skills + meta-skill, visual classifications, and porting specs.
2. **`scratch/builderio_skills/`**: Verified local clone of `BuilderIO/skills` repository.
3. **`m3_skills_report.md`** (this file): Subagent detailed report and execution plan.
4. **`progress.md`**: Heartbeat and task progress log.
5. **`handoff.md`**: Handoff report following 5-component protocol.
