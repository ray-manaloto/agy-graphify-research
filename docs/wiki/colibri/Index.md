---
title: Wiki Navigation & System Knowledge Index
doc_id: okf-wiki-index
version: 1.0.0
type: guide
status: approved
author: agy-graphify
tags:
  - wiki
  - index
  - graphify
  - ast
---

# Wiki Navigation & System Knowledge Index

## Overview

This Obsidian-formatted documentation hub provides a cross-linked knowledge index of `agy-graphify-research` AST graphs, LSP symbols, dependency clones, and system architecture.

### Obsidian Wiki Graph Navigation

- **[[Graph_Architecture]]**: Tree-Sitter AST & LSP symbol extraction pipeline.
- **[[Dependencies]]**: 3rd-party vendor repositories and dependency cloning specifications.
- **[[Symbol_Navigation]]**: Symbol map and location index across core codebase modules.

```mermaid
flowchart TD
    Index[[Index.md]] --> GA[[Graph_Architecture.md]]
    Index --> Dep[[Dependencies.md]]
    Index --> SN[[Symbol_Navigation.md]]
    GA --> Out[graphify-out/graph.json]
    Dep --> Vendor[vendor/ Directory]
    SN --> AST[AST & LSP Symbol Index]
```

## Context

The knowledge base is continuously indexed via `graphify_index_action` in `src/agy_graphify/tasks.py`.
