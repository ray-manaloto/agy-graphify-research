"""Fail-fast log monitoring and error assertion watchdog module."""

import sys
from pathlib import Path

from agy_graphify.logger import setup_universal_logging, logger

setup_universal_logging()

UNIVERSAL_LOG_PATH = Path(".gemini") / "telemetry" / "universal.log"

class FailFastMonitor:
    """Scans log files for errors, warnings, and consecutive timeouts to fail fast."""

    def __init__(self, max_consecutive_errors: int = 3) -> None:
        self.max_consecutive_errors = max_consecutive_errors

    def scan_log(self, log_path: Path | None = None) -> list[str]:
        target = log_path or UNIVERSAL_LOG_PATH
        if not target.exists():
            logger.info(f"Log file {target} does not exist yet. No issues found.")
            return []

        lines = target.read_text(encoding="utf-8", errors="ignore").splitlines()
        critical_issues: list[str] = []
        consecutive_errors = 0

        operational_targets = ("colibri_extractor", "source_registry", "verify", "graph_engine", "ingest", "extract")
        for line in lines:
            if ("ERROR" in line or "Traceback" in line or "Failed to clone" in line) and "Unknown action" not in line and any(t in line for t in operational_targets):
                consecutive_errors += 1
                critical_issues.append(line)
                if consecutive_errors >= self.max_consecutive_errors:
                    logger.error(f"FAIL-FAST ALERT: {consecutive_errors} consecutive operational errors detected in log!")
            else:
                consecutive_errors = 0

        logger.info(f"Fail-Fast Watchdog Scan: Found {len(critical_issues)} critical issues across {len(lines)} log lines.")
        return critical_issues

    def assert_no_critical_errors(self) -> None:
        issues = self.scan_log()
        if issues:
            logger.error(f"Fail-Fast Monitor Assertion Failed: {len(issues)} critical log issues detected.")
            sys.exit(1)
        else:
            logger.info("Fail-Fast Monitor Assertion Passed: 0 critical log issues detected.")


def monitor_logs() -> None:
    """CLI Entrypoint for monitoring logs."""
    monitor = FailFastMonitor()
    monitor.assert_no_critical_errors()


__all__ = ["FailFastMonitor", "monitor_logs"]
