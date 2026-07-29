"""Flexible async task dispatcher wrapping python library functions for skills and mise tasks."""

import argparse
import asyncio
import sys
from collections.abc import Awaitable, Callable
from typing import Any

from .logger import logger


class TaskDispatcher:
    """Dispatches tasks and skill parameters to underlying Python library functions."""

    def __init__(self) -> None:
        self._registry: dict[str, Callable[..., Awaitable[Any] | Any]] = {}

    def register(self, name: str, func: Callable[..., Awaitable[Any] | Any]) -> None:
        """Register a function handler for a skill or automation task."""
        self._registry[name] = func

    async def dispatch(self, action: str, *args: Any, **kwargs: Any) -> Any:
        """Execute a registered action asynchronously with flexible arguments."""
        if action not in self._registry:
            msg = f"Unknown action '{action}'. Available actions: {list(self._registry.keys())}"
            logger.error(msg)
            raise KeyError(msg)

        func = self._registry[action]
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        return func(*args, **kwargs)


async def async_main() -> None:
    """Async CLI entrypoint for task dispatcher."""
    parser = argparse.ArgumentParser(description="Flexible Async Python Task Dispatcher")
    parser.add_argument("action", nargs="?", default="help", help="Action to execute")
    parser.add_argument("params", nargs=argparse.REMAINDER, help="Action parameters")

    parsed_args = parser.parse_args()

    dispatcher = TaskDispatcher()

    from .graph import async_main as graph_main
    from .orchestration import async_main as orchestrate_main
    from .verify import EnvironmentVerifier

    async def verify_action(*_params: str) -> None:
        verifier = EnvironmentVerifier()
        exit_code = await verifier.verify_and_output()
        if exit_code != 0:
            sys.exit(exit_code)

    dispatcher.register("verify", verify_action)
    dispatcher.register("graphify", graph_main)
    dispatcher.register("orchestrate", orchestrate_main)

    if parsed_args.action in ("help", "-h", "--help"):
        parser.print_help()
        sys.exit(0)

    try:
        await dispatcher.dispatch(parsed_args.action, *parsed_args.params)
    except KeyError as err:
        logger.error(f"Task dispatch error: {err}")
        sys.exit(1)


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
