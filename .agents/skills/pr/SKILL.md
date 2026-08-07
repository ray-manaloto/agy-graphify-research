---
name: pr
description: Rebase-first PR workflow skill to create feature branches off main, stage PRs via gh CLI, and return workspace to main.
---

# PR Workflow Skill (`pr`)

1. **Rebase & Checkout Main**:
   - Always ensure local `main` is updated and rebased against `origin/main` before branching.
   - Run `git checkout main && git pull --rebase origin main` (or `uv run agy-task sync-main`).

2. **Create Feature Branch**:
   - Create a fresh feature branch off rebased `main`:
     `git checkout -b feat/<feature-name>`

3. **Stage, Commit & Create PR**:
   - Stage changes cleanly: `git add -A`
   - Commit with descriptive message: `git commit -m "feat(...): ..."`
   - Create PR using gh CLI wrapper: `uv run agy-task create-pr feat/<feature-name>` or `gh pr create --fill --head feat/<feature-name>`.

4. **Return Workspace to Main**:
   - Immediately switch back to `main` after staging the PR so the active working environment remains on a clean `main`:
     `git checkout main`

5. **Verify Clean State**:
   - Run `uv run agy-verify` to ensure zero `.sh` shell script violations and clean environment state on `main`.
