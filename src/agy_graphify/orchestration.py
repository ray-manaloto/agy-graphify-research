"""Async Multi-Agent Orchestration & Workflow Dispatcher."""

import argparse
import asyncio
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from .logger import logger
from .models.orchestration_schema import Agent, OrchestrationPlan
from .skillopt import SkillOptAdapter
from .telemetry import TelemetryCollector


class SentinelHeartbeatMonitor:
    """Monitors subagent liveness timestamps and detects unresponsive background agents (>10m timeout)."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir
        self.liveness_file = self.project_dir / ".gemini" / "telemetry" / "liveness.json"

    def record_heartbeat(self, agent_id: str, role: str) -> None:
        self.liveness_file.parent.mkdir(parents=True, exist_ok=True)
        data: dict[str, Any] = {}
        if self.liveness_file.is_file():
            try:
                raw_data = json.loads(self.liveness_file.read_text(encoding="utf-8"))
                if isinstance(raw_data, dict):
                    data = raw_data
            except Exception as exc:
                logger.warning(f"Corrupted liveness file {self.liveness_file}: {exc}")
                data = {}
        data[agent_id] = {
            "role": role,
            "last_heartbeat": time.time(),
            "status": "active",
        }
        with tempfile.NamedTemporaryFile(
            "w", dir=self.liveness_file.parent, delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(json.dumps(data, indent=2))
            tmp_name = tmp.name
        os.replace(tmp_name, self.liveness_file)

    def check_unresponsive(self, timeout_seconds: float = 600.0) -> list[str]:
        if not self.liveness_file.is_file():
            return []
        now = time.time()
        unresponsive: list[str] = []
        try:
            raw_data = json.loads(self.liveness_file.read_text(encoding="utf-8"))
            if isinstance(raw_data, dict):
                for agent_id, info in raw_data.items():
                    if not isinstance(info, dict):
                        continue
                    last_hb = info.get("last_heartbeat")
                    if isinstance(last_hb, (int, float)) and (now - last_hb > timeout_seconds):
                        role = info.get("role", "unknown")
                        unresponsive.append(
                            f"Agent '{agent_id}' ({role}) unresponsive for >{timeout_seconds}s"
                        )
        except Exception as exc:
            logger.warning(f"Error checking unresponsive heartbeats: {exc}")
        return unresponsive


class OrchestrationEngine:
    """Manages multi-agent task breakdown, subagent roles, and parallel workflow execution."""

    def __init__(self, project_dir: Path | None = None) -> None:
        self.project_dir = project_dir or Path.cwd()

    async def plan_workflow(
        self,
        task_description: str,
        agent_roles: list[str] | None = None,
        stage: str | None = None,
        execution_mode: str | None = None,
        optimize_prompts: bool = False,
    ) -> OrchestrationPlan:
        """Break down complex task into subagent execution plan asynchronously."""
        collector = TelemetryCollector(project_dir=self.project_dir)
        with collector.trace_subagent_span(
            "plan_workflow", attributes={"task": task_description, "stage": stage or "unknown"}
        ):
            if optimize_prompts:
                adapter = SkillOptAdapter(project_dir=self.project_dir)
                adapter.optimize_prompts()
            roles = agent_roles or [
                "coordinator",
                "researcher",
                "developer",
                "verifier",
                "qa_reviewer",
                "okf_specialist",
                "learning_agent",
            ]

        task_name = f"[{stage}] {task_description}" if stage else task_description
        mode = execution_mode or "parallel"

        plan = OrchestrationPlan(
            task=task_name,
            project=self.project_dir.name,
            agents=[
                Agent(
                    role=role,
                    status="pending",
                    subtasks=[f"Execute subtask for {role} in stage '{stage or 'all'}'"],
                )
                for role in roles
            ],
            execution_mode=mode,
        )

        plan_file = self.project_dir / ".gemini" / "orchestration_plan.json"
        plan_file.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w", dir=plan_file.parent, delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(plan.model_dump_json(indent=2))
            tmp_name = tmp.name
        os.replace(tmp_name, plan_file)

        logger.info(
            f"Planned workflow for task '{task_name}' with {len(plan.agents)} agents in '{mode}' mode."
        )
        return plan

    async def execute_agents(self, plan: OrchestrationPlan) -> str:
        """Simulate or coordinate subagent execution based on plan asynchronously."""
        collector = TelemetryCollector(project_dir=self.project_dir)
        with collector.trace_subagent_span(
            "execute_agents", attributes={"task": plan.task, "agent_count": len(plan.agents)}
        ):
            agent_count = len(plan.agents)
            logger.info(f"Dispatching {agent_count} subagents for task '{plan.task}'.")
            return f"Successfully dispatched {agent_count} subagents for task: '{plan.task}'"


async def run_auto_daemon(workflow_path: str | None = None, interval_seconds: float = 10.0) -> None:
    """Run autonomous background daemon loop for periodic self-healing, graph state evaluation, and telemetry maintenance."""
    project_dir = Path.cwd()
    pause_file = project_dir / ".gemini" / "PAUSE"
    logger.info(
        f"[Auto-Daemon] Starting standing background daemon (check interval: {interval_seconds}s)..."
    )

    from .graph_engine import EventDispatcher, StateGraphEngine
    from .telemetry import MemoryStoreAdapter
    from .workflow_parser import SymphonyWorkflowParser

    dispatcher = EventDispatcher()
    memory_adapter = MemoryStoreAdapter(output_dir=project_dir / ".gemini" / "telemetry")
    memory_adapter.subscribe_to_dispatcher(dispatcher)

    graph_engine = StateGraphEngine(project_dir=project_dir, dispatcher=dispatcher)

    iteration = 0
    while True:
        iteration += 1
        if pause_file.is_file():
            logger.info(
                f"[Auto-Daemon] Iteration #{iteration}: Paused cleanly via {pause_file}. Waiting..."
            )
            await asyncio.sleep(interval_seconds)
            continue

        logger.info(f"[Auto-Daemon] Iteration #{iteration}: Checking system state and telemetry...")
        sentinel = SentinelHeartbeatMonitor(project_dir=project_dir)
        unresponsive = sentinel.check_unresponsive()
        if unresponsive:
            logger.warning(f"[Auto-Daemon] Detected unresponsive agents: {unresponsive}")

        if workflow_path and Path(workflow_path).is_file():
            try:
                logger.info(
                    f"[Auto-Daemon] Executing declarative Symphony workflow: {workflow_path}"
                )
                schema = SymphonyWorkflowParser.parse_yaml_file(Path(workflow_path))
                await graph_engine.execute_graph(schema)
            except Exception as exc:
                logger.error(f"[Auto-Daemon] Workflow execution error: {exc}")

        await asyncio.sleep(interval_seconds)


async def async_main(*params: str) -> None:
    """Async main function for CLI integration."""
    import sys

    parser = argparse.ArgumentParser(description="Multi-Agent Orchestration Engine")
    parser.add_argument(
        "task", nargs="?", default="Default workflow", help="Workflow task description"
    )
    parser.add_argument("--roles", nargs="+", help="Agent roles to include")
    parser.add_argument("--stage", help="Stage tag or stage identifier")
    parser.add_argument(
        "--execution-mode",
        choices=["parallel", "sequential", "dag"],
        default="parallel",
        help="Workflow execution strategy",
    )
    parser.add_argument("--workflow", help="Path to declarative OpenAI Symphony YAML workflow spec")
    parser.add_argument(
        "--auto-daemon", action="store_true", help="Launch standing background daemon loop"
    )
    parser.add_argument(
        "--pause", action="store_true", help="Create .gemini/PAUSE marker to pause auto-daemon"
    )
    parser.add_argument(
        "--resume", action="store_true", help="Remove .gemini/PAUSE marker to resume auto-daemon"
    )
    parser.add_argument(
        "--daemon-interval", type=float, default=10.0, help="Daemon check interval in seconds"
    )

    cli_args = list(params) if params else sys.argv[1:]
    args = parser.parse_args(cli_args)

    project_dir = Path.cwd()
    pause_file = project_dir / ".gemini" / "PAUSE"

    if args.pause:
        pause_file.parent.mkdir(parents=True, exist_ok=True)
        pause_file.write_text("PAUSED", encoding="utf-8")
        print(
            f"Created pause marker at {pause_file}. Background daemon will pause cleanly after active step."
        )
        return

    if args.resume:
        if pause_file.is_file():
            pause_file.unlink()
            print(f"Removed pause marker at {pause_file}. Background daemon resumed.")
        else:
            print("No pause marker found. Daemon is already active.")
        return

    if getattr(args, "auto_daemon", False):
        await run_auto_daemon(workflow_path=args.workflow, interval_seconds=args.daemon_interval)
        return

    if args.workflow and Path(args.workflow).is_file():
        from .graph_engine import EventDispatcher, StateGraphEngine
        from .telemetry import MemoryStoreAdapter
        from .workflow_parser import SymphonyWorkflowParser

        dispatcher = EventDispatcher()
        memory_adapter = MemoryStoreAdapter(output_dir=project_dir / ".gemini" / "telemetry")
        memory_adapter.subscribe_to_dispatcher(dispatcher)

        graph_engine = StateGraphEngine(project_dir=project_dir, dispatcher=dispatcher)
        schema = SymphonyWorkflowParser.parse_yaml_file(Path(args.workflow))
        res_schema = await graph_engine.execute_graph(schema)
        print(f"Workflow '{res_schema.graph_id}' completed with status: {res_schema.status}")
        return

    engine = OrchestrationEngine()
    plan = await engine.plan_workflow(
        args.task,
        agent_roles=args.roles,
        stage=args.stage,
        execution_mode=args.execution_mode,
    )
    result = await engine.execute_agents(plan)
    print(result)


def main(*params: str) -> None:
    asyncio.run(async_main(*params))


if __name__ == "__main__":
    main()
