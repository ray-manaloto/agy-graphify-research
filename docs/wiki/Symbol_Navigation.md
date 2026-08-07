---
title: Symbol Navigation & Codebase Map
doc_id: okf-wiki-symbol-nav
version: 1.0.0
type: spec
status: approved
author: agy-graphify
tags:
  - wiki
  - symbols
  - lsp
  - navigation
---

# Symbol Navigation & Codebase Map

## Overview

LSP symbol locations, function signatures, and class definitions parsed across core source code and vendor repositories.

### Related Wiki Documentation

- Main Index: [[Index]]
- Graph Pipeline: [[Graph_Architecture]]
- Vendor Dependencies: [[Dependencies]]

Total Active LSP Symbols Indexed: 143

```mermaid
flowchart TD
    LSP[LSP Symbol Indexer] --> Classes[Class Definitions]
    LSP --> Funcs[Function / Coroutine Definitions]
    LSP --> Modules[Module Imports]
    Classes --> Map[docs/wiki/Symbol_Navigation.md]
    Funcs --> Map
    Modules --> Map
```

## Context

Symbols are extracted via `graphify_index_action` in `src/agy_graphify/tasks.py` and exported into `graphify-out/lsp_symbols.json`.
