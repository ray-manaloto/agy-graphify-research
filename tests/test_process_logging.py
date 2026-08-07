import os
from pathlib import Path
import pytest
from loguru import logger
from agy_graphify.logger import setup_universal_logging
from agy_graphify.tasks import TaskDispatcher, clean_logs_action

def test_process_logging_format_and_sink(tmp_path):
    # Loguru caches global state, so we need to reset/configure carefully
    # But setup_universal_logging has _UNIVERSAL_LOGGING_INITIALIZED guard.
    import agy_graphify.logger
    agy_graphify.logger._UNIVERSAL_LOGGING_INITIALIZED = False
    logger.remove()
    
    target_log = tmp_path / "telemetry" / "universal.log"
    setup_universal_logging(log_file=target_log)
    
    logger.info("Test process log entry")
    
    # Let loguru flush enqueue
    import time
    logger.complete()
    
    pid = os.getpid()
    proc_log = tmp_path / "telemetry" / f"proc_{pid}.log"
    
    assert target_log.exists()
    assert proc_log.exists()
    
    universal_content = target_log.read_text()
    proc_content = proc_log.read_text()
    
    assert f"PID:{pid}" in universal_content
    assert f"PID:{pid}" in proc_content

@pytest.mark.asyncio
async def test_clean_logs_action(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    telemetry_dir = Path(".gemini/telemetry")
    telemetry_dir.mkdir(parents=True)
    
    old_log = telemetry_dir / "proc_9999.log"
    old_log.write_text("old")
    
    new_log = telemetry_dir / "proc_8888.log"
    new_log.write_text("new")
    
    import time
    os.utime(old_log, (time.time() - 8 * 86400, time.time() - 8 * 86400))
    
    dispatcher = TaskDispatcher()
    dispatcher.register("clean-logs", clean_logs_action)
    
    await dispatcher.dispatch("clean-logs")
    
    assert not old_log.exists()
    assert new_log.exists()
