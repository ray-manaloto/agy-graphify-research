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
- **Explicit File Truncation Rule**: Never prefix shell commands with bare file redirection (`> path/to/file && command`). File truncations MUST use explicit commands (`: > path/to/file` or `cat /dev/null > path/to/file` or Python file methods) to prevent shell execution syntax errors.

---

## 6. Manifest Binding & State Graph Preservation Invariant

- **Target Manifest Binding**: Whenever generating or resuming a StateGraphEngine DAG (`.gemini/graph_state.json`), the target source manifest (`config/sources.json` or `extended_repo_manifest.json`) MUST be explicitly bound to the graph state.
- **100% Repository Representation Verification**: Bounding checks MUST verify that 100% of all registered repositories in `config/sources.json` are present in `graphify-out/graph.json` before marking any DAG ingestion milestone as `completed`.

---

## 7. Rebase-First PR Creation & Return-to-Main Invariant

- **Rebase-First Feature Branching**: All new feature branches MUST be created directly off a rebased `main` branch (`git checkout main && git pull --rebase origin main`). Never create feature branches chained off unmerged feature branches.
- **Post-PR Workspace Return**: Immediately after staging a Pull Request via `gh pr create` or `uv run agy-task create-pr`, the workspace MUST be returned to `main` (`git checkout main`) to preserve a clean base working environment for subsequent tasks.

---

## 8. In-Process Colibri Graphify & Repo Ingest Standards

- **Repo Ingest Skill**: Repository differential tracking and manifest updates MUST use `uv run agy-task update-all-sources` per `.agents/skills/repo_ingest/SKILL.md`.
- **Zero-Token Graph Extraction**: Local knowledge graph updates MUST use `uv run agy-task colibri-graphify` (`ServerlessColibriRunner`) per `.agents/skills/colibri_graphify/SKILL.md`.

---

## 9. Cross-Process State Locking & Subagent Dispatch Invariant

- **POSIX `fcntl.flock` Atomic State Protection**: All reads and writes to `.gemini/graph_state.json` MUST use OS-level `fcntl.flock` (`LOCK_SH` for reads, `LOCK_EX` for writes) to prevent cross-process state corruption during concurrent CLI invocations.
- **Subagent Role Dispatch Guard**: Task nodes with assigned subagent roles MUST NOT be silently marked `completed` without executing a registered handler or emitting `NODE_PENDING_SUBAGENT`. Workflows containing skipped task nodes MUST mark overall graph status as `failed`.
- **Multiprocess Queue Safety & PID Tagging**: All Loguru log sinks MUST pass `enqueue=True` for multiprocess-safe queueing. Log format strings MUST include `PID:{process.id} ({process.name})`, and processes automatically write to isolated `.gemini/telemetry/proc_<PID>.log` sinks alongside central `universal.log`.

---

## 10. Local & Remote Branch Protection Invariant

- **Strict Branch Enforcement**: Direct commits to `main` (or detached HEAD matching `main` SHA) are strictly prohibited across all terminals and IDEs via native `.git/hooks/pre-commit` and `EnvironmentVerifier._check_branch_enforcement()`.
- **Administrative Override Guard**: Administrative system syncs (`create_pr_action`, `sync_main_action`) MUST explicitly supply `ALLOW_MAIN_COMMIT=1` in subprocess environments to pass pre-commit checks, while logging prominent telemetry warnings.



