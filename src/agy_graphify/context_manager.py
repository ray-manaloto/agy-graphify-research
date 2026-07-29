"""Async Context Manager, Subagent Orchestrator, & Self-Learning Release Reviewer."""

import argparse
import asyncio
import json
import subprocess
from pathlib import Path

from pydantic import BaseModel

from .logger import logger


class ContextMetrics(BaseModel):
    """Metrics tracking conversation token consumption and subagent delegation status."""

    estimated_context_tokens: int
    context_limit_tokens: int = 200000
    utilization_percentage: float
    requires_subagent_delegation: bool
    recommended_model: str = "flash"


class ReleaseUpdate(BaseModel):
    """Tool version release update detected during self-learning loop."""

    tool: str
    current_version: str
    latest_version: str | None = None
    update_available: bool = False


class ContextManagerEngine:
    """Monitors context window usage (<50% threshold), manages subagent delegation, and checks release updates."""

    def __init__(self, project_dir: Path | None = None) -> None:
        self.project_dir = project_dir or Path.cwd()
        self.mise_file = self.project_dir / ".mise.toml"

    async def evaluate_context(self, estimated_tokens: int = 40000) -> ContextMetrics:
        """Evaluate context window consumption against the 50% maximum threshold."""
        limit = 200000
        utilization = (estimated_tokens / limit) * 100.0
        should_delegate = utilization >= 40.0

        metrics = ContextMetrics(
            estimated_context_tokens=estimated_tokens,
            context_limit_tokens=limit,
            utilization_percentage=utilization,
            requires_subagent_delegation=should_delegate,
            recommended_model="flash_lite" if utilization > 45.0 else "flash",
        )

        logger.info(
            f"Context Utilization: {utilization:.1f}% ({estimated_tokens}/{limit} tokens). "
            f"Subagent Delegation Required: {should_delegate}"
        )
        return metrics

    async def check_tool_updates(self) -> list[ReleaseUpdate]:
        """Check for new release updates across pinned toolchain to drive self-learning loop."""
        updates: list[ReleaseUpdate] = []
        if not self.mise_file.is_file():
            return updates

        try:
            proc = await asyncio.create_subprocess_exec(
                "mise",
                "outdated",
                cwd=self.project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            if proc.returncode == 0:
                for line in stdout.decode("utf-8").splitlines():
                    parts = line.split()
                    if len(parts) >= 3:
                        tool, curr, latest = parts[0], parts[1], parts[2]
                        updates.append(
                            ReleaseUpdate(
                                tool=tool,
                                current_version=curr,
                                latest_version=latest,
                                update_available=True,
                            )
                        )
        except (OSError, subprocess.SubprocessError) as exc:
            logger.warning(f"Could not check tool release updates: {exc}")

        logger.info(f"Release Reviewer found {len(updates)} toolchain updates.")
        return updates


async def async_main(*params: str) -> None:
    """Async main for context manager & self-learning CLI."""
    parser = argparse.ArgumentParser(description="Context Window & Release Reviewer Engine")
    parser.add_argument("--tokens", type=int, default=40000, help="Estimated context tokens")

    args = parser.parse_args(list(params) if params else None)

    engine = ContextManagerEngine()
    metrics = await engine.evaluate_context(estimated_tokens=args.tokens)
    updates = await engine.check_tool_updates()

    output = {
        "context_metrics": metrics.model_dump(),
        "release_updates": [u.model_dump() for u in updates],
    }
    print(json.dumps(output, indent=2))


def main(*params: str) -> None:
    asyncio.run(async_main(*params))


if __name__ == "__main__":
    main()
