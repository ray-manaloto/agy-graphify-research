"""Async Multi-Agent Orchestration & Workflow Dispatcher."""

import argparse
import asyncio
from pathlib import Path

from .logger import logger
from .models.orchestration_schema import Agent, OrchestrationPlan


class OrchestrationEngine:
    """Manages multi-agent task breakdown, subagent roles, and parallel workflow execution."""

    def __init__(self, project_dir: Path | None = None) -> None:
        self.project_dir = project_dir or Path.cwd()

    async def plan_workflow(
        self, task_description: str, agent_roles: list[str] | None = None
    ) -> OrchestrationPlan:
        """Break down complex task into subagent execution plan asynchronously."""
        roles = agent_roles or ["researcher", "developer", "verifier"]

        plan = OrchestrationPlan(
            task=task_description,
            project=self.project_dir.name,
            agents=[
                Agent(
                    role=role,
                    status="pending",
                    subtasks=[f"Execute subtask for {role}"],
                )
                for role in roles
            ],
            execution_mode="parallel",
        )

        plan_file = self.project_dir / ".gemini" / "orchestration_plan.json"
        plan_file.parent.mkdir(parents=True, exist_ok=True)
        plan_file.write_text(plan.model_dump_json(indent=2), encoding="utf-8")

        logger.info(
            f"Planned workflow for task '{task_description}' with {len(plan.agents)} agents."
        )
        return plan

    async def execute_agents(self, plan: OrchestrationPlan) -> str:
        """Simulate or coordinate subagent execution based on plan asynchronously."""
        agent_count = len(plan.agents)
        logger.info(f"Dispatching {agent_count} subagents for task '{plan.task}'.")
        return f"Successfully dispatched {agent_count} subagents for task: '{plan.task}'"


async def async_main(*params: str) -> None:
    """Async main function for CLI integration."""
    parser = argparse.ArgumentParser(description="Multi-Agent Orchestration Engine")
    parser.add_argument(
        "task", nargs="?", default="Default workflow", help="Workflow task description"
    )
    parser.add_argument("--roles", nargs="+", help="Agent roles to include")

    args = parser.parse_args(list(params) if params else None)

    engine = OrchestrationEngine()
    plan = await engine.plan_workflow(args.task, agent_roles=args.roles)
    result = await engine.execute_agents(plan)
    print(result)


def main(*params: str) -> None:
    asyncio.run(async_main(*params))


if __name__ == "__main__":
    main()
