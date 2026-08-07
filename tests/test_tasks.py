"""Unit tests for tasks module including vendor_clone_action and graphify_index_action."""

import json
from pathlib import Path

import pytest

from agy_graphify.tasks import TaskDispatcher, graphify_index_action, vendor_clone_action


@pytest.mark.asyncio
async def test_task_dispatcher_registration() -> None:
    dispatcher = TaskDispatcher()

    async def dummy_async_action(name: str) -> str:
        return f"hello {name}"

    def dummy_sync_action(x: int) -> int:
        return x * 2

    dispatcher.register("greet", dummy_async_action)
    dispatcher.register("double", dummy_sync_action)

    res_async = await dispatcher.dispatch("greet", "world")
    assert res_async == "hello world"

    res_sync = await dispatcher.dispatch("double", 21)
    assert res_sync == 42

    with pytest.raises(KeyError, match="Unknown action 'unknown'"):
        await dispatcher.dispatch("unknown")


@pytest.mark.asyncio
async def test_vendor_clone_action_default(tmp_path: Path) -> None:
    vendor_dir = tmp_path / "vendor"
    cloned_paths = await vendor_clone_action(vendor_dir=vendor_dir)

    assert len(cloned_paths) == 4
    expected_names = {"graphifyy", "mindwalk", "codebase-memory-mcp", "code-review-graph"}
    actual_names = {p.name for p in cloned_paths}
    assert expected_names == actual_names

    for p in cloned_paths:
        assert p.exists()
        assert p.is_dir()


@pytest.mark.asyncio
async def test_vendor_clone_action_custom_repos(tmp_path: Path) -> None:
    vendor_dir = tmp_path / "custom_vendor"
    cloned_paths = await vendor_clone_action(
        "custom/repo1",
        "https://github.com/custom/repo2.git",
        vendor_dir=vendor_dir,
    )

    assert len(cloned_paths) == 2
    actual_names = {p.name for p in cloned_paths}
    assert actual_names == {"repo1", "repo2"}


@pytest.mark.asyncio
async def test_graphify_index_action(tmp_path: Path) -> None:
    src_dir = tmp_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    sample_file = src_dir / "sample.py"
    sample_file.write_text(
        "class DummyModel:\n"
        "    pass\n\n"
        "async def process_data(item: str) -> bool:\n"
        "    return True\n",
        encoding="utf-8",
    )

    out_dir = tmp_path / "graphify-out"
    wiki_dir = tmp_path / "docs" / "wiki"

    result = await graphify_index_action(
        target_dir=tmp_path,
        output_dir=out_dir,
        wiki_dir=wiki_dir,
    )

    assert result["status"] == "success"
    assert result["ast_nodes"] >= 2
    assert result["lsp_symbols"] >= 2

    ast_graph_file = out_dir / "ast_graph.json"
    lsp_symbols_file = out_dir / "lsp_symbols.json"
    assert ast_graph_file.exists()
    assert lsp_symbols_file.exists()

    ast_data = json.loads(ast_graph_file.read_text(encoding="utf-8"))
    assert "nodes" in ast_data
    assert "edges" in ast_data

    lsp_data = json.loads(lsp_symbols_file.read_text(encoding="utf-8"))
    symbol_names = {s["name"] for s in lsp_data}
    assert "DummyModel" in symbol_names
    assert "process_data" in symbol_names

    wiki_files = list(wiki_dir.glob("*.md"))
    wiki_names = {f.name for f in wiki_files}
    assert {
        "Index.md",
        "Graph_Architecture.md",
        "Dependencies.md",
        "Symbol_Navigation.md",
    }.issubset(wiki_names)

    index_text = (wiki_dir / "Index.md").read_text(encoding="utf-8")
    assert "[[Graph_Architecture]]" in index_text
    assert "[[Dependencies]]" in index_text
    assert "[[Symbol_Navigation]]" in index_text
    assert "```mermaid" in index_text
    assert "---" in index_text
    assert "doc_id: okf-wiki-index" in index_text


# ──────────────────────────────────────────────────────────
# Tests for _parse_c_symbols and _C_FAMILY_EXTENSIONS
# ──────────────────────────────────────────────────────────

from agy_graphify.tasks import _C_FAMILY_EXTENSIONS, _parse_c_symbols


def test_parse_c_symbols_simple_function() -> None:
    """Single C function should be extracted."""
    source = "int main(int argc, char **argv) {\n    return 0;\n}\n"
    nodes, edges, symbols = _parse_c_symbols(source, "test.c", "file:test.c")

    assert any(s["name"] == "main" and s["kind"] == "Function" for s in symbols)
    assert any(n["label"] == "main" and n["type"] == "function" for n in nodes)
    assert any(e["source"] == "file:test.c" and e["type"] == "CONTAINS" for e in edges)


def test_parse_c_symbols_struct() -> None:
    """Struct definition should be extracted."""
    source = "struct MyConfig {\n    int value;\n};\n"
    nodes, edges, symbols = _parse_c_symbols(source, "config.h", "file:config.h")

    assert any(s["name"] == "MyConfig" and s["kind"] == "Struct" for s in symbols)
    assert any(n["type"] == "struct" for n in nodes)


def test_parse_c_symbols_filters_keywords() -> None:
    """C keywords like if, for, while should be filtered out."""
    source = "if (x > 0) {\n}\nfor (int i = 0; i < n; i++) {\n}\nwhile (running) {\n}\n"
    nodes, edges, symbols = _parse_c_symbols(source, "test.c", "file:test.c")

    names = {s["name"] for s in symbols}
    assert "if" not in names
    assert "for" not in names
    assert "while" not in names


def test_parse_c_symbols_multiple_functions() -> None:
    """Multiple functions in one file should all be extracted."""
    source = (
        "void init(void) {}\n"
        "int compute(int x) { return x * 2; }\n"
        "static float helper(float a, float b) { return a + b; }\n"
    )
    nodes, edges, symbols = _parse_c_symbols(source, "multi.c", "file:multi.c")

    names = {s["name"] for s in symbols}
    assert "init" in names
    assert "compute" in names
    assert "helper" in names


def test_parse_c_symbols_empty_source() -> None:
    """Empty source should return empty lists."""
    nodes, edges, symbols = _parse_c_symbols("", "empty.c", "file:empty.c")
    assert nodes == []
    assert edges == []
    assert symbols == []


def test_parse_c_symbols_line_numbers() -> None:
    """Line numbers should be correctly computed."""
    source = "// comment\nvoid foo(void) {}\n// another\nint bar(int x) {}\n"
    nodes, edges, symbols = _parse_c_symbols(source, "lines.c", "file:lines.c")

    foo_sym = next(s for s in symbols if s["name"] == "foo")
    bar_sym = next(s for s in symbols if s["name"] == "bar")
    assert foo_sym["location"]["line"] == 2
    assert bar_sym["location"]["line"] == 4


def test_c_family_extensions_completeness() -> None:
    """_C_FAMILY_EXTENSIONS should contain all expected extensions."""
    expected = {".c", ".h", ".cpp", ".cc", ".cxx", ".hpp", ".cu", ".mm", ".m", ".metal"}
    assert expected == _C_FAMILY_EXTENSIONS


def test_c_family_extensions_excludes_python() -> None:
    """_C_FAMILY_EXTENSIONS should NOT include .py or .js."""
    assert ".py" not in _C_FAMILY_EXTENSIONS
    assert ".js" not in _C_FAMILY_EXTENSIONS


# ──────────────────────────────────────────────────────────
# Tests for root-level file discovery fallback
# ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_graphify_index_root_level_fallback(tmp_path: Path) -> None:
    """When no src/ or vendor/ dirs exist, index should fall back to root-level scan."""
    # Put .c and .h files directly in the base_dir (no src/ subdir)
    c_file = tmp_path / "main.c"
    c_file.write_text(
        "int entry_point(void) {\n    return 0;\n}\n",
        encoding="utf-8",
    )
    h_file = tmp_path / "config.h"
    h_file.write_text(
        "struct AppConfig {\n    int debug;\n};\n",
        encoding="utf-8",
    )

    out_dir = tmp_path / "graphify-out"
    wiki_dir = tmp_path / "docs" / "wiki"

    result = await graphify_index_action(
        target_dir=tmp_path,
        output_dir=out_dir,
        wiki_dir=wiki_dir,
    )

    assert result["status"] == "success"
    # Should find at least the file nodes + function + struct
    assert result["ast_nodes"] >= 2
    assert result["lsp_symbols"] >= 1

    lsp_data = json.loads((out_dir / "lsp_symbols.json").read_text(encoding="utf-8"))
    symbol_names = {s["name"] for s in lsp_data}
    assert "entry_point" in symbol_names or "AppConfig" in symbol_names
