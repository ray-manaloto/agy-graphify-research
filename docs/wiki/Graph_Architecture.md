---
title: Graph Architecture & Tree-Sitter AST Indexing
doc_id: okf-wiki-graph-arch
version: 1.0.0
type: architecture
status: approved
author: agy-graphify
tags:
  - wiki
  - architecture
  - tree-sitter
  - lsp
---

# Graph Architecture & Tree-Sitter AST Indexing

## Overview

This document outlines the Graphify knowledge graph engine architecture, Tree-Sitter AST parser integration, and LSP symbol extraction pipeline.

### Architectural Index

- Main entrypoint: [[Index]]
- Vendor Repositories: [[Dependencies]]
- Symbol Lookup: [[Symbol_Navigation]]

Total Indexed AST Nodes: 1161 (57 files, 1104 symbols)
Total Indexed AST Edges: 1159 (including cross-reference edges)

```mermaid
flowchart LR
    Sub[Source Repositories] --> TS[Tree-Sitter / AST Parser]
    Sub --> LSP[LSP Symbol Extractor]
    TS --> Graph[GraphifyEngine / GraphData]
    LSP --> Graph
    Graph --> Out[graphify-out/ast_graph.json]
    Graph --> Wiki[docs/wiki/ Obsidian Pages]
```

## Context

Knowledge graph extraction processes local source code in `src/agy_graphify/` and cloned third-party dependencies in `vendor/`. Persistent artifacts are serialized to `graphify-out/graph.json` and `graphify-out/ast_graph.json`.
