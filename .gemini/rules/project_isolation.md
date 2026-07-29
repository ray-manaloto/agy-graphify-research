# Agent Guardrail Rule: Strict Project Isolation

- **Zero Global Mutations**: Agents MUST NOT install, copy, or write plugins, skills, extensions, or custom settings into global directories (`~/.gemini/`, `~/.config/`, etc.).
- **Project Scope**: All plugins, skills, hooks, configurations, and temporary artifacts MUST reside exclusively within the project directory (`/Users/rmanaloto/agy-graphify-research/`).
- **Verification Gate**: Any attempt to write outside the workspace will be rejected by pre-commit hooks and environment verifiers.
