---
name: verify-state
description: "Verify that all skills, plugins, and settings strictly originate from this project."
trigger: /verify-state
---

# /verify-state

Verifies project state isolation and checks for external pollution.

## Execution

This skill delegates execution to the project's Python library via `mise`:

```bash
mise run verify -- "$@"
```
