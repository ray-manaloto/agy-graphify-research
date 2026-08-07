---
title: 3rd-Party Vendor Dependencies & Repository Cloning
doc_id: okf-wiki-dependencies
version: 1.0.0
type: reference
status: approved
author: agy-graphify
tags:
  - wiki
  - dependencies
  - vendor
  - cloning
---

# 3rd-Party Vendor Dependencies & Repository Cloning

## Overview

Documentation of third-party repository dependencies cloned into `vendor/` via `vendor_clone_action` in `src/agy_graphify/tasks.py`.

### Dependency Index

- Navigation: [[Index]]
- Graph Architecture: [[Graph_Architecture]]
- Symbols: [[Symbol_Navigation]]

### Tracked Vendor Repositories

1. **`graphifyy`**: Tree-Sitter code graph extraction engine (`https://github.com/graphifyy/graphifyy.git`).
2. **`cosmtrek/mindwalk`**: Go codebase visual exploration engine (`https://github.com/cosmtrek/mindwalk.git`).
3. **`DeusData/codebase-memory-mcp`**: Model Context Protocol graph memory server (`https://github.com/DeusData/codebase-memory-mcp.git`).
4. **`tirth8205/code-review-graph`**: Automated git review graph parser (`https://github.com/tirth8205/code-review-graph.git`).

```mermaid
flowchart TD
    VCA[vendor_clone_action] --> G[graphifyy]
    VCA --> M[cosmtrek/mindwalk]
    VCA --> C[DeusData/codebase-memory-mcp]
    VCA --> R[tirth8205/code-review-graph]
    G --> Vendor[vendor/ Directory]
    M --> Vendor
    C --> Vendor
    R --> Vendor
```

## Context

Dependencies are cloned asynchronously using `asyncio.create_subprocess_exec` adhering strictly to the zero shell script policy.
