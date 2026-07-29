---
name: mise-tasks
description: "List and execute pinned project tasks defined in .mise.toml."
trigger: /mise
---

# /mise

Executes pinned project tasks defined in `.mise.toml`.

## Execution

This skill delegates execution to `mise`:

```bash
mise run "$@"
```
