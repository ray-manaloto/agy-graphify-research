"""Integration test for OpenAI Symphony Colibri MoE Benchmarking Campaign workflow."""

import json
from pathlib import Path

import pytest

from agy_graphify.graph_engine import EventDispatcher, StateGraphEngine
from agy_graphify.models.graph_engine_schema import Status, Status1
from agy_graphify.telemetry import CausalTelemetryEvent, MemoryStoreAdapter
from agy_graphify.workflow_parser import SymphonyWorkflowParser


@pytest.mark.asyncio
async def test_colibri_moe_benchmark_workflow_execution(tmp_path: Path) -> None:
    yaml_path = Path("docs/workflows/colibri_moe_benchmark.yaml")
    assert yaml_path.is_file()

    # Step 1: Parse workflow with SymphonyWorkflowParser
    schema = SymphonyWorkflowParser.parse_yaml_file(str(yaml_path))
    assert schema.graph_id == "colibri_moe_benchmark_workflow"
    assert len(schema.nodes) == 5

    expected_nodes = [
        "plan_benchmark",
        "inspect_metal_shaders",
        "execute_benchmark_suite",
        "verify_telemetry_spans",
        "qa_adversarial_review",
    ]
    node_ids = [n.id for n in schema.nodes]
    assert node_ids == expected_nodes

    # Setup mock project guardrails in tmp_path
    gemini_dir = tmp_path / ".gemini"
    gemini_dir.mkdir(parents=True, exist_ok=True)
    (gemini_dir / "settings.json").write_text("{}", encoding="utf-8")
    rules_dir = gemini_dir / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    (rules_dir / "test_rule.md").write_text("# Test Rule", encoding="utf-8")
    mise_file = tmp_path / ".mise.toml"
    mise_content = (
        "[tools]\n"
        'python = "3.14.7"\n'
        'uv = "0.12.2"\n'
        'ruff = "0.16.1"\n'
        'ty = "0.0.68"\n'
        'hk = "1.54.0"\n'
        'fnox = "1.32.0"\n'
        'pkl = "0.32.1"\n'
        'taplo = "0.10.0"\n'
        'gh = "2.97.0"\n'
    )
    mise_file.write_text(mise_content, encoding="utf-8")

    # Step 2: Instantiate engine and dispatcher
    dispatcher = EventDispatcher()
    engine = StateGraphEngine(project_dir=tmp_path, dispatcher=dispatcher)

    # Step 3: Subscribe MemoryStoreAdapter to EventDispatcher
    telemetry_dir = tmp_path / ".gemini" / "telemetry"
    memory_adapter = MemoryStoreAdapter(output_dir=telemetry_dir)
    memory_adapter.subscribe_to_dispatcher(dispatcher)

    # Step 4: Execute graph
    result_schema = await engine.execute_graph(schema)

    # Step 5: Assert execution status
    assert result_schema.status == Status.completed
    for n in result_schema.nodes:
        assert n.status == Status1.completed
        assert n.status.value == "completed"

    # Step 6: Verify causal_events.jsonl and SHA-256 hash chains
    causal_file = telemetry_dir / "causal_events.jsonl"
    assert causal_file.is_file()

    lines = [line for line in causal_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 12

    prev_hash = ""
    for line in lines:
        raw = json.loads(line)
        event = CausalTelemetryEvent.model_validate(raw)
        expected_hash = event.compute_causal_hash(prev_hash)
        assert event.causal_hash == expected_hash
        assert len(event.causal_hash) == 64
        prev_hash = event.causal_hash
