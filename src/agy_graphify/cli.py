"""Main Async CLI entrypoint for agy-graphify-research."""

import argparse
import asyncio
import sys

from .graph import async_main as graph_main
from .orchestration import async_main as orchestrate_main
from .tasks import async_main as tasks_main
from .verify import EnvironmentVerifier


async def async_cli_main() -> None:
    parser = argparse.ArgumentParser(
        description="agy-graphify CLI - Unified Automation & Multi-Agent Orchestration"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    subparsers.add_parser("verify", help="Verify project state and isolation")
    subparsers.add_parser("graphify", help="Run knowledge graph extraction & query")
    subparsers.add_parser("orchestrate", help="Run multi-agent workflow orchestration")
    subparsers.add_parser("task", help="Execute flexible task dispatcher")

    args, remaining = parser.parse_known_args()

    if args.command == "verify":
        verifier = EnvironmentVerifier()
        sys.exit(await verifier.verify_and_output())
    elif args.command == "graphify":
        await graph_main(*remaining)
    elif args.command == "orchestrate":
        await orchestrate_main(*remaining)
    elif args.command == "task":
        await tasks_main()
    else:
        parser.print_help()


def main() -> None:
    asyncio.run(async_cli_main())


if __name__ == "__main__":
    main()
