## 2026-08-08T03:21:53Z
You are a Worker subagent (Worker 3).
Working directory: /Users/rmanaloto/agy-graphify-research/.agents/teamwork_preview_worker_m4_1
Original Request Path: /Users/rmanaloto/agy-graphify-research/.agents/ORIGINAL_REQUEST.md
PROJECT.md Path: /Users/rmanaloto/agy-graphify-research/.agents/teamwork_preview_orchestrator_2/PROJECT.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your Task (Milestone 4):
1. Update `tests/test_workspace_layout_standards.py`:
   - Add unit tests verifying:
     a) `raw/papers/.gitkeep`, `raw/media/.gitkeep`, `raw/web/.gitkeep`, `raw/images/.gitkeep` exist at workspace root.
     b) `config/sources.json` is version `1.1.0` and contains explicit `sources` mappings (`git_repositories`, `raw_papers`, `raw_media`, `raw_web`, `raw_images`).

2. Run full unit test suite via `uv run pytest`. Verify 130+ tests pass cleanly (100% pass rate).
3. Run environment verifier: `ALLOW_MAIN_COMMIT=1 uv run agy-verify`. Verify `decision: allow`.
4. Create PR and squash-merge into `main`:
   - Follow project PR rules: use `uv run agy-task create-pr` or standard PR workflow (`git checkout main && git pull --rebase origin main` -> feature branch -> `gh pr create` -> `gh pr merge --squash --delete-branch` -> return workspace to `main`).
   - If using `uv run agy-task create-pr`, supply branch name (e.g. `feat/multimodal-sources-layout`).

5. Report complete status, test results, verifier output, and PR merge status in `.agents/teamwork_preview_worker_m4_1/handoff.md` and `.agents/teamwork_preview_worker_m4_1/progress.md`.
Send a message back when done.
