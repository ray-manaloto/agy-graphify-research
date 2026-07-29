---
name: orchestrate
description: "Multi-agent workflow orchestration, subagent role planning, and task decomposition."
trigger: /orchestrate
---

# /orchestrate

Plans and dispatches multi-agent workflows for complex tasks.

## Execution

This skill delegates execution to the project's Python library via `mise`:

```bash
mise run orchestrate -- "$@"
```

## Parameters

- `<task>`: Task description for multi-agent workflow
- `--roles`: Subagent roles to include (`researcher`, `developer`, `verifier`)
