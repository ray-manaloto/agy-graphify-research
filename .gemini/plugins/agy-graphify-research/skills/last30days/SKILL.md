---
name: last30days
description: "Review recent commits, file modifications, and design evolutions in the repository."
trigger: /last30days
---

# /last30days

Analyzes git history and recent project modifications over the last 30 days.

## Execution

This skill delegates execution to the project's Python library via `mise`:

```bash
mise run task -- git_history "$@"
```
