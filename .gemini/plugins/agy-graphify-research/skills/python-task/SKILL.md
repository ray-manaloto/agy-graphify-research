---
name: python-task
description: "Flexible Python library task dispatcher accepting action names and skill parameters."
trigger: /task
---

# /task

Runs custom Python library automation actions dynamically.

## Execution

This skill delegates execution to the project's Python library via `mise`:

```bash
mise run task -- "$@"
```

## Parameters

- `<action>`: Action handler name registered in `TaskDispatcher` (`verify`, `graphify`, `orchestrate`)
- `[params...]`: Positional and keyword parameters passed to the action function
