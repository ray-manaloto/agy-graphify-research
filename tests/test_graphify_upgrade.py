"""Unit tests for Graphify 0.9.35 upgrade, Python SDK skill auto-generation, and fail-fast log monitoring."""

import os
from pathlib import Path
import pytest
from agy_graphify.monitor import FailFastMonitor, monitor_logs
from agy_graphify.tasks import graphify_setup_action
from agy_graphify.verify import EnvironmentVerifier

def test_graphify_version_in_config_files():
    pyproject_content = Path("pyproject.toml").read_text(encoding="utf-8")
    assert "graphifyy>=0.9.35" in pyproject_content

    mise_content = Path(".mise.toml").read_text(encoding="utf-8")
    assert '"pipx:graphifyy" = { version = "0.9.35"' in mise_content

@pytest.mark.asyncio
async def test_graphify_setup_action_auto_generates_version_file():
    await graphify_setup_action()
    version_file = Path(".agents") / "skills" / "graphify" / ".graphify_version"
    assert version_file.is_file()
    assert version_file.read_text(encoding="utf-8").strip() == "0.9.35"

def test_fail_fast_monitor_warnings_as_errors(tmp_path: Path):
    log_file = tmp_path / "test_universal.log"
    log_file.write_text(
        "2026-08-07 00:00:00 | WARNING | agy_graphify.verify:run_check:10 - Test warning in verify\n",
        encoding="utf-8"
    )
    monitor = FailFastMonitor()
    
    # Without fail_on_warnings, single warning is ignored
    issues_default = monitor.scan_log(log_path=log_file, fail_on_warnings=False)
    assert len(issues_default) == 0

    # With fail_on_warnings=True, warning is caught
    issues_strict = monitor.scan_log(log_path=log_file, fail_on_warnings=True)
    assert len(issues_strict) == 1
