"""Unit tests for /dag slash command skill, StateGraphEngine goal planning, and task dispatcher DAG actions."""

from pathlib import Path

import pytest

from agy_graphify.graph_engine import StateGraphEngine
from agy_graphify.models.graph_engine_schema import Status
from agy_graphify.tasks import TaskDispatcher, dag_plan_action, dag_resume_action


def setup_valid_project(tmp_path: Path) -> None:
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


@pytest.mark.asyncio
async def test_state_graph_engine_plan_goal(tmp_path: Path) -> None:
    setup_valid_project(tmp_path)
    engine = StateGraphEngine(project_dir=tmp_path)
    goal = "Upgrade all dependencies to latest and verify tests"
    schema = await engine.plan_goal(goal, graph_id="test_plan_graph")

    assert schema.graph_id == "test_plan_graph"
    assert schema.status == Status.pending
    # 3 base tasks + 3*3 verification nodes (reviewer, challenger, auditor) = 12 nodes
    assert len(schema.nodes) == 12

    node_ids = [n.id for n in schema.nodes]
    assert "research_and_ingest" in node_ids
    assert "research_and_ingest_reviewer" in node_ids
    assert "research_and_ingest_challenger" in node_ids
    assert "research_and_ingest_auditor" in node_ids

    # Confirm atomic JSON persistence
    loaded = await engine.load_state_cold_start("test_plan_graph")
    assert loaded.graph_id == "test_plan_graph"
    assert len(loaded.nodes) == 12


@pytest.mark.asyncio
async def test_state_graph_engine_execute_planned_dag(tmp_path: Path) -> None:
    setup_valid_project(tmp_path)
    engine = StateGraphEngine(project_dir=tmp_path)
    schema = await engine.plan_goal("Fix resume bypass", graph_id="test_exec_graph")

    # Define simple mock handlers for task nodes
    executed_nodes = []

    def mock_handler(node):
        executed_nodes.append(node.id)

    handlers = {n.id: mock_handler for n in schema.nodes}

    result = await engine.execute_graph(schema, task_handlers=handlers)
    assert result.status == Status.completed
    assert len(executed_nodes) == 12


@pytest.mark.asyncio
async def test_task_dispatcher_dag_actions(tmp_path: Path, monkeypatch) -> None:
    setup_valid_project(tmp_path)
    dispatcher = TaskDispatcher()
    dispatcher.register("dag-plan", dag_plan_action)
    dispatcher.register("dag-resume", dag_resume_action)

    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

    # Dispatch dag-plan
    await dispatcher.dispatch("dag-plan", "Refactor", "telemetry", "tracing")
    state_file = tmp_path / ".gemini" / "graph_state.json"
    assert state_file.exists()

    # Dispatch dag-resume
    await dispatcher.dispatch("dag-resume")
    engine = StateGraphEngine(project_dir=tmp_path)
    schema = await engine.load_state_cold_start()
    assert schema.status == Status.completed
