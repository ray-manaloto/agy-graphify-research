"""Async unit tests for OrchestrationEngine using pytest."""

import pytest

from agy_graphify.orchestration import OrchestrationEngine


@pytest.mark.asyncio
async def test_plan_and_execute(tmp_path):
    engine = OrchestrationEngine(project_dir=tmp_path)
    plan = await engine.plan_workflow("Test workflow", agent_roles=["developer", "verifier"])

    assert plan.task == "Test workflow"
    assert len(plan.agents) == 2
    assert (tmp_path / ".gemini" / "orchestration_plan.json").is_file()

    result = await engine.execute_agents(plan)
    assert "2 subagents" in result
