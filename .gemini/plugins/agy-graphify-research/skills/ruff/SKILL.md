---
name: ruff
description: "Run Ruff linter and formatter using pyproject.toml rules."
trigger: /ruff
---

# /ruff

Runs Ruff check and format across all Python code.

## Execution

This skill delegates execution to `mise`:

```bash
mise run lint -- "$@"
```
