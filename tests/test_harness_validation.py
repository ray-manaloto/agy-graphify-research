"""Unit tests for Multi-Agent Orchestration Graph Harness, Telemetry, and Task Dispatcher."""

import json
from pathlib import Path

import pytest

from agy_graphify.orchestration import OrchestrationEngine
from agy_graphify.tasks import TaskDispatcher
from agy_graphify.telemetry import TelemetryCollector, TelemetryEvent


@pytest.mark.asyncio
async def test_orchestration_engine_parameterized_plan(tmp_path: Path) -> None:
    engine = OrchestrationEngine(project_dir=tmp_path)
    plan = await engine.plan_workflow(
        task_description="Benchmarking MoE Inference Engine",
        agent_roles=["coordinator", "researcher", "verifier"],
        stage="stage-3",
        execution_mode="dag",
    )

    assert plan.task == "[stage-3] Benchmarking MoE Inference Engine"
    assert plan.execution_mode == "dag"
    assert len(plan.agents) == 3
    assert [a.role for a in plan.agents] == ["coordinator", "researcher", "verifier"]

    plan_file = tmp_path / ".gemini" / "orchestration_plan.json"
    assert plan_file.is_file()
    saved_data = json.loads(plan_file.read_text(encoding="utf-8"))
    assert saved_data["execution_mode"] == "dag"


@pytest.mark.asyncio
async def test_telemetry_collector_remediation(tmp_path: Path) -> None:
    collector = TelemetryCollector(project_dir=tmp_path)
    events = [
        TelemetryEvent(
            conversation_id="conv-123",
            step_index=1,
            event_type="TOOL_CALL",
            source="MODEL",
            status="ERROR",
            content_summary="Tool failed due to permission denied",
            tool_calls=[{"name": "run_command", "args": {"CommandLine": "bad_cmd"}}],
        )
    ]

    failed = collector.analyze_failed_tools(events)
    assert len(failed) == 1
    assert failed[0]["tool"] == "run_command"
    assert failed[0]["args"] == {"CommandLine": "bad_cmd"}


@pytest.mark.asyncio
async def test_task_dispatcher_registration() -> None:
    dispatcher = TaskDispatcher()
    dispatched_calls: list[str] = []

    async def sample_handler(task_name: str, *args: str) -> str:
        dispatched_calls.append(task_name)
        return f"Handled {task_name}"

    dispatcher.register("test_action", sample_handler)
    res = await dispatcher.dispatch("test_action", "subtask-1")

    assert res == "Handled subtask-1"
    assert dispatched_calls == ["subtask-1"]
