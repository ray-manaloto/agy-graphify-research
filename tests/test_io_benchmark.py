"""Unit tests for the io_benchmark module (analyze_io_pipeline, generate_benchmark_report)."""

import json
from pathlib import Path
from typing import Any

import pytest

from agy_graphify.io_benchmark import (
    IO_PIPELINE_SYMBOLS,
    OPTIMIZATION_SURFACES,
    analyze_io_pipeline,
    generate_benchmark_report,
    run_colibri_io_analysis,
)


def _make_graph(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    return {"nodes": nodes, "edges": edges}


def _write_graph(tmp_path: Path, graph: dict[str, Any]) -> Path:
    p = tmp_path / "ast_graph.json"
    p.write_text(json.dumps(graph), encoding="utf-8")
    return p


# ---------- analyze_io_pipeline ----------


def test_analyze_io_pipeline_empty_graph(tmp_path: Path) -> None:
    """Empty graph should return zeros and 0% coverage."""
    path = _write_graph(tmp_path, _make_graph([], []))
    result = analyze_io_pipeline(path)

    assert result["graph_summary"]["total_nodes"] == 0
    assert result["graph_summary"]["total_edges"] == 0
    assert result["io_pipeline"]["coverage_pct"] == 0.0
    assert result["io_pipeline"]["symbols_found"] == 0
    assert len(result["io_pipeline"]["missing"]) == len(IO_PIPELINE_SYMBOLS)


def test_analyze_io_pipeline_full_coverage(tmp_path: Path) -> None:
    """Graph with all IO_PIPELINE_SYMBOLS present should reach 100% coverage."""
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    for i, (name, info) in enumerate(IO_PIPELINE_SYMBOLS.items()):
        file_path = info["file"]
        node_id = f"file:{file_path}"
        func_id = f"symbol:{file_path}:{name}@L{10 * (i + 1)}"
        if not any(n["id"] == node_id for n in nodes):
            nodes.append({"id": node_id, "label": file_path, "type": "file", "path": file_path})
        nodes.append({"id": func_id, "label": name, "type": "function", "line": 10 * (i + 1)})
        edges.append({"source": node_id, "target": func_id, "type": "CONTAINS"})

    path = _write_graph(tmp_path, _make_graph(nodes, edges))
    result = analyze_io_pipeline(path)

    assert result["io_pipeline"]["coverage_pct"] == 100.0
    assert result["io_pipeline"]["symbols_found"] == len(IO_PIPELINE_SYMBOLS)
    assert result["io_pipeline"]["missing"] == []


def test_analyze_io_pipeline_partial_coverage(tmp_path: Path) -> None:
    """Only some symbols present → partial coverage."""
    first_sym = list(IO_PIPELINE_SYMBOLS.keys())[0]
    info = IO_PIPELINE_SYMBOLS[first_sym]
    nodes = [
        {"id": f"file:{info['file']}", "label": info["file"], "type": "file", "path": info["file"]},
        {
            "id": f"symbol:{info['file']}:{first_sym}@L1",
            "label": first_sym,
            "type": "function",
            "line": 1,
        },
    ]
    edges = [
        {
            "source": f"file:{info['file']}",
            "target": f"symbol:{info['file']}:{first_sym}@L1",
            "type": "CONTAINS",
        }
    ]

    path = _write_graph(tmp_path, _make_graph(nodes, edges))
    result = analyze_io_pipeline(path)

    assert 0.0 < result["io_pipeline"]["coverage_pct"] < 100.0
    assert result["io_pipeline"]["symbols_found"] == 1
    assert first_sym not in result["io_pipeline"]["missing"]


def test_analyze_io_pipeline_structs_counted(tmp_path: Path) -> None:
    """Struct nodes contribute to total_structs count."""
    nodes = [
        {"id": "file:test.h", "label": "test.h", "type": "file", "path": "test.h"},
        {"id": "symbol:test.h:MyStruct@L5", "label": "MyStruct", "type": "struct", "line": 5},
    ]
    edges = [{"source": "file:test.h", "target": "symbol:test.h:MyStruct@L5", "type": "CONTAINS"}]
    path = _write_graph(tmp_path, _make_graph(nodes, edges))
    result = analyze_io_pipeline(path)

    assert result["graph_summary"]["total_structs"] == 1
    assert result["graph_summary"]["total_files"] == 1


def test_analyze_io_pipeline_optimization_surfaces_returned(tmp_path: Path) -> None:
    """Optimization surfaces should always be returned regardless of graph content."""
    path = _write_graph(tmp_path, _make_graph([], []))
    result = analyze_io_pipeline(path)

    assert result["optimization_surfaces"] == OPTIMIZATION_SURFACES
    assert len(result["optimization_surfaces"]) == 6


# ---------- generate_benchmark_report ----------


def test_generate_benchmark_report_creates_file(tmp_path: Path) -> None:
    """Report file should be created with markdown content."""
    analysis = {
        "graph_summary": {
            "total_nodes": 10,
            "total_edges": 5,
            "total_files": 3,
            "total_functions": 5,
            "total_structs": 2,
        },
        "io_pipeline": {
            "coverage_pct": 40.0,
            "symbols_found": 2,
            "symbols_expected": 5,
            "symbols": {},
            "missing": ["pread_full"],
        },
        "io_files": {},
        "optimization_surfaces": OPTIMIZATION_SURFACES,
    }

    out = tmp_path / "report.md"
    generate_benchmark_report(analysis, out)

    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "# Colibri MoE Direct I/O Pipeline" in text
    assert "40.0%" in text
    assert "pread_full" in text


def test_generate_benchmark_report_with_symbols(tmp_path: Path) -> None:
    """Report should render the symbol table when symbols are present."""
    analysis = {
        "graph_summary": {
            "total_nodes": 5,
            "total_edges": 3,
            "total_files": 1,
            "total_functions": 2,
            "total_structs": 0,
        },
        "io_pipeline": {
            "coverage_pct": 100.0,
            "symbols_found": 1,
            "symbols_expected": 1,
            "symbols": {
                "expert_load": {
                    "file": "colibri.c",
                    "role": "primary_hotpath",
                    "io_mode": ["buffered_pread", "O_DIRECT_pread"],
                    "line": 100,
                    "found": True,
                }
            },
            "missing": [],
        },
        "io_files": {},
        "optimization_surfaces": [],
    }

    out = tmp_path / "report2.md"
    generate_benchmark_report(analysis, out)

    text = out.read_text(encoding="utf-8")
    assert "`expert_load`" in text
    assert "`colibri.c`" in text
    assert "primary_hotpath" in text


def test_generate_benchmark_report_no_missing(tmp_path: Path) -> None:
    """Report should not have missing-symbols alert when missing is empty."""
    analysis = {
        "graph_summary": {
            "total_nodes": 0,
            "total_edges": 0,
            "total_files": 0,
            "total_functions": 0,
            "total_structs": 0,
        },
        "io_pipeline": {
            "coverage_pct": 100.0,
            "symbols_found": 5,
            "symbols_expected": 5,
            "symbols": {},
            "missing": [],
        },
        "io_files": {},
        "optimization_surfaces": [],
    }

    out = tmp_path / "report3.md"
    generate_benchmark_report(analysis, out)

    text = out.read_text(encoding="utf-8")
    assert "Missing symbols" not in text


# ---------- run_colibri_io_analysis ----------


@pytest.mark.asyncio
async def test_run_colibri_io_analysis_file_not_found(tmp_path: Path) -> None:
    """Should raise FileNotFoundError when the graph file doesn't exist."""
    with pytest.raises(FileNotFoundError, match="AST graph not found"):
        await run_colibri_io_analysis(ast_graph_path=tmp_path / "nonexistent.json")


@pytest.mark.asyncio
async def test_run_colibri_io_analysis_end_to_end(tmp_path: Path) -> None:
    """Full pipeline: analyze + generate report + JSON output."""
    nodes = [
        {"id": "file:colibri.c", "label": "colibri.c", "type": "file", "path": "colibri.c"},
        {
            "id": "symbol:colibri.c:expert_load@L100",
            "label": "expert_load",
            "type": "function",
            "line": 100,
        },
    ]
    edges = [
        {
            "source": "file:colibri.c",
            "target": "symbol:colibri.c:expert_load@L100",
            "type": "CONTAINS",
        }
    ]
    graph_path = _write_graph(tmp_path, _make_graph(nodes, edges))
    report_path = tmp_path / "report.md"

    result = await run_colibri_io_analysis(ast_graph_path=graph_path, report_path=report_path)

    assert result["status"] == "success"
    assert result["coverage_pct"] == 20.0
    assert result["optimization_surfaces"] == 6
    assert report_path.exists()

    json_path = report_path.with_suffix(".json")
    assert json_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert "graph_summary" in data
