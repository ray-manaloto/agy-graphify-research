# Agent Guardrail Rule: Language Standards

- **Python & C++ Only**: All project code, scripting, tools, and automation MUST be written strictly in Python and C++. Bash scripts and shell logic are prohibited in source control.
- **Tooling Stack**: All Python workflows MUST utilize `mise`, `uv`, `ruff`, `ty`, `hk`, and `fnox`.
- **Ruff Linter**: Code must pass `ruff check .` with `select = ["ALL"]`.
- **Ty Type Checker**: Code must pass `ty check .` static analysis.
