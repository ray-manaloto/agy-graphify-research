"""Empirical test suite for Remediation Gate 2 verification."""

import asyncio
import os
import sys
import time
from pathlib import Path
import pytest

from agy_graphify.tasks import _run_subprocess_check, clean_logs_action


async def test_run_subprocess_check_success():
    """Verify _run_subprocess_check succeeds on valid commands."""
    env = os.environ.copy()
    git_bin = "/usr/bin/git" if os.path.exists("/usr/bin/git") else "git"
    code, stdout = await _run_subprocess_check([git_bin, "--version"], env=env)
    assert code == 0
    assert "git version" in stdout
    print("✓ test_run_subprocess_check_success passed")


async def test_run_subprocess_check_failing():
    """Verify _run_subprocess_check raises RuntimeError on failing command (e.g. invalid git command)."""
    env = os.environ.copy()
    git_bin = "/usr/bin/git" if os.path.exists("/usr/bin/git") else "git"
    failing_cmd = [git_bin, "non-existent-git-subcommand-xyz123"]
    try:
        await _run_subprocess_check(failing_cmd, env=env)
        pytest.fail("Expected RuntimeError was not raised!")
    except RuntimeError as exc:
        err_str = str(exc)
        assert f"Command '{git_bin} non-existent-git-subcommand-xyz123' failed with exit code" in err_str
        assert "is not a git command" in err_str
        print(f"✓ test_run_subprocess_check_failing passed with expected error:\n  {err_str}")


async def test_clean_logs_action():
    """Verify clean_logs_action truncates universal.log and cleans old process logs."""
    telemetry_dir = Path.cwd() / ".gemini" / "telemetry"
    telemetry_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create a dummy old proc log (8 days old)
    old_proc_log = telemetry_dir / "proc_999999_test_old.log"
    old_proc_log.write_text("Dummy old log content\n", encoding="utf-8")
    eight_days_ago = time.time() - (8 * 24 * 60 * 60)
    os.utime(old_proc_log, (eight_days_ago, eight_days_ago))

    # 2. Write content into universal.log
    universal_log = telemetry_dir / "universal.log"
    universal_log.write_text("Some dirty test logs in universal.log\n", encoding="utf-8")
    assert universal_log.stat().st_size > 0

    # 3. Execute clean_logs_action
    await clean_logs_action()

    # 4. Verify old proc log unlinked
    assert not old_proc_log.exists(), "Old proc_*.log was not unlinked by clean_logs_action!"

    # 5. Verify universal.log truncated and empty
    assert universal_log.exists(), "universal.log should exist after clean_logs_action"
    content = universal_log.read_text(encoding="utf-8")
    assert content == "", f"universal.log expected empty string, but got len {len(content)}"
    print("✓ test_clean_logs_action passed: old log unlinked, universal.log truncated to size 0.")


async def test_allow_main_commit_agy_verify():
    """Verify ALLOW_MAIN_COMMIT=1 EnvironmentVerifier returns decision: allow."""
    from agy_graphify.verify import EnvironmentVerifier, Decision
    env = os.environ.copy()
    env["ALLOW_MAIN_COMMIT"] = "1"
    
    verifier = EnvironmentVerifier()
    # Save original env ALLOW_MAIN_COMMIT
    orig_val = os.environ.get("ALLOW_MAIN_COMMIT")
    os.environ["ALLOW_MAIN_COMMIT"] = "1"
    try:
        res = await verifier.run_check(use_cache=False)
        assert res.decision == Decision.allow, f"Expected decision 'allow', got '{res.decision}' with reason: {res.reason}"
        print(f"✓ test_allow_main_commit_agy_verify passed: decision is '{res.decision.value}'")
    finally:
        if orig_val is None:
            os.environ.pop("ALLOW_MAIN_COMMIT", None)
        else:
            os.environ["ALLOW_MAIN_COMMIT"] = orig_val


async def main():
    print("=== STARTING REMEDIATION GATE 2 EMPIRICAL TESTS ===")
    await test_run_subprocess_check_success()
    await test_run_subprocess_check_failing()
    await test_clean_logs_action()
    await test_allow_main_commit_agy_verify()
    print("=== ALL EMPIRICAL TESTS PASSED SUCCESSFULLY ===")


if __name__ == "__main__":
    asyncio.run(main())
