---
name: telemetry
description: "Collect conversation events, tool calls, and execution telemetry into project-scoped JSONL and MsgPack files for self-reflection."
trigger: /telemetry
---

# /telemetry

Parses conversation transcripts and records structured telemetry for self-learning.

## Execution

This skill delegates execution to the project's Python library via `mise`:

```bash
mise run telemetry -- "$@"
```
