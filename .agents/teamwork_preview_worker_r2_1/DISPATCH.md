## 2026-08-08T08:08:19Z
<USER_REQUEST>
You are teamwork_preview_worker_r2_1 operating in /Users/rmanaloto/agy-graphify-research.
Your assigned working directory is /Users/rmanaloto/agy-graphify-research/.agents/teamwork_preview_worker_r2_1.

Please read the following authoritative task instructions and prior reports before executing:
- ORIGINAL_REQUEST.md: /Users/rmanaloto/agy-graphify-research/.agents/ORIGINAL_REQUEST.md
- Victory Audit Failure Report: /Users/rmanaloto/agy-graphify-research/.agents/teamwork_preview_victory_auditor_m7_1/handoff.md
- Previous Orchestrator Progress: /Users/rmanaloto/agy-graphify-research/.agents/teamwork_preview_orchestrator_2/progress.md
- PR Skill Instructions: /Users/rmanaloto/agy-graphify-research/.agents/skills/pr/SKILL.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your objective:
1. Verify git status. Ensure raw/ subdirectories (raw/papers/.gitkeep, raw/media/.gitkeep, raw/web/.gitkeep, raw/images/.gitkeep) and tests/test_source_registry.py are staged/tracked in git.
2. Run unit test suite `uv run pytest` and verify 135+ tests pass cleanly.
3. Perform the full PR lifecycle following /Users/rmanaloto/agy-graphify-research/.agents/skills/pr/SKILL.md:
   a) Clean up any broken rebase state (git rebase --abort if needed).
   b) Checkout main and pull rebased origin main (ALLOW_MAIN_COMMIT=1 uv run agy-task sync-main or git checkout main && git pull --rebase origin main). Use BypassSandbox: true when running remote git operations.
   c) Create feature branch: git checkout -b feat/multimodal-sources-layout.
   d) Stage all changes: git add -A.
   e) Commit changes: git commit -m "feat(sources): refactor multi-modal sources directory layout and registry scanning".
   f) Create PR using ALLOW_MAIN_COMMIT=1 uv run agy-task create-pr feat/multimodal-sources-layout or gh pr create --fill --head feat/multimodal-sources-layout. Make sure create_pr_action actually succeeds and does not fail silently.
   g) Merge PR to remote main: gh pr merge feat/multimodal-sources-layout --squash --delete-branch.
   h) Rebase local main and delete local feature branch: git checkout main && git pull --rebase origin main && git branch -D feat/multimodal-sources-layout.
   i) Confirm git status shows a clean working workspace on main.
4. Run uv run agy-task clean-logs to prune/sanitize any telemetry logs that might cause the Fail-Fast Watchdog to trigger.
5. Run ALLOW_MAIN_COMMIT=1 uv run agy-verify and confirm it returns {"decision":"allow",...}.
6. Write a complete handoff report to /Users/rmanaloto/agy-graphify-research/.agents/teamwork_preview_worker_r2_1/handoff.md detailing:
   - Git log HEAD on main
   - Git status output
   - Pytest output and pass count
   - ALLOW_MAIN_COMMIT=1 uv run agy-verify JSON output showing decision: allow
   - PR URL and merge confirmation details
7. Send a message to orchestrator upon completion.
</USER_REQUEST>
