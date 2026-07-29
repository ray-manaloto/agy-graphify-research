---
name: security
description: "Run SAST security analysis, secret scanning (detect-private-key, betterleaks), and dependency checks."
trigger: /security
---

# /security

Runs security analysis, secret detection, and dependency audit across project scope.

## Execution

This skill delegates execution to the project's Python library via `mise`:

```bash
hk check -- "$@"
```
