"""Async unit tests for GraphifyEngine using pytest."""

import pytest

from agy_graphify.graph import GraphifyEngine


@pytest.mark.asyncio
async def test_build_graph(tmp_path):
    engine = GraphifyEngine(target_dir=tmp_path)
    graph_data = await engine.build_graph(mode="deep")

    assert len(graph_data.nodes) == 3
    assert len(graph_data.edges) == 2
    assert (tmp_path / "graphify-out" / "graph.json").is_file()
    assert (tmp_path / "graphify-out" / "GRAPH_REPORT.md").is_file()


@pytest.mark.asyncio
async def test_query_graph(tmp_path):
    engine = GraphifyEngine(target_dir=tmp_path)
    result = await engine.query_graph("How does graphify work?", traversal="bfs")

    assert "BFS" in result
    assert "Query" in result
