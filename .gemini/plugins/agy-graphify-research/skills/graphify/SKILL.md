---
name: graphify
description: "Extract knowledge graph, community structure, and persistent graph.json for the project."
trigger: /graphify
---

# /graphify

Builds or queries a persistent knowledge graph for the repository.

## Execution

This skill delegates execution to the project's Python library via `mise`:

```bash
mise run graphify -- "$@"
```

## Parameters

- `<path>`: Target path to extract/build graph (defaults to `.`)
- `--mode`: Extraction mode (`standard` or `deep`)
- `--query "<question>"`: Query existing knowledge graph
