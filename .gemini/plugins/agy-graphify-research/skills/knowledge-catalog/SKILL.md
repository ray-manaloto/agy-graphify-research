---
name: knowledge-catalog
description: "Browse and index Open Knowledge Format (OKF) documentation catalog in docs/."
trigger: /knowledge-catalog
---

# /knowledge-catalog

Indexes, searches, and validates all OKF specification files in `docs/`.

## Execution

This skill delegates execution to the project's Python library via `mise`:

```bash
mise run okf -- "$@"
```
