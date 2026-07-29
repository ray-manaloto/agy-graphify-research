---
name: code-review
description: "Run automated multi-agent code review, Ruff static analysis, and type safety checks."
trigger: /code-review
---

# /code-review

Runs multi-agent code review across Python source code, schema generation, and static type analysis.

## Execution

This skill delegates execution to the project's Python library via `mise`:

```bash
mise run check -- "$@"
```
