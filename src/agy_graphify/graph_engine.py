"""Sol-Orchestrator Inspired Multi-Agent State Graph Engine with OpenAI Symphony Spec & Event Convergences."""

import argparse
import asyncio
import inspect
import os
import sys
import tempfile
import uuid
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .logger import logger
from .models.graph_engine_schema import (
    EventType,
    ExecutionMode,
    GraphEngineSchema,
    Node,
    NodeType,
    Status,
    Status1,
    SymphonyEvent,
)
from .workflow_parser import SymphonyWorkflowParser  # noqa: F401


class DAGCycleError(ValueError):
    """Raised when a static dependency cycle is detected in the DAG structure."""


class MaxRemediationExceededError(RuntimeError):
    """Raised when runtime remediation attempts exceed the configured max limit."""


class EventDispatcher:
    """Asynchronous event bus for StateGraphEngine lifecycle observers."""

    def __init__(self) -> None:
        self._listeners: dict[
            EventType, list[Callable[[SymphonyEvent], Awaitable[None] | None]]
        ] = defaultdict(list)
        self._event_history: list[SymphonyEvent] = []

    def subscribe(
        self, event_type: EventType, listener: Callable[[SymphonyEvent], Awaitable[None] | None]
    ) -> None:
        self._listeners[event_type].append(listener)

    async def dispatch(self, event: SymphonyEvent) -> None:
        self._event_history.append(event)
        event_name = (
            event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type)
        )
        logger.debug(
            f"[EventDispatcher] Emitting {event_name} for node '{event.node_id}' in graph '{event.graph_id}'"
        )
        for listener in self._listeners.get(event.event_type, []):
            try:
                res = listener(event)
                if asyncio.iscoroutine(res):
                    await res
            except Exception as exc:
                logger.error(f"[EventDispatcher] Listener error for {event_name}: {exc}")


import fcntl


class StateGraphEngine:
    """Manages Sol-Orchestrator inspired DAG graph state, node dependencies, event dispatching, and atomic checkpointing."""

    def __init__(
        self, project_dir: Path | None = None, dispatcher: EventDispatcher | None = None
    ) -> None:
        self.project_dir = project_dir or Path.cwd()
        self.state_file = self.project_dir / ".gemini" / "graph_state.json"
        self._lock = asyncio.Lock()
        self.dispatcher = dispatcher or EventDispatcher()
        self._verifier: Any | None = None

    def _create_event(
        self,
        graph_id: str,
        event_type: EventType,
        node_id: str | None = None,
        error_message: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> SymphonyEvent:
        return SymphonyEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.now(UTC).isoformat(),
            graph_id=graph_id,
            node_id=node_id,
            payload=payload or {},
            error_message=error_message,
        )

    def register_default_listeners(
        self, auditor: Any | None = None, skillopt: Any | None = None
    ) -> None:
        """Register IntegrityAuditor AST inspection and SkillOptAdapter trajectory evaluation on event dispatcher."""
        if auditor:

            async def _audit_listener(event: SymphonyEvent) -> None:
                violations = await auditor.audit_codebase()
                if violations:
                    logger.warning(
                        f"IntegrityAuditor discovered violations upon node '{event.node_id}' completion: {violations}"
                    )

            self.dispatcher.subscribe(EventType.NODE_COMPLETED, _audit_listener)

        if skillopt:

            def _skillopt_listener(event: SymphonyEvent) -> None:
                logger.info(
                    f"SkillOptAdapter evaluating trajectory on event {event.event_type} for node '{event.node_id}'"
                )
                skillopt.evaluate_trajectories()

            self.dispatcher.subscribe(EventType.NODE_FAILED, _skillopt_listener)
            self.dispatcher.subscribe(EventType.REMEDIATION_TRIGGERED, _skillopt_listener)

    def validate_dag(self, nodes: list[Node]) -> list[str]:
        """Validate DAG static dependencies using Kahn's algorithm for topological sorting.

        Returns a topologically sorted list of node IDs.
        Raises DAGCycleError if a static cycle is detected.
        """
        node_map = {n.id: n for n in nodes}
        in_degree: dict[str, int] = {n.id: 0 for n in nodes}
        adj_list: dict[str, list[str]] = defaultdict(list)

        for n in nodes:
            if n.dependencies:
                for dep in n.dependencies:
                    if dep not in node_map:
                        msg = f"Node '{n.id}' depends on non-existent node '{dep}'"
                        logger.error(msg)
                        raise ValueError(msg)
                    adj_list[dep].append(n.id)
                    in_degree[n.id] += 1

        queue = deque([node_id for node_id, count in in_degree.items() if count == 0])
        topo_order: list[str] = []

        while queue:
            curr = queue.popleft()
            topo_order.append(curr)
            for neighbor in adj_list[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(topo_order) != len(nodes):
            msg = f"Static dependency cycle detected in graph nodes. Total: {len(nodes)}, Sorted: {len(topo_order)}"
            logger.error(msg)
            raise DAGCycleError(msg)

        return topo_order

    def expand_verification_subgraph(self, nodes: list[Node]) -> list[Node]:
        """Expand task nodes into explicit Reviewer -> Challenger -> Auditor subgraphs for 3-phase verification."""
        expanded: list[Node] = []
        for n in nodes:
            expanded.append(n)
            if n.node_type == NodeType.task:
                base_id = n.id.removesuffix("_task")
                rev_node = Node(
                    id=f"{base_id}_reviewer",
                    node_type=NodeType.evaluator,
                    status=Status1.pending,
                    dependencies=[n.id],
                )
                chal_node = Node(
                    id=f"{base_id}_challenger",
                    node_type=NodeType.evaluator,
                    status=Status1.pending,
                    dependencies=[rev_node.id],
                )
                aud_node = Node(
                    id=f"{base_id}_auditor",
                    node_type=NodeType.evaluator,
                    status=Status1.pending,
                    dependencies=[chal_node.id],
                )
                expanded.extend([rev_node, chal_node, aud_node])
        return expanded

    async def save_state_atomic(self, schema: GraphEngineSchema) -> None:
        """Atomically serialize state to .gemini/graph_state.json using asyncio.Lock, POSIX fcntl.flock, and tempfile replace."""
        async with self._lock:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            data_json = schema.model_dump_json(indent=2)
            lock_file_path = self.state_file.with_suffix(".json.lock")
            with open(lock_file_path, "a+", encoding="utf-8") as lock_file:
                try:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                    with tempfile.NamedTemporaryFile(
                        "w", dir=self.state_file.parent, delete=False, encoding="utf-8"
                    ) as tmp:
                        tmp.write(data_json)
                        tmp_name = tmp.name
                    os.replace(tmp_name, self.state_file)
                    logger.debug(f"Saved atomic graph state to {self.state_file}")
                finally:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    async def load_state_cold_start(
        self, graph_id: str = "default_graph", reset_failed: bool = True
    ) -> GraphEngineSchema:
        """Load state from .gemini/graph_state.json with cold-start resilience and POSIX fcntl.flock read locking."""
        async with self._lock:
            if not self.state_file.is_file():
                logger.info(f"Cold-start: Initializing new GraphEngineSchema for '{graph_id}'")
                return GraphEngineSchema(
                    graph_id=graph_id,
                    execution_mode=ExecutionMode.dag,
                    status=Status.pending,
                    remediation_count=0,
                    max_remediations=3,
                    nodes=[],
                )

            try:
                lock_file_path = self.state_file.with_suffix(".json.lock")
                lock_file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(lock_file_path, "a+", encoding="utf-8") as lock_file:
                    try:
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_SH)
                        content = self.state_file.read_text(encoding="utf-8")
                    finally:
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

                schema = GraphEngineSchema.model_validate_json(content)
                if reset_failed:
                    failed_ids = {n.id for n in schema.nodes if n.status == Status1.failed}
                    if failed_ids:
                        logger.info(
                            f"Rehydrating state: resetting failed nodes {failed_ids} and dependent skipped nodes to pending."
                        )
                        for n in schema.nodes:
                            if n.status == Status1.failed:
                                n.status = Status1.pending
                                n.error_message = None
                            elif (
                                n.status == Status1.skipped
                                and n.dependencies
                                and any(dep in failed_ids for dep in n.dependencies)
                            ):
                                n.status = Status1.pending
                                n.error_message = None
                return schema
            except Exception as err:
                logger.warning(
                    f"Could not parse state file {self.state_file}: {err}. Resetting state."
                )
                return GraphEngineSchema(
                    graph_id=graph_id,
                    execution_mode=ExecutionMode.dag,
                    status=Status.pending,
                    remediation_count=0,
                    max_remediations=3,
                    nodes=[],
                )

    async def execute_graph(
        self,
        schema: GraphEngineSchema,
        task_handlers: dict[str, Any] | None = None,
    ) -> GraphEngineSchema:
        """Execute graph nodes in topological order with bounded remediation loops and event emissions."""
        topo_order = self.validate_dag(schema.nodes)
        node_map = {n.id: n for n in schema.nodes}

        schema.status = Status.running
        await self.save_state_atomic(schema)
        await self.dispatcher.dispatch(
            self._create_event(schema.graph_id, EventType.WORKFLOW_STARTED)
        )

        remediation_count = schema.remediation_count or 0
        max_remediations = schema.max_remediations or 3

        for node_id in topo_order:
            node = node_map[node_id]

            if node.status == Status1.completed:
                logger.debug(f"Node '{node.id}' already completed. Skipping during state resume.")
                continue

            # Check dependency statuses
            if node.dependencies:
                dep_statuses = [node_map[dep].status for dep in node.dependencies]
                if any(st in (Status1.failed, Status1.skipped) for st in dep_statuses):
                    node.status = Status1.skipped
                    node.error_message = "Skipped due to failed or skipped dependency"
                    await self.save_state_atomic(schema)
                    await self.dispatcher.dispatch(
                        self._create_event(
                            schema.graph_id,
                            EventType.NODE_SKIPPED,
                            node_id=node.id,
                            error_message=node.error_message,
                        )
                    )
                    continue

            node.status = Status1.running
            await self.save_state_atomic(schema)
            await self.dispatcher.dispatch(
                self._create_event(schema.graph_id, EventType.NODE_STARTED, node_id=node.id)
            )

            try:
                if node.node_type == NodeType.remediation:
                    remediation_count += 1
                    if remediation_count > max_remediations:
                        msg = f"Remediation limit ({max_remediations}) exceeded at node '{node.id}'"
                        logger.error(msg)
                        node.status = Status1.failed
                        node.error_message = msg
                        schema.status = Status.failed
                        await self.save_state_atomic(schema)
                        await self.dispatcher.dispatch(
                            self._create_event(
                                schema.graph_id,
                                EventType.NODE_FAILED,
                                node_id=node.id,
                                error_message=msg,
                            )
                        )
                        await self.dispatcher.dispatch(
                            self._create_event(
                                schema.graph_id,
                                EventType.WORKFLOW_FAILED,
                                error_message=msg,
                            )
                        )
                        raise MaxRemediationExceededError(msg)
                    await self.dispatcher.dispatch(
                        self._create_event(
                            schema.graph_id,
                            EventType.REMEDIATION_TRIGGERED,
                            node_id=node.id,
                        )
                    )

                # Execute handler if provided
                if task_handlers and node.id in task_handlers:
                    handler = task_handlers[node.id]
                    if inspect.iscoroutinefunction(handler):
                        await handler(node)
                    else:
                        handler(node)
                    if node.status == Status1.running:
                        node.status = Status1.completed
                elif "pypi" in node.id.lower():
                    await self._execute_pypi_version_check_node(node)
                    node.status = Status1.completed
                elif "github" in node.id.lower():
                    await self._execute_github_version_check_node(node)
                    node.status = Status1.completed
                elif node.node_type == NodeType.evaluator or node.subagent_role in (
                    "research",
                    "developer",
                    "verifier",
                    "qa_reviewer",
                ):
                    await self._run_automated_node_verification(node)
                    node.status = Status1.completed
                else:
                    node.status = Status1.completed

                if node.status == Status1.pending_subagent_dispatch:
                    msg = f"Task node '{node.id}' requires subagent role '{node.subagent_role}' dispatch."
                    logger.info(msg)
                    await self.dispatcher.dispatch(
                        self._create_event(
                            schema.graph_id,
                            EventType.NODE_PENDING_SUBAGENT,
                            node_id=node.id,
                            payload={
                                "subagent_role": node.subagent_role,
                                "task_action": node.task_action,
                            },
                        )
                    )

                await self.save_state_atomic(schema)

                if node.status == Status1.completed:
                    await self.dispatcher.dispatch(
                        self._create_event(
                            schema.graph_id, EventType.NODE_COMPLETED, node_id=node.id
                        )
                    )
            except Exception as exc:
                if isinstance(exc, MaxRemediationExceededError):
                    raise
                logger.error(f"Node '{node.id}' failed: {exc}")
                node.status = Status1.failed
                node.error_message = str(exc)
                await self.save_state_atomic(schema)
                await self.dispatcher.dispatch(
                    self._create_event(
                        schema.graph_id,
                        EventType.NODE_FAILED,
                        node_id=node.id,
                        error_message=str(exc),
                    )
                )

        schema.remediation_count = remediation_count
        failed_count = sum(1 for n in schema.nodes if n.status == Status1.failed)
        skipped_count = sum(1 for n in schema.nodes if n.status == Status1.skipped)
        pending_dispatch_count = sum(
            1 for n in schema.nodes if n.status == Status1.pending_subagent_dispatch
        )

        # Mandatory Final Verification Gate
        if failed_count == 0 and skipped_count == 0 and pending_dispatch_count == 0:
            final_result = await self._run_final_verification_gate()
            if not final_result:
                failed_count += 1

        if failed_count > 0 or skipped_count > 0:
            schema.status = Status.failed
        elif pending_dispatch_count > 0:
            schema.status = Status.running
        else:
            schema.status = Status.completed

        await self.save_state_atomic(schema)

        if schema.status == Status.completed:
            await self.dispatcher.dispatch(
                self._create_event(schema.graph_id, EventType.WORKFLOW_COMPLETED)
            )
        elif schema.status == Status.failed:
            await self.dispatcher.dispatch(
                self._create_event(schema.graph_id, EventType.WORKFLOW_FAILED)
            )

        return schema

    async def _execute_pypi_version_check_node(self, node: Node) -> None:
        """Ingest and execute live PyPI API package version checks within DAG node."""
        from .verify import EnvironmentVerifier

        verifier = EnvironmentVerifier(project_dir=self.project_dir)
        _, statuses = await verifier._check_pypi_versions()
        logger.info(f"DAG Node '{node.id}' executed PyPI version check: {', '.join(statuses)}")

    async def _execute_github_version_check_node(self, node: Node) -> None:
        """Ingest and execute live GitHub API release checks within DAG node."""
        from .verify import EnvironmentVerifier

        verifier = EnvironmentVerifier(project_dir=self.project_dir)
        _, statuses = await verifier._check_github_versions()
        logger.info(f"DAG Node '{node.id}' executed GitHub version check: {', '.join(statuses)}")

    async def _run_automated_node_verification(self, node: Node) -> None:
        """Run mandatory verification assertions (EnvironmentVerifier check & IntegrityAuditor codebase audit)."""
        from .verify import EnvironmentVerifier

        if not (self.project_dir / ".gemini" / "settings.json").is_file():
            logger.debug(
                f"Skipping node verification check in unconfigured temp directory: {self.project_dir}"
            )
            return

        if self._verifier is None:
            self._verifier = EnvironmentVerifier(project_dir=self.project_dir)

        result = await self._verifier.run_check(use_cache=True)
        if result.decision.value != "allow":
            msg = f"Automated node verification failed at node '{node.id}': {result.reason}"
            logger.error(msg)
            raise RuntimeError(msg)

        from .monitor import monitor_logs
        monitor_logs()

    async def _run_final_verification_gate(self) -> bool:
        """Enforce final verification gate before completing DAG workflow."""
        from .verify import EnvironmentVerifier

        if not (self.project_dir / ".gemini" / "settings.json").is_file():
            logger.debug(
                f"Skipping final verification gate in unconfigured temp directory: {self.project_dir}"
            )
            return True

        if self._verifier is None:
            self._verifier = EnvironmentVerifier(project_dir=self.project_dir)

        result = await self._verifier.run_check(use_cache=True)
        if result.decision.value != "allow":
            logger.error(f"Final verification gate denied workflow completion: {result.reason}")
            return False
        return True

    async def plan_goal(
        self, goal_text: str, graph_id: str = "dag_goal_workflow"
    ) -> GraphEngineSchema:
        """Parse natural language goal into structured GraphEngineSchema DAG nodes with 3-phase verification expansion."""
        base_nodes = [
            Node(
                id="research_and_ingest",
                node_type=NodeType.task,
                status=Status1.pending,
                subagent_role="research",
                task_action=f"Research dependencies, codebase AST, and requirements for goal: {goal_text}",
                dependencies=[],
            ),
        ]

        if any(
            kw in goal_text.lower() for kw in ("pypi", "github", "version", "api", "convergence")
        ):
            base_nodes.extend(
                [
                    Node(
                        id="pypi_version_check",
                        node_type=NodeType.task,
                        status=Status1.pending,
                        subagent_role="research",
                        task_action="Execute live PyPI API package version checks for project dependencies.",
                        dependencies=["research_and_ingest"],
                    ),
                    Node(
                        id="github_version_check",
                        node_type=NodeType.task,
                        status=Status1.pending,
                        subagent_role="research",
                        task_action="Execute live GitHub API release checks for pinned tool repositories.",
                        dependencies=["pypi_version_check"],
                    ),
                ]
            )
            impl_deps = ["github_version_check"]
        else:
            impl_deps = ["research_and_ingest"]

        base_nodes.extend(
            [
                Node(
                    id="implement_changes",
                    node_type=NodeType.task,
                    status=Status1.pending,
                    subagent_role="developer",
                    task_action=f"Execute required code, configuration, or dependency edits for goal: {goal_text}",
                    dependencies=impl_deps,
                ),
                Node(
                    id="verify_and_audit",
                    node_type=NodeType.task,
                    status=Status1.pending,
                    subagent_role="verifier",
                    task_action="Run pytest unit tests, OKF doc spec checks, live API version checks, and agy-verify shell script audit.",
                    dependencies=["implement_changes"],
                ),
            ]
        )

        expanded_nodes = self.expand_verification_subgraph(base_nodes)
        schema = GraphEngineSchema(
            graph_id=graph_id,
            execution_mode=ExecutionMode.dag,
            status=Status.pending,
            remediation_count=0,
            max_remediations=3,
            nodes=expanded_nodes,
        )
        await self.save_state_atomic(schema)
        await self.dispatcher.dispatch(
            self._create_event(graph_id, EventType.WORKFLOW_STARTED, payload={"goal": goal_text})
        )
        return schema


async def async_main(*params: str) -> None:
    """Async CLI entrypoint for graph engine."""
    parser = argparse.ArgumentParser(
        description="Sol-Orchestrator Inspired Multi-Agent State Graph Engine"
    )
    parser.add_argument("--graph-id", default="default_graph", help="Identifier for state graph")
    parser.add_argument(
        "--check-dag", action="store_true", help="Validate DAG topology for static cycles"
    )
    parser.add_argument("--execute", action="store_true", help="Execute pending state graph")
    parser.add_argument(
        "--plan",
        type=str,
        default="",
        help="Natural language goal to convert into a state graph DAG",
    )
    parser.add_argument(
        "--resume", action="store_true", help="Resume uncompleted nodes in current graph state"
    )

    args = parser.parse_args(list(params) if params else sys.argv[1:])

    engine = StateGraphEngine()

    if args.plan:
        schema = await engine.plan_goal(args.plan, graph_id=args.graph_id)
        print(
            f"Planned goal DAG '{schema.graph_id}' with {len(schema.nodes)} nodes saved to {engine.state_file}"
        )
        return

    schema = await engine.load_state_cold_start(graph_id=args.graph_id)

    if args.check_dag:
        try:
            topo = engine.validate_dag(schema.nodes)
            print(f"DAG topology valid. Execution order ({len(topo)} nodes): {topo}")
        except DAGCycleError as err:
            print(f"DAG Validation Failed: {err}")
            raise SystemExit(1)

    if args.execute or args.resume:
        updated_schema = await engine.execute_graph(schema)
        print(f"Graph execution complete. Status: {updated_schema.status.value}")


def main(*params: str) -> None:
    asyncio.run(async_main(*params))


if __name__ == "__main__":
    main()
