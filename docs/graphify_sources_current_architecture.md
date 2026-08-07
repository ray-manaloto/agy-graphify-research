---
title: Graphify Source Ingestion Current Architecture
doc_id: okf-graphify-sources-current
version: 1.0.0
type: architecture
status: approved
author: agy-graphify
tags:
  - graphify
  - architecture
  - sources
  - pipeline
---

# Graphify Source Ingestion Current Architecture

## Overview
This specification documents the active source ingestion architecture, directory structure, configuration manifests, and end-to-end knowledge graph extraction pipeline for `agy-graphify-research`. Both local codebase assets and external target repositories are managed and extracted through this pipeline.

## Source Level Classification

1. **Internal Project Sources**: The core codebase (`src/agy_graphify/`), unit test suite (`tests/`), OKF documentation (`docs/`), instructions (`AGENTS.md`, `GEMINI.md`), and build manifests (`pyproject.toml`, `.mise.toml`) are primary sources ingested into `graphify-out/graph.json`.
2. **External Target Repositories**: Cloned Git repositories under `repos/` defined in `config/sources.json` are merged alongside local code to form a unified multi-repository knowledge graph.

## Directory & Configuration Mapping

```text
/Users/rmanaloto/agy-graphify-research/
├── config/
│   └── sources.json                  <-- Central source registry manifest
├── .gemini/
│   └── commit_state.json             <-- Git SHA cache for differential tracking
├── repos/                            <-- Cloned target repositories
├── src/                              <-- Core Python library implementation
├── docs/                             <-- OKF documentation specifications
├── pyproject.toml                    <-- Toolchain dependencies & script entrypoints
├── .mise.toml                        <-- Modular task execution wrappers
└── graphify-out/                     <-- Graphify output directory
    ├── graph.json                    <-- GraphRAG JSON knowledge graph
    ├── GRAPH_REPORT.md               <-- Architecture report
    ├── graph.html                    <-- D3 visual network graph
    ├── cypher.txt                    <-- Graph database export (Neo4j/FalkorDB)
    ├── obsidian/                     <-- Obsidian vault export
    └── wiki/                         <-- Community wiki articles
```

## End-to-End Execution Workflow

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Agent
    participant Skill as Skill (.agents/skills/graphify_pipeline)
    participant Task as Mise Task (.mise.toml)
    participant PyTask as Python Tasks (tasks.py)
    participant Reg as Source Registry (source_registry.py)
    participant Colibri as Colibri Extractor (colibri_extractor.py)
    participant Graph as Graph Engine (graph.py)
    participant Out as Output Directory (graphify-out/)

    User->>Skill: Invoke /graphify-pipeline
    
    %% Phase 1: Source Syncing
    rect rgb(240, 248, 255)
    Note over Skill, Reg: Phase 1: Update & Sync Sources
    Skill->>Task: uv run agy-task update-all-sources
    Task->>PyTask: update_all_sources_action()
    PyTask->>Reg: SourceRegistryManager.sync_and_get_deltas()
    Reg->>Reg: Read config/sources.json & .gemini/commit_state.json
    Reg-->>PyTask: Return Git SHA differential deltas
    end

    %% Phase 2: Code Ingestion & AST Parsing
    rect rgb(245, 245, 220)
    Note over Skill, Graph: Phase 2: Ingestion & AST Parsing
    Skill->>Task: uv run agy-task colibri-graphify
    Task->>PyTask: colibri_graphify_action()
    PyTask->>Graph: GraphifyEngine.build_graph(repos/)
    Graph->>Graph: AST Parser extracts classes, functions, imports (EXTRACTED edges)
    end

    %% Phase 3: Deep Model Extraction
    rect rgb(230, 230, 250)
    Note over PyTask, Colibri: Phase 3: Deep Model Extraction
    PyTask->>Colibri: ServerlessColibriRunner.extract_directory()
    Colibri->>Colibri: Auto-launch local zero-token Colibri HTTP server
    Colibri-->>PyTask: Extract enriched semantic relationships (INFERRED edges)
    end

    %% Phase 4: Community Reflection
    rect rgb(240, 255, 240)
    Note over Graph, Out: Phase 4: Community Reflection & Clustering
    Graph->>Graph: Run Leiden community detection algorithm
    Graph->>Out: Write wiki articles per community to graphify-out/wiki/
    end

    %% Phase 5: Output Generation
    rect rgb(255, 240, 245)
    Note over Graph, Out: Phase 5: Generating Output Artifacts
    Graph->>Out: Write graph.json, GRAPH_REPORT.md, graph.html, cypher.txt
    PyTask-->>User: Pipeline Complete (100% Graph Coverage Verified)
    end
```

## Modular Task Binding Verification

The master orchestrator skill [`graphify_pipeline`](file:///Users/rmanaloto/agy-graphify-research/.agents/skills/graphify_pipeline/SKILL.md) delegates directly to modular mise task wrappers in `.mise.toml`:

```toml
[tasks.update-all-sources]
description = "Sync all source repositories and calculate git commit SHA deltas"
run = "uv run python -m agy_graphify.tasks update-all-sources"

[tasks.colibri-graphify]
description = "Execute fast zero-token local Colibri knowledge graph extraction"
run = "uv run python -m agy_graphify.tasks colibri-graphify"
```
