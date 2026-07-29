# Contributing to agy-graphify-research

Thank you for contributing to `agy-graphify-research`!

## Development & Code Quality Setup

This project uses modern tooling (`mise`, `uv`, `ruff`, `ty`, `hk`, `fnox`) and enforces Python code quality and strict project isolation.

### Setup Instructions

1. **Install Tooling via Mise**:
   ```bash
   mise install
   ```

2. **Run All Quality & State Verification Checks**:
   ```bash
   mise run check
   ```

3. **Git Pre-commit and Post-commit Hooks**:
   ```bash
   hk install
   hk check
   ```

## Rules & Standards

- All project code and scripting must be written in Python or C++.
- Code must pass `ruff check .` with `select = ["ALL"]` enabled.
- Code must pass `ty check .` type analysis.
- Agents and contributors must audit existing free/open-source modern 3rd-party libraries before building custom code.
- Zero modifications to global user configurations (`~/.gemini`). All configuration must reside in `.gemini/`.
