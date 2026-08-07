"""Fail-fast log monitoring and error assertion watchdog module."""

import sys
from pathlib import Path

from agy_graphify.logger import setup_universal_logging, logger

setup_universal_logging()

UNIVERSAL_LOG_PATH = Path(".gemini") / "telemetry" / "universal.log"

class FailFastMonitor:
    """Scans log files for errors, warnings, and consecutive timeouts to fail fast."""

    def __init__(self, max_consecutive_errors: int = 1, allowed_patterns: list[str] | None = None) -> None:
        self.max_consecutive_errors = max_consecutive_errors
        self.allowed_patterns = allowed_patterns or []

    def scan_log(self, log_path: Path | None = None, fail_on_warnings: bool = False) -> list[str]:
        target = log_path or UNIVERSAL_LOG_PATH
        if not target.exists():
            logger.info(f"Log file {target} does not exist yet. No issues found.")
            return []

        all_lines = target.read_text(encoding="utf-8", errors="ignore").splitlines()
        lines = all_lines[-50:] if len(all_lines) > 50 else all_lines
        critical_issues: list[str] = []
        consecutive_errors = 0

        for line in lines:
            if self.allowed_patterns and any(p in line for p in self.allowed_patterns):
                continue
            is_issue = ("ERROR" in line or "CRITICAL" in line or "Traceback" in line or "Exception" in line or "Failed to clone" in line or (fail_on_warnings and "WARNING" in line))
            if is_issue and "Unknown action" not in line:
                consecutive_errors += 1
                critical_issues.append(line)
                if consecutive_errors >= self.max_consecutive_errors:
                    logger.error(f"FAIL-FAST ALERT: {consecutive_errors} consecutive operational errors/warnings detected in log!")
            else:
                consecutive_errors = 0

        logger.info(f"Fail-Fast Watchdog Scan: Found {len(critical_issues)} critical issues across {len(lines)} log lines.")
        return critical_issues

    def assert_no_critical_errors(self, fail_on_warnings: bool = False, log_path: Path | None = None) -> None:
        issues = self.scan_log(log_path=log_path, fail_on_warnings=fail_on_warnings)
        if issues:
            logger.error(f"Fail-Fast Monitor Assertion Failed: {len(issues)} critical log issues detected.")
            sys.exit(1)
        else:
            logger.info("Fail-Fast Monitor Assertion Passed: 0 critical log issues detected.")


def monitor_logs(fail_on_warnings: bool = False, log_path: Path | None = None) -> None:
    """CLI Entrypoint for monitoring logs."""
    import os
    env_fail = os.environ.get("FAIL_ON_WARNINGS") == "1"
    monitor = FailFastMonitor()
    monitor.assert_no_critical_errors(fail_on_warnings=fail_on_warnings or env_fail, log_path=log_path)


__all__ = ["FailFastMonitor", "monitor_logs"]
