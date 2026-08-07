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


UNIVERSAL_LOG_PATH = Path(".gemini") / "telemetry" / "universal.log"


_UNIVERSAL_LOGGING_INITIALIZED: bool = False


def setup_universal_logging(
    log_file: Path | None = None,
    level: str = "INFO",
) -> Path:
    """Redirect loguru logs, stdout, and stderr to a single universal log file with multi-process queue safety."""
    global _UNIVERSAL_LOGGING_INITIALIZED
    target_log = log_file or UNIVERSAL_LOG_PATH
    target_log.parent.mkdir(parents=True, exist_ok=True)

    if _UNIVERSAL_LOGGING_INITIALIZED:
        return target_log

    _UNIVERSAL_LOGGING_INITIALIZED = True

    # Add console sink (multiprocess-safe via enqueue=True)
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        enqueue=True,
    )

    # Add universal file sink (multiprocess-safe via enqueue=True)
    logger.add(
        str(target_log),
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="50 MB",
        retention="10 days",
        enqueue=True,
    )

    logger.info(f"Universal logging initialized at {target_log}")
    return target_log


__all__ = ["configure_logger", "logger", "setup_universal_logging", "UNIVERSAL_LOG_PATH"]
