"""Async unit tests for OrchestrationEngine using pytest."""

import json
import time
from unittest.mock import MagicMock, patch

import pytest

from agy_graphify.orchestration import OrchestrationEngine, SentinelHeartbeatMonitor


@pytest.mark.asyncio
@patch("agy_graphify.orchestration.SkillOptAdapter.optimize_prompts")
@patch("agy_graphify.orchestration.TelemetryCollector.trace_subagent_span")
async def test_plan_and_execute(mock_trace, mock_optimize, tmp_path):
    mock_trace.return_value.__enter__.return_value = MagicMock()
    engine = OrchestrationEngine(project_dir=tmp_path)
    plan = await engine.plan_workflow(
        "Test workflow", agent_roles=["developer", "verifier"], optimize_prompts=True
    )

    assert plan.task == "Test workflow"
    assert len(plan.agents) == 2
    assert (tmp_path / ".gemini" / "orchestration_plan.json").is_file()
    mock_optimize.assert_called_once()
    assert mock_trace.call_count >= 1

    result = await engine.execute_agents(plan)
    assert "2 subagents" in result
    assert mock_trace.call_count >= 2


def test_sentinel_heartbeat_monitor_resilience(tmp_path):
    monitor = SentinelHeartbeatMonitor(project_dir=tmp_path)

    # Record a heartbeat
    monitor.record_heartbeat("agent-1", "developer")
    liveness_file = tmp_path / ".gemini" / "telemetry" / "liveness.json"
    assert liveness_file.is_file()

    # Corrupt liveness file with invalid JSON
    liveness_file.write_text("invalid json {", encoding="utf-8")
    monitor.record_heartbeat("agent-2", "verifier")
    data = json.loads(liveness_file.read_text(encoding="utf-8"))
    assert "agent-2" in data

    # Test check_unresponsive with stale entry
    data["agent-1"] = {"role": "developer", "last_heartbeat": time.time() - 1000}
    liveness_file.write_text(json.dumps(data), encoding="utf-8")
    unresponsive = monitor.check_unresponsive(timeout_seconds=600)
    assert len(unresponsive) == 1
    assert "agent-1" in unresponsive[0]
