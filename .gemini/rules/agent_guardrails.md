# Agent Execution Guardrails & Rules

To ensure reliable, deterministic, and isolated execution, all agents operating on this codebase MUST follow these mandatory guardrails:

## 1. Zero Direct Main Commits or Pushes (PR Workflow Mandatory)
- **Feature Branches Required**: Agents MUST NEVER commit directly to `main` or push directly to `main`.
- **Pull Requests**: All work MUST be conducted on feature branches (`feature/<name>`) and submitted via Pull Request using `gh pr create`.

## 2. Zero System-Wide / Global Mutations
- Agents MUST NOT write, create, or alter files outside the current project workspace directory.
- All `.gemini/` configurations, rules, skills, and plugins MUST be kept within the project root directory.

## 3. Strict Language Standard: Python & C++ Only
- All scripting, automation, helper functions, and tools MUST be written in Python (using Python 3.11+ / 3.14+) or C++.
- Bash scripts, shell scripts, and raw inline multi-line shell code are strictly prohibited in the codebase.
- Command-line workflows must delegate to Python modules via `mise run <task>`.

## 4. Mandatory Toolchain & Schema Compliance
- All models must be generated via `datamodel-code-generator` from `schemas/`.
- No print statements or raw stdout outputs in library code; use `loguru` with zero default stdout sinks.
- All documentation in `docs/` must satisfy the Open Knowledge Format (OKF) specification.
- All code changes must pass `mise run check` and `hk check` cleanly before completion.
