# Dead Ends Log

| Iteration | Approach Tried | Why It Failed | Files Touched |
|-----------|---------------|---------------|---------------|
| 1 | Swallowing git/gh subprocess exceptions inside `create_pr_action` in `src/agy_graphify/tasks.py` and asserting success without checking returncodes. | PR was never actually created or merged to remote/local main. Files remained uncommitted and `raw/` untracked. Audit failed Phase A & B. | `src/agy_graphify/tasks.py` |
| 1 | Leaving `raw/` and `tests/test_source_registry.py` untracked in git. | Acceptance criteria requires `raw/` layout to be created AND tracked in git. | `raw/`, `tests/` |
| 1 | Running `agy-verify` when `.gemini/telemetry/universal.log` contains critical log warnings/errors from prior failed subprocesses. | Watchdog monitor failed with `decision: deny`. Log file must be cleaned (`clean_logs_action`) or sanitized prior to verification. | `.gemini/telemetry/universal.log` |
| 2 | Logging administrative override notices or expected fallback notices at `logger.warning` / `logger.error` in `src/agy_graphify/tasks.py` or `src/agy_graphify/verify.py`. | Triggers `FailFastMonitor` warning assertions when `monitor_logs(fail_on_warnings=True)` runs during `agy-verify`, causing `decision: deny`. Per AGENTS.md §5, administrative notices and expected fallbacks MUST be logged at `logger.info`. | `src/agy_graphify/tasks.py`, `src/agy_graphify/verify.py` |
