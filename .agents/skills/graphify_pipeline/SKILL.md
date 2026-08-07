---
name: graphify-pipeline
description: Master orchestrator skill calling repo-ingest and colibri-benchmark skills for multi-repo extraction and grading.
---

# Graphify Master Pipeline Orchestrator

This skill orchestrates the entire Graphify zero-token Colibri knowledge graph extraction pipeline. It follows a strictly layered execution architecture:

## Modular Flow Architecture

1. **Modular Skill (`SKILL.md`)**: High-level natural language intent, agent guardrails, and overarching step definition.
2. **Modular Mise Task (`.mise.toml`)**: `uv run agy-task <action>` commands that decouple the agent from brittle bash scripts, handling toolchain/dependency complexity.
3. **Modular Python Library Modules (`src/agy_graphify/tasks.py`)**: Abstract Python implementations executed cleanly across any platform without relying on shell commands.

## 1. Update and Ingest Sources

Invoke the `repo-ingest` pipeline to cleanly resolve and sync source code differentials.

Command:
```bash
uv run agy-task update-all-sources
```

## 2. Execute Zero-Token Local Extraction

Trigger the fast, in-process Colibri knowledge graph extraction which outputs the `graphify-out/` DAG state.

Command:
```bash
uv run agy-task colibri-graphify
```

## 3. Verify Output

Ensure that both `graphify-out/graph.json` and `graphify-out/GRAPH_REPORT.md` are populated properly and reflect the latest source changes.

