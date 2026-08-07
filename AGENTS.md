# AGENTS.md - Multi-Agent Architecture & Progressive Disclosure Guidelines

This document outlines the roles, responsibilities, execution rules, and progressive disclosure standards for AI agents and subagents operating on `agy-graphify-research`.

## 1. Subagent Roles & Responsibilities

| Role | Subagent Type | Recommended Model | Primary Responsibility |
| :--- | :--- | :--- | :--- |
| **Coordinator / Planner** | `main` | `pro` / `inherit` | High-level planning, user communication, and orchestration. |
| **Code Base Researcher** | `research` | `flash` | Directory exploration, codebase searching, and dependency inspection. |
| **Schema & Model Builder** | `self` / `developer` | `flash` | Modifying `schemas/` and generating Pydantic V2 models via `datamodel-code-generator`. |
| **Verifier & Reviewer** | `self` / `verifier` | `flash_lite` | Running `mise run check`, `hk check`, and validating code consistency. |
| **QA & Adversarial Reviewer** | `self` / `qa_reviewer` | `pro` | Edge-case analysis, hardware stress testing, and adversarial plan review. |
| **OKF Compliance Specialist** | `self` / `okf_specialist` | `flash` | Validating Open Knowledge Format schemas, frontmatter, and doc generators. |
| **Self-Healing & Learning Specialist** | `self` / `learning_agent` | `flash` | Analyzing telemetry traces & failed tool calls, emitting remediation rules & LESSONS.md. |

---

## 2. Context Window Management (< 50% Limit)

To prevent context bloat:
- **Threshold**: When context token usage exceeds **40%–50%** (80k–100k tokens), delegate subtasks to background subagents via `invoke_subagent`.
- **Lazy Loading**: DO NOT read large documentation files or entire packages into prompt context. Use targeted line ranges (`view_file` with `StartLine`/`EndLine`) and directory-specific skill lookups.

---

## 3. Progressive Disclosure Architecture

Documentation must be loaded progressively:
- **Level 1 (Session Handoff)**: Lightweight summary provided via session hook (`verify_environment.py`).
- **Level 2 (Directory Index)**: `AGENTS.md` and directory-level `README.md` files loaded when traversing specific modules.
- **Level 3 (Symbol Level)**: Targeted symbol views loaded via `view_file` or `/doc-lookup` skill.

---

## 4. Session Handoff Protocol

When ending a session or completing a major task:
1. Run `mise run post-task` to log conversation telemetry into `.gemini/telemetry/`.
2. Update `.gemini/orchestration_plan.json` with completed and remaining tasks.
3. Next session startup hook automatically parses telemetry and state to supply progressive handoff context.

---

## 5. Strict Execution & Tooling Guardrails

- **Mandatory `uv run` Tooling**: All commands, tests, and tasks MUST be executed through `uv run` via `.mise.toml` task wrappers backed by `pyproject.toml` entrypoints.
- **Zero Shell Script Policy (`*.sh` Ban)**: Shell scripts (`*.sh`) are strictly prohibited in the codebase (outside vendor/3rd-party repositories). Enforcement is strictly checked by `hk.pkl` (`no_shell_scripts` linter), `src/agy_graphify/verify.py` (`EnvironmentVerifier`), and git pre-commit hooks.
- **Python Library-First Architecture**: All tasks, graph execution engines, telemetry loops, and plugins must be written in Python inside `src/agy_graphify/` and exposed via `pyproject.toml` script entrypoints.

---

## 6. Manifest Binding & State Graph Preservation Invariant

- **Target Manifest Binding**: Whenever generating or resuming a StateGraphEngine DAG (`.gemini/graph_state.json`), the target source manifest (`config/sources.json` or `extended_repo_manifest.json`) MUST be explicitly bound to the graph state.
- **100% Repository Representation Verification**: Bounding checks MUST verify that 100% of all registered repositories in `config/sources.json` are present in `graphify-out/graph.json` before marking any DAG ingestion milestone as `completed`.


