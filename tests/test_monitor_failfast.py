import pytest
import sys
from pathlib import Path
from agy_graphify.monitor import FailFastMonitor, monitor_logs

def test_single_error_triggers_failure(tmp_path):
    log_file = tmp_path / "test.log"
    log_file.write_text("INFO: starting\nERROR: something failed\n", encoding="utf-8")
    
    monitor = FailFastMonitor(max_consecutive_errors=1)
    issues = monitor.scan_log(log_path=log_file)
    assert len(issues) == 1
    
    with pytest.raises(SystemExit):
        monitor.assert_no_critical_errors(log_path=log_file)

def test_single_warning_triggers_failure_when_flag_set(tmp_path):
    log_file = tmp_path / "test.log"
    log_file.write_text("INFO: starting\nWARNING: low disk space\n", encoding="utf-8")
    
    monitor = FailFastMonitor(max_consecutive_errors=1)
    issues = monitor.scan_log(log_path=log_file, fail_on_warnings=True)
    assert len(issues) == 1
    
    with pytest.raises(SystemExit):
        monitor.assert_no_critical_errors(log_path=log_file, fail_on_warnings=True)

    # Should not fail if flag is false
    issues = monitor.scan_log(log_path=log_file, fail_on_warnings=False)
    assert len(issues) == 0

def test_non_consecutive_errors_trigger_failure(tmp_path):
    log_file = tmp_path / "test.log"
    log_file.write_text("ERROR: first\nINFO: ok\nERROR: second\n", encoding="utf-8")
    
    monitor = FailFastMonitor(max_consecutive_errors=1)
    issues = monitor.scan_log(log_path=log_file)
    assert len(issues) == 2
    
    with pytest.raises(SystemExit):
        monitor.assert_no_critical_errors(log_path=log_file)

def test_unfiltered_module_error_lines_trigger_failure(tmp_path):
    log_file = tmp_path / "test.log"
    log_file.write_text("ERROR from some_random_module: bad\n", encoding="utf-8")
    
    monitor = FailFastMonitor(max_consecutive_errors=1)
    issues = monitor.scan_log(log_path=log_file)
    assert len(issues) == 1

def test_log_target_isolation(tmp_path):
    log1 = tmp_path / "test1.log"
    log2 = tmp_path / "test2.log"
    log1.write_text("ERROR: bad\n", encoding="utf-8")
    log2.write_text("INFO: good\n", encoding="utf-8")
    
    monitor = FailFastMonitor(max_consecutive_errors=1)
    issues1 = monitor.scan_log(log_path=log1)
    issues2 = monitor.scan_log(log_path=log2)
    
    assert len(issues1) == 1
    assert len(issues2) == 0

def test_allowed_patterns_ignored(tmp_path):
    log_file = tmp_path / "test.log"
    log_file.write_text("ERROR: initialization failed [BENIGN]\nERROR: real issue\n", encoding="utf-8")
    
    monitor = FailFastMonitor(max_consecutive_errors=1, allowed_patterns=["[BENIGN]"])
    issues = monitor.scan_log(log_path=log_file)
    assert len(issues) == 1
    assert "real issue" in issues[0]
