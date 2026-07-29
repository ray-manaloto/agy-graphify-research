---
name: exa-mcp-server
description: "Perform web search, neural retrieval, and 3rd-party tool audits for project dependencies."
trigger: /exa-search
---

# /exa-search

Performs deep web research and neural tool retrieval to find open-source 3rd-party packages before custom code is written.

## Execution

This skill delegates execution to the project's Python library via `mise`:

```bash
mise run task -- search_tools "$@"
```
