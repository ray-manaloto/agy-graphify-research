"""Execution script for OpenAI Symphony Colibri MoE Benchmarking Campaign workflow."""

import asyncio
import json
from pathlib import Path

from agy_graphify.graph_engine import EventDispatcher, StateGraphEngine
from agy_graphify.models.graph_engine_schema import Status, Status1
from agy_graphify.telemetry import CausalTelemetryEvent, MemoryStoreAdapter
from agy_graphify.workflow_parser import SymphonyWorkflowParser


async def execute_colibri_workflow(
    yaml_path: str = "docs/workflows/colibri_moe_benchmark.yaml",
    project_dir: Path | None = None,
) -> dict:
    proj_dir = (project_dir or Path.cwd()).resolve()
    telemetry_dir = proj_dir / ".gemini" / "telemetry"

    # Step 1: Parse workflow spec
    schema = SymphonyWorkflowParser.parse_yaml_file(yaml_path)
    assert schema.graph_id == "colibri_moe_benchmark_workflow"
    assert len(schema.nodes) == 5

    # Step 2: Instantiate StateGraphEngine and EventDispatcher
    dispatcher = EventDispatcher()
    engine = StateGraphEngine(project_dir=proj_dir, dispatcher=dispatcher)

    # Step 3: Subscribe MemoryStoreAdapter to EventDispatcher
    memory_adapter = MemoryStoreAdapter(output_dir=telemetry_dir)
    memory_adapter.subscribe_to_dispatcher(dispatcher)

    # Step 4: Execute the 5 DAG nodes
    result_schema = await engine.execute_graph(schema)

    # Step 5: Assert execution status
    expected_nodes = [
        "plan_benchmark",
        "inspect_metal_shaders",
        "execute_benchmark_suite",
        "verify_telemetry_spans",
        "qa_adversarial_review",
    ]
    node_dict = {n.id: n for n in result_schema.nodes}
    assert result_schema.status == Status.completed or result_schema.status.value == "completed"

    for node_id in expected_nodes:
        assert node_id in node_dict, f"Node {node_id} missing from executed graph"
        node_status = node_dict[node_id].status
        assert node_status == Status1.completed or node_status.value == "completed", (
            f"Node {node_id} status is {node_status}, expected 'completed'"
        )

    # Step 6: Verify causal_events.jsonl and SHA-256 hash chains
    causal_file = telemetry_dir / "causal_events.jsonl"
    assert causal_file.is_file(), f"Telemetry file {causal_file} not found"

    lines = [line for line in causal_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) >= 12, f"Expected at least 12 causal events, found {len(lines)}"

    # Validate SHA-256 hash chain
    prev_hash = ""
    events = []
    for line in lines:
        raw = json.loads(line)
        event = CausalTelemetryEvent.model_validate(raw)
        events.append(event)
        expected_hash = event.compute_causal_hash(prev_hash)
        assert event.causal_hash == expected_hash, (
            f"SHA-256 hash mismatch for event {event.event_id}: expected {expected_hash}, got {event.causal_hash}"
        )
        prev_hash = event.causal_hash

    return {
        "workflow_status": result_schema.status.value,
        "node_count": len(result_schema.nodes),
        "node_statuses": {n.id: n.status.value for n in result_schema.nodes},
        "causal_events_count": len(lines),
        "hash_chain_valid": True,
    }


def main():
    res = asyncio.run(execute_colibri_workflow())
    print("Colibri MoE Benchmark Workflow Execution Success:")
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
