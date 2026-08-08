# DISPATCH

## 2026-08-07T21:37:11Z
Execute the proposed standard architecture enhancements per `docs/graphify_sources_proposal_architecture.md`:

1. Update `clean_logs_action()` in `src/agy_graphify/tasks.py`:
   - Add automated pruning of legacy workspace root directories (`graphify-out-antigravity/` and nested `graphify-out/graphify-out/`).

2. Add `tests/test_workspace_layout_standards.py`:
   - Add unit tests verifying:
     a) `graphify-out/` is the single canonical output directory at the workspace root.
     b) Zero non-standard `graphify-out*` folders exist.
     c) `ColibriExtractor` recognizes multi-modal extensions (`.py`, `.md`, `.pdf`, `.mp4`, `.mp3`, `.png`).

3. Complete Transition & Decommissioning:
   - Update `status: approved` in `docs/graphify_sources_proposal_architecture.md`.
   - Remove obsolete `docs/graphify_sources_current_architecture.md`.

4. Verification & PR creation:
   - Run full test suite (`uv run pytest`), verify `ALLOW_MAIN_COMMIT=1 uv run agy-verify` returns `decision: allow`.
   - Squash-merge changes to `main` via `uv run agy-task create-pr`.

## 2026-08-07T21:55:25Z
Execute Milestone 4 (E2E Verification & PR Creation):
1. Dispatch worker_m4 (teamwork_preview_worker) to:
   - Run full test suite (`uv run pytest`).
   - Verify `ALLOW_MAIN_COMMIT=1 uv run agy-verify` returns `decision: allow`.
   - Execute PR creation & merge via `uv run agy-task create-pr`.
2. Dispatch verification subagents (Reviewers, Challengers, Forensic Auditor) for Milestone 4.
3. Once all gate checks pass cleanly, write final handoff.md and report success to parent.
