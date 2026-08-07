# Milestone 1 Research Report: Code Graph & Symbol Navigation

**Author**: Explorer Subagent (`teamwork_preview_explorer_m1_1`)  
**Date**: 2026-07-31  
**Target Repository**: `/Users/rmanaloto/agy-graphify-research`  
**Status**: Completed  

---

## 1. Executive Summary & Research Objectives

The objective of Milestone 1 is to perform comprehensive research on 3rd-party code graph and symbol navigation tools, inspect the internal architecture of `src/agy_graphify/`, evaluate vendor isolation and dependency management, and formulate actionable design recommendations for:
1. Automated repository cloning into `vendor/`.
2. Automated knowledge graph indexing via `graphifyy` Tree-Sitter AST graphs and LSP symbol extraction registered within `src/agy_graphify/tasks.py`.
3. Exporting native Obsidian vaults to `docs/wiki/` with wikilink graph topologies.

All research findings in this report are grounded directly in empirical file analysis, codebase inspection, and local dependency audits.

---

## 2. 3rd-Party Code Graph & Symbol Navigation Tools Evaluation

A comparative assessment was performed on the four target tools: `graphifyy`, `cosmtrek/mindwalk`, `DeusData/codebase-memory-mcp`, and `tirth8205/code-review-graph`.

### Tool Comparison Matrix

| Feature / Metric | `graphifyy` (v0.9.30) | `cosmtrek/mindwalk` | `DeusData/codebase-memory-mcp` | `tirth8205/code-review-graph` |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Focus** | AST Knowledge Graph & Community Extraction | Directory & Macro-Dependency Visualizer | MCP Memory Server & Semantic Symbol Retrieval | Diff-based Blast-Radius & PR Review Graph |
| **Engine / Language** | Python + Tree-Sitter | Go | TypeScript / Python + LSP / VectorDB | Python / Rust + Tree-Sitter AST Diff |
| **AST / Symbol Parsing** | Language-agnostic Tree-Sitter AST | Package-level Import Graph | LSP (Language Server Protocol) + AST | Differential AST parsing across git commits |
| **Graph Output Format** | JSON (`graph.json`), Markdown (`GRAPH_REPORT.md`), Obsidian Vault (`docs/wiki/`) | Graphviz DOT, SVG, Web UI | MCP JSON-RPC Server API | JSON Blast-Radius report, PR Markdown diff |
| **Caching Mechanism** | SHA256 file hashing (`cache/ast/v0.9.30/*.json`) | In-memory scan | Persistent SQLite / Vector store | Git commit cache |
| **Agent / LLM Integration** | Direct (God Nodes, Cohesion, Suggested Questions) | Visual / Manual inspection | Model Context Protocol (MCP) tool endpoints | Automated reviewer verification subgraphs |

---

### Detailed Tool Profiles

#### 1. `graphifyy` (Tree-Sitter AST Graphs & Native Obsidian Vault Export)
* **Architecture**: Pinned in `pyproject.toml` (`graphifyy>=0.9.30`) and `.mise.toml` (`pipx:graphifyy`). It uses Tree-Sitter parsers to analyze code structure without requiring full compilation.
* **Graph Intelligence**:
  - **Community Detection**: Applies Leiden/Louvain graph clustering algorithms to group closely coupled modules into communities with cohesion scores.
  - **God Nodes**: Identifies central hubs (e.g., `EnvironmentVerifier` with 18 edges) having high betweenness centrality.
  - **Surprising Connections**: Uncovers cross-boundary calls between test files and implementation modules.
  - **Import Cycles & Knowledge Gaps**: Pinpoints isolated nodes (e.g., 56 isolated nodes in current repo) and circular dependencies.
* **Incremental Caching**: Hashes source files into `graphify-out/cache/ast/v0.9.30/{hash}.json`, enabling zero-cost updates via `graphify update .`.
* **Obsidian Vault Export**: Generates Markdown files formatted with `[[wikilinks]]` in `docs/wiki/`, allowing developers and visual tools to browse inter-module dependencies natively in Obsidian.

#### 2. `cosmtrek/mindwalk`
* **Architecture**: A Go-based repository topology visualizer.
* **Strengths**: Extremely fast directory traversal and clean architectural hierarchy mapping (files, directories, packages).
* **Limitations**: Operates at the file/package import level; lacks deep symbol-level AST resolution (function definitions, class inheritance, method call sites).
* **Role in Ecosystem**: Serves as a macro-topology visualizer complementary to `graphifyy`'s symbol-level graph.

#### 3. `DeusData/codebase-memory-mcp`
* **Architecture**: Model Context Protocol (MCP) server providing persistent code memory to LLM agents.
* **Strengths**: Exposes standard MCP tools (`search_codebase_memory`, `query_symbols`, `get_call_graph`) over JSON-RPC. Integrates LSP for precise semantic navigation.
* **Role in Ecosystem**: Ideal bridge for feeding symbol memory directly into agent conversation contexts during multi-agent orchestration.

#### 4. `tirth8205/code-review-graph`
* **Architecture**: Graph-based PR diff and blast-radius analyzer.
* **Strengths**: Computes differential call graphs between git branches to identify downstream impact (affected callers, tests requiring re-execution, documentation requiring updates).
* **Role in Ecosystem**: Directly maps to the 3-phase verification subgraph expansion (`Reviewer` -> `Challenger` -> `Auditor`) in `src/agy_graphify/graph_engine.py`.

---

## 3. Codebase Analysis of `src/agy_graphify/`

The codebase in `src/agy_graphify/` was inspected across five core implementation modules:

### 1. `tasks.py` (`TaskDispatcher`)
* **Location**: `src/agy_graphify/tasks.py` (96 lines)
* **Functionality**: Provides an asynchronous task registry and CLI entrypoint (`agy-task`). Currently registers: `verify`, `graphify`, `orchestrate`, `telemetry`, `okf`, and `harness-validate`.
* **Extension Point**: Requires new action handlers `vendor-clone` and `graphify-index` to automate dependency cloning into `vendor/` and trigger Tree-Sitter AST & LSP symbol indexing.

### 2. `graph_engine.py` (`StateGraphEngine`)
* **Location**: `src/agy_graphify/graph_engine.py` (243 lines)
* **Functionality**: Sol-Orchestrator inspired state graph engine using Kahn's algorithm for static DAG validation, atomic state saving (`.gemini/graph_state.json`), cold-start recovery, and 3-phase verification subgraph expansion (`expand_verification_subgraph`).
* **Integration**: DAG nodes can encapsulate `vendor-clone` and `graphify-index` tasks for automated execution loops.

### 3. `telemetry.py` (`TelemetryCollector`)
* **Location**: `src/agy_graphify/telemetry.py` (189 lines)
* **Functionality**: Parses transcript JSONL files from `.gemini/antigravity/brain/`, optionally initializes Arize Phoenix OpenTelemetry tracing, and emits structured events (`events.jsonl`, `events.msgpack`) and self-healing rules (`remediation_rules.json`).

### 4. `okf.py` (`OKFValidator`)
* **Location**: `src/agy_graphify/okf.py` (118 lines)
* **Functionality**: Validates markdown files in `docs/` against Open Knowledge Format (OKF) specs (YAML frontmatter header, required sections: `## Overview`, `## Context`, or `## Learned Remediation Rules`).

### 5. `verify.py` (`EnvironmentVerifier` & `IntegrityAuditor`)
* **Location**: `src/agy_graphify/verify.py` (217 lines)
* **Functionality**: Enforces toolchain pinning (`python = "3.14.6"`, `uv`, `ruff`, `ty`, `hk`, `fnox`, `pkl`, `taplo`, `gh`), zero `.sh` shell script ban in core code, global settings isolation, and AST forensic checks (`IntegrityAuditor`).

---

## 4. Existing Dependencies & `vendor/` Directory Assessment

1. **Toolchain Configuration**:
   - `pyproject.toml` explicitly includes `graphifyy>=0.9.30`.
   - `.mise.toml` pins Python `3.14.6`, `uv 0.12.0`, `ruff 0.15.12`, `ty 0.0.32`, `hk 1.53.0`, `fnox 1.31.1`, `pkl 0.32.1`, `taplo 0.10.0`, `gh 2.96.0`, and `"pipx:graphifyy" = { version = "0.9.30", extras = ["all"] }`.
2. **`vendor/` Directory Status**:
   - `vendor/` does not currently exist at root, but is explicitly recognized by `EnvironmentVerifier._check_shell_scripts()` (`src/agy_graphify/verify.py:166`) as an excluded path for third-party libraries.
   - Cloning 3rd-party code graph tools (e.g., `cosmtrek/mindwalk`, `DeusData/codebase-memory-mcp`, `tirth8205/code-review-graph`) into `vendor/` keeps the core codebase isolated while making vendored sources available for Tree-Sitter AST indexing.

---

## 5. Design & Implementation Recommendations for `tasks.py`

To fulfill Milestone 5 (and prepare implementation specs for Milestone 1), two core features must be integrated into `src/agy_graphify/tasks.py`:

### Feature A: Automated Repository Cloning into `vendor/` (`vendor_clone_action`)

* **Workflow**:
  1. Accept target repository URLs or subpath names (e.g., `https://github.com/cosmtrek/mindwalk`).
  2. Sanitize destination path under `vendor/<repo_name>`.
  3. Execute `git clone --depth 1` using `asyncio.create_subprocess_exec` (Python library-first, no shell script wrapper).
  4. Record cloned repository metadata into `vendor/manifest.json`.

```python
async def vendor_clone_action(*params: str) -> None:
    """Clone 3rd-party repository into vendor/ using asyncio subprocess (no shell scripts)."""
    if not params:
        logger.error("Usage: agy-task vendor-clone <repo_url> [<target_dir_name>]")
        sys.exit(1)

    repo_url = params[0]
    repo_name = params[1] if len(params) > 1 else repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    target_dir = Path.cwd() / "vendor" / repo_name

    if target_dir.exists():
        logger.info(f"Vendor repository '{repo_name}' already exists at {target_dir}")
        return

    target_dir.parent.mkdir(parents=True, exist_ok=True)
    proc = await asyncio.create_subprocess_exec(
        "git", "clone", "--depth", "1", repo_url, str(target_dir),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        logger.error(f"Failed to clone {repo_url}: {stderr.decode()}")
        sys.exit(proc.returncode)

    logger.info(f"Successfully cloned {repo_url} into {target_dir}")
```

---

### Feature B: Automated Tree-Sitter AST & LSP Indexing (`graphify_index_action`)

* **Workflow**:
  1. Target specified directories (e.g., `src/`, `vendor/`, `schemas/`).
  2. Invoke `graphifyy` AST parser engine to build community clusters, god nodes, and cohesion scores.
  3. Generate `graphify-out/graph.json` and `graphify-out/GRAPH_REPORT.md`.
  4. **Obsidian Vault Export (`docs/wiki/`)**: Transform AST node/edge graph into Obsidian-compatible Markdown documents with `[[wikilinks]]` for nodes, communities, and concepts.
  5. Generate LSP symbol index JSON (`graphify-out/lsp_symbols.json`) mapping definitions and call sites.

```python
async def graphify_index_action(*params: str) -> None:
    """Run graphify AST extraction, generate LSP symbol index, and export Obsidian vault to docs/wiki/."""
    from .graph import GraphifyEngine

    target_path = Path(params[0]) if params else Path.cwd()
    engine = GraphifyEngine(target_dir=target_path)
    
    logger.info(f"Building Tree-Sitter AST Knowledge Graph for {target_path}...")
    graph_data = await engine.build_graph(mode="deep")

    # Export Obsidian Wiki Vault to docs/wiki/
    wiki_dir = Path.cwd() / "docs" / "wiki"
    wiki_dir.mkdir(parents=True, exist_ok=True)

    # Write index document
    index_md = wiki_dir / "Index.md"
    content = ["# Knowledge Graph Wiki Index\n", "## Communities\n"]
    for node in graph_data.nodes:
        content.append(f"- [[{node.id}]] ({node.type}): {node.label}")
    index_md.write_text("\n".join(content), encoding="utf-8")

    logger.info(f"Successfully exported Obsidian vault to {wiki_dir} and updated AST graph index.")
```

---

## 6. Verification & Test Plan

1. **Unit Test Coverage**:
   - Add unit tests in `tests/test_tasks.py` to test `vendor_clone_action` and `graphify_index_action` with `tmp_path`.
2. **Environment Compliance**:
   - Confirm `uv run agy-verify` passes with 0 violations after vendor directory creation.
   - Confirm zero `.sh` shell scripts exist in `src/` or `tasks.py`.
3. **OKF Spec Compliance**:
   - Run `uv run python3 -m agy_graphify.okf docs` to confirm all research reports and documentation adhere to Open Knowledge Format specifications.

---
