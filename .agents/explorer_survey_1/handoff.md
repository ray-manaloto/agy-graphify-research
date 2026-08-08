# Handoff Report — Explorer Survey 1

**Task**: Investigation of `clean_logs_action()` automated pruning logic, legacy directory structure (`graphify-out-antigravity/`, nested `graphify-out/graphify-out/`), safety checks, and potential side effects.

---

## 1. Observation

### 1.1 Current `clean_logs_action()` Implementation
In `src/agy_graphify/tasks.py` (lines 585–601):
```python
async def clean_logs_action(*_params: str) -> None:
    import time
    logger.info("Cleaning up process logs older than 7 days...")
    telemetry_dir = Path(".gemini/telemetry")
    if not telemetry_dir.exists():
        return
    
    now = time.time()
    seven_days_ago = now - (7 * 24 * 60 * 60)
    count = 0
    for log_file in telemetry_dir.glob("proc_*.log"):
        if log_file.stat().st_mtime < seven_days_ago:
            log_file.unlink()
            count += 1
    
    logger.info(f"Cleaned up {count} old process logs.")
```

**Key Observation**: The function currently only handles deleting old process log files in `.gemini/telemetry/`. Crucially, line 589 (`if not telemetry_dir.exists(): return`) causes the function to exit early if `.gemini/telemetry/` does not exist, which would bypass any subsequent directory pruning logic if left as-is.

### 1.2 Existing Legacy Directory Artifacts in Workspace
Using `find_by_name` and `list_dir` on `/Users/rmanaloto/agy-graphify-research`:
- `graphify-out/` — Canonical workspace root output directory (contains `graph.json`, `GRAPH_REPORT.md`, `ast_graph.json`, `lsp_symbols.json`, `extended_repo_manifest.json`, `wiki/`).
- `graphify-out-antigravity/` — Root-level legacy directory containing 3 files (`.graphify_learning.json`, `GRAPH_REPORT.md`, `graph.json`) and 2 subdirectories (`memory/`, `reflections/`). Total size: ~850KB.
- `graphify-out/graphify-out/` — Nested legacy output directory inside `graphify-out/` containing `.graphify_analysis.json`, `.graphify_root`, `graph.json`, `manifest.json`, `cache/`. Total size: ~58MB.

### 1.3 References in Codebase & Configuration
- `.gitignore` (Line 17): Lists `graphify-out-antigravity/`.
- `docs/graphify_agent_comparison_report.md` (Lines 26, 57, 58, 65, 67, 76): References historical comparative evaluation between Colibrì Engine (`graphify-out/`) and Antigravity Agent (`graphify-out-antigravity/`).
- `docs/graphify_sources_proposal_architecture.md` (Lines 42–45): Explicitly identifies `graphify-out-antigravity/` and nested `graphify-out/graphify-out/` as non-standard layout artifacts and mandates updating `clean_logs_action()` in `src/agy_graphify/tasks.py` to prune them during `uv run agy-task clean-logs`.
- `src/agy_graphify/colibri_extractor.py` (Line 235): Filters files during directory scanning with `and "graphify-out" not in p.parts`. While this excludes `graphify-out/` and `graphify-out/graphify-out/`, it does **not** exclude `graphify-out-antigravity/` (because `p.parts` element is `"graphify-out-antigravity"` rather than `"graphify-out"`).
- `tests/test_process_logging.py` (Lines 37–57): Contains `test_clean_logs_action()` which tests `clean_logs_action()` using `tmp_path` and `monkeypatch.chdir(tmp_path)`.

---

## 2. Logic Chain

1. **Requirement Analysis**:
   - The user request and `docs/graphify_sources_proposal_architecture.md` require `clean_logs_action()` to automatically prune legacy workspace root directories (`graphify-out-antigravity/` and nested `graphify-out/graphify-out/`) whenever `uv run agy-task clean-logs` is executed.
   - Requirement 2b of the proposal mandates that `tests/test_workspace_layout_standards.py` verify zero non-standard `graphify-out*` folders exist after pruning.

2. **Refactoring `clean_logs_action()` Structure**:
   - To prevent premature exit when `.gemini/telemetry/` is missing, the log file deletion logic must be wrapped in `if telemetry_dir.exists(): ...` without an early `return`.
   - The directory pruning logic must execute unconditionally after (or independently of) the log file cleanup.

3. **Targeting Pruning Patterns**:
   - **Pattern 1: Non-canonical root-level directories**: Glob `Path.cwd().glob("graphify-out*")`. Filter for directories (`entry.is_dir()`) where `entry.name != "graphify-out"`. This matches `graphify-out-antigravity` and any other non-standard `graphify-out*` folder created at root.
   - **Pattern 2: Nested legacy output directories**: Check `Path.cwd() / "graphify-out" / "graphify-out"`. If it exists and is a directory, target it for removal.

4. **Safety Checks & Guardrails**:
   - **Path Traversal & Root Safeguard**: Ensure target directory `.resolve()` is strictly within `Path.cwd().resolve()` and is not equal to `Path.cwd().resolve()` or `(Path.cwd() / "graphify-out").resolve()`.
   - **Canonical Exclude Safeguard**: Explicitly assert `entry.name != "graphify-out"` so canonical output data is never deleted.
   - **Exception Resilience**: Wrap each `shutil.rmtree(target_dir)` call in `try...except Exception as exc:` and log warnings on failure so permissions/file locks do not crash task execution.
   - **Informative Logging**: Log logger.info messages for each pruned directory and summarize the total pruned count.

---

## 3. Caveats

- **Historical Data Removal**: Pruning `graphify-out-antigravity/` and `graphify-out/graphify-out/` permanently deletes those historical output files locally (~59MB total). Active graph data remains intact in canonical `graphify-out/`.
- **Concurrent File Handles**: If another active process has an open file handle inside `graphify-out/graphify-out/` or `graphify-out-antigravity/`, `shutil.rmtree` could raise an `OSError`/`PermissionError`. The proposed try-except guard catches this and logs a warning.
- **Scope Restriction**: This analysis is read-only; no edits to `src/agy_graphify/tasks.py` have been made in this phase.

---

## 4. Conclusion

### Exact Proposed Code for `clean_logs_action()` in `src/agy_graphify/tasks.py`

```python
async def clean_logs_action(*_params: str) -> None:
    import shutil
    import time
    from pathlib import Path

    root_dir = Path.cwd()

    # 1. Telemetry log cleanup (.gemini/telemetry)
    telemetry_dir = root_dir / ".gemini" / "telemetry"
    if telemetry_dir.exists():
        logger.info("Cleaning up process logs older than 7 days...")
        now = time.time()
        seven_days_ago = now - (7 * 24 * 60 * 60)
        log_count = 0
        for log_file in telemetry_dir.glob("proc_*.log"):
            if log_file.stat().st_mtime < seven_days_ago:
                try:
                    log_file.unlink()
                    log_count += 1
                except Exception as exc:
                    logger.warning(f"Failed to unlink process log {log_file.name}: {exc}")
        logger.info(f"Cleaned up {log_count} old process logs.")

    # 2. Legacy workspace directory automated pruning
    pruned_count = 0

    # Pattern A: Non-standard root-level graphify-out* directories (excluding canonical graphify-out)
    for entry in root_dir.glob("graphify-out*"):
        if entry.is_dir() and entry.name != "graphify-out":
            resolved = entry.resolve()
            # Safety check: path must be inside workspace root and must not equal workspace root
            if resolved != root_dir.resolve() and root_dir.resolve() in resolved.parents:
                try:
                    shutil.rmtree(entry)
                    pruned_count += 1
                    logger.info(f"Pruned legacy workspace directory: {entry.name}")
                except Exception as exc:
                    logger.warning(f"Failed to prune legacy directory {entry.name}: {exc}")

    # Pattern B: Nested graphify-out directory inside canonical graphify-out (graphify-out/graphify-out)
    canonical_out = root_dir / "graphify-out"
    if canonical_out.exists() and canonical_out.is_dir():
        nested_legacy = canonical_out / "graphify-out"
        if nested_legacy.exists() and nested_legacy.is_dir():
            resolved_nested = nested_legacy.resolve()
            if resolved_nested != canonical_out.resolve() and canonical_out.resolve() in resolved_nested.parents:
                try:
                    shutil.rmtree(nested_legacy)
                    pruned_count += 1
                    logger.info(f"Pruned nested legacy directory: {canonical_out.name}/{nested_legacy.name}")
                except Exception as exc:
                    logger.warning(f"Failed to prune nested legacy directory {nested_legacy.name}: {exc}")

    logger.info(f"Automated pruning complete. Pruned {pruned_count} legacy directory artifact(s).")
```

### Potential Side Effects & Assessment

| Side Effect | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| Deletion of legacy graph outputs | Deletes `graphify-out-antigravity/` and `graphify-out/graphify-out/` | Desired behavior per proposal; canonical `graphify-out/` is preserved. |
| Potential `OSError` if files are locked | Execution crash if unhandled | Handled cleanly via `try...except Exception` with `logger.warning`. |
| Missing `.gemini/telemetry` directory | Skipping pruning in current code | Removed early `return`; log cleanup and pruning run independently. |
| Accidental deletion of `graphify-out` | Loss of canonical knowledge graph | Guarded by `entry.name != "graphify-out"` and path ancestor verification. |

---

## 5. Verification Method

1. **Unit Test Verification**:
   - Run existing logging unit test:
     ```bash
     uv run pytest tests/test_process_logging.py
     ```
   - In new `tests/test_workspace_layout_standards.py`, add test cases:
     - Create dummy `graphify-out-antigravity` and `graphify-out/graphify-out` directories in `tmp_path`.
     - Invoke `clean_logs_action()`.
     - Assert `graphify-out-antigravity` and `graphify-out/graphify-out` no longer exist, while canonical `graphify-out` remains intact.

2. **Integration Verification Command**:
   ```bash
   uv run agy-task clean-logs
   ```
   Verify console/telemetry output reports pruning of `graphify-out-antigravity` and `graphify-out/graphify-out`.

3. **Workspace Layout Verification**:
   - Check workspace root:
     - `graphify-out/` exists.
     - `graphify-out-antigravity/` does NOT exist.
     - `graphify-out/graphify-out/` does NOT exist.

4. **Suite & Environment Guard Verification**:
   ```bash
   uv run pytest
   ALLOW_MAIN_COMMIT=1 uv run agy-verify
   ```
   Invalidation condition: Any test failure or `agy-verify` returning `decision: deny`.
