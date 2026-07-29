"""Sink-configurable structured logging for agy_graphify using Loguru."""

import sys
from pathlib import Path

from loguru import logger

# Remove default stderr handler so there is zero unconfigured output
logger.remove()


def configure_logger(
    enable_stdout: bool = False,
    json_path: Path | None = None,
    binary_path: Path | None = None,
    level: str = "INFO",
) -> None:
    """Configure log sinks dynamically."""
    logger.remove()

    if enable_stdout:
        logger.add(
            sys.stdout,
            level=level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        )

    if json_path:
        logger.add(
            str(json_path),
            level=level,
            serialize=True,
            rotation="10 MB",
        )

    if binary_path:
        logger.add(
            str(binary_path),
            level=level,
            format="{time} {level} {message}",
            rotation="10 MB",
        )


__all__ = ["configure_logger", "logger"]
