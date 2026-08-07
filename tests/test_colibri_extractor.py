from pathlib import Path

import pytest

from agy_graphify.colibri_extractor import ColibriExtractor
from agy_graphify.config import ColibriConfig, GraphifyConfig
from agy_graphify.graph import GraphifyEngine
from agy_graphify.models.graph_schema import GraphData


def test_graphify_config_load_save(tmp_path: Path):
    cfg_file = tmp_path / "config.json"
    cfg = GraphifyConfig(
        active_llm_assistant="colibri",
        colibri=ColibriConfig(server_url="http://127.0.0.1:8080/v1", context_length=8192),
        global_memory_dir=str(tmp_path / "global_memory"),
    )
    cfg.save(cfg_file)
    assert cfg_file.is_file()

    loaded = GraphifyConfig.load(cfg_file)
    assert loaded.active_llm_assistant == "colibri"
    assert loaded.colibri.server_url == "http://127.0.0.1:8080/v1"
    assert loaded.colibri.context_length == 8192


@pytest.mark.asyncio
async def test_colibri_extractor_fallback_extraction(tmp_path: Path):
    sample_file = tmp_path / "engine.py"
    sample_file.write_text("class ColibriEngine:\n    pass\n", encoding="utf-8")

    cfg = GraphifyConfig(
        active_llm_assistant="colibri",
        colibri=ColibriConfig(server_url="http://127.0.0.1:9999/v1", auto_launch=False),
        global_memory_dir=str(tmp_path / "global_memory"),
    )
    extractor = ColibriExtractor(config=cfg)

    graph_data = await extractor.extract_file(sample_file)
    assert isinstance(graph_data, GraphData)
    assert len(graph_data.nodes) >= 1
    assert graph_data.metadata["extractor"] == "ColibriExtractor"


@pytest.mark.asyncio
async def test_colibri_extractor_directory(tmp_path: Path):
    (tmp_path / "mod1.py").write_text("def fn1(): pass\n", encoding="utf-8")
    (tmp_path / "doc.md").write_text("# Title\nContent\n", encoding="utf-8")

    cfg = GraphifyConfig(
        active_llm_assistant="colibri",
        colibri=ColibriConfig(server_url="http://127.0.0.1:9999/v1", auto_launch=False),
        global_memory_dir=str(tmp_path / "global_memory"),
    )
    extractor = ColibriExtractor(config=cfg)

    graph_data = await extractor.extract_directory(tmp_path)
    assert isinstance(graph_data, GraphData)
    assert len(graph_data.nodes) >= 1
    assert graph_data.metadata["total_files"] == 2


def test_colibri_record_learning(tmp_path: Path):
    global_mem = tmp_path / "global_memory"
    cfg = GraphifyConfig(
        active_llm_assistant="colibri",
        global_memory_dir=str(global_mem),
    )
    extractor = ColibriExtractor(config=cfg)

    node = extractor.record_learning(
        "How does Metal GPU acceleration work?", "Colibri uses backend_metal.mm shaders."
    )
    assert node.type == "qa_learning"
    assert (global_mem / "learnings.jsonl").is_file()


@pytest.mark.asyncio
async def test_graphify_engine_colibri_mode(tmp_path: Path):
    cfg_dir = Path.home() / ".graphify"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / "main.c").write_text("int main() { return 0; }\n", encoding="utf-8")
    engine = GraphifyEngine(target_dir=tmp_path)
    graph_data = await engine.build_graph(mode="colibri")
    assert isinstance(graph_data, GraphData)
    assert (tmp_path / "graphify-out" / "graph.json").is_file()
