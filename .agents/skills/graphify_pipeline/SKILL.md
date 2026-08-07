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

## 1. Parse, Deduplicate, and Ingest Multi-Modal Sources

- **Code Repositories**: Accept GitHub URLs, organisation pages, or Crates.io packages cloned into `repos/`.
- **PDF Papers & Books**: Process `.pdf` documents placed in `raw/` or fetched via `graphify add <url>`.
- **Video & Audio**: Process `.mp4`, `.mp3`, `.m4a`, `.wav` media files placed in `raw/` via Whisper transcription.
- **Scraped Web URLs**: Fetch and convert web articles, documentation pages, or Wikipedia entries into `raw/`.
- Deduplicate target URLs against existing registered repositories in `config/sources.json`.
- Execute multi-threaded clone and Git SHA differential tracking to resolve new or changed source code:

Command:
```bash
uv run agy-task update-all-sources
```

## 2. Execute Zero-Token Local Extraction

Trigger fast, in-process Colibri knowledge graph extraction which outputs the `graphify-out/` DAG state:

Command:
```bash
uv run agy-task colibri-graphify
```

## 3. Verify Output

Ensure that both `graphify-out/graph.json` and `graphify-out/GRAPH_REPORT.md` are populated properly and reflect 100% representation of all registered repositories.

