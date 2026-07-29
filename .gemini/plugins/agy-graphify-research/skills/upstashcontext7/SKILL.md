---
name: upstashcontext7
description: "Lookup live API documentation, package references, and external library schemas."
trigger: /context7
---

# /context7

Looks up live documentation and schema references for external libraries.

## Execution

This skill delegates execution to the project's Python library via `mise`:

```bash
mise run task -- lookup_docs "$@"
```
