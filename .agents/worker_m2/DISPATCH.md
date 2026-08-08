## 2026-08-07T21:43:29Z
You are teamwork_preview_worker for Milestone 2 (Workspace Layout Test Suite).
Working Directory: /Users/rmanaloto/agy-graphify-research/.agents/worker_m2

Read the original user request at /Users/rmanaloto/agy-graphify-research/.agents/ORIGINAL_REQUEST.md.
Also read explorer handoff reports at:
- /Users/rmanaloto/agy-graphify-research/.agents/explorer_survey_2/handoff.md
- /Users/rmanaloto/agy-graphify-research/.agents/worker_m1/handoff.md

Your tasks for Milestone 2:
Add `tests/test_workspace_layout_standards.py` containing unit tests verifying:
a) `graphify-out/` is the single canonical output directory at workspace root.
b) Zero non-standard `graphify-out*` folders exist at workspace root or nested inside `graphify-out/`.
c) `clean_logs_action()` automatically prunes legacy directories (`graphify-out-antigravity/` and `graphify-out/graphify-out/`) using tmp_path and monkeypatch.
d) `ColibriExtractor` recognizes multi-modal extensions (`.py`, `.md`, `.pdf`, `.mp4`, `.mp3`, `.png`).
e) `ColibriExtractor.extract_directory` scans and indexes multi-modal files in a directory.

File you exclusively own for editing:
- `tests/test_workspace_layout_standards.py`

DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Run `uv run pytest tests/test_workspace_layout_standards.py` and `uv run pytest` to verify 100% pass rate.
Write your completion report to /Users/rmanaloto/agy-graphify-research/.agents/worker_m2/handoff.md and report back via send_message.
