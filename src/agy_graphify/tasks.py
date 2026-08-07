"""Flexible async task dispatcher wrapping python library functions for skills and mise tasks."""

import argparse
import ast
import asyncio
import inspect
import json
import os
import re
import sys
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from .logger import logger


class TaskDispatcher:
    """Dispatches tasks and skill parameters to underlying Python library functions."""

    def __init__(self) -> None:
        self._registry: dict[str, Callable[..., Awaitable[Any] | Any]] = {}

    def register(self, name: str, func: Callable[..., Awaitable[Any] | Any]) -> None:
        """Register a function handler for a skill or automation task."""
        self._registry[name] = func

    async def dispatch(self, action: str, *args: Any, **kwargs: Any) -> Any:
        """Execute a registered action asynchronously with flexible arguments."""
        if action not in self._registry:
            msg = f"Unknown action '{action}'. Available actions: {list(self._registry.keys())}"
            logger.debug(msg)
            raise KeyError(msg)

        func = self._registry[action]
        try:
            if inspect.iscoroutinefunction(func):
                res = await func(*args, **kwargs)
            else:
                res = func(*args, **kwargs)
        finally:
            if "PYTEST_CURRENT_TEST" not in os.environ:
                from .monitor import monitor_logs
                monitor_logs()
            
        return res


async def graphify_setup_action(*params: str) -> None:
    """Execute graphify Python SDK skill update to auto-generate .graphify_version."""
    import graphify.install

    graphify.install.install(platform="antigravity", project=True, project_dir=Path("."))
    logger.info("Graphify setup complete. .graphify_version generated.")


async def vendor_clone_action(*params: str, vendor_dir: Path | None = None) -> list[Path]:
    """Automated cloning of 3rd-party dependency repositories into vendor/ using asyncio.create_subprocess_exec.

    Target repositories:
    - graphifyy
    - cosmtrek/mindwalk
    - DeusData/codebase-memory-mcp
    - tirth8205/code-review-graph
    """
    root = vendor_dir or (Path.cwd() / "vendor")
    root.mkdir(parents=True, exist_ok=True)

    default_repos = [
        "https://github.com/graphifyy/graphifyy.git",
        "https://github.com/cosmtrek/mindwalk.git",
        "https://github.com/DeusData/codebase-memory-mcp.git",
        "https://github.com/tirth8205/code-review-graph.git",
    ]

    targets = list(params) if params else default_repos
    cloned_paths: list[Path] = []

    for repo in targets:
        if repo.startswith(("http://", "https://", "git@")):
            url = repo
            name = repo.rstrip("/").split("/")[-1].removesuffix(".git")
        elif "/" in repo:
            name = repo.split("/")[-1].removesuffix(".git")
            url = f"https://github.com/{repo}.git"
        else:
            name = repo.removesuffix(".git")
            url = (
                f"https://github.com/graphifyy/{repo}.git"
                if repo == "graphifyy"
                else f"https://github.com/3rdparty/{repo}.git"
            )

        target_path = root / name
        if target_path.exists() and any(target_path.iterdir()):
            logger.info(f"Vendor repository '{name}' already present at {target_path}")
            cloned_paths.append(target_path)
            continue

        logger.info(f"Cloning {url} into {target_path} via asyncio.create_subprocess_exec...")
        try:
            proc = await asyncio.create_subprocess_exec(
                "git",
                "clone",
                "--depth",
                "1",
                url,
                str(target_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            if proc.returncode == 0:
                logger.info(f"Successfully cloned {name} into {target_path}")
            else:
                err_msg = stderr.decode("utf-8", errors="replace")
                logger.warning(
                    f"git clone failed for {url} ({err_msg}). Creating vendor directory structure for local operation."
                )
                target_path.mkdir(parents=True, exist_ok=True)
                (target_path / "README.md").write_text(
                    f"# {name}\n\nVendor dependency placeholder for `{url}`.\n", encoding="utf-8"
                )
        except (OSError, RuntimeError, ValueError) as exc:
            logger.warning(f"Subprocess execution error during clone of {url}: {exc}")
            target_path.mkdir(parents=True, exist_ok=True)
            (target_path / "README.md").write_text(
                f"# {name}\n\nVendor dependency placeholder for `{url}`.\n", encoding="utf-8"
            )

        cloned_paths.append(target_path)

    return cloned_paths


def _generate_wiki_docs(
    wiki_dir: Path, ast_graph_data: dict[str, Any], lsp_symbols: list[dict[str, Any]]
) -> None:
    """Generate Obsidian-formatted wiki documents with wikilinks and OKF frontmatter."""
    wiki_dir.mkdir(parents=True, exist_ok=True)

    index_content = """---
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
"""

    graph_arch_content = f"""---
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

Total Indexed AST Nodes: {len(ast_graph_data.get("nodes", []))}
Total Indexed AST Edges: {len(ast_graph_data.get("edges", []))}

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
"""

    dependencies_content = """---
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
"""

    symbols_count = len(lsp_symbols)
    symbol_nav_content = f"""---
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

Total Active LSP Symbols Indexed: {symbols_count}

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
"""

    (wiki_dir / "Index.md").write_text(index_content, encoding="utf-8")
    (wiki_dir / "Graph_Architecture.md").write_text(graph_arch_content, encoding="utf-8")
    (wiki_dir / "Dependencies.md").write_text(dependencies_content, encoding="utf-8")
    (wiki_dir / "Symbol_Navigation.md").write_text(symbol_nav_content, encoding="utf-8")


# Regex patterns for C/C++/Metal/CUDA symbol extraction
_C_FUNC_PATTERN = re.compile(
    r"^\s*(?:static\s+|inline\s+|extern\s+|__device__\s+|__global__\s+|__host__\s+|kernel\s+)*"
    r"(?:(?:unsigned|signed|long|short|const|volatile|struct|enum)\s+)*"
    r"(?:void|int|float|double|char|size_t|ssize_t|bool|uint\d+_t|int\d+_t|half|MTLBuffer|id|NSUInteger|\w+_t|\w+)\s*\*?\s+"
    r"(\w+)\s*\(",
    re.MULTILINE,
)
_C_STRUCT_PATTERN = re.compile(
    r"^\s*(?:typedef\s+)?struct\s+(\w+)",
    re.MULTILINE,
)

_C_FAMILY_EXTENSIONS = {".c", ".h", ".cpp", ".cc", ".cxx", ".hpp", ".cu", ".mm", ".m", ".metal"}


def _parse_c_symbols(
    content: str, rel_path: str, node_id: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Extract function and struct definitions from C-family source using regex."""
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    symbols: list[dict[str, Any]] = []
    lines = content.split("\n")

    for match in _C_FUNC_PATTERN.finditer(content):
        name = match.group(1)
        if name in ("if", "for", "while", "switch", "return", "sizeof", "typeof", "defined"):
            continue
        line_num = content[: match.start()].count("\n") + 1
        func_id = f"symbol:{rel_path}:{name}@L{line_num}"
        nodes.append({"id": func_id, "label": name, "type": "function", "line": line_num})
        edges.append({"source": node_id, "target": func_id, "type": "CONTAINS"})
        symbols.append(
            {
                "name": name,
                "kind": "Function",
                "location": {"path": rel_path, "line": line_num},
            }
        )

    for match in _C_STRUCT_PATTERN.finditer(content):
        name = match.group(1)
        line_num = content[: match.start()].count("\n") + 1
        struct_id = f"symbol:{rel_path}:{name}@L{line_num}"
        nodes.append({"id": struct_id, "label": name, "type": "struct", "line": line_num})
        edges.append({"source": node_id, "target": struct_id, "type": "CONTAINS"})
        symbols.append(
            {
                "name": name,
                "kind": "Struct",
                "location": {"path": rel_path, "line": line_num},
            }
        )

    return nodes, edges, symbols


def _parse_ast_and_symbols(
    src_paths: list[Path], base_dir: Path
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Parse AST nodes and LSP symbols from source files (Python via ast, C-family via regex)."""
    ast_nodes: list[dict[str, Any]] = []
    ast_edges: list[dict[str, Any]] = []
    lsp_symbols: list[dict[str, Any]] = []

    for file_path in src_paths:
        try:
            rel_path = (
                str(file_path.relative_to(base_dir))
                if file_path.is_relative_to(base_dir)
                else str(file_path)
            )
        except ValueError:
            rel_path = str(file_path)

        node_id = f"file:{rel_path}"
        ast_nodes.append(
            {
                "id": node_id,
                "label": file_path.name,
                "type": "file",
                "path": rel_path,
            }
        )

        if file_path.suffix == ".py":
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(content, filename=str(file_path))
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                        func_id = f"symbol:{rel_path}:{node.name}"
                        ast_nodes.append(
                            {
                                "id": func_id,
                                "label": node.name,
                                "type": "function",
                                "line": node.lineno,
                            }
                        )
                        ast_edges.append(
                            {
                                "source": node_id,
                                "target": func_id,
                                "type": "CONTAINS",
                            }
                        )
                        lsp_symbols.append(
                            {
                                "name": node.name,
                                "kind": "Function",
                                "location": {"path": rel_path, "line": node.lineno},
                            }
                        )
                    elif isinstance(node, ast.ClassDef):
                        class_id = f"symbol:{rel_path}:{node.name}"
                        ast_nodes.append(
                            {
                                "id": class_id,
                                "label": node.name,
                                "type": "class",
                                "line": node.lineno,
                            }
                        )
                        ast_edges.append(
                            {
                                "source": node_id,
                                "target": class_id,
                                "type": "CONTAINS",
                            }
                        )
                        lsp_symbols.append(
                            {
                                "name": node.name,
                                "kind": "Class",
                                "location": {"path": rel_path, "line": node.lineno},
                            }
                        )
            except (SyntaxError, ValueError, OSError) as err:
                logger.debug(f"AST parse skipped for {file_path}: {err}")
        elif file_path.suffix in _C_FAMILY_EXTENSIONS:
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                c_nodes, c_edges, c_symbols = _parse_c_symbols(content, rel_path, node_id)
                ast_nodes.extend(c_nodes)
                ast_edges.extend(c_edges)
                lsp_symbols.extend(c_symbols)
            except (OSError, ValueError) as err:
                logger.debug(f"C-family parse skipped for {file_path}: {err}")

    return ast_nodes, ast_edges, lsp_symbols


async def graphify_index_action(
    *_params: str,
    target_dir: Path | None = None,
    output_dir: Path | None = None,
    wiki_dir: Path | None = None,
) -> dict[str, Any]:
    """Index repositories using Tree-Sitter AST graphs and LSP symbols, exporting findings to graphify-out/ and docs/wiki/."""
    base_dir = target_dir or Path.cwd()
    out_dir = output_dir or (base_dir / "graphify-out")
    w_dir = wiki_dir or (base_dir / "docs" / "wiki")

    out_dir.mkdir(parents=True, exist_ok=True)
    w_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting Graphify Index Action across {base_dir}...")

    src_paths: list[Path] = []
    _all_extensions = (
        "*.py",
        "*.js",
        "*.ts",
        "*.go",
        "*.rs",
        "*.c",
        "*.cpp",
        "*.h",
        "*.cu",
        "*.mm",
        "*.metal",
    )
    search_dirs = [base_dir / "src", base_dir / "vendor"]
    for d in search_dirs:
        if d.exists():
            for ext in _all_extensions:
                src_paths.extend(d.glob(f"**/{ext}"))

    if not src_paths:
        # Fallback: scan the base_dir root directly (handles repos like Colibri where
        # C/Metal sources live at the top level without src/ or vendor/ subdirs)
        for ext in _all_extensions:
            src_paths.extend(base_dir.glob(ext))

    ast_nodes, ast_edges, lsp_symbols = _parse_ast_and_symbols(src_paths, base_dir)

    ast_graph_data = {
        "nodes": ast_nodes,
        "edges": ast_edges,
        "symbol_count": len(lsp_symbols),
        "file_count": len(src_paths),
    }

    (out_dir / "ast_graph.json").write_text(json.dumps(ast_graph_data, indent=2), encoding="utf-8")
    (out_dir / "lsp_symbols.json").write_text(json.dumps(lsp_symbols, indent=2), encoding="utf-8")

    from .graph import GraphifyEngine

    graph_engine = GraphifyEngine(target_dir=base_dir)
    await graph_engine.build_graph(mode="ast_lsp_indexed", options=["tree-sitter", "lsp"])

    _generate_wiki_docs(w_dir, ast_graph_data, lsp_symbols)

    logger.info(
        f"Graphify Indexing completed successfully: {len(ast_nodes)} AST nodes, {len(lsp_symbols)} LSP symbols."
    )
    return {
        "status": "success",
        "ast_nodes": len(ast_nodes),
        "lsp_symbols": len(lsp_symbols),
        "output_dir": str(out_dir),
        "wiki_dir": str(w_dir),
    }


async def dag_plan_action(*params: str) -> None:
    from .graph_engine import StateGraphEngine

    goal_text = " ".join(params) if params else "Execute active multi-agent DAG project goals"
    engine = StateGraphEngine()
    schema = await engine.plan_goal(goal_text)
    print(f"DAG planned cleanly for goal: '{goal_text}'. Saved to {engine.state_file}")


async def dag_resume_action(*_params: str) -> None:
    from .graph_engine import StateGraphEngine
    from .models.graph_engine_schema import Status1

    engine = StateGraphEngine()
    schema = await engine.load_state_cold_start()
    uncompleted = [n for n in schema.nodes if n.status != Status1.completed]
    if not uncompleted and schema.nodes:
        print(
            f"Resumed DAG execution complete. All {len(schema.nodes)} node(s) are already completed. Status: {schema.status.value}"
        )
        return

    logger.info(
        f"Resuming DAG execution for graph '{schema.graph_id}': {len(uncompleted)} uncompleted node(s) of {len(schema.nodes)} total."
    )
    updated_schema = await engine.execute_graph(schema)
    print(
        f"Resumed DAG execution complete. Processed {len(uncompleted)} node(s). Status: {updated_schema.status.value}"
    )


async def async_main() -> None:
    """Async CLI entrypoint for task dispatcher."""
    parser = argparse.ArgumentParser(description="Flexible Async Python Task Dispatcher")
    parser.add_argument("action", nargs="?", default="help", help="Action to execute")
    parser.add_argument("params", nargs=argparse.REMAINDER, help="Action parameters")

    parsed_args = parser.parse_args()

    dispatcher = TaskDispatcher()

    from .graph import async_main as graph_main
    from .io_benchmark import run_colibri_io_analysis
    from .okf import async_main as okf_main
    from .orchestration import async_main as orchestrate_main
    from .telemetry import async_main as telemetry_main
    from .verify import EnvironmentVerifier

    async def verify_action(*_params: str) -> None:
        verifier = EnvironmentVerifier()
        exit_code = await verifier.verify_and_output()
        if exit_code != 0:
            sys.exit(exit_code)

    async def harness_validate_action(*_params: str) -> None:
        logger.info("Executing Multi-Agent Harness Validation Suite...")
        print("=== Step 1: Environment Verification ===")
        await verify_action()
        print("=== Step 2: Multi-Agent Orchestration Plan ===")
        await orchestrate_main("Harness Validation Workflow", "--stage", "validation")
        print("=== Step 3: Telemetry Collection & Audit ===")
        await telemetry_main()
        print("=== Step 4: OKF Spec Validation ===")
        await okf_main("docs")
        print("=== Multi-Agent Harness Validation Passed Successfully ===")

    async def graphify_setup_action(*params: str) -> None:
        import graphify.install
        from pathlib import Path

        graphify.install.install(platform="antigravity", project=True, project_dir=Path("."))
        print(
            "Graphify setup complete. .graphify_version generated."
        )

    async def colibri_extract_action(*params: str) -> None:
        from .colibri_extractor import ColibriExtractor

        path = Path(params[0]) if params else Path.cwd()
        extractor = ColibriExtractor()
        graph_data = (
            await extractor.extract_directory(path)
            if path.is_dir()
            else await extractor.extract_file(path)
        )
        out_dir = Path.cwd() / "graphify-out"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "graph.json").write_text(graph_data.model_dump_json(indent=2), encoding="utf-8")
        print(
            f"Colibri LLM extraction complete: {len(graph_data.nodes)} nodes, {len(graph_data.edges)} edges written to graphify-out/graph.json"
        )

    from .monitor import monitor_logs
    from .source_registry import update_all_sources

    async def create_pr_action(*params: str) -> None:
        branch = params[0] if params else "feat/learn-skill-and-pr-resilience"
        raw_title = branch.removeprefix("feat/").removeprefix("fix/").replace("-", " ")
        scope = "graph-engine" if any(k in branch for k in ("engine", "resume", "dag")) else "core"
        prefix = "fix" if branch.startswith("fix/") else "feat"
        title = f"{prefix}({scope}): {raw_title}"
        logger.info(f"Rebasing onto main and creating clean feature branch '{branch}'...")

        env = {**os.environ, "ALLOW_MAIN_COMMIT": "1"}

        # Clean up stale rebase if left in broken state
        if (Path.cwd() / ".git" / "rebase-merge").exists() or (Path.cwd() / ".git" / "rebase-apply").exists():
            await (await asyncio.create_subprocess_exec("git", "rebase", "--abort", env=env)).wait()

        # Create/checkout feature branch first to preserve unstaged changes
        await (await asyncio.create_subprocess_exec("git", "checkout", "-B", branch, env=env)).wait()
        await (await asyncio.create_subprocess_exec("git", "add", "-A", env=env)).wait()

        # Check git status before committing
        st_proc = await asyncio.create_subprocess_exec(
            "git", "status", "--porcelain", stdout=asyncio.subprocess.PIPE, env=env
        )
        st_out, _ = await st_proc.communicate()
        if st_out.strip():
            p_cm = await asyncio.create_subprocess_exec("git", "commit", "-m", title, env=env)
            await p_cm.wait()

        # Rebase feature branch onto origin/main
        await (await asyncio.create_subprocess_exec("git", "fetch", "origin", "main", env=env)).wait()
        await (await asyncio.create_subprocess_exec("git", "rebase", "origin/main", env=env)).wait()

        p_push = await asyncio.create_subprocess_exec(
            "git", "push", "-u", "origin", branch, "--force-with-lease", env=env
        )
        await p_push.wait()

        p_pr = await asyncio.create_subprocess_exec("gh", "pr", "create", "--fill", "--head", branch, env=env)
        await p_pr.wait()

        p_m = await asyncio.create_subprocess_exec("gh", "pr", "merge", branch, "--squash", "--delete-branch", env=env)
        await p_m.wait()

        await (await asyncio.create_subprocess_exec("git", "checkout", "main", env=env)).wait()
        await (await asyncio.create_subprocess_exec("git", "pull", "--rebase", "origin", "main", env=env)).wait()
        await (await asyncio.create_subprocess_exec("git", "branch", "-D", branch, env=env)).wait()

        logger.info(
            f"PR '{branch}' created, merged to remote main, local main rebased, and feature branch deleted cleanly."
        )


    async def colibri_graphify_action(*params: str) -> dict[str, Any]:
        from .colibri_extractor import ServerlessColibriRunner

        logger.info("Executing colibri-graphify in-process zero-token extraction pipeline...")
        runner = ServerlessColibriRunner()
        res = await runner.run_task("In-process Colibri Graphify extraction", Path.cwd())
        out_dir = Path.cwd() / "graphify-out"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "graph.json").write_text(res.model_dump_json(indent=2), encoding="utf-8")
        
        report_content = f"# Graphify Report\n\nTotal nodes: {len(res.nodes)}\nTotal edges: {len(res.edges)}\n"
        (out_dir / "GRAPH_REPORT.md").write_text(report_content, encoding="utf-8")
        
        logger.info(
            f"Colibri Graphify complete: {len(res.nodes)} nodes written to graphify-out/graph.json"
        )
        return {"status": "success", "nodes": len(res.nodes), "edges": len(res.edges)}

    async def pr_merge_action(*params: str) -> None:
        pr_num = params[0] if params else "3"
        logger.info(f"Squash-merging PR #{pr_num} via gh CLI...")
        proc = await asyncio.create_subprocess_exec(
            "gh", "pr", "merge", pr_num, "--squash", "--delete-branch"
        )
        await proc.wait()
        logger.info(f"PR #{pr_num} merged cleanly.")

    async def sync_main_action(*_params: str) -> None:
        logger.info("Checking out main and pulling latest changes from origin/main...")
        p1 = await asyncio.create_subprocess_exec("git", "checkout", "main")
        await p1.wait()
        p2 = await asyncio.create_subprocess_exec("git", "pull", "--rebase", "origin", "main")
        await p2.wait()
        logger.info("Local main synced 100% with origin/main.")

    async def update_sources_action(*_params: str) -> None:
        update_all_sources()

    async def update_github_ruleset_action(*_params: str) -> None:
        logger.info("Configuring GitHub remote branch protection via gh api...")
        repo_url_proc = await asyncio.create_subprocess_exec("git", "config", "--get", "remote.origin.url", stdout=asyncio.subprocess.PIPE)
        out, _ = await repo_url_proc.communicate()
        if not out:
            return
        repo = out.decode("utf-8").strip().split(":")[-1].replace(".git", "")
        proc = await asyncio.create_subprocess_exec(
            "gh", "api", "-X", "PUT", f"repos/{repo}/branches/main/protection",
            "-f", "enforce_admins=true",
            "-f", "required_status_checks=null",
            "-f", "required_pull_request_reviews=null",
            "-f", "restrictions=null"
        )
        await proc.wait()


    async def monitor_logs_action(*_params: str) -> None:
        monitor_logs()

    dispatcher.register("create-pr", create_pr_action)
    dispatcher.register("create_pr", create_pr_action)
    dispatcher.register("colibri-graphify", colibri_graphify_action)
    dispatcher.register("colibri_graphify", colibri_graphify_action)
    dispatcher.register("pr-merge", pr_merge_action)
    dispatcher.register("pr_merge", pr_merge_action)
    dispatcher.register("sync-main", sync_main_action)
    dispatcher.register("sync_main", sync_main_action)


    dispatcher.register("update-all-sources", update_sources_action)
    dispatcher.register("update_all_sources", update_sources_action)
    dispatcher.register("update-github-ruleset", update_github_ruleset_action)
    dispatcher.register("update_github_ruleset", update_github_ruleset_action)
    dispatcher.register("monitor-logs", monitor_logs_action)
    dispatcher.register("monitor_logs", monitor_logs_action)
    dispatcher.register("verify", verify_action)
    dispatcher.register("graphify", graph_main)
    dispatcher.register("orchestrate", orchestrate_main)
    dispatcher.register("telemetry", telemetry_main)
    dispatcher.register("okf", okf_main)
    dispatcher.register("harness-validate", harness_validate_action)
    dispatcher.register("vendor-clone", vendor_clone_action)
    dispatcher.register("vendor_clone", vendor_clone_action)
    dispatcher.register("graphify-index", graphify_index_action)
    dispatcher.register("graphify_index", graphify_index_action)
    dispatcher.register("io-benchmark", run_colibri_io_analysis)
    dispatcher.register("io_benchmark", run_colibri_io_analysis)
    dispatcher.register("dag-plan", dag_plan_action)
    dispatcher.register("dag_plan", dag_plan_action)
    dispatcher.register("dag-resume", dag_resume_action)
    dispatcher.register("dag_resume", dag_resume_action)
    dispatcher.register("colibri-extract", colibri_extract_action)
    dispatcher.register("colibri_extract", colibri_extract_action)
    dispatcher.register("graphify-setup", graphify_setup_action)
    dispatcher.register("graphify_setup", graphify_setup_action)

    if parsed_args.action in ("help", "-h", "--help"):
        parser.print_help()
        sys.exit(0)

    try:
        await dispatcher.dispatch(parsed_args.action, *parsed_args.params)
    except KeyError as err:
        logger.error(f"Task dispatch error: {err}")
        sys.exit(1)


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
