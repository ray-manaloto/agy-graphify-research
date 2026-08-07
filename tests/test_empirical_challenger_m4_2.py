"""Adversarial Empirical Stress Tests for Telemetry, Atomic Writes, and Environment Verification (Milestone 4 Challenger 2)."""

import asyncio
import json
import time
from pathlib import Path

import pytest

from agy_graphify.graph_engine import StateGraphEngine
from agy_graphify.models.graph_engine_schema import (
    ExecutionMode,
    GraphEngineSchema,
    Node,
    NodeType,
    Status,
    Status1,
)
from agy_graphify.okf import OKFValidator
from agy_graphify.orchestration import OrchestrationEngine, SentinelHeartbeatMonitor
from agy_graphify.telemetry import TelemetryCollector
from agy_graphify.verify import EnvironmentVerifier


@pytest.mark.asyncio
async def test_telemetry_parse_transcript_file_adversarial(tmp_path: Path):
    """Test TelemetryCollector._parse_transcript_file with malformed JSON, non-dict lines, null tool calls, and case-varied error statuses."""
    collector = TelemetryCollector(project_dir=tmp_path, app_data_dir=tmp_path)
    conv_dir = tmp_path / "conv_test_1"
    logs_dir = conv_dir / ".system_generated" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    transcript_file = logs_dir / "transcript.jsonl"

    lines = [
        "",  # Empty line
        "   ",  # Whitespace line
        "{malformed json line",  # Invalid JSON
        '{"unclosed_key": "val"',  # Unclosed JSON
        "12345",  # Non-dict JSON integer
        '"just a raw string"',  # Non-dict JSON string
        "true",  # Non-dict JSON boolean
        "null",  # Non-dict JSON null
        "[1, 2, 3]",  # Non-dict JSON array
        json.dumps(
            {"step_index": "invalid_int", "type": "tool", "status": "DONE"}
        ),  # Non-integer step index
        json.dumps(
            {"step_index": None, "type": "tool", "status": "DONE"}
        ),  # Null step index -> defaults to 0
        json.dumps(
            {"step_index": 1, "type": "tool", "status": "DONE", "tool_calls": None}
        ),  # Null tool_calls
        json.dumps(
            {"step_index": 2, "type": "tool", "status": "DONE", "tool_calls": "not_a_list"}
        ),  # String tool_calls
        json.dumps(
            {
                "step_index": 3,
                "type": "tool",
                "status": "ERROR",
                "tool_calls": [None, 123, "str", {"name": "run_cmd", "args": {"cmd": "ls"}}],
            }
        ),  # List with non-dict tool calls
        json.dumps(
            {
                "step_index": 4,
                "type": "tool",
                "status": "failed",
                "tool_calls": [{"name": "edit_file"}],
            }
        ),  # Lowercase failed status
        json.dumps(
            {
                "step_index": 5,
                "type": "tool",
                "status": "Failed",
                "tool_calls": [{"name": "write_file"}],
            }
        ),  # Mixed-case Failed status
        json.dumps(
            {"step_index": 6, "type": "tool", "status": "ErRoR", "tool_calls": [{"name": "grep"}]}
        ),  # Case-varied ErRoR status
        json.dumps(
            {"step_index": 7, "type": "tool", "status": None, "tool_calls": []}
        ),  # Null status -> str(None) -> "None"
        json.dumps(
            {"step_index": 8, "type": "tool", "status": "DONE", "content": "x" * 300}
        ),  # Content > 200 chars -> should truncate
    ]

    transcript_file.write_text("\n".join(lines), encoding="utf-8")

    events = collector._parse_transcript_file(conv_dir)

    # Validate parsing results: 8 events successfully parsed
    assert isinstance(events, list)
    assert len(events) == 8

    parsed_step_indices = [ev.step_index for ev in events]
    # Step 3 was dropped because tool_calls contains non-dict items (None, 123, 'str') causing Pydantic ValidationError
    assert 3 not in parsed_step_indices

    # Check content summary truncation
    step_8_event = next(ev for ev in events if ev.step_index == 8)
    assert len(step_8_event.content_summary) == 200

    # Now test self-healing failure extraction via analyze_failed_tools
    failed_tools = collector.analyze_failed_tools(events)
    failed_steps = [ft["step_index"] for ft in failed_tools]
    assert 4 in failed_steps  # failed
    assert 5 in failed_steps  # Failed
    assert 6 in failed_steps  # ErRoR


@pytest.mark.asyncio
async def test_telemetry_missing_file(tmp_path: Path):
    """Test TelemetryCollector handling when transcript.jsonl does not exist."""
    collector = TelemetryCollector(project_dir=tmp_path, app_data_dir=tmp_path)
    conv_dir = tmp_path / "non_existent_conv"
    events = collector._parse_transcript_file(conv_dir)
    assert events == []


@pytest.mark.asyncio
async def test_heartbeat_atomic_write_and_corruption_recovery(tmp_path: Path):
    """Test SentinelHeartbeatMonitor.record_heartbeat for atomic writing, crash resilience, and corruption recovery."""
    monitor = SentinelHeartbeatMonitor(project_dir=tmp_path)

    # Initial write to non-existent file
    monitor.record_heartbeat("agent_1", "developer")
    assert monitor.liveness_file.is_file()

    # Read and verify content
    data = json.loads(monitor.liveness_file.read_text(encoding="utf-8"))
    assert "agent_1" in data
    assert data["agent_1"]["role"] == "developer"
    assert data["agent_1"]["status"] == "active"

    # Corrupt liveness file with invalid JSON
    monitor.liveness_file.write_text("CORRUPTED_JSON_DATA{{{", encoding="utf-8")

    # Record heartbeat again -> should recover gracefully from corrupted file
    monitor.record_heartbeat("agent_2", "verifier")
    assert monitor.liveness_file.is_file()
    data_after = json.loads(monitor.liveness_file.read_text(encoding="utf-8"))
    assert "agent_2" in data_after
    assert data_after["agent_2"]["role"] == "verifier"


@pytest.mark.asyncio
async def test_heartbeat_concurrent_writes(tmp_path: Path):
    """Test SentinelHeartbeatMonitor concurrent updates from multiple threads/coroutine tasks."""
    monitor = SentinelHeartbeatMonitor(project_dir=tmp_path)

    def write_worker(agent_id: str):
        for _ in range(20):
            monitor.record_heartbeat(agent_id, f"role_{agent_id}")
            time.sleep(0.001)

    # Launch 5 concurrent threads writing heartbeats
    loop = asyncio.get_running_loop()
    tasks = [loop.run_in_executor(None, write_worker, f"agent_{i}") for i in range(5)]
    await asyncio.gather(*tasks)

    # Verify target file is still valid JSON and uncorrupted
    assert monitor.liveness_file.is_file()
    data = json.loads(monitor.liveness_file.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_plan_workflow_atomic_write(tmp_path: Path):
    """Test OrchestrationEngine.plan_workflow atomic writing and file integrity."""
    engine = OrchestrationEngine(project_dir=tmp_path)
    plan = await engine.plan_workflow(
        task_description="Empirical stress test task",
        agent_roles=["researcher", "developer"],
        stage="m4_test",
        execution_mode="parallel",
    )

    plan_file = tmp_path / ".gemini" / "orchestration_plan.json"
    assert plan_file.is_file()

    # Verify file content is valid JSON matching OrchestrationPlan schema
    raw_content = plan_file.read_text(encoding="utf-8")
    parsed = json.loads(raw_content)
    assert parsed["task"] == "[m4_test] Empirical stress test task"
    assert parsed["execution_mode"] == "parallel"
    assert len(parsed["agents"]) == 2


@pytest.mark.asyncio
async def test_state_graph_atomic_save_and_cold_start(tmp_path: Path):
    """Test StateGraphEngine.save_state_atomic and load_state_cold_start for atomic persistence and corruption recovery."""
    engine = StateGraphEngine(project_dir=tmp_path)

    # Cold start initial load (file missing)
    schema = await engine.load_state_cold_start("test_graph")
    assert schema.graph_id == "test_graph"
    assert schema.nodes == []

    # Modify schema and save atomically
    schema.nodes.append(Node(id="n1_task", node_type=NodeType.task, status=Status1.pending))
    await engine.save_state_atomic(schema)

    assert engine.state_file.is_file()

    # Reload and verify
    reloaded = await engine.load_state_cold_start("test_graph")
    assert len(reloaded.nodes) == 1
    assert reloaded.nodes[0].id == "n1_task"

    # Corrupt state file
    engine.state_file.write_text("{NOT_VALID_JSON: true", encoding="utf-8")

    # Cold start recovery from corrupted state file
    recovered = await engine.load_state_cold_start("test_graph")
    assert recovered.graph_id == "test_graph"
    assert recovered.nodes == []  # Reset state on corruption


@pytest.mark.asyncio
async def test_state_graph_concurrent_atomic_saves(tmp_path: Path):
    """Test concurrent save_state_atomic calls under asyncio.gather."""
    engine = StateGraphEngine(project_dir=tmp_path)

    async def save_worker(idx: int):
        schema = GraphEngineSchema(
            graph_id=f"graph_{idx}",
            execution_mode=ExecutionMode.dag,
            status=Status.pending,
            remediation_count=idx,
            max_remediations=3,
            nodes=[Node(id=f"node_{idx}", node_type=NodeType.task, status=Status1.pending)],
        )
        await engine.save_state_atomic(schema)

    # Gather 20 concurrent save operations
    await asyncio.gather(*[save_worker(i) for i in range(20)])

    # Verify target state_file is valid JSON and not corrupt
    assert engine.state_file.is_file()
    content = engine.state_file.read_text(encoding="utf-8")
    data = json.loads(content)
    assert "graph_id" in data


@pytest.mark.asyncio
async def test_environment_verifier_and_okf(tmp_path: Path):
    """Test EnvironmentVerifier and OKFValidator programmatic execution."""
    verifier = EnvironmentVerifier(project_dir=Path.cwd())
    v_res = await verifier.run_check()
    assert v_res.decision.value in ("allow", "deny")

    okf_val = OKFValidator(target_dir=Path.cwd())
    okf_res = await okf_val.validate_all()
    assert okf_res.decision.value in ("allow", "deny")
