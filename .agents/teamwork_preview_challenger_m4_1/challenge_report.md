# Milestone 4: Empirical Stress Test & Adversarial Challenge Report

## Executive Summary

- **Overall Risk Assessment**: **MEDIUM**
- **Pytest Suite Verification**: 32 / 32 passed (Target: >= 25/25).
- **Harness Validation Workflow**: 4 / 4 steps passed (`uv run --active --no-sync agy-task harness-validate`).
- **ContextManagerEngine**: High performance (180,887 ops/sec). Robust handling of negative and overflow tokens. Fractional float token input triggers Pydantic V2 `ValidationError`.
- **SkillSnapshotContext**: Verified rollback on exception. **Vulnerability identified**: Relative path fallback (`Path(s_dir.name)`) causes snapshot directory overwrite collisions when multiple skill paths reside outside `project_dir` and share identical folder names.

---

## 1. Automated Verification Pipeline Results

### 1.1 Pytest Test Suite Execution
- **Command**: `.venv/bin/python -m pytest`
- **Result**: `32 passed, 153 warnings in 10.32s`
- **Verification**: 32 / 32 tests passed (exceeds requirement of >= 25/25).
- **Breakdown**:
  - `tests/test_context_manager.py` (2 passed)
  - `tests/test_graph.py` (2 passed)
  - `tests/test_graph_engine.py` (5 passed)
  - `tests/test_harness_validation.py` (3 passed)
  - `tests/test_models.py` (2 passed)
  - `tests/test_okf.py` (5 passed)
  - `tests/test_orchestration.py` (2 passed)
  - `tests/test_serializer.py` (1 passed)
  - `tests/test_skillopt.py` (5 passed)
  - `tests/test_telemetry.py` (3 passed)
  - `tests/test_verify.py` (2 passed)

### 1.2 Multi-Agent Harness Validation
- **Command**: `uv run --active --no-sync agy-task harness-validate`
- **Result**: All 4 validation steps completed successfully.
  - Step 1: Environment Verification -> PASS
  - Step 2: Multi-Agent Orchestration Plan -> PASS
  - Step 3: Telemetry Collection & Audit -> PASS
  - Step 4: OKF Spec Validation -> PASS
- **Observation / Telemetry Warning**: Non-fatal startup warning in Phoenix telemetry server (`RuntimeError: Failed to bind to address [::]:4317`) due to port 4317 being already occupied by an active process on macOS. The harness gracefully completes with `=== Multi-Agent Harness Validation Passed Successfully ===`.

---

## 2. Empirical Stress Test Findings

### 2.1 ContextManagerEngine.evaluate_context

| Test Scenario | Input (`estimated_tokens`) | Expected Behavior | Actual Behavior | Pass/Fail |
|---|---|---|---|---|
| Negative Tokens | `-1`, `-100`, `-999999`, `-sys.maxsize` | Clamped to 0 tokens, 0% utilization | Clamped to 0 tokens, 0% utilization, `requires_subagent_delegation=False`, model `"flash"` | **PASS** |
| Zero Tokens | `0` | 0% utilization | 0% utilization, delegation `False` | **PASS** |
| Delegation Boundary | `79,999` (39.9995%) | Utilization < 40%, no delegation | Utilization 39.9995%, delegation `False`, model `"flash"` | **PASS** |
| Delegation Boundary | `80,000` (40.0%) | Utilization >= 40%, delegation required | Utilization 40.0%, delegation `True`, model `"flash"` | **PASS** |
| Model Switch Boundary | `89,999` (44.9995%) | Utilization < 45%, recommended `"flash"` | Utilization 44.9995%, delegation `True`, model `"flash"` | **PASS** |
| Model Switch Boundary | `90,000` (45.0%) | Utilization >= 45%, recommended `"pro"` | Utilization 45.0%, delegation `True`, model `"pro"` | **PASS** |
| Context Limit / Overflow | `200,000` to `sys.maxsize` | Utilization clamped to 100%, delegation required | Utilization capped at 100.0%, delegation `True`, model `"pro"` | **PASS** |
| Fractional Float Tokens | `85000.5` | Graceful integer coercion | Raises Pydantic V2 `ValidationError` (`estimated_context_tokens: Input should be a valid integer`) | **FAIL (Minor)** |
| High Concurrency Stress | 10,000 parallel async calls | < 2.0 seconds execution | 10,000 calls completed in 0.0553s (~180,887 ops/sec) | **PASS** |

---

## 3. Adversarial Challenges & Failure Mode Analysis

### [Medium] Challenge 1: SkillSnapshotContext Path Resolution Collision for External Skill Directories

- **Assumption Challenged**: Skill directories configured in `SkillSnapshotContext.skills_dirs` are always strict subdirectories of `self.project_dir`.
- **Attack Scenario**:
  If custom skill directories reside outside `self.project_dir` (e.g. symlinked paths or external skill locations) and share identical directory names (e.g., `/var/external_a/skills` and `/var/external_b/skills`), `s_dir.relative_to(self.project_dir)` raises `ValueError`.
  The exception block executes: `rel_path = Path(s_dir.name)`.
  This maps both paths to `self.temp_dir / "skills"`.
  The second snapshot overwrites the first snapshot in `temp_dir`.
- **Blast Radius**: Upon rollback, directory B's snapshot overwrites directory A's contents, causing corrupt/lossy state restoration for external skill directories.
- **Mitigation Recommendation**:
  Replace `rel_path = Path(s_dir.name)` with a unique path hashing scheme or index-suffixed directory mapping (e.g., `rel_path = Path(f"skill_dir_{idx}_{s_dir.name}")`).

### [Low] Challenge 2: ContextMetrics Fractional Token Input Validation Error

- **Assumption Challenged**: Input token estimations are always pre-cast to `int`.
- **Attack Scenario**: Callers passing calculated float estimates (e.g., `evaluate_context(estimated_tokens=float(total_chars)/4)`) where result has fractional parts trigger a Pydantic `ValidationError` rather than automatic truncation.
- **Blast Radius**: Unhandled exception in evaluation loop if non-integer float is passed.
- **Mitigation Recommendation**: In `evaluate_context`, explicitly cast `estimated_tokens` using `int(estimated_tokens)` prior to model instantiation or accept `float | int` and convert.

---

## 4. Stress Test Script Reference

Empirical test suite script saved and executed at:
`/Users/rmanaloto/agy-graphify-research/.agents/teamwork_preview_challenger_m4_1/stress_test.py`
