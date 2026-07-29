# Agent Guardrail Rule: Audit 3rd-Party Open-Source Tools First

- **Mandatory Audit**: Autonomous agents and developers MUST search for existing, active, modern free/open-source 3rd-party tools, packages, or libraries before writing custom code or building custom tools.
- **Reuse Over Re-invention**: Avoid re-inventing functionality provided by high-quality PyPI / GitHub projects (e.g. `uv`, `ruff`, `ty`, `graphify`, `pydantic`, `rich`).
- **Documentation Requirement**: If custom code is built, the pull request or task report must explicitly state which 3rd-party options were evaluated and why a custom solution was required.
