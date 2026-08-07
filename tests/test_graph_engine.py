"""Unit tests for Sol-Orchestrator Inspired StateGraphEngine with OpenAI Symphony spec and event convergences."""

from pathlib import Path

import pytest

from agy_graphify.graph_engine import (
    DAGCycleError,
    EventDispatcher,
    MaxRemediationExceededError,
    StateGraphEngine,
    SymphonyWorkflowParser,
)
from agy_graphify.models.graph_engine_schema import (
    EventType,
    ExecutionMode,
    GraphEngineSchema,
    Node,
    NodeType,
    Status,
    Status1,
    SymphonyEvent,
)
from agy_graphify.skillopt import SkillOptAdapter
from agy_graphify.verify import IntegrityAuditor


@pytest.mark.asyncio
async def test_dag_validation_and_topo_sort(tmp_path: Path) -> None:
    engine = StateGraphEngine(project_dir=tmp_path)
    nodes = [
        Node(id="node_a", node_type=NodeType.task, status=Status1.pending),
        Node(id="node_b", node_type=NodeType.task, status=Status1.pending, dependencies=["node_a"]),
        Node(id="node_c", node_type=NodeType.task, status=Status1.pending, dependencies=["node_b"]),
    ]

    topo_order = engine.validate_dag(nodes)
    assert topo_order == ["node_a", "node_b", "node_c"]


@pytest.mark.asyncio
async def test_dag_static_cycle_detection(tmp_path: Path) -> None:
    engine = StateGraphEngine(project_dir=tmp_path)
    # Static cycle: node_a -> node_b -> node_a
    nodes = [
        Node(id="node_a", node_type=NodeType.task, status=Status1.pending, dependencies=["node_b"]),
        Node(id="node_b", node_type=NodeType.task, status=Status1.pending, dependencies=["node_a"]),
    ]

    with pytest.raises(DAGCycleError) as exc_info:
        engine.validate_dag(nodes)
    assert "Static dependency cycle detected" in str(exc_info.value)


@pytest.mark.asyncio
async def test_atomic_state_serialization(tmp_path: Path) -> None:
    engine = StateGraphEngine(project_dir=tmp_path)
    schema = GraphEngineSchema(
        graph_id="test_graph",
        execution_mode=ExecutionMode.dag,
        status=Status.pending,
        remediation_count=0,
        max_remediations=3,
        nodes=[Node(id="n1", node_type=NodeType.task, status=Status1.pending)],
    )

    await engine.save_state_atomic(schema)

    state_file = tmp_path / ".gemini" / "graph_state.json"
    assert state_file.is_file()

    loaded = await engine.load_state_cold_start(graph_id="test_graph")
    assert loaded.graph_id == "test_graph"
    assert len(loaded.nodes) == 1
    assert loaded.nodes[0].id == "n1"


@pytest.mark.asyncio
async def test_bounded_remediation_loop(tmp_path: Path) -> None:
    engine = StateGraphEngine(project_dir=tmp_path)
    # Node marked as remediation with initial remediation_count = 3 (max_remediations = 3)
    schema = GraphEngineSchema(
        graph_id="test_remediation",
        execution_mode=ExecutionMode.dag,
        status=Status.pending,
        remediation_count=3,
        max_remediations=3,
        nodes=[Node(id="rem_1", node_type=NodeType.remediation, status=Status1.pending)],
    )

    with pytest.raises(MaxRemediationExceededError) as exc_info:
        await engine.execute_graph(schema)

    assert "Remediation limit (3) exceeded" in str(exc_info.value)


def test_verification_subgraph_expansion(tmp_path: Path) -> None:
    engine = StateGraphEngine(project_dir=tmp_path)
    nodes = [Node(id="code_mod_task", node_type=NodeType.task, status=Status1.pending)]

    expanded = engine.expand_verification_subgraph(nodes)
    # Expected: original task + reviewer + challenger + auditor = 4 nodes
    assert len(expanded) == 4
    ids = [n.id for n in expanded]
    assert ids == ["code_mod_task", "code_mod_reviewer", "code_mod_challenger", "code_mod_auditor"]
    assert expanded[1].dependencies == ["code_mod_task"]
    assert expanded[2].dependencies == ["code_mod_reviewer"]
    assert expanded[3].dependencies == ["code_mod_challenger"]


@pytest.mark.asyncio
async def test_symphony_workflow_parser_yaml_str() -> None:
    yaml_content = """
name: test_symphony_workflow
version: 1.0.0
description: Declarative test workflow
execution_mode: dag
max_remediations: 5
nodes:
  - id: ingest_data
    node_type: task
    role: researcher
    instructions: Ingest telemetry logs
  - id: process_data
    node_type: task
    role: developer
    instructions: Process ingested logs
    dependencies:
      - ingest_data
"""
    schema = SymphonyWorkflowParser.parse_yaml_str(yaml_content)
    assert schema.graph_id == "test_symphony_workflow"
    assert schema.execution_mode == ExecutionMode.dag
    assert schema.max_remediations == 5
    assert len(schema.nodes) == 2

    node_map = {n.id: n for n in schema.nodes}
    assert node_map["ingest_data"].subagent_role == "researcher"
    assert node_map["process_data"].dependencies == ["ingest_data"]


@pytest.mark.asyncio
async def test_symphony_workflow_parser_yaml_file(tmp_path: Path) -> None:
    yaml_path = tmp_path / "workflow.yaml"
    yaml_path.write_text(
        """
name: file_based_workflow
execution_mode: dag
nodes:
  - id: task_1
    node_type: task
""",
        encoding="utf-8",
    )
    schema = SymphonyWorkflowParser.parse_yaml_file(yaml_path)
    assert schema.graph_id == "file_based_workflow"
    assert len(schema.nodes) == 1
    assert schema.nodes[0].id == "task_1"


@pytest.mark.asyncio
async def test_event_dispatcher_lifecycle_events(tmp_path: Path) -> None:
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

    dispatcher = EventDispatcher()
    dispatched_events: list[SymphonyEvent] = []

    def listener(event: SymphonyEvent) -> None:
        dispatched_events.append(event)

    for event_type in [
        EventType.WORKFLOW_STARTED,
        EventType.NODE_STARTED,
        EventType.NODE_COMPLETED,
        EventType.WORKFLOW_COMPLETED,
    ]:
        dispatcher.subscribe(event_type, listener)

    engine = StateGraphEngine(project_dir=tmp_path, dispatcher=dispatcher)
    schema = GraphEngineSchema(
        graph_id="event_test_graph",
        execution_mode=ExecutionMode.dag,
        status=Status.pending,
        remediation_count=0,
        max_remediations=3,
        nodes=[
            Node(id="step_1", node_type=NodeType.task, status=Status1.pending),
            Node(
                id="step_2",
                node_type=NodeType.task,
                status=Status1.pending,
                dependencies=["step_1"],
            ),
        ],
    )

    result_schema = await engine.execute_graph(schema)
    assert result_schema.status == Status.completed

    event_types = [e.event_type for e in dispatched_events]
    assert EventType.WORKFLOW_STARTED in event_types
    assert EventType.NODE_STARTED in event_types
    assert EventType.NODE_COMPLETED in event_types
    assert EventType.WORKFLOW_COMPLETED in event_types


@pytest.mark.asyncio
async def test_event_dispatcher_failure_and_remediation_events(tmp_path: Path) -> None:
    dispatcher = EventDispatcher()
    dispatched_types: list[EventType] = []

    def track_event(event: SymphonyEvent) -> None:
        dispatched_types.append(event.event_type)

    dispatcher.subscribe(EventType.REMEDIATION_TRIGGERED, track_event)
    dispatcher.subscribe(EventType.NODE_FAILED, track_event)
    dispatcher.subscribe(EventType.WORKFLOW_FAILED, track_event)

    engine = StateGraphEngine(project_dir=tmp_path, dispatcher=dispatcher)

    # Failing handler task
    def failing_handler(node: Node) -> None:
        raise RuntimeError("Simulated node failure")

    schema = GraphEngineSchema(
        graph_id="failing_graph",
        execution_mode=ExecutionMode.dag,
        status=Status.pending,
        remediation_count=0,
        max_remediations=3,
        nodes=[Node(id="fail_node", node_type=NodeType.task, status=Status1.pending)],
    )

    result_schema = await engine.execute_graph(schema, task_handlers={"fail_node": failing_handler})
    assert result_schema.status == Status.failed
    assert EventType.NODE_FAILED in dispatched_types
    assert EventType.WORKFLOW_FAILED in dispatched_types


@pytest.mark.asyncio
async def test_register_default_listeners_integration(tmp_path: Path) -> None:
    auditor = IntegrityAuditor(project_dir=tmp_path)
    skillopt = SkillOptAdapter(project_dir=tmp_path)
    dispatcher = EventDispatcher()

    engine = StateGraphEngine(project_dir=tmp_path, dispatcher=dispatcher)
    engine.register_default_listeners(auditor=auditor, skillopt=skillopt)

    # Ensure listeners subscribed to dispatcher
    assert len(dispatcher._listeners[EventType.NODE_COMPLETED]) >= 1
    assert len(dispatcher._listeners[EventType.NODE_FAILED]) >= 1
    assert len(dispatcher._listeners[EventType.REMEDIATION_TRIGGERED]) >= 1


@pytest.mark.asyncio
async def test_dag_resume_skips_completed_nodes(tmp_path: Path) -> None:
    engine = StateGraphEngine(project_dir=tmp_path)
    executed_nodes: list[str] = []

    def handler(node: Node) -> None:
        executed_nodes.append(node.id)

    schema = GraphEngineSchema(
        graph_id="resume_test",
        execution_mode=ExecutionMode.dag,
        status=Status.running,
        nodes=[
            Node(id="n1", node_type=NodeType.task, status=Status1.completed),
            Node(id="n2", node_type=NodeType.task, status=Status1.pending, dependencies=["n1"]),
        ],
    )

    handlers = {"n1": handler, "n2": handler}
    res = await engine.execute_graph(schema, task_handlers=handlers)
    assert res.status == Status.completed
    # n1 was already completed, so only n2 should execute
    assert executed_nodes == ["n2"]


@pytest.mark.asyncio
async def test_cascading_skip_and_completion_guard(tmp_path: Path) -> None:
    engine = StateGraphEngine(project_dir=tmp_path)

    def failing_handler(node: Node) -> None:
        raise RuntimeError("Simulated failure")

    schema = GraphEngineSchema(
        graph_id="cascading_skip_test",
        execution_mode=ExecutionMode.dag,
        status=Status.pending,
        nodes=[
            Node(id="n1", node_type=NodeType.task, status=Status1.pending),
            Node(id="n2", node_type=NodeType.task, status=Status1.pending, dependencies=["n1"]),
            Node(id="n3", node_type=NodeType.task, status=Status1.pending, dependencies=["n2"]),
        ],
    )

    res = await engine.execute_graph(schema, task_handlers={"n1": failing_handler})
    node_map = {n.id: n for n in res.nodes}
    assert node_map["n1"].status == Status1.failed
    assert node_map["n2"].status == Status1.skipped
    assert node_map["n3"].status == Status1.skipped
    assert res.status == Status.failed


@pytest.mark.asyncio
async def test_unhandled_subagent_role_dispatch(tmp_path: Path) -> None:
    dispatcher = EventDispatcher()
    dispatched_events: list[SymphonyEvent] = []

    def track(e: SymphonyEvent) -> None:
        dispatched_events.append(e)

    dispatcher.subscribe(EventType.NODE_PENDING_SUBAGENT, track)

    def pending_subagent_handler(node: Node) -> None:
        node.status = Status1.pending_subagent_dispatch

    engine = StateGraphEngine(project_dir=tmp_path, dispatcher=dispatcher)
    schema = GraphEngineSchema(
        graph_id="unhandled_subagent_test",
        execution_mode=ExecutionMode.dag,
        status=Status.pending,
        nodes=[
            Node(
                id="dev_task",
                node_type=NodeType.task,
                status=Status1.pending,
                subagent_role="developer",
                task_action="Write new feature",
            )
        ],
    )

    res = await engine.execute_graph(schema, task_handlers={"dev_task": pending_subagent_handler})
    assert res.nodes[0].status == Status1.pending_subagent_dispatch
    assert res.status == Status.running
    assert len(dispatched_events) == 1
    assert dispatched_events[0].event_type == EventType.NODE_PENDING_SUBAGENT
    assert dispatched_events[0].node_id == "dev_task"


@pytest.mark.asyncio
async def test_cross_process_file_lock(tmp_path: Path) -> None:
    engine = StateGraphEngine(project_dir=tmp_path)
    schema = GraphEngineSchema(
        graph_id="lock_test",
        execution_mode=ExecutionMode.dag,
        status=Status.pending,
        nodes=[Node(id="n1", node_type=NodeType.task, status=Status1.pending)],
    )

    # Save state using atomic POSIX fcntl.flock write lock
    await engine.save_state_atomic(schema)
    assert (tmp_path / ".gemini" / "graph_state.json").is_file()

    # Load state using atomic POSIX fcntl.flock read lock
    loaded = await engine.load_state_cold_start("lock_test")
    assert loaded.graph_id == "lock_test"

    import asyncio

    # Spawn 2 concurrent CLI subprocesses reading state simultaneously
    p1 = await asyncio.create_subprocess_exec(
        "uv", "run", "agy-graph-engine", "--check-dag", cwd=str(tmp_path)
    )
    p2 = await asyncio.create_subprocess_exec(
        "uv", "run", "agy-graph-engine", "--check-dag", cwd=str(tmp_path)
    )

    c1, c2 = await asyncio.gather(p1.wait(), p2.wait())
    assert c1 == 0
    assert c2 == 0

