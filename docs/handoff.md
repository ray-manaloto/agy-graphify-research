---
title: Session Handoff & Progressive State Specification
doc_id: okf-hand-001
version: 1.0.0
type: reference
tags:
  - handoff
  - telemetry
  - session
  - hooks
---

# Session Handoff & Progressive State Specification

## Overview

Defines how project state, knowledge graph data, telemetry logs, and pending tasks are packaged by hooks to provide seamless session handoffs to new agent turns.

## Core Concepts

- **Handoff Payload**: Session hook `.gemini/hooks/verify_environment.py` inspects `.gemini/telemetry/events.jsonl`, `graphify-out/graph.json`, and `.gemini/orchestration_plan.json`.
- **Progressive Disclosure**: Hook emits a compact 3-line summary in `additionalContext` with pointers to target documents, preventing context bloat.
- **State Persistence**: `mise run post-task` automatically refreshes handoff state after every major task or PR.

## Session Handoff Flowchart

```mermaid
flowchart LR
    TurnEnd[Task / Turn Completion] --> PostTask[mise run post-task]
    PostTask --> Telemetry[.gemini/telemetry/events.jsonl]
    PostTask --> Graph[graphify-out/graph.json]
    PostTask --> Plan[.gemini/orchestration_plan.json]
    Telemetry --> HandoffHook[.gemini/hooks/verify_environment.py]
    Graph --> HandoffHook
    Plan --> HandoffHook
    HandoffHook --> Summary[Compact 3-Line Handoff Summary]
```

## Relationships & References

- Registered in `.gemini/trusted_hooks.json`.
- Parsed by `TelemetryCollector` in `src/agy_graphify/telemetry.py`.
