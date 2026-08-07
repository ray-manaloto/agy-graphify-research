# Milestone 3: Bug Remediation & Hardening Report

**Worker Agent**: `teamwork_preview_worker_m3_1`  
**Milestone**: Milestone 3 — Bug Remediation & Hardening  
**Date**: 2026-07-31  

---

## Executive Summary

All 26 technical defects identified in the Milestone 1 technical analysis (`/Users/rmanaloto/agy-graphify-research/.agents/teamwork_preview_explorer_m1_1/analysis.md`) have been fully remediated across the codebase with zero shortcuts, hardcoding, or dummy facades. 

All code modifications adhere strictly to the minimal change principle, preserve project conventions, and comply with `AGENTS.md` guidelines and zero shell script policies.

Verification results:
- **Pytest**: 32/32 tests passing (`.venv/bin/python -m pytest`)
- **Harness Validation**: 4/4 workflow steps passing (`uv run --active --no-sync agy-task harness-validate`)
- **Environment & AST Verification**: Zero shell scripts and clean AST (`uv run --active --no-sync agy-verify`)
- **OKF Spec Validation**: All documentation OKF-compliant (`uv run --active --no-sync python3 -m agy_graphify.okf docs`)

---

## Detailed Remediation Summary

### 1. `src/agy_graphify/orchestration.py`

| Defect / Requirement | Remediation Applied |
| :--- | :--- |
| **Atomic Writes in Heartbeat Persistence** | Replaced direct `write_text` in `SentinelHeartbeatMonitor.record_heartbeat` with atomic tempfile creation (`tempfile.NamedTemporaryFile`) and `os.replace`. Checked JSON root type (`isinstance(raw_data, dict)`). |
| **Atomic Writes in Plan Dispatch** | Replaced direct `write_text` in `OrchestrationEngine.plan_workflow` with atomic tempfile write (`tempfile.NamedTemporaryFile`) and `os.replace` to prevent corrupted plan JSONs. |
| **Exception Logging in Heartbeat Monitor** | Replaced silent `except Exception: pass` in `check_unresponsive` with explicit warning logging (`logger.warning`). Added strict type checks (`isinstance(info, dict)`, `isinstance(last_hb, (int, float))`). |
| **Decoupled Prompt Optimization** | Added `optimize_prompts: bool = False` parameter to `plan_workflow`. Pure workflow planning operates without mutating prompts or `LESSONS.md` unless explicitly enabled. |

### 2. `src/agy_graphify/skillopt.py`

| Defect / Requirement | Remediation Applied |
| :--- | :--- |
| **Safe Pytest Subprocess Execution** | Replaced bare `subprocess.run(["uv", "run", "pytest"])` in `mutate_subagent_prompts` with `[sys.executable, "-m", "pytest"]`. Handled `(subprocess.CalledProcessError, FileNotFoundError, OSError)` to guarantee snapshot rollback if test execution fails or binary is missing. |
| **Robust Path Resolution** | Resolved `project_dir` and `skills_dirs` with `.resolve()`. Added `try...except ValueError` guard for `relative_to` path resolution. |
| **Complete Rollback for New Directories** | Tracked `self.created_dirs` in `SkillSnapshotContext`. Modified `rollback()` to clean up newly created skill directories that did not exist before snapshot entry. |
| **Line-by-Line Telemetry Log Parsing** | Refactored `SkillOptAdapter.evaluate_trajectories` to parse lines individually inside a per-line `try...except` block, preventing a single malformed JSON line from discarding subsequent valid telemetry events. |
| **Capped Error Rate Calculation** | Applied `min(1.0, max(0.0, raw_error_rate))` in `evaluate_trajectories` to bound `error_rate` within `[0.0, 1.0]`. |
| **Deduplicated `LESSONS.md` & Dynamic Timestamps** | Tracked existing remediation rules in `update_lessons_okf_atomic` to prevent exponential duplicate rule accumulation. Preserved existing `created_at` frontmatter timestamp or generated dynamic ISO timestamp instead of static string. |

### 3. `src/agy_graphify/telemetry.py`

| Defect / Requirement | Remediation Applied |
| :--- | :--- |
| **Resilient Transcript File Parsing** | Updated `_parse_transcript_file` to validate root JSON line structure (`isinstance(raw, dict)`), default null or non-list `tool_calls` to `[]`, and catch `(json.JSONDecodeError, AttributeError, TypeError, ValidationError, ValueError)`. |
| **Case-Insensitive Failed Tool Analysis** | Updated `analyze_failed_tools` to validate tool call item structures (`isinstance(tc, dict)`) and perform case-insensitive status matching (`ev.status.upper() in ("ERROR", "FAILED")`). |
| **Single Phoenix Server Launch Guard** | Added class-level flag `_phoenix_initialized: bool = False` to prevent redundant server launch attempts across multiple `TelemetryCollector` instantiations. |
| **Non-Existent Conversation Logging** | Added `logger.warning` in `collect_events` when a specific non-existent `conversation_id` is requested. |

### 4. `src/agy_graphify/context_manager.py`

| Defect / Requirement | Remediation Applied |
| :--- | :--- |
| **`AGENTS.md` Model Allocation Alignment** | Aligned `recommended_model` logic in `evaluate_context` to output `"pro"` for high context utilization (`>= 45.0%`) and `"flash"` for normal utilization, matching `AGENTS.md` subagent model guidance. |
| **Clamped Token & Utilization Inputs** | Clamped `estimated_tokens` to `max(0, estimated_tokens)` and `utilization` to `[0.0, 100.0]`. |
| **Timeout Guard & Table Header Filtering** | Added `asyncio.wait_for(proc.communicate(), timeout=10.0)` in `check_tool_updates` to catch process hangs. Added filtering to skip table header lines (e.g. `Tool Current Latest`) returned by `mise outdated`. |

### 5. `src/agy_graphify/models/orchestration_schema.py`

| Defect / Requirement | Remediation Applied |
| :--- | :--- |
| **Non-Null `Agent.subtasks` Default** | Changed `subtasks` field definition from `list[str] | None = None` to `list[str] = Field(default_factory=list)`. Prevents `TypeError` during subtask iteration on deserialized agent instances. |

---

## Verification Results Matrix

```
====================== 32 passed in 10.81s ======================
Step 1: Environment Verification -> ALLOW
Step 2: Multi-Agent Orchestration Plan -> DISPATCHED 7 AGENTS
Step 3: Telemetry Collection & Audit -> PROCESSED
Step 4: OKF Spec Validation -> ALLOW
=== Multi-Agent Harness Validation Passed Successfully ===
agy-verify -> ALLOW (Zero shell scripts & clean AST)
okf docs -> ALLOW (OKF documentation compliant)
```
